
import datetime
import os
import random
import string
from urllib.parse import urlparse
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from core_account.renderers import UserRenderer
from rest_framework.views import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from google.auth.transport import requests
from google.oauth2.id_token import verify_oauth2_token
import requests as efwe
from django.core.files.base import ContentFile
from requests.exceptions import HTTPError
from rest_framework import generics
from social_django.utils import load_strategy, load_backend
from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import MissingBackend, AuthTokenError, AuthForbidden
from django.contrib.auth import get_user_model
from core_account.token import get_tokens_for_user
from core_account.utiles import send_otp_email, get_user_by_identifier
from core_account.utiles import generate_otp
from django.contrib.auth import login, authenticate
from core_account.serializers import ForgotPasswordSerializer, UserSerializer, ResetPasswordSerializer
from django.contrib.auth.hashers import make_password
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.utils.translation import gettext as _
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from rest_framework.decorators import api_view

from core_account.serializers import (
    CreateUserSerializer,
    SocialSerializer,
)

User = get_user_model()
# =================== ACCOUNT MANAGEMENT SECTION # =================== #

class CreateUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = CreateUserSerializer(data=request.data)

        if serializer.is_valid():
            validated_data = serializer.validated_data
            interests_data = validated_data.pop('Interest', [])
            account = serializer.save()
            interest_names = [interest_obj.interests for interest_obj in interests_data]
            account.Interest.add(*interests_data)

            # Generate OTP
            otp = generate_otp()
            
            send_otp_email(account, otp)
           
            account.otp = otp
            account.save()
            
           

            response_data = {
                'response': 'Account has been created',
                'id': account.id,
                'username': account.username,
                'email': account.email,
                'interests': interest_names,
                
            }

            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Email for this user not found"}, status=status.HTTP_400_BAD_REQUEST)

        authenticated_user = authenticate(request, username=user.email, password=password)

        if authenticated_user is None:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if authenticated_user.two_factor_auth:
            otp = generate_otp()
            subject = 'Your OTP for two-factor authentication'
            message = f'Your OTP is: {otp}'
            send_otp_email(authenticated_user, subject, message)

            # Save OTP to the authenticated user instance
            user.otp = otp
            user.save()

            return Response({"message": "Two-factor authentication OTP sent"}, status=status.HTTP_200_OK)

        if not authenticated_user.is_verified:
            return Response({"error": "Account not verified"}, status=status.HTTP_400_BAD_REQUEST)

        if authenticated_user.is_blocked:
            return Response({"error": "Account banned"}, status=status.HTTP_400_BAD_REQUEST)

        profile_url = settings.BACKEND + authenticated_user.profile.url if authenticated_user.profile else None
        token = get_tokens_for_user(authenticated_user)

        interests = list(authenticated_user.Interest.all().values_list('interests', flat=True))

        user_data = {
            "user_id": authenticated_user.id,
            "username": authenticated_user.username,
            "profile": profile_url,
            "fullname": authenticated_user.full_name,
            "info": authenticated_user.profile_info if authenticated_user.profile_info else None,
            "interests": interests,
            "token": token,
            "two-factor-auth": authenticated_user.two_factor_auth
        }

        return Response({"message": "Logged in", "user": user_data}, status=status.HTTP_202_ACCEPTED)

