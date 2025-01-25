cd /media/frigate/exports

echo "$(date +"@%b%d %H:%M:%S")"
current_date=$(date +%Y%m%d)
previous_day=$(date -d "yesterday 13:00" '+%Y%m%d')

input_file=$(ls -t | head -n 1)
file_date=$(date -r "$input_file" +%Y%m%d)
file_size=$(stat -c %s "$input_file" | numfmt --to=iec)

if [ "$file_date" = "$current_date" ]; then
    echo "The file $input_file ($file_size) is create today $(date -r "$input_file" +%b%dT%H:%M:%S)."
else
    echo "Failed. The latest file '$input_file' was created $file_date."
    exit 0
fi

# -crf 0-51 & -qp 0-38/23
ffmpeg \
    -i "$input_file" \
    -vf setpts=0.1*PTS \
    -r 60 \
    -crf 28 \
    -hide_banner \
    -loglevel error \
    -threads 2 \
    "/media/DayIn1/OneMin_$previous_day.mp4"

echo "$(date +"=DONE= %H:%M:%S")"

# check default codec ffmpeg -h muxer=mp4
