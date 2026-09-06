import re

with open('backend/api/routes/datasets.py', 'r') as f:
    text = f.read()

new_get_endpoint = '''@router.get("", response_model=List[DatasetResponse])
def list_datasets(db: Session = Depends(get_db)):
    repo = DatasetRepository(db)
    datasets = repo.get_all_datasets() # Need to check if this exists, if not we will implement it
    
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

@router.get("/{dataset_id}/versions",'''

text = text.replace('@router.get("/{dataset_id}/versions",', new_get_endpoint)

with open('backend/api/routes/datasets.py', 'w') as f:
    f.write(text)
