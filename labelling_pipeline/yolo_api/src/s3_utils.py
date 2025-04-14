# src/s3_utils.py
import boto3
import os
from config import S3_BUCKET_NAME
import logging

logger = logging.getLogger(__name__)

def create_s3_client():
    """S3 클라이언트를 생성하여 반환"""
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        logger.info("S3 클라이언트 생성 완료.")
        return s3_client
    except Exception as e:
        logger.error(f"S3 클라이언트 생성 실패: {e}")
        raise
