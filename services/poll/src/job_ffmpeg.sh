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

############################
######### manual ###########
# input_file=...
# previous_day=20230918
############################
# -crf 0-51 & -qp 0-38/23
# changed to copy only, since export is ready
cp $input_file /media/DayIn1/OneMinX_$previous_day.mp4
echo "=TimelapseCopyDone= $(date +"%H:%M:%S")"

ffmpeg \
    -i "/media/DayIn1/OneMinX_$previous_day.mp4" \
    -vf "transpose=1" \
    -threads 2 \
    -hide_banner \
    -loglevel error \
    "/media/DayIn1/OneMin_$previous_day.mp4"

echo "=VideoRotation= $(date +"%H:%M:%S")"
# check default codec ffmpeg -h muxer=mp4


#################################################
### UPLOAD ###
#################################################

# dest="$(date -d "yesterday 13:00" '+%Y%m')/yard_$(date -d "yesterday 13:00" '+%Y%m%d').mp4"

# gcloud auth login --cred-file=/gcpstorage.json
# gcloud config set disable_prompts true
# gcloud config set project yyyaaannn
# gcloud config set storage/parallel_composite_upload_enabled True
# gcloud storage cp "/media/DayIn1/OneMin_$previous_day.mp4"  "gs://yyyiot/onemin/$dest"
# gcloud storage cp "$input_file" "gs://yyyiot/cam/$dest" 
/usr/local/bin/python /app/helper_upload.py --source-file "/media/DayIn1/OneMin_$previous_day.mp4" --bucket-name yyyCam --dest-path "onemin/$(date -d "yesterday 13:00" '+%Y%m')"

echo "=UploadDone= $(date +"%H:%M:%S")"


#################################################
### Finial Cleanup and Fast Loading ###
#################################################
rm "/media/DayIn1/OneMinX_$previous_day.mp4"

ffmpeg \
    -i "/media/DayIn1/OneMin_$previous_day.mp4" \
    -vf "scale=-2:1620" -r 30 -crf 35 \
    -loglevel error \
    "/media/DayIn1/A_$previous_day.mp4"

echo "=VideoFinalDone= $(date +"%H:%M:%S")"