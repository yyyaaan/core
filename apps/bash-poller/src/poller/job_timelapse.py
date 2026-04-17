# this file is moved into kubernetes manifest start point
from datetime import datetime, timedelta
from time import sleep
from requests import get, post

offset = 0 # yesterday
hours = 24 # a whole day
name_prefix = "day90sec"
max_polling_hours = 8
polling_interval_seconds = 300
frigate_url = "http://frigate-service.home-internal.svc.cluster.local:5000"

print("Started")
now = datetime.now()
end_polling_time = now + timedelta(hours=max_polling_hours)

yesterday_end = datetime(now.year, now.month, now.day)
ts = int(yesterday_end.timestamp()) - offset * 3600
ts0 = ts - hours * 3600

r = post(
    url=f"{frigate_url}/api/export/yard/start/{ts0}/end/{ts}",
    json={
        "playback": "timelapse_25x",  # actual speed set in frigate config
        "name": f"{name_prefix}_{datetime.fromtimestamp(ts0):%Y%m%d}.mp4",
    },
)

print(
    r.status_code,
    f"{datetime.fromtimestamp(ts0):%b%dT%H:%M:%S}--{datetime.fromtimestamp(ts):%b%dT%H:%M:%S}",
    r.text,
    flush=True,
)


# polling for completion
export_id = r.json()["export_id"]

def check_completion(export_id: str) -> bool:
    """poll for completion (the opposite of in progress)"""
    r_status = get(url=f"{frigate_url}/api/exports")
    for item in r_status.json():
        if item["id"] == export_id:
            return not item["in_progress"]
    raise Exception("Export ID not found in polling endpoint")


export_completed = False
while not export_completed:
    sleep(10)
    export_completed = check_completion(export_id)
    print("waiting...", flush=True)
    if datetime.now() > end_polling_time:
        raise Exception("Polling ends due to time limit. Export not completed")
    sleep(polling_interval_seconds)

print("Ready!")
