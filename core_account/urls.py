from django.urls import path
from core_account.views import (ChangePasswordAccount,TurnOffTwoFactorAuth, CreateUserView, DeactvateAccount, ForgotPassword, GoogleAuthAPIView, GetNewOtp, ResetPassword, VerifyOtp, UserLogin, UserSearchView, MutePeopleView, BlockedPeopleView, MakeaccoutPrivate)
from core_account.views import verify_2fa, enable_2fa, catch_and_enable_2fa
urlpatterns = [
    # Endpoint for Google authentication
    path("public/auth/u/google", GoogleAuthAPIView.as_view(), name="new-user-google"),

    # Endpoint for user registration
    path("public/u/register", CreateUserView.as_view(), name="new-user"),

    # Endpoint for user login
    path("public/u/login", UserLogin.as_view(), name="user-login"),
    # Endpoint for user who enabled the 2fa and verify otp then login
    path("public/u/verify-login-2fa", verify_2fa, name="verify-2fa"),

    # Endpoint for generating a new OTP (One Time Password)
    path("public/u/auth/getnewotp", GetNewOtp.as_view(), name="account-otp"),

    # Endpoint for verifying OTP during user registration
    path("public/u/auth/verify", VerifyOtp.as_view(), name="new-user-verify"),

    # Endpoint for searching user accounts
    path('public/u/search/account', UserSearchView.as_view(), name='search-account'),

    # Endpoint for Mute and Unmute peoples
    path('public/u/mute', MutePeopleView.as_view(), name='mute-account'),
    path('public/u/unmute', MutePeopleView.as_view(), name='unmute-account'),

    # Endpoint for Block and UnBlock peoples
    path('public/u/block', BlockedPeopleView.as_view(), name='block-account'), # Use For message logic
    path('public/u/unblock', BlockedPeopleView.as_view(), name='unblock-account'),  # Use For message logic
    # Endpoint for make account private/ public
    path('public/u/account/make-private', MakeaccoutPrivate.as_view(), name='private-account'),
    path('public/u/account/make-public', MakeaccoutPrivate.as_view(), name='public-account'),


    # ==================================== Acount settings area ==================================== #

    # Enpoint to change password
    path('public/u/changepassword', ChangePasswordAccount.as_view(), name='change-pass-account'),
    # Endpoint to deactivate accuont
    path('public/u/deactivate', DeactvateAccount.as_view(), name='deactivate-account'),
    # Endpoint to forgot password
    path('public/u/forgotpassword', ForgotPassword.as_view(), name='forgot-account-password'),
    # Endpoint to forgot password utile
    path('resetpassword/<str:uidb64>/<str:token>/', ResetPassword.as_view(), name='reset_password'),
    # Endpoint for user who want to enabled the 2fa
    path("public/u/enable-2fa", enable_2fa, name="enable-2fa"),
    # Endpoint for user who want to disable the 2fa
    path("public/u/disable-2fa", TurnOffTwoFactorAuth.as_view(), name="disable-2fa"),
    # Endpoint for user who want to enabled the 2fa and verify otp then the 2 factor authentication wil enable
    path("public/u/verify-enabled-2fa", catch_and_enable_2fa, name="verify-enabled-2fa"),
]
