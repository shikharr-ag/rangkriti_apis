from __future__ import print_function
import time
import random
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pprint import pprint

def generate_otp(length=6):
    """Generates a random numeric OTP of the specified length."""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

def create_otp_email_html(otp):
    """Creates the HTML email content with the given OTP."""

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your OTP</title>
    </head>
    <body style="font-family: sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">

        <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">

            <p style="margin-bottom: 20px;">Dear User,</p>

            <p style="margin-bottom: 20px;">Please use the following OTP to complete your login:</p>

            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 4px; text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 20px;">
                <span id="otp">{}</span> </div> <p style="margin-bottom: 20px;">This OTP is valid for 10 minutes. Do not share this OTP with anyone.</p>

            <p style="margin-bottom: 20px;">If you did not request this OTP, please ignore this email.</p>

            <p>Thank you,<br>Rangkriti
            </p>
        </div>

    </body>
    </html>
    """.format(otp)  # Use .format() to insert the OTP

    return html_content

def send_email(apiKey, otp,email):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = apiKey

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    subject = "OTP for logging into Rangkriti"
    html_content = create_otp_email_html(otp)
    sender = {"name":"VAL Powdercoating","email":"valpowdercoating@gmail.com"}
    to = [{"email":email}]
    # cc = [{"email":"example2@example2.com","name":"Janice Doe"}]
    # bcc = [{"name":"John Doe","email":"example@example.com"}]
    # reply_to = {"email":"replyto@domain.com","name":"John Doe"}
    headers = {"header": "some header"}
    params = {"subject":"Authentication Code for Rangkriti"}
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, 
                                                #    bcc=bcc, cc=cc,
                                                    # reply_to=reply_to,
                                                    headers=headers, html_content=html_content, sender=sender, subject=subject)

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)