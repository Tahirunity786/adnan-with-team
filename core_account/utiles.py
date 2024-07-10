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
def send_otp_email(user, otp, new_register=False):
    try:
        """
        Helper function to send OTP via email.
    
        Parameters:
        - user (User): The user object.
        - subject (str): The subject of the email.
        - message (str): The message body containing the OTP.
        """
        subject = "Welcome to ADN - Your OTP for Secure Access"
        if new_register:
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
                        <p><a href="https://adn.social">www.adn.social</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            
            html_content = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>OTP Verification</title>
                    <style>
                        body {{
                            font-family: 'Arial', sans-serif;
                            background-color: #f4f4f4;
                            margin: 0;
                            padding: 0;
                        }}
                        .container {{
                            background-color: #ffffff;
                            padding: 20px;
                            border-radius: 8px;
                            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                            max-width: 600px;
                            margin: 40px auto;
                        }}
                        .header {{
                            text-align: center;
                            background-color: #007bff;
                            color: #ffffff;
                            padding: 20px;
                            border-radius: 8px 8px 0 0;
                        }}
                        .header img {{
                            max-width: 100px;
                            margin-bottom: 10px;
                        }}
                        .content {{
                            margin-top: 20px;
                            color: #333333;
                        }}
                        .content p {{
                            font-size: 16px;
                            line-height: 1.6;
                        }}
                        .otp {{
                            background-color: #007bff;
                            color: #ffffff;
                            font-size: 24px;
                            padding: 15px;
                            border-radius: 4px;
                            text-align: center;
                            margin: 20px 0;
                            font-weight: bold;
                            letter-spacing: 2px;
                        }}
                        .footer {{
                            margin-top: 20px;
                            text-align: center;
                            font-size: 12px;
                            color: #777777;
                        }}
                        .footer a {{
                            color: #007bff;
                            text-decoration: none;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <img src="https://www.yourwebsite.com/logo.png" alt="ADN Logo" />
                        </div>
                        <div class="content">
                            <p>Hi {user.full_name},</p>
                            <p>We received a request for OTP verification.</p>
                            <p>Here is your OTP:</p>
                            <div class="otp">{otp}</div>
                            <p>Please note that the OTP will expire in 5 minutes.</p>
                        </div>
                        <div class="footer">
                            <p>If you did not request this, please ignore this email or contact support.</p>
                            <p><a href="https://adn.social">www.adn.social</a></p>
                        </div>
                    </div>
                </body>
                </html>
                """

 
        mail = MailAgent()
        handle_mail = mail.mailer(user, subject, html_content)
        return handle_mail
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}", exc_info=True)
        return False

def rest_password_otp(user, link):
    subject = "ADN - Password Reset Request"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Password</title>
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                background-color: #ffffff;
                padding: 20px;
                border: 1px solid #dddddd;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                max-width: 600px;
                margin: 40px auto;
            }}
            .header {{
                text-align: center;
                background-color: #000000;
                color: #ffffff;
                padding: 20px;
                border-radius: 8px 8px 0 0;
            }}
            .header img {{
                max-width: 100px;
                margin-bottom: 10px;
            }}
            .content {{
                margin-top: 20px;
                color: #333333;
            }}
            .content p {{
                font-size: 16px;
                line-height: 1.6;
            }}
            .button-container {{
                text-align: center;
                margin-top: 20px;
            }}
            .button {{
                background-color: #ffffff;
                color: #000000;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 5px;
                border: 1px solid #000000;
                font-size: 16px;
                display: inline-block;
            }}
            .button:hover {{
                background-color: #000000;
                color: #ffffff;
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
            .footer a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://www.yourwebsite.com/logo.png" alt="ADN Logo" />
                <h2>Password Reset</h2>
            </div>
            <div class="content">
                <p>Hi {user.full_name},</p>
                <p>You requested to reset your password. Please click the button below to proceed with the password reset.</p>
                <div class="button-container">
                    <a href="{link}" class="button">Reset Password</a>
                </div>
            </div>
            <div class="footer">
                <p>If you did not request this, please ignore this email or contact support.</p>
                <p>The link will expire after 30 minutes.</p>
                <p><a href="https://adn.social">www.adn.social</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    mail = MailAgent()
    handle_mail = mail.mailer(user, subject, html_content)
    return handle_mail

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