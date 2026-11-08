"""Publish trained model directories and dataset files to local S3-compatible storage."""
import argparse
import os
from pathlib import Path

import boto3

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-version", choices=("v1", "v2"))
    parser.add_argument("--dataset", action="store_true")
    args = parser.parse_args()
    client = boto3.client("s3", endpoint_url=os.getenv("S3_ENDPOINT", "http://localhost:8333"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "local-access-key"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "local-secret-key"),
        region_name="us-east-1")
    items = []
    if args.dataset:
        candidates = [(ROOT / "data/commands_pool.jsonl", "datasets/commands_pool.jsonl"),
                      (ROOT / "datasets/v1/train.jsonl", "datasets/v1/train.jsonl"),
                      (ROOT / "datasets/v1/train.sha256", "datasets/v1/train.sha256")]
        candidates += [(path, f"datasets/teacher/{path.name}")
                       for path in (ROOT / "datasets/teacher").glob("shard-*.jsonl")]
        items.extend((path, key) for path, key in candidates if path.is_file())
    if args.model_version:
        base = ROOT / "models" / args.model_version
        items.extend((path, f"models/{args.model_version}/{path.relative_to(base).as_posix()}")
                     for path in base.rglob("*") if path.is_file())
    if not args.model_version and not args.dataset:
        parser.error("select --model-version and/or --dataset")
    buckets = {"datasets", "models"}
    for bucket in buckets:
        try:
            client.create_bucket(Bucket=bucket)
        except Exception:
            pass  # Bucket may already exist (including SeaweedFS region-specific responses).
    for path, key in items:
        bucket, _, key = key.partition("/")
        if not path.is_file():
            raise SystemExit(f"missing artifact: {path}")
        client.upload_file(str(path), bucket, key)
        print(f"s3://{bucket}/{key}")


if __name__ == "__main__":
    main()
