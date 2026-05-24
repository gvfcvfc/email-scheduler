from functools import lru_cache
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from app.config import settings

@lru_cache(maxsize=1)
def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ROOT_USER,
        aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        region_name="us-east-1",
        config=Config(signature_version="s3v4")
    )
@lru_cache(maxsize=1)
def get_s3_public_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.MINIO_PUBLIC_ENDPOINT,
        aws_access_key_id=settings.MINIO_ROOT_USER,
        aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        region_name="us-east-1",
        config=Config(signature_version="s3v4")
    )

def ensure_bucket_exists() -> None:
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=settings.MINIO_BUCKET)
    except ClientError:
        s3.create_bucket(Bucket=settings.MINIO_BUCKET)
    
def upload_fileobj(file_obj, key: str, content_type: str) -> None:
    s3 = get_s3_client()
    s3.upload_fileobj(
        Fileobj=file_obj,
        Bucket=settings.MINIO_BUCKET,
        Key=key,
        ExtraArgs={"ContentType": content_type}
    )

def generate_presigned_download_url(key: str, expires_in: int = 300) -> str:
    s3 = get_s3_public_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.MINIO_BUCKET, "Key": key},
        ExpiresIn=expires_in
    )

def delete_object(key: str) -> None:
    s3 = get_s3_client()
    s3.delete_object(Bucket=settings.MINIO_BUCKET, Key=key)