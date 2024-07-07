from __future__ import print_function
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint
from django.conf import settings
# Configure API key authorization: api-key
configuration = sib_api_v3_sdk.Configuration()



class MailAgent():
    def __init__(self):
        configuration.api_key['api-key'] = settings.BREVO_API
    def mailer(self, user, *args):
        # Create an instance of the API class
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        print(user.email)
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": user.email, "name": user.full_name}],
            sender={"email": "donotreply@adn.social", "name": "ADN"},
            params={"name": args[0]},
            headers={
                "charset": "iso-8859-1"
            },
            subject=args[1],
            html_content=args[2]
            )
        try:
            # Send a transactional email
            api_response = api_instance.send_transac_email(send_smtp_email)
            pprint(api_response)
            return True
        except ApiException as e:
            print("Exception when calling TransactionalEmailsApi->send_transac_email: %s\n" % e)
            return False