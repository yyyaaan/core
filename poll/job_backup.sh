echo "$(date +"@%b%d %H:%M:%S") backup procedure"

##############
### Backup ###
##############
echo "=MariaDBDump= $(date +"%H:%M:%S")"
export MYSQL_PWD=$MARIADB_ROOT_PASSWORD
mariadb-dump -h 192.168.4.81 -u root --all-databases | gzip > mariadb_dump.sql.gz
/usr/local/bin/python /app/helper_upload.py --source-file mariadb_dump.sql.gz --bucket-name yyyBackup --dest-path "Database10DaySnapshots" && rm mariadb_dump.sql.gz
echo "=UploadDone= $(date +"%H:%M:%S")"

dow=$(date +%u)  # 1=Mon ... 7=Sun
if [ "$dow" = 2 ] || [ "$dow" = 6 ]; then
    echo "=ConfBackups= $(date +"%H:%M:%S")"
    zip -qr config_archive.zip /backup -x '*/backup/*' '*/backups/*'
    /usr/local/bin/python /app/helper_upload.py --source-file config_archive.zip --bucket-name yyyBackup --dest-path "Configs10DaySnapshots" && rm config_archive.zip
    echo "=UploadDone= $(date +"%H:%M:%S")"
else
    echo "=ConfBackups= Skipped"
fi

###########################################
### Check Video Export Success or Retry ###
###########################################
previous_day=$(date -d "yesterday 13:00" '+%Y%m%d')
output_file="/media/DayIn1/A_$previous_day.mp4"

if [ -f "$output_file" ]; then
    echo "Video export check completed - no action needed"
else
    /bin/bash /app/job_ffmpeg.sh
fi    
