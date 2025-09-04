from playwright.async_api import async_playwright
from random import randint


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
        self.url = url
        self.wait_for_load_state = wait_for_load_state
        self.cookies = cookies
        self.override_headers = override_headers
        self.timeout = timeout
        self.playwright = None
        self.browser = None
        self.page = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()
        self.context = await self.browser.new_context()

        self.context.set_default_timeout(self.timeout)
        if len(self.cookies):
            self.context.add_cookies(self.cookies)

        self.page = await self.context.new_page()
        await self.page.set_viewport_size({"width": 1680, "height": 1080})
        await self.page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",  # noqa: E501
            "Accept-Language": "en",
            **self.override_headers,
        })
        await self.page.goto(self.url)
        if len(self.wait_for_load_state):
            await self.page.wait_for_load_state(self.wait_for_load_state)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
