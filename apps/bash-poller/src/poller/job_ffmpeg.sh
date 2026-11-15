#!/usr/bin/env bash
# Daily: rotate yesterday's Frigate export, upload to R2 (+ B2 during transition), refresh the catalog.
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

# one decode, two outputs: full quality, and a lite copy for mobile data (R2 only, not kept locally)
# lite must not be named OneMin_* in $out: the monthly job concats every OneMin_<month>*.mp4
lite=$(mktemp --suffix=.mp4)
trap 'rm -f "$lite"' EXIT
ffmpeg -hide_banner -loglevel error -y \
    -i "$input_file" \
    -filter_complex "[0:v]transpose=1,split=2[hi][lo];[lo]fps=30,scale=-2:'min(1280,ih)',setsar=1[lite]" \
    -map "[hi]" -map "0:a?" -threads 2 -movflags +faststart \
    "$out/OneMin_$day.mp4" \
    -map "[lite]" -threads 1 -crf 30 -maxrate 1500k -bufsize 3000k -pix_fmt yuv420p -movflags +faststart \
    "$lite"
echo "=VideoRotation= $(date +%H:%M:%S) lite $(stat -c %s "$lite" | numfmt --to=iec)"

python /app/upload.py r2 "$out/OneMin_$day.mp4" "timelapse/daily/$day.mp4"
python /app/upload.py r2 "$lite" "timelapse/daily/${day}_lite.mp4" || echo "Lite upload failed (non-fatal)"
python /app/upload.py b2 "$out/OneMin_$day.mp4" "onemin/${day:0:6}/OneMin_$day.mp4" --bucket yyyCam \
    || echo "B2 upload failed (non-fatal)"
echo "=UploadDone= $(date +%H:%M:%S)"
python /app/catalog.py || echo "Catalog update failed (non-fatal)"

# local retention by the day in the filename; monthly/ is kept (OneMinX_/A_ are legacy, no longer created)
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