class GoogleAuthAPIView(APIView):
    """
    Google Authentication API View.
    """

    def post(self, request):
        """
        Authenticate user using Google ID token.

        Args:
            request: HTTP request object containing ID token.

        Returns:
            HTTP response with user data and authentication token.
        """
        id_token = request.data.get('idToken')

        try:
            # Verify the ID token
            id_info = verify_oauth2_token(id_token, requests.Request())

            # Get user info
            user_email = id_info.get('email')
            user_image_url = id_info.get('picture')
            name = id_info.get('name')

            if not user_email:
                return Response({"error": "Email not provided in ID token"}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the user exists in the database, or create a new one
            try:
                user = User.objects.get(email=user_email)
                created = False
            except User.DoesNotExist:
                # Generate a random username and password for new user
                username = user_email.split('@')[0]
                password = ''.join(random.choices(
                    string.ascii_letters + string.digits, k=12))
                user = User.objects.create_user(
                    email=user_email, username=username, password=password, full_name=name)
                created = True
            # Download and save the profile picture if available
            if user_image_url:
                try:
                    image_response = efwe.get(user_image_url)
                    image_response.raise_for_status()  # Raise exception for non-200 status codes
                    file_extension = os.path.splitext(
                        urlparse(user_image_url).path)[1] or '.jpg'
                    random_filename = ''.join(random.choices(
                        string.ascii_letters + string.digits, k=12))
                    file_path = os.path.join(
                        settings.MEDIA_ROOT, random_filename + file_extension)
                    with open(file_path, 'wb') as f:
                        f.write(image_response.content)
                    user.profile.save(random_filename + file_extension,
                                      ContentFile(image_response.content), save=True)
                except (requests.RequestException, IOError) as e:
                    return Response({"error": f"Error while fetching image: {e}"}, status=status.HTTP_400_BAD_REQUEST)

            # Generate authentication token
            token = get_tokens_for_user(user)

            # Construct response data
            response_data = {
                'response': 'Account Created' if created else 'Account Logged In',
                'id': user.id,
                'username': user.username,
                'profile_image': user.profile.url if user.profile else None,
                'email': user.email,
                'token': token
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as e:
            # Invalid token
            return Response({"error": f"Invalid token: {e}"}, status=status.HTTP_400_BAD_REQUEST)


class VerifyOtp(APIView):
    """
    API endpoint to verify OTP (One Time Password) for user authentication.

    This endpoint verifies whether the provided OTP matches the OTP associated
    with the user account and marks the user as verified if the OTP is valid.

    Request Parameters:
        - username: The username or email of the user.
        - otp: The One Time Password to verify.

    Returns:
        - HTTP 202 ACCEPTED if OTP is valid and user is marked as verified.
        - HTTP 400 BAD REQUEST with an error message if:
            - Username or OTP is not provided.
            - User is not found.
            - OTP is invalid or expired.
            - Any other error occurs during processing.

    Permissions:
        - This endpoint allows any user to access it.

    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handles POST requests to verify OTP for user authentication.

        Args:
            request: HTTP request object containing username and OTP.

        Returns:
            HTTP response indicating the status of OTP verification.

        """
        # Extracting username and OTP from request data
        username = request.data.get('email')
        otp = request.data.get('otp')
        if username and otp:
            try:
                # Check if the provided username is an email or username
                if '@' in username:
                    usr = User.objects.get(email=username)
                else:
                    usr = User.objects.get(username=username)

                # Check if the OTP matches
                if str(usr.otp) == otp:
                    current_time = datetime.datetime.now().time()

                    # Check if OTP delay is within 5 minutes
                    if (current_time.minute - usr.otp_delay.minute) > 5:
                        return Response(
                            status=status.HTTP_400_BAD_REQUEST,
                            data={"message": "Otp Expired"},
                        )

                    # Mark user as verified
                    usr.is_verified = True
                    usr.save()
                    return Response(
                        status=status.HTTP_202_ACCEPTED,
                        data={"message": "Account verified"},
                    )
                else:
                    return Response(
                        status=status.HTTP_400_BAD_REQUEST,
                        data={"message": "Invalid Otp"},
                    )
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"message": "User not found"},
                )
            except Exception as e:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"message": f"An error occurred: {str(e)}"},
                )
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Username and OTP are required fields"},
            )


