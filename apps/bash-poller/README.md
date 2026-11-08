# Polling Services including ffmpeg

CronJobs in `home-internal`, schedules in UTC (`helm-chart/values.yaml`); scripts compute dates in `TZ` from the `tz-config` secret.

| Job | Script | What |
|-----|--------|------|
| `cronjob-elenia` | `job_elenia.py` | Elenia energy polling |
| `cronjob-video` | init container (inline) + `job_ffmpeg.sh` | Frigate export of yesterday (yard, 1000x), rotate, upload |
| `cronjob-ffmpeg-monthly` | `job_monthly.sh` | Concat last month's dailies at 10x, upload |

## Timelapse storage

Uploads go to Cloudflare R2 (bucket from `R2_BUCKET`, shared `static` bucket) via `helper_r2.py`, and to B2 `yyyCam` via `helper_upload.py` during the transition.

- `timelapse/daily/YYYYMMDD.mp4`: R2 lifecycle rule deletes after 7 days
- `timelapse/monthly/YYYYMM.mp4`: R2 lifecycle rule deletes after 730 days (24 months)

Retention lives in the R2 bucket's lifecycle rules (Cloudflare dashboard), not in code. Never put anything else under `timelapse/`. Credentials: `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` in `infra/credentials/poll.env` (token: Object Read & Write, scoped to the bucket).
