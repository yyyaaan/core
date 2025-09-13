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
# changed to copy only, since export is ready
# ffmpeg \
#     -i "$input_file" \
#     -vf setpts=0.1*PTS \
#     -r 120 \
#     -crf 28 \
#     -hide_banner \
#     -loglevel error \
#     -threads 2 \
#     "/media/DayIn1/OneMinX_$previous_day.mp4"
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
python /app/helper_upload.py --source-file "/media/DayIn1/OneMin_$previous_day.mp4" --bucket-name yyyCam --dest-path "onemin/$(date -d "yesterday 13:00" '+%Y%m')"

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


#################################################
### Backup Procedures ###
#################################################
echo "=MariaDBDump= $(date +"%H:%M:%S")"
export MYSQL_PWD=$MARIADB_ROOT_PASSWORD
mariadb-dump -h 192.168.4.81 -u root --all-databases | gzip > mariadb_dump.sql.gz
python /app/helper_upload.py --source-file mariadb_dump.sql.gz --bucket-name yyyBackup --dest-path "Database10DaySnapshots" && rm mariadb_dump.sql.gz
echo "=UploadDone= $(date +"%H:%M:%S")"

echo "=ConfBackups= $(date +"%H:%M:%S")"
zip -qr config_archive.zip /backup -x '*/backup/*' '*/backups/*'
python /app/helper_upload.py --source-file config_archive.zip --bucket-name yyyBackup --dest-path "Configs10DaySnapshots" && rm config_archive.zip
echo "=UploadDone= $(date +"%H:%M:%S")"

