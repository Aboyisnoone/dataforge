from fastapi import UploadFile
import uuid
import os
import tempfile
import time
import logging
logger = logging.getLogger(__name__)
from datetime import datetime, timezone
from backend.datasets.storage import FileStorage
from backend.persistence.repositories.datasets import DatasetRepository
from core.dataset import Dataset, DatasetVersion
from core.profiler import Profiler
from core.loader import load_dataset_version
from core.storage import get_storage_service

class DatasetService:
    def __init__(self, repo: DatasetRepository):
        self.repo = repo
        
    def upload_dataset(self, file: UploadFile, dataset_name: str = None, workspace_id: str = 'ws_local_dev') -> DatasetVersion:
        start_time = time.time()
        if not dataset_name:
            dataset_name = os.path.splitext(file.filename)[0]
            
        dataset = self.repo.get_dataset_by_name(dataset_name, workspace_id)
        if not dataset:
            dataset = Dataset(
                id=f"ds_{uuid.uuid4().hex[:8]}",
                name=dataset_name,
                workspace_id=workspace_id,
                versions=[]
            )
            self.repo.create_dataset(dataset)
            
        temp_id = f"v_{uuid.uuid4().hex[:8]}"
        storage_path, size_bytes, sha256 = FileStorage.save(file, temp_id)
        
        ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        format_type = ext if ext in ('csv', 'parquet', 'json', 'ndjson') else 'unknown'

        existing_version = self.repo.get_version_by_hash(dataset.id, sha256)
        if existing_version:
            # Storage cleanup could go here
            return existing_version
            
        version_num = self.repo.get_next_version_number(dataset.id)
        
        # Download file to a temp path for profiling to remain stateless
        storage = get_storage_service()
        with tempfile.NamedTemporaryFile(suffix=f".{format_type}", delete=False) as tmp:
            tmp_path = tmp.name
            
        try:
            storage.download_file(storage_path, tmp_path)
            
            profiler = Profiler()
            stats = profiler.profile(tmp_path, format_type)
            
            dv_temp = load_dataset_version("temp", tmp_path)
            schema = dv_temp.schema
        finally:
            os.remove(tmp_path)
        
        new_version = DatasetVersion(
            id=temp_id,
            dataset_id=dataset.id,
            version_number=version_num,
            file_hash=sha256,
            file_size=size_bytes,
            storage_path=storage_path,
            format=format_type,
            schema=schema,
            row_count=stats.get("row_count", 0),
            created_at=datetime.now(timezone.utc)
        )
        new_version.stats = stats 
        
        self.repo.create_version(new_version)
        
        ingestion_time_ms = (time.time() - start_time) * 1000
        logger.info(f"Dataset {dataset.name} v{version_num} ingested", extra={
            "telemetry": {
                "type": "ingestion",
                "dataset_id": dataset.id,
                "version_id": temp_id,
                "file_size_bytes": size_bytes,
                "row_count": new_version.row_count,
                "duration_ms": round(ingestion_time_ms, 2)
            }
        })
        
        return new_version
        
    def get_latest_version(self, dataset_id: str, workspace_id: str) -> DatasetVersion:
        dataset = self.repo.get_dataset_by_id(dataset_id, workspace_id)
        if not dataset or not dataset.versions:
            return None
        return max(dataset.versions, key=lambda v: v.version_number)

    def get_dataset(self, dataset_id: str, workspace_id: str) -> Dataset:
        return self.repo.get_dataset_by_id(dataset_id, workspace_id)
