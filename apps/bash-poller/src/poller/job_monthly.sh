#!/usr/bin/env bash
# Monthly: concat last month's daily timelapses at 10x; full quality to B2, bitrate-capped copy to R2.
set -euo pipefail
shopt -s nullglob
cd /media/DayIn1 || exit 1
mkdir -p monthly

month=$(date -d "$(date +%Y-%m-15) -1 month" +%Y%m)  # mid-month anchor avoids "Mar 31 - 1 month" overflow
days=(OneMin_"$month"*.mp4)
if [ ${#days[@]} -eq 0 ]; then
    echo "No daily files for $month"
    exit 1
fi
expected=$(date -d "$(date +%Y-%m-01) -1 day" +%-d)
echo "@$(date +'%b%d %H:%M:%S') $month: ${#days[@]} of $expected days"

list=$(mktemp)
trap 'rm -f "$list"' EXIT
for d in "${days[@]}"; do printf "file '%s/%s'\n" "$PWD" "$d"; done > "$list"

full=monthly/$month.mp4
ffmpeg -hide_banner -loglevel error -y \
    -f concat -safe 0 -i "$list" \
    -vf "setpts=0.1*PTS" -r 30 -crf 23 \
    -threads 1 \
    "$full"
echo "=Concat= $(date +%H:%M:%S) $(stat -c %s "$full" | numfmt --to=iec)"

# ~6 Mbit/s cap: a 31-day month is ~4.5 min, so <=~200 MB and 24 months stay well under R2's 10 GB free tier
r2=monthly/${month}_r2.mp4
ffmpeg -hide_banner -loglevel error -y \
    -i "$full" \
    -vf "scale=-2:1620" -r 30 -crf 28 -maxrate 6M -bufsize 12M \
    -movflags +faststart \
    "$r2"
python /app/upload.py r2 "$r2" "timelapse/monthly/$month.mp4"
python /app/catalog.py || echo "Catalog update failed (non-fatal)"
rm "$r2"

python /app/upload.py b2 "$full" "monthly/$month.mp4" --bucket yyyCam \
    || echo "B2 upload failed (non-fatal)"

# local copy: 5x faster again and light
ffmpeg -hide_banner -loglevel error -y \
    -i "$full" \
    -vf "setpts=0.2*PTS,scale=-2:1620" -r 30 -crf 35 \
    "monthly/${month}f.mp4"
mv "monthly/${month}f.mp4" "$full"
echo "=Done= $(date +%H:%M:%S)"
