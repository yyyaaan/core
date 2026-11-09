"""Upload one file to object storage under an explicit key.

python /app/upload.py r2 /media/DayIn1/OneMin_20261107.mp4 timelapse/daily/20261107.mp4
python /app/upload.py b2 /media/DayIn1/OneMin_20261107.mp4 onemin/202611/OneMin_20261107.mp4 --bucket yyyCam
"""

import argparse
import mimetypes
import os
import sys


def require_env(*keys: str) -> list[str]:
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        sys.exit(f"Missing env vars: {', '.join(missing)}")
    return [os.environ[k] for k in keys]


def r2_client():
    """(boto3 S3 client, default bucket) for R2 from the R2_* env vars."""
    import boto3
    from botocore.config import Config

    endpoint, key_id, secret, bucket = require_env(
        "R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"
    )
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
    return s3, bucket


def upload_r2(path: str, key: str, bucket: str | None, content_type: str) -> str:
    s3, default_bucket = r2_client()
    bucket = bucket or default_bucket
    s3.upload_file(path, bucket, key, ExtraArgs={"ContentType": content_type})
    return bucket


def upload_b2(path: str, key: str, bucket: str | None, content_type: str) -> str:
    from b2sdk.v2 import B2Api, InMemoryAccountInfo

    if not bucket:
        sys.exit("--bucket is required for b2")
    key_id, app_key = require_env("BACKBLAZE_KEY_ID", "BACKBLAZE_KEY")
    api = B2Api(InMemoryAccountInfo())
    api.authorize_account("production", key_id, app_key)
    api.get_bucket_by_name(bucket).upload_local_file(
        local_file=path, file_name=key, content_type=content_type
    )
    return bucket


# backends import their SDK lazily, so dropping one only needs its pip package removed
BACKENDS = {"r2": upload_r2, "b2": upload_b2}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", choices=BACKENDS)
    parser.add_argument("source_file")
    parser.add_argument(
        "key", help="full object key, e.g. timelapse/daily/20261107.mp4"
    )
    parser.add_argument("--bucket", help="r2: defaults to $R2_BUCKET; b2: required")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.source_file):
        sys.exit(f"Not a file: {args.source_file}")
    content_type = (
        mimetypes.guess_type(args.source_file)[0] or "application/octet-stream"
    )
    size_mb = os.path.getsize(args.source_file) / 1e6

    bucket = BACKENDS[args.target](
        args.source_file, args.key, args.bucket, content_type
    )
    print(
        f"Uploaded {args.source_file} ({size_mb:.1f} MB) to {args.target}://{bucket}/{args.key}"
    )


if __name__ == "__main__":
    main()
