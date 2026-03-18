"""将 MinIO bucket 设置为公开只读"""

import json
import sys
import os

# 读取 .env 配置
env = {}
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()

from minio import Minio

endpoint   = env.get("MINIO_ENDPOINT", "localhost:9000")
access_key = env.get("MINIO_ACCESS_KEY", "minioadmin")
secret_key = env.get("MINIO_SECRET_KEY", "minioadmin")
bucket     = env.get("MINIO_BUCKET", env.get("MINIO_BUCKET_NAME", "images"))
secure     = env.get("MINIO_SECURE", "false").lower() == "true"

client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

# 公开只读策略：允许任何人 GetObject
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{bucket}/*"],
        }
    ],
}

client.set_bucket_policy(bucket, json.dumps(policy))
print(f"✓ bucket '{bucket}' 已设置为公开只读")
