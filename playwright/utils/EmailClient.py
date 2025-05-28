from base64 import b64encode
from os import getenv
from requests import post


class EmailClient:
    """
    email API using SMTP2GO or SendGrid
    """

    audiences = ["yan@yan.fi", "lixiaoyuan23@gmail.com"]
    sender = "bot@yanpan.fi"  # BotYYY@yan.fi
    api_key_send_grid = getenv("SENDGRID_API_KEY", "")
    api_key_smtp2go = getenv("SMTP2GO_API_KEY", "")

    def send_email(self, subject, content, audience_length=1):
        self.__send_smtp2go_email(subject, content, audience_length)

    def __to_mime(self, subject, content, audience_length=1):
        headers = [
            f"From: {self.sender}",
            f"To: {', '.join(self.audiences[:audience_length])}",
            f"Subject: {subject}",
            "MIME-Version: 1.0",
            "Content-Type: text/html; charset=utf-8",
            ""
        ]
        mime_message = "\r\n".join(headers) + "\r\n" + content
        return b64encode(mime_message.encode('utf-8')).decode('utf-8')

    def __send_smtp2go_email(self, subject, content, audience_length=1):
        res = post(
            url="https://api.smtp2go.com/v3/email/mime",
            headers={
                "X-Smtp2go-Api-Key": self.api_key_smtp2go,
                "Content-Type": "application/json",
                "accept": "application/json",
            },
            json={"mime_email": self.__to_mime(subject, content, audience_length)}  # noqa: E501
        )
        print(res.status_code, res.text)

    def __send_grid_email(self, subject, content, audience_length=1):
        audiences = self.audiences[:audience_length]
        res = post(
            url="https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {self.api_key_send_grid}",
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
