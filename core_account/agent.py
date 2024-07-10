import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class MailAgent:

    def mailer(self, user, *args):
        # Create an instance of the API class
        try:
            subject = args[0]
            message = args[1]
            
            message = Mail(
                from_email='donotreply@adn.social',
                to_emails=[user.email],
                subject=subject,
                html_content=message)
            try:
                sg = SendGridAPIClient('')
                sg.send(message)
                
            except Exception as e:
                print(e)
            
        except Exception as e:
            print(f"Exception when calling TransactionalEmailsApi->send_transac_email: {e}")
            return False




