"""
python /app/helper_upload.py --source-file /media/DayIn1/OneMin_20250912.mp4 --bucket-name yyyCam --dest-path "onemin/202509"
python /app/helper_upload.py --source-file mariadb_dump.sql.gz --bucket-name yyyBackup --dest-path "Database10DaySnapshots"
"""

import os
import sys
import argparse
from b2sdk.v2 import B2Api, InMemoryAccountInfo, TqdmProgressListener

B2_KEY_ID = os.environ.get('BACKBLAZE_KEY_ID')
B2_APP_KEY = os.environ.get('BACKBLAZE_KEY')

def main():
    if not B2_KEY_ID or not B2_APP_KEY:
        print("Error: B2_APPLICATION_KEY_ID and B2_APPLICATION_KEY environment variables must be set.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Upload a file to a Backblaze B2 bucket.")
    parser.add_argument('--source-file', required=True, help="The local path to the file you want to upload.")
    parser.add_argument('--bucket-name', required=True, help="The name of the B2 bucket to upload to.")
    parser.add_argument('--dest-path', required=True, help="The destination path/folder inside the bucket (e.g., 'videos/archive/').")
    args = parser.parse_args()

    # --- Initialize and Authorize with B2 SDK ---
    try:
        info = InMemoryAccountInfo()
        b2_api = B2Api(info)
        b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
        print("Auth OK")
    except Exception as e:
        print(f"Error during B2 authorization: {e}")
        sys.exit(1)

    # --- Get the Bucket and Prepare for Upload ---
    source_file_path = args.source_file
    bucket_name = args.bucket_name
    dest_path = args.dest_path
    
    file_name = os.path.basename(source_file_path)
    b2_file_name = os.path.join(dest_path, file_name).replace("\\", "/")

    try:
        bucket = b2_api.get_bucket_by_name(bucket_name)
        progress_listener = TqdmProgressListener(f'Uploading {file_name}')
        uploaded_file = bucket.upload_local_file(
            local_file=source_file_path,
            file_name=b2_file_name,
            progress_listener=progress_listener
        )

        print("\nUpload successful!")

    except FileNotFoundError:
        print(f"Error: Source file not found at '{source_file_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred during the upload: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
