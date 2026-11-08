"""Upload a file to Cloudflare R2 over the S3 API.

python /app/helper_r2.py --source-file /media/DayIn1/OneMin_20261107.mp4 --key timelapse/daily/20261107.mp4
"""

import argparse
import mimetypes
import os
import sys

import boto3
from botocore.config import Config

ENV_KEYS = ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET")


def main():
    parser = argparse.ArgumentParser(description="Upload a file to Cloudflare R2.")
    parser.add_argument("--source-file", required=True)
    parser.add_argument(
        "--key", required=True, help="object key, e.g. timelapse/daily/20261107.mp4"
    )
    args = parser.parse_args()

    missing = [k for k in ENV_KEYS if not os.environ.get(k)]
    if missing:
        sys.exit(f"Missing env vars: {', '.join(missing)}")
    endpoint, key_id, secret, bucket = (os.environ[k] for k in ENV_KEYS)

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
        region_name="auto",
        # boto3>=1.36 default CRC checksums are a known S3-compat pitfall; R2 doesn't need them
        config=Config(
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )

    content_type = (
        mimetypes.guess_type(args.source_file)[0] or "application/octet-stream"
    )
    size_mb = os.path.getsize(args.source_file) / 1e6
    s3.upload_file(
        args.source_file, bucket, args.key, ExtraArgs={"ContentType": content_type}
    )
    print(f"Uploaded {args.source_file} ({size_mb:.1f} MB) to r2://{bucket}/{args.key}")


if __name__ == "__main__":
    main()
