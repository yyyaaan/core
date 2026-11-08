#!/usr/bin/env bash
# Daily: rotate yesterday's Frigate export, keep a light local copy, upload to R2 (+ B2 during transition).
set -euo pipefail

day=$(date -d "yesterday 13:00" +%Y%m%d)
out=/media/DayIn1
echo "@$(date +'%b%d %H:%M:%S') processing $day"

# path handed over by the frigate-export init container; fall back to the newest export made today
input_file=$(cat /handoff/export_path 2>/dev/null || true)
if [ -z "$input_file" ] || [ ! -f "$input_file" ]; then
    echo "No handoff path, falling back to newest export"
    input_file=$(ls -t /media/frigate/exports/*.mp4 2>/dev/null | head -n 1) || true  # ls may SIGPIPE on a big dir
    if [ -z "$input_file" ] || [ "$(date -r "$input_file" +%Y%m%d)" != "$(date +%Y%m%d)" ]; then
        echo "Failed. Latest export '$input_file' was not created today."
        exit 1
    fi
fi
echo "Input $input_file ($(stat -c %s "$input_file" | numfmt --to=iec))"

ffmpeg -hide_banner -loglevel error -y \
    -i "$input_file" \
    -vf "transpose=1" \
    -threads 2 \
    -movflags +faststart \
    "$out/OneMin_$day.mp4"
echo "=VideoRotation= $(date +%H:%M:%S)"

ffmpeg -hide_banner -loglevel error -y \
    -i "$out/OneMin_$day.mp4" \
    -vf "scale=-2:1620" -r 30 -crf 35 \
    "$out/A_$day.mp4"
echo "=VideoFinalDone= $(date +%H:%M:%S)"

python /app/upload.py r2 "$out/OneMin_$day.mp4" "timelapse/daily/$day.mp4"
python /app/upload.py b2 "$out/OneMin_$day.mp4" "onemin/${day:0:6}/OneMin_$day.mp4" --bucket yyyCam \
    || echo "B2 upload failed (non-fatal)"
echo "=UploadDone= $(date +%H:%M:%S)"