class GetNewOtp(APIView):
    """
    API endpoint to generate and send a new OTP (One-Time Password) for account verification via email.
    """
    permission_classes = [
        AllowAny]  # Allow any user, authenticated or not, to access this endpoint.

    def post(self, request):
        """
        POST method to handle the generation and sending of a new OTP.

        Parameters:
        - request: HTTP request object containing user data.

        Returns:
        - Response: HTTP response indicating the success or failure of the OTP generation and sending process.
        """
        try:
            # Extracting the username or email from the request data
            query = request.data.get('username')
            usr = get_user_by_identifier(query)

            if usr is None:
                # If user is not found, return a 400 Bad Request response with a relevant message
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": "User with provided credentials not found"})

            # Checking OTP limit
            if usr.otp_limit is not None and usr.otp_limit >= 30:
                # If OTP limit has been reached or exceeded, return a 400 Bad Request response with a relevant message
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": "Otp Limit Ended, please try with another email!"})

            # Sending a new OTP for account verification via email
            subject = 'Account Verification: Social Media'
            otp = generate_otp()
            message = f'Your Account is created, please verify with this OTP {otp}. Otp will expire within 5 minutes.'

            # Assign the generated OTP to the user instance
            usr.otp = otp

            # Incrementing OTP limit if it's not None
            if usr.otp_limit is not None:
                usr.otp_limit += 1
            else:
                # If OTP limit is None, initialize it to 1
                usr.otp_limit = 1

            usr.save()  # Saving the updated user instance
            # Send the OTP email to the user
            send_otp_email(usr, subject, message)

            return Response(status=status.HTTP_200_OK, data={"message": f"Otp sent to {usr.email}"})
        except Exception as e:
            # Catch any exceptions that occur during the process and return a 400 Bad Request response with a generic error messag
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": f"An error occurred while processing the request"})


class SocialLoginView(generics.GenericAPIView):
    """Log in using Facebook"""

    # Assuming SocialSerializer is defined elsewhere
    serializer_class = SocialSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        """Authenticate user through the provider and access_token"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.validated_data.get(
            'provider')  # Use validated_data instead of data
        access_token = serializer.validated_data.get(
            'access_token')  # Use validated_data instead of data

        strategy = load_strategy(request)

        try:
            backend = load_backend(
                strategy=strategy, name=provider, redirect_uri=None)
        except MissingBackend:
            return Response({'error': 'Please provide a valid provider'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if isinstance(backend, BaseOAuth2):
                user = backend.do_auth(access_token)
        except (HTTPError, AuthTokenError, AuthForbidden) as error:
            return Response({'error': 'Invalid credentials', 'details': str(error)}, status=status.HTTP_400_BAD_REQUEST)

        if user and user.is_active:
            # Generate JWT token
            login(request, user)
            # Assuming get_tokens_for_user is defined elsewhere
            token = get_tokens_for_user(user)

            # Customize the response
            response_data = {
                'email': user.email,
                'username': user.username,
                'token': token
            }
            return Response(response_data, status=status.HTTP_200_OK)

        return Response({'error': 'Failed to authenticate user'}, status=status.HTTP_400_BAD_REQUEST)


class UserSearchView(generics.ListAPIView):
    """
    View for searching/filtering user accounts by username.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]  # Adjust permissions as needed

    def get_queryset(self):
        """
        Get queryset filtered by username.
        """
        username = self.request.data.get('username', None)
        if username:
            return User.objects.filter(username__icontains=username).order_by("-id")
        return User.objects.none()  # Return an empty queryset if no username provided

