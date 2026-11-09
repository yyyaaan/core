#!/usr/bin/env bash
# Daily: rotate yesterday's Frigate export, keep a light local copy, upload to R2 (+ B2 during transition).
set -euo pipefail

# set by the frigate-export init container, which only succeeds once the export is finished
day=$(cat /handoff/day)
input_file=$(cat /handoff/export_path)
out=/media/DayIn1
echo "@$(date +'%b%d %H:%M:%S') processing $day"

if [ ! -f "$input_file" ]; then
    echo "Failed. Export file '$input_file' not found."
    exit 1
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

# local retention by the day in the filename; monthly/ is kept
cutoff=$(date -d "$(date +%Y-%m-%d) -${LOCAL_RETENTION_DAYS:-49} days" +%Y%m%d)
shopt -s nullglob
removed=0
for f in "$out"/OneMin_*.mp4 "$out"/OneMinX_*.mp4 "$out"/A_*.mp4; do
    d=$(basename "$f" .mp4)
    d=${d##*_}
    if [[ $d =~ ^[0-9]{8}$ && $d < $cutoff ]]; then
        rm -- "$f"
        removed=$((removed + 1))
    fi
done
echo "=Retention= removed $removed local files before $cutoff"
