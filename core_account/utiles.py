import random
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .agent import MailAgent
UserModel = get_user_model()

logger = logging.getLogger(__name__)
# Helper for sending mail for OTP
def send_otp_email(user, otp):
    try:
        """
        Helper function to send OTP via email.
    
        Parameters:
        - user (User): The user object.
        - subject (str): The subject of the email.
        - message (str): The message body containing the OTP.
        """
        subject = "Welcome to ADN - Your OTP for Secure Access"
        params={"name": f"{user.full_name}"}
        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    background-color: #ffffff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    max-width: 600px;
                    margin: auto;
                }}
                .header {{
                    text-align: center;
                    background-color: #000000;
                    color: #ffffff;
                    padding: 20px;
                    border-radius: 10px 10px 0 0;
                }}
                .header img {{
                    max-width: 150px;
                    margin-bottom: 10px;
                }}
                .content {{
                    margin-top: 20px;
                }}
                .content p {{
                    font-size: 16px;
                    line-height: 1.5;
                    color: #333333;
                }}
                .otp {{
                    background-color: #000000;
                    color: #ffffff;
                    font-size: 24px;
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #777777;
                }}
                .footer a {{
                    color: #000000;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="https://www.yourwebsite.com/logo.png" alt="ADN Logo" />
                    <h1>Welcome to ADN</h1>
                </div>
                <div class="content">
                    <p>Dear {user.full_name},</p>
                    <p>We are delighted to welcome you to ADN!</p>
                    <p>Thank you for registering with us. We are committed to providing you with the best services and a seamless experience. Whether you are here to explore, learn, or achieve new milestones, we are here to support you every step of the way.</p>
                    <p>To help you get started, here are a few resources you might find useful:</p>
                    <ul>
                        <li><a href="https://www.yourwebsite.com/user-guide">User Guide</a></li>
                        <li><a href="https://www.yourwebsite.com/faq">FAQ</a></li>
                        <li><a href="mailto:tahirunity786@gmail.com">Customer Support</a></li>
                    </ul>
                    <p>If you have any questions or need assistance, please do not hesitate to contact our support team at <a href="mailto:support@adn.com">support@adn.com</a> or call us at (123) 456-7890. We are here to help you 24/7.</p>
                    <p>Here is your OTP:</p>
                    <div class="otp">{otp}</div>
                    <p>Once again, welcome to our community! We look forward to a successful journey together.</p>
                </div>
                <div class="footer">
                    <p>Best Regards,</p>
                    <p>ADN Team</p>
                    <p><a href="https://www.yourwebsite.com">www.yourwebsite.com</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        mail = MailAgent()
        handle_mail = mail.mailer(user, params, subject, html_content)
        print(handle_mail)
        return handle_mail
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}", exc_info=True)
        return False

def get_user_by_identifier(identifier):
    """
    Retrieve a user by email or username.

    Parameters:
    - identifier (str): The email or username used to identify the user.

    Returns:
    - User: The user corresponding to the provided identifier.

    Raises:
    - Http404: If no user is found with the given identifier.
    """
    if '@' in identifier:
        # If '@' is present, assume the identifier is an email
        return get_object_or_404(UserModel, email=identifier)
    else:
        # Otherwise, assume the identifier is a username
        return get_object_or_404(UserModel, username=identifier)


def generate_otp():
    """
    Generate a six-digit OTP code.
    """
    return ''.join(random.choices('0123456789', k=6))