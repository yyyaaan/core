# %%
from datetime import datetime, timedelta
from http.cookies import SimpleCookie
from json import loads, dumps
from os import getenv
from requests import get, post

user, password = getenv("ELENIA_U"), getenv("ELENIA_P")
fixed_unit_price = 8.96  # cent/kWh


# %% Proxy and application tokens
def login(user, password):
    login = post(
        url="https://api.aina.elenia.fi/api/auth/login/credentials-authentication",
        headers={
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "origin": "https://aina.elenia.fi",
                "referer": "https://aina.elenia.fi/",
                "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36"
            },
        json={
            "email": user,
            "password": password
        }
    )
    print("Login", login.status_code, f"u{len(user)}p{len(password)}", end=" ")
    login.raise_for_status()
    cookies_login = SimpleCookie()
    cookies_login.load(login.headers["set-cookie"])
    session_id = cookies_login.get("sessionId").value
    csrf_token = cookies_login.get("csrf_token").value
    access_token = cookies_login.get("access_token").value
    id_token = cookies_login.get("id_token").value
    refresh_token = cookies_login.get("refresh_token").value
    print(f"{session_id} {csrf_token[:5]}*** OK")

    proxy = post(
        url="https://api.aina.elenia.fi/api/auth/access/token/6255f4a4-9091-70be-d4d0-c3b13c8d1773",
        headers={
            "accept": "application/json, text/plain, */*",
            "cookie": f"sessionId={session_id}; csrf_token={csrf_token}; access_token={access_token}; id_token={id_token}; refresh_token={refresh_token}",
            "x-csrf-token": csrf_token,
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36"
        }
    )
    print("Proxy", login.status_code, f"csrf{len(csrf_token)}", end=" ")
    proxy.raise_for_status()
    cookies_proxy = SimpleCookie()
    cookies_proxy.load(proxy.headers["set-cookie"])
    applications_token = cookies_proxy.get("applications_token").value
    print(f"{applications_token[:5]}***")
    return applications_token


# %%
def get_service_token(application_token):
    auth = get(
        url="https://public.sgp-prod.aws.elenia.fi/api/gen/customer_data_and_token",
        headers={"Authorization": f"Bearer {application_token}"}
    )

    print("SvcApp", auth.status_code, end=" ")
    auth.raise_for_status()
    token = auth.json()["token"]
    print(f"{token[:5]}***")
    return token


def get_meter_reading(token):
    meter_reading = get(
        url=(
            "https://public.sgp-prod.aws.elenia.fi/api/gen/meter_reading"
            "?customer_ids=7757079"
            "&gsrn=643006966035524955"
            f"&day={datetime.now().strftime('%Y-%m-%d')}"
        ),
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    print("Meter", meter_reading.status_code, end=" ")
    meter_reading.raise_for_status()
    meter = meter_reading.json()
    print(f"n={len(meter)}", meter[-1]['dt'][-11:],  meter[-1]['a'])
    return meter


# %%
def get_spot_prices(force_update=False):
    try:
        with open("/mnt/spot_price.json", "r") as f:
            spot_prices_fi = loads(f.read())
    except Exception as e:
        print("Spot price cache", e)
        force_update = True

    if force_update:
        spot_price = get(
            url=(
                "https://dashboard.elering.ee/api/nps/price"
                f"?start={datetime.now()-timedelta(days=1):%Y-%m-%d}T20:59:59.999Z"
                f"&end={datetime.now()+timedelta(days=1):%Y-%m-%d}T03:59:59.999Z"
            )
        )
        print("Elering EE", spot_price.status_code, end=" ")
        spot_prices_fi = spot_price.json().get("data", {}).get("fi", [])
        with open("/mnt/spot_price.json", "w") as f:
            f.write(dumps(spot_prices_fi, indent=2))

        print(f"n={len(spot_prices_fi)}", f"{datetime.fromtimestamp(spot_prices_fi[-1]['timestamp']):%b%d %H:%M}")
    return spot_prices_fi


def matching_price_for_dt(dt, tax_rate=0.255):
    """unit cent/kWh"""
    ts = int(datetime.fromisoformat(dt).timestamp())
    matched = [x for x in get_spot_prices() if x['timestamp'] <= ts]
    if len(matched) < 1 or (ts - matched[-1]['timestamp'] > 3601):
        price = get_spot_prices(force_update=True)
        matched = [x for x in price if x['timestamp'] <= ts]

    matched_price = matched[-1]['price'] * (1 + tax_rate)
    return matched_price/1000


def estimate_sales_price(meter):
    spot_price, fixed_price, consumption = 0.0, 0.0, 0  # float float int
    for i in range(len(meter)-1):
        try:
            this_consumption = meter[i+1]['a'] - meter[i]['a']
            consumption += this_consumption
            spot_price += matching_price_for_dt(meter[i]['dt']) * this_consumption / 1000
            fixed_price += fixed_unit_price / 100_000 * this_consumption
        except Exception:
            pass
    return spot_price, fixed_price, consumption


# %%
def main():
    try:
        with open("/mnt/token_elenia", "r") as f:
            token = f.read()
        meter = get_meter_reading(token)
    except Exception:
        print()
        token_app = login(user, password)
        token = get_service_token(token_app)
        with open("/mnt/token_elenia", "w") as f:
            f.write(token)
        meter = get_meter_reading(token)

    with open("/media/data_energy.txt", "a") as f:
        f.write(f"\n{meter[-1]['dt']}\n{meter[-1]['a']}")

    # end of normal elenia polling

    try:
        spot, fixed, consumption = estimate_sales_price(meter)
        with open("/media/data_energy_prices.txt", "a") as f:
            content = f"{spot:.2f},{fixed:.2f},{consumption}"
            f.write(f"\n{meter[-1]['dt']}\n{content}")
        print("prices", content)
    except Exception:
        pass


if __name__ == "__main__":
    print(f"@{datetime.now():%b%d %H:%M:%S}")
    main()
