from backend.datasets.storage import FileTooLargeError
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.persistence.database import get_db
from backend.datasets.service import DatasetService
from backend.persistence.repositories.datasets import DatasetRepository
from pydantic import BaseModel
from datetime import datetime
from backend.api.auth import get_current_workspace

router = APIRouter(prefix="/datasets", tags=["Datasets"])

class DatasetVersionResponse(BaseModel):
    id: str
    version_number: int
    file_hash: str
    file_size: int
    format: str
    row_count: int
    created_at: datetime

class DatasetResponse(BaseModel):
    id: str
    name: str
    latest_version: DatasetVersionResponse

class DatasetHistoryResponse(BaseModel):
    dataset_id: str
    versions: List[DatasetVersionResponse]

@router.post("", response_model=DatasetResponse)
def upload_dataset(
    file: UploadFile = File(...), 
    dataset_name: Optional[str] = Form(None),
    workspace_id: str = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    try:
        repo = DatasetRepository(db)
        svc = DatasetService(repo)
        
        from backend.orchestrator.pipeline import PipelineOrchestrator
        orchestrator = PipelineOrchestrator(db)
        
        import os
        name_to_use = dataset_name if dataset_name else os.path.splitext(file.filename)[0]
        
        dataset = repo.get_dataset_by_name(name_to_use, workspace_id)
        if not dataset:
            import uuid
            from core.dataset import Dataset
            dataset = Dataset(id=f"ds_{uuid.uuid4().hex[:8]}", name=name_to_use, workspace_id=workspace_id, versions=[])
            repo.create_dataset(dataset)
            
        version = orchestrator.process_new_version(dataset.id, file, workspace_id)
        dataset = svc.get_dataset(version.dataset_id, workspace_id)
        
        return DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            latest_version=DatasetVersionResponse(
                id=version.id,
                version_number=version.version_number,
                file_hash=version.file_hash,
                file_size=version.file_size,
                format=version.format,
                row_count=version.row_count,
                created_at=version.created_at
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{dataset_id}/versions", response_model=DatasetVersionResponse)
def create_dataset_version(
    dataset_id: str,
    file: UploadFile = File(...),
    workspace_id: str = Depends(get_current_workspace),
    db: Session = Depends(get_db)
):
    try:
        from backend.orchestrator.pipeline import PipelineOrchestrator
        orchestrator = PipelineOrchestrator(db)
        version = orchestrator.process_new_version(dataset_id, file, workspace_id)
        
        return DatasetVersionResponse(
            id=version.id,
            version_number=version.version_number,
            file_hash=version.file_hash,
            file_size=version.file_size,
            format=version.format,
            row_count=version.row_count,
            created_at=version.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[DatasetResponse])
def list_datasets(workspace_id: str = Depends(get_current_workspace), db: Session = Depends(get_db)):
    repo = DatasetRepository(db)
    datasets = repo.get_all_datasets(workspace_id)
    
    responses = []
    for dataset in datasets:
        latest = max(dataset.versions, key=lambda v: v.version_number) if dataset.versions else None
        if latest:
            responses.append(DatasetResponse(
                id=dataset.id,
                name=dataset.name,
                latest_version=DatasetVersionResponse(
                    id=latest.id,
                    version_number=latest.version_number,
                    file_hash=latest.file_hash,
                    file_size=latest.file_size,
                    format=latest.format,
                    row_count=latest.row_count,
                    created_at=latest.created_at
                )
            ))
    return responses

@router.get("/{dataset_id}/versions", response_model=DatasetHistoryResponse)
def get_versions(dataset_id: str, workspace_id: str = Depends(get_current_workspace), db: Session = Depends(get_db)):
    repo = DatasetRepository(db)
    dataset = repo.get_dataset_by_id(dataset_id, workspace_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    sorted_versions = sorted(dataset.versions, key=lambda v: v.version_number)
    return DatasetHistoryResponse(
        dataset_id=dataset.id,
        versions=[
            DatasetVersionResponse(
                id=v.id,
                version_number=v.version_number,
                file_hash=v.file_hash,
                file_size=v.file_size,
                format=v.format,
                row_count=v.row_count,
                created_at=v.created_at
            ) for v in sorted_versions
        ]
    )
