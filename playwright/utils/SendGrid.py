from os import getenv
from requests import post


class SendGrid:
    """
    email API using send grid
    """

    audiences = ["yan@yan.fi", "lixiaoyuan23@gmail.com"]

    def __init__(self):
        self.api_key = getenv("SENDGRID_API_KEY", "")

    def send_email(self, subject, content, audience_length=1):
        audiences = self.audiences[:audience_length]
        res = post(
            url="https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{
                    "to": [{"email": to} for to in audiences],
                }],
                "from": {
                    "email": "BotYYY@yan.fi"
                },
                "subject": subject,
                "content": [{
                    "type": "text/html",
                    "value": content
                }]
            }
        )
        print(res.status_code, res.text)
