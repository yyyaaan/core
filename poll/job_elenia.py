# %%
from datetime import datetime, timedelta
from json import loads, dumps
from os import getenv
from requests import get, post

user, password = getenv("ELENIA_U"), getenv("ELENIA_P")
fixed_unit_price = 8.96  # cent/kWh

# %% AWS Cognito access token
def login(user, password):
    login = post(
        url="https://cognito-idp.eu-west-1.amazonaws.com/",
        headers={
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,fi-FI;q=0.8,fi;q=0.7,zh-CN;q=0.6,zh;q=0.5",
            "cache-control": "max-age=0",
            "content-type": "application/x-amz-json-1.1",
            "dnt": "1",
            "origin": "https://idm.asiakas.elenia.fi",
            "priority": "u=1, i",
            "referer": "https://idm.asiakas.elenia.fi/",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": "\"Android\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
            "x-amz-target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "x-amz-user-agent": "aws-amplify/5.0.4 js amplify-authenticator"
        },
        json={
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": "k4s2pnm04536t1bm72bdatqct",
            "AuthParameters": {
                "USERNAME": user,
                "PASSWORD": password
            },
            "ClientMetadata": {}
        }
    )

    print("AWS", login.status_code, f"u{len(user)}p{len(password)}", end=" ")
    if login.status_code > 299:
        raise Exception(f"Exception {login.status_code}")
    token_aws = login.json()["AuthenticationResult"]["AccessToken"]
    print(token_aws[:9], "***", sep="")
    return token_aws


# %%
def get_service_token(token_aws):
    auth = get(
        url="https://public.sgp-prod.aws.elenia.fi/api/gen/customer_data_and_token",
        headers={"Authorization": f"Bearer {token_aws}"}
    )

    print("Elenia Cust", auth.status_code, end=" ")
    if auth.status_code > 299:
        raise Exception(f"Exception {auth.status_code}")
    token = auth.json()["token"]
    print(token[:9], "***", sep="")
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

    print("Elenia Meter", meter_reading.status_code, end=" ")
    if meter_reading.status_code > 299:
        raise Exception(f"Exception {meter_reading.status_code}")
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
        token_aws = login(user, password)
        token = get_service_token(token_aws)
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
