from datetime import date
from urllib.parse import parse_qsl, urlsplit

from scout.sites.marriott import search


def test_search_url():
    url = search.search_url(date(2027, 5, 3), 4, 2)
    params = dict(parse_qsl(urlsplit(url).query))
    assert url.startswith("https://www.marriott.com/search/findHotels.mi?")
    assert params["fromDate"] == "05/03/2027" and params["toDate"] == "05/07/2027"
    assert params["lengthOfStay"] == "4" and params["numAdultsPerRoom"] == "2"
    assert params["isRateCalendar"] == "true" and params["flexibleDateSearch"] == "true"

    fixed = dict(
        parse_qsl(
            urlsplit(search.search_url(date(2027, 5, 3), 4, 2, flexible=False)).query
        )
    )
    assert fixed["flexibleDateSearch"] == "false" and fixed["isRateCalendar"] == "false"
