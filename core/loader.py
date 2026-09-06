import os
import polars as pl
from datetime import datetime, timezone
import hashlib
from .dataset import DatasetVersion

def load_dataset_version(name: str, filepath: str) -> DatasetVersion:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    ext = os.path.splitext(filepath)[1].lower()
    
    try:
        if ext == '.csv':
            df = pl.scan_csv(filepath)
            fmt = 'csv'
        elif ext == '.parquet':
            df = pl.scan_parquet(filepath)
            fmt = 'parquet'
        elif ext == '.ndjson':
            df = pl.scan_ndjson(filepath)
            fmt = 'ndjson'
        elif ext == '.json':
            df = pl.read_json(filepath).lazy()
            fmt = 'json'
        else:
            raise ValueError(f"Unsupported format: {ext}")
            
        schema = {k: str(v) for k, v in df.collect_schema().items()}
        
    except Exception as e:
        raise ValueError(f"Malformed dataset file. Parser error: {str(e)}")
        
    schema_str = "".join([f"{k}:{v}" for k, v in sorted(schema.items())])
    schema_fingerprint = hashlib.sha256(schema_str.encode()).hexdigest()[:16]
    
    stat = os.stat(filepath)
    fast_fingerprint_str = f"{filepath}_{stat.st_size}_{stat.st_mtime}_{schema_fingerprint}"
    fingerprint = hashlib.sha256(fast_fingerprint_str.encode()).hexdigest()[:16]
    
    version_id = f"v_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    return DatasetVersion(
        id=version_id,
        dataset_id=name,
        version_number=1,
        file_hash=fingerprint,
        file_size=stat.st_size,
        storage_path=filepath,
        format=fmt,
        schema=schema,
        row_count=0,
        created_at=datetime.now(timezone.utc)
    )
