from shared import PlayPage

def __not_in__use():
    user_agents = ['Random: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36', 'Chrome: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36', 'IE: Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)', 'Firefox: Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0', 'Safari: Mozilla/5.0 (iPhone; CPU iPhone OS 11_2_5 like Mac OS X) AppleWebKit/604.5.6 (KHTML, like Gecko) Version/11.0 Mobile/15D60 Safari/604.1', 'Android: Mozilla/5.0 (Linux; Android 6.0; MYA-L22 Build/HUAWEIMYA-L22) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36', 'MacOSX: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14', 'IOS: Mozilla/5.0 (iPhone; CPU iPhone OS 10_1 like Mac OS X) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0 Mobile/14B72 Safari/602.1', 'Linux: Mozilla/5.0 (X11; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0', 'IPhone: Mozilla/5.0 (iPhone; CPU iPhone OS 10_2 like Mac OS X) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0 Mobile/14C92 Safari/602.1', 'IPad: Mozilla/5.0 (iPad; CPU OS 5_0_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A405 Safari/7534.48.3', 'Computer: Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0', 'Mobile: Mozilla/5.0 (Linux; Android 7.0; Redmi Note 4 Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.111 Mobile Safari/537.36']

    play = PlayPage(
        url="https://www.marriott.com/search/default.mi",
        timeout=12000,
        # cookies=[{
        #     "name": "OptanonAlertBoxClosed",
        #     "value": "2024-05-19T11:02:09.241Z",
        #     "domain": "www.marriott.com",
        #     "path": "/"
        # }, {
        #     "name": "OptanonConsent",
        #     "value": "isGpcEnabled=0&datestamp=Thu+May+23+2024+11%3A40%3A38+GMT%2B0300+(Eastern+European+Summer+Time)&version=202401.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&landingPath=NotLandingPage&groups=1%3A1%2C3%3A0%2C4%3A0%2C6%3A0&geolocation=FI%3B&AwaitingReconsent=false",
        #     "domain": "www.marriott.com",
        #     "path": "/"
        # }],
        override_headers={
            "User-Agent": user_agents[1],
            'Accept-Language': 'en',
        }
    )

    # play.page.click("button#onetrust-accept-btn-handler")

    play.page.query_selector("input[name='input-text-Destination']").fill("fort lau")
    play.page.click("div#downshift-1-item-0")

    play.page.click("input#\\:r2\\:")
    month = play.page.query_selector("div.DayPicker-Caption").inner_text()
    while ("October" not in month):
        play.page.click("span.DayPicker-NavButton--next")
        play.page.wait_for_timeout(1000)
        month = play.page.query_selector("div.DayPicker-Caption").inner_text()
    play.page.click("div[aria-label='Tue Oct 08 2024']")
    play.page.click("div[aria-label='Fri Oct 11 2024']")
    play.page.click("button[aria-label='Done']")

    play.page.click("div.document_search_form > div:last-child")

    # play.page.wait_for_selector("div.search-form-container")
    play.page.wait_for_timeout(5000)
    _ = play.page.screenshot(path="marriott.png")
    play.stop()
