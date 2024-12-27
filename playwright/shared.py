from os import getenv
from playwright.sync_api import sync_playwright
from random import randint
from requests import post


def random_color():
    color = "#"
    candidates = "0123456789ABCDEF"
    for _ in range(6):
        color += candidates[randint(0, 15)]
    return color


class PlayPage:
    """
    Initiate playwright instance and open page.
    """

    def __init__(
        self,
        url,
        wait_for_load_state="domcontentloaded",
        cookies=[],
        override_headers={},
        timeout=30000,
    ):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        self.context = self.browser.new_context()

        self.context.set_default_timeout(timeout)
        if len(cookies):
            self.context.add_cookies(cookies)

        self.page = self.context.new_page()
        self.page.set_viewport_size({"width": 1680, "height": 1080})
        self.page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",  # noqa: E501
            'Accept-Language': 'en',
            **override_headers,
        })
        self.page.goto(url)
        if len(wait_for_load_state):
            self.page.wait_for_load_state(wait_for_load_state)
        return None

    def stop(self):
        self.playwright.stop()


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
