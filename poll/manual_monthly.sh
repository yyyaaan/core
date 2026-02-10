cd /media/DayIn1/

last_month=$(date -d "1 month ago" '+%Y%m')
output_file=./monthly/${last_month}

ls -1 OneMin_${last_month}*.mp4 > files.txt
sed -i '' -e 's/^/file /' files.txt
ffmpeg -f concat -safe 0 -i files.txt \
    -vf "setpts=0.1*PTS" \
    -r 30 \
    -crf 23 \
    -threads 1 \
    ${output_file}.mp4

rm files.txt

python /app/helper_upload.py --source-file ${output_file}.mp4 --bucket-name yyyCam --dest-path "monthly"
# faster & scratch
ffmpeg -i ${output_file}.mp4 -vf "setpts=0.2*PTS,scale=-2:1620" -r 30 -crf 35 ${output_file}f.mp4

rm ${output_file}.mp4
mv ${output_file}f.mp4 ${output_file}.mp4
