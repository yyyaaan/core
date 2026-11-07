"""Hotel search URL (findHotels.mi). Loading it sets the session's search, which the
calendar and rate list pages read instead of their own URL params."""

from datetime import date, timedelta
from urllib.parse import urlencode

SEARCH_URL = "https://www.marriott.com/search/findHotels.mi"
# a Bora Bora hotel search as the site's form submits it; search_url() adds dates, party and mode.
# Only the destination is Bora Bora specific: the calendar picks the hotel by propertyCode, and the
# rate list needs the hotel among the results (its Continue button).
SEARCH_PARAMS = {
    "childrenCountBox": "0 Children Per Room",
    "childrenCount": "0",
    "clusterCode": "none",
    "useRewardsPoints": "false",
    "isAdvanceSearch": "true",
    "isNGSF": "false",
    "recordsPerPage": "20",
    "destinationAddress.type": "Hotel Name",
    "destinationAddress.latitude": "-16.497141499999998",
    "isInternalSearch": "true",
    "vsInitialRequest": "false",
    "searchType": "InCity",
    "destinationAddress.stateProvinceDisplayName": "Leeward Islands",
    "countryName": "PF",
    "destinationAddress.stateProvince": "Leeward Islands",
    "searchRadius": "50",
    "singleSearchAutoSuggest": "Unmatched",
    "destinationAddress.placeId": "ChIJx-RZnHCXvXYR95AaxgOP5OY",
    "for-hotels-nearme": "Near",
    "destinationAddress.country": "PF",
    "destinationAddress.address": "MOTU TAPE, BP 190, Bora-Bora 98730, French Polynesia",
    "collapseAccordian": "is-hidden",
    "singleSearch": "true",
    "destinationAddress.secondaryText": "Leeward Islands, PF",
    "destinationAddress.city": "Bora-Bora",
    "destinationAddress.mainText": "Bora-Bora",
    "isTransient": "true",
    "destinationAddress.longitude": "-151.7018508",
    "initialRequest": "false",
    "flexibleDateSearchRateDisplay": "false",
    "isSearch": "true",
    "destinationAddress.destination": "The Westin Bora Bora Resort Spa",
    "isHideFlexibleDateCalendar": "false",
    "roomCountBox": "1 Room",
    "roomCount": "1",
    "deviceType": "desktop-web",
    "view": "list",
}


def search_url(check_in: date, nights: int, adults: int, flexible: bool = True) -> str:
    def us(d: date) -> str:
        return d.strftime("%m/%d/%Y")

    check_out = check_in + timedelta(days=nights)
    return f"{SEARCH_URL}?" + urlencode(
        {
            **SEARCH_PARAMS,
            "fromDate": us(check_in),
            "fromDateDefaultFormat": us(check_in),
            "t-start": us(check_in),
            "toDate": us(check_out),
            "toDateDefaultFormat": us(check_out),
            "t-end": us(check_out),
            "fromToDate_submit": us(check_out),
            "lengthOfStay": str(nights),
            "numAdultsPerRoom": str(adults),
            "guestCountBox": f"{adults} Adult Per Room",
            "flexibleDateSearch": str(flexible).lower(),
            "isRateCalendar": str(flexible).lower(),
        }
    )