class MutePeopleView(APIView):
    """
    API endpoint for muting/unmuting a user.

    Permissions:
        - User must be authenticated.

    Request Method:
        - POST

    Request Payload:
        - user_id: ID of the user to be muted.

    logic:
        Muted people can't able to  see user's post, comment, story

    Response:
        - HTTP 200 OK: If the user is successfully muted/unmuted.
        - HTTP 404 Not Found: If the user with the given ID does not exist.
        - HTTP 400 Bad Request: If the request payload is invalid or incomplete.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Method to mute/unmute a user.

        Args:
            request (HttpRequest): HTTP request object.

        Returns:
            Response: JSON response indicating success or failure.
        """
        user = request.user
        mute_user_id = request.data.get("user_id")

        if not mute_user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        d_user = get_object_or_404(User, id=mute_user_id)

        # Check if the user is already muted or not
        if d_user in user.mute_peoples.all():
            user.mute_peoples.remove(d_user)
            action = "unmuted"
        else:
            # Only following people along with user will be muted
            if d_user in user.following.all():
                user.mute_peoples.add(d_user)
                action = "muted"
            else:
                return Response({"message": "You can only mute users you are following."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": f"User {d_user.username} has been {action}."}, status=status.HTTP_200_OK)


class BlockedPeopleView(APIView):
    """
    API endpoint for Blocked/Unblocked a user.

    Permissions:
        - User must be authenticated.

    Request Method:
        - POST

    Request Payload:
        - user_id: ID of the user to be Block.

    Response:
        - HTTP 200 OK: If the user is successfully block/unblock.
        - HTTP 404 Not Found: If the user with the given ID does not exist.
        - HTTP 400 Bad Request: If the request payload is invalid or incomplete.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Method to block/unblock a user.

        Args:
            request (HttpRequest): HTTP request object.

        Returns:
            Response: JSON response indicating success or failure.
        """
        user = request.user
        blocked_user_id = request.data.get("user_id")

        if not blocked_user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        b_user = get_object_or_404(User, id=blocked_user_id)

        # Logic to mute/unmute the user (modify as needed)
        if b_user in user.blockek_peoples.all():
            user.blockek_peoples.remove(b_user)
            action = "Unblock"
        else:
            user.blockek_peoples.add(b_user)
            action = "Block"

        return Response({"message": f"User {b_user.username} has been {action}."}, status=status.HTTP_200_OK)


class MakeaccoutPrivate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Logic to Private/Public the user account (modify as needed)
        if user.account_mode == "Private":
            user.account_mode = "Public"
            action = "Public"
        else:
            user.account_mode = "Private"
            action = "Private"

        user.save()

        return Response({"message": f"User {user.username} has been set to {action} mode."}, status=status.HTTP_200_OK)

# ==================================== Acount settings area ==================================== #


class ChangePasswordAccount(APIView):
    """
    API endpoint for changing user's account password.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        POST method to change user's account password.

        Args:
            request (HttpRequest): HTTP request object.

        Returns:
            Response: Response indicating success or failure.
        """
        # Retrieve current user
        user = request.user

        # Retrieve old password, new password, and confirm password from request data
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        # Check if new password and confirm password match
        if new_password != confirm_password:
            return Response({"error": "New password and confirm password do not match."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if old password is correct
        if not user.check_password(old_password):
            return Response({"error": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        # Set new password
        user.password = make_password(new_password)
        user.save()

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


class DeactvateAccount(APIView):
    """
    API endpoint for deleting a user account.

    Only authenticated users can access this endpoint.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handle POST request to delete user account.

        Args:
            request: HTTP request object.

        Returns:
            Response: JSON response indicating success or failure of account deletion.
        """
        user = request.user

        try:
            # Assuming you have a soft delete mechanism, such as setting is_active to False
            user.is_active = False
            user.save()

            return Response({"detail": "Account successfully deleted."}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"detail": "Failed to delete account.", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForgotPassword(APIView):
    """
    API endpoint to handle forgot password functionality.
    """

    def post(self, request):
        """
        Handle POST request for forgot password functionality.

        Args:
            request: HTTP request object.

        Returns:
            HTTP response indicating success or failure.
        """
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user_email = serializer.validated_data['email']
            user = User.objects.filter(email=user_email).first()
            if user:
                # Generate a password reset token
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                # Create password reset link
                reset_link = request.build_absolute_uri(
                    reverse('reset_password', kwargs={
                            'uidb64': uid, 'token': token})
                )

                # Send password reset email
                subject = _('Password Reset Request')
                message = f"Please click the following link to reset your password: {reset_link}"
                from_email = settings.EMAIL_HOST_USER
                to_email = user_email
                send_mail(subject, message, from_email, [to_email])

                return Response({'detail': _('Password reset email has been sent.')}, status=status.HTTP_200_OK)
            else:
                return Response({'error': _('User with this email does not exist.')}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPassword(APIView):
    """
    API endpoint to handle resetting password.
    """
    # def get(request):
    #     """_summary_

    #     Here you will able to add rest_password_page
    #     """
    #     pass

    def post(self, request, uidb64, token):
        """
        Handle POST request for resetting password.
        """
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            uid = uidb64
            new_password = serializer.validated_data['new_password']

            # Decode uid to get user id
            try:
                user_id = str(urlsafe_base64_decode(uid), 'utf-8')
                user = User.objects.get(pk=user_id)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None

            # Check if user is valid
            if user is not None and default_token_generator.check_token(user, token):
                # Set new password
                user.set_password(new_password)
                user.save()
                return Response({'detail': _('Password has been reset successfully.')}, status=status.HTTP_200_OK)
            else:
                return Response({'error': _('Invalid user or token.')}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def verify_2fa(request):
    """
    Verify two-factor authentication (2FA) for user login.

    Args:
        request: Django request object containing user email and OTP.

    Returns:
        Response: JSON response indicating login success or failure.
    """

    if request.method != "POST":
        return Response({"Error": "Only POST method allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    email = request.data.get('email')
    otp = request.data.get('otp')

    # Check if email and OTP are provided
    if not email:
        return Response({"Error": "Email not provided"}, status=status.HTTP_400_BAD_REQUEST)
    if not otp:
        return Response({"Error": "OTP not provided"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"Error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"Error": f"Error retrieving user: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Check if provided OTP matches user's OTP
    if str(user.otp) != otp:
        return Response({"Error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if OTP is expired
    current_time = datetime.datetime.now().time()
    if (current_time.minute - user.otp_delay.minute) > 5:
        return Response({"Error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

    # Generate system token and prepare user data for response
    sys_token = get_tokens_for_user(user)
    profile_url = settings.BACKEND + user.profile.url if user.profile else None
    user_data = {
        "user_id": user.id,
        "username": user.username,
        "profile": profile_url,
        "fullname": user.full_name,
        "info": user.profile_info if user.profile_info else None,
        "token": sys_token,
        "two-factor-auth":user.two_factor_auth

    }

    return Response({"Success": "Logged in", "user": user_data}, status=status.HTTP_202_ACCEPTED)


@api_view(['POST'])
def enable_2fa(request):
    """
    Enable two-factor authentication for a user's account.

    Args:
        request: Django request object containing user email and preferred 2FA method.

    Returns:
        Response: JSON response indicating the success or failure of enabling 2FA.

    Procedure / Logic:
            The User when want to enable the 2fa then user will email will provide and method also provide such as Email, SMS, Whatsapp that will use to verify.


    """
    if request.method == 'POST':
        email = request.data.get('email')
        method = request.data.get('method')

        # Check if email and method are provided
        if not email or not method:
            return Response({"error": "Email and method are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the method is valid
        valid_methods = [choice[0] for choice in User.TWOFAUTH]
        if method not in valid_methods:
            return Response({"error": "Invalid method."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the user
            user = User.objects.get(email=email)

            # Generate OTP
            generated_otp = generate_otp()
            subject = 'Verify Identity'
            message = f'Your two-factor authentication code is {generated_otp}. Opt will expire in 5 minutes.'
            otp_sent = send_otp_email(user, subject, message)

            if not otp_sent:
                return Response({"error": "Failed to send OTP"}, status=status.HTTP_400_BAD_REQUEST)

            # Save method
            user.two_factor_auth_method = method
            # Store OTP in user object temporarily
            user.otp = generated_otp
            user.save()

            return Response({"message": f"OTP sent to {user.email}. Verify to enable 2FA."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({"error": "Only POST method allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
def catch_and_enable_2fa(request):
    """
    Verify OTP and enable two-factor authentication for the user.

    Args:
        request: Django request object containing user email and OTP.

    Returns:
        Response: JSON response indicating the success or failure of enabling 2FA.
    """
    if request.method == 'POST':
        email = request.data.get('email')
        otp = request.data.get('otp')

        # Check if email and OTP are provided
        if not email or not otp:
            return Response({"error": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the user
            user = User.objects.get(email=email)

            # Check if OTP matches
            if str(user.otp) == otp:
                # Check if OTP is expired
                current_time = datetime.datetime.now().time()
                if (current_time.minute - user.otp_delay.minute) > 5 or not user.otp:
                    return Response({"Error": "OTP expired or not valid."}, status=status.HTTP_400_BAD_REQUEST)

                # Enable 2FA for the user
                user.two_factor_auth = True
                user.save()

                # Clear OTP
                user.otp = None
                user.save()

                return Response({"message": "Two-factor authentication enabled successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({"error": "Only POST method allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class TurnOffTwoFactorAuth(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.two_factor_auth:
            return Response({"error": "Two-factor authentication is already disabled for this user."}, status=status.HTTP_400_BAD_REQUEST)

        # Disable two-factor authentication
        user.two_factor_auth = False
        user.two_factor_auth_method = None  # Reset two-factor authentication method if desired
        user.save()

        return Response({"message": "Two-factor authentication disabled successfully."}, status=status.HTTP_200_OK)