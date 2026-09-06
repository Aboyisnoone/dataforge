import os
import shutil
import tempfile
from typing import BinaryIO
from core.config import settings

class StorageService:
    def upload_file(self, filename: str, file_obj: BinaryIO) -> str:
        raise NotImplementedError

    def download_file(self, filename: str, target_path: str):
        raise NotImplementedError

class LocalStorageService(StorageService):
    def __init__(self):
        self.base_dir = os.path.abspath(".dataforge/datasets")
        os.makedirs(self.base_dir, exist_ok=True)
        
    def upload_file(self, filename: str, file_obj: BinaryIO) -> str:
        filepath = os.path.join(self.base_dir, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
        return filename  # return key instead of absolute path
        
    def download_file(self, filename: str, target_path: str):
        filepath = os.path.join(self.base_dir, filename)
        shutil.copyfile(filepath, target_path)

class S3StorageService(StorageService):
    def __init__(self):
        import boto3
        from botocore.client import Config
        self.bucket = settings.S3_BUCKET
        self.client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )
        # Ensure bucket exists
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:
            self.client.create_bucket(Bucket=self.bucket)

    def upload_file(self, filename: str, file_obj: BinaryIO) -> str:
        self.client.upload_fileobj(file_obj, self.bucket, filename)
        return filename

    def download_file(self, filename: str, target_path: str):
        self.client.download_file(self.bucket, filename, target_path)

def get_storage_service() -> StorageService:
    if settings.STORAGE_BACKEND.lower() == "s3":
        return S3StorageService()
    return LocalStorageService()
