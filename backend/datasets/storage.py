import os
import hashlib
from core.config import settings
import tempfile
from fastapi import UploadFile
from pathlib import Path
from core.storage import get_storage_service

MAX_UPLOAD_SIZE = settings.MAX_UPLOAD_SIZE_BYTES

class FileTooLargeError(Exception):
    pass

class FileStorage:
    @staticmethod
    def save(file: UploadFile, dataset_id: str) -> tuple[str, int, str]:
        filename = file.filename
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in ("csv", "parquet", "json", "ndjson"):
            raise ValueError(f"Unsupported format '{ext}'. Only CSV, Parquet, JSON, and NDJSON are supported.")
            
        safe_name = f"{dataset_id}.{ext}"
        
        h = hashlib.sha256()
        size = 0
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            while chunk := file.file.read(8192 * 10):
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    tmp.close()
                    os.remove(tmp_path)
                    raise FileTooLargeError(f"File exceeds maximum upload size of {MAX_UPLOAD_SIZE} bytes.")
                h.update(chunk)
                tmp.write(chunk)
                
        # Upload to target storage
        storage = get_storage_service()
        with open(tmp_path, "rb") as f:
            final_path = storage.upload_file(safe_name, f)
            
        # Clean up temp file
        os.remove(tmp_path)
                
        return final_path, size, h.hexdigest()

    @staticmethod
    def delete(storage_path: str):
        # We'd add delete_file to storage service, but for now we skip this
        pass
