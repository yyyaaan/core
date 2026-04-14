from argparse import ArgumentParser
from datetime import datetime
from requests import post

parser = ArgumentParser(prog="Timelapse Preparation")
parser.add_argument("--hours", type=int, default=24)
parser.add_argument("--offset", type=int, default=0)

args = parser.parse_args()

print(f"@{datetime.now():%b%d %H:%M:%S}")

# always relative to yesterday last hour
now = datetime.now()
yesterday_end = datetime(now.year, now.month, now.day)
ts = int(yesterday_end.timestamp()) - args.offset * 3600
ts0 = ts -  args.hours * 3600

r = post(
    url=f"http://192.168.4.81:5000/api/export/yard/start/{ts0}/end/{ts}",
    json={
        "playback": "timelapse_25x", # actual speed set in frigate config
        "name": f"day90sec_{datetime.fromtimestamp(ts0):%Y%m%d}.mp4"
    }
)

print(
    r.status_code, 
    f"{datetime.fromtimestamp(ts0):%b%dT%H:%M:%S}--{datetime.fromtimestamp(ts):%b%dT%H:%M:%S}",
    r.text
)
