from argparse import ArgumentParser
from datetime import datetime, timedelta
from time import sleep

from requests import get, post

print("Started")


parser = ArgumentParser(prog="Timelapse Preparation")
parser.add_argument("--hours", type=int, default=24)
parser.add_argument("--offset", type=int, default=0)
parser.add_argument("--limit-polling-hours", type=int, default=9)
args = parser.parse_args()


# always relative to yesterday last hour
now = datetime.now()
end_polling_time = now + timedelta(hours=args.limit_polling_hours)

yesterday_end = datetime(now.year, now.month, now.day)
ts = int(yesterday_end.timestamp()) - args.offset * 3600
ts0 = ts - args.hours * 3600

r = post(
    url=f"http://frigate-service.home-internal.svc.cluster.local:5000/api/export/yard/start/{ts0}/end/{ts}",
    json={
        "playback": "timelapse_25x",  # actual speed set in frigate config
        "name": f"day90sec_{datetime.fromtimestamp(ts0):%Y%m%d}.mp4",
    },
)

print(
    r.status_code,
    f"{datetime.fromtimestamp(ts0):%b%dT%H:%M:%S}--{datetime.fromtimestamp(ts):%b%dT%H:%M:%S}",
    r.text,
)


# polling for completion
export_id = r.json()["export_id"]


def check_completion(export_id: str) -> bool:
    """poll for completion (the opposite of in progress)"""
    r_status = get(url="http://frigate-service.home-internal.svc.cluster.local:5000/api/exports")
    for item in r_status.json():
        if item["id"] == export_id:
            return not item["in_progress"]
    raise Exception("Export ID not found in polling endpoint")


export_completed = False
while not export_completed:
    export_completed = check_completion(export_id)
    print("waiting...")
    if datetime.now() > end_polling_time:
        raise Exception("Polling ends due to time limit. Export not completed")
    sleep(300)

print("Ready!")

# python job_timelapse.py --hours 1 --limit-polling-hours 1
