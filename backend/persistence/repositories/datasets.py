from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.persistence import models
from core.dataset import Dataset, DatasetVersion, Profile, ColumnProfile
from typing import Optional, List
import json

class DatasetRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_datasets(self, workspace_id: str) -> List[Dataset]:
        orms = self.db.query(models.DatasetORM).filter(models.DatasetORM.workspace_id == workspace_id).all()
        return [self._to_domain_dataset(orm) for orm in orms]

    def get_dataset_by_name(self, name: str, workspace_id: str) -> Optional[Dataset]:
        orm = self.db.query(models.DatasetORM).filter(
            models.DatasetORM.name == name,
            models.DatasetORM.workspace_id == workspace_id
        ).first()
        if not orm:
            return None
        return self._to_domain_dataset(orm)

    def get_dataset_by_id(self, id: str, workspace_id: str) -> Optional[Dataset]:
        orm = self.db.query(models.DatasetORM).filter(
            models.DatasetORM.id == id,
            models.DatasetORM.workspace_id == workspace_id
        ).first()
        if not orm:
            return None
        return self._to_domain_dataset(orm)

    # version getters usually just query by ID, but we should join Dataset to verify workspace
    def get_version_by_id(self, version_id: str, workspace_id: str) -> Optional[DatasetVersion]:
        orm = self.db.query(models.DatasetVersionORM).join(models.DatasetORM).filter(
            models.DatasetVersionORM.id == version_id,
            models.DatasetORM.workspace_id == workspace_id
        ).first()
        if not orm:
            return None
        return self._to_domain_version(orm)

    def get_version_by_hash(self, dataset_id: str, file_hash: str) -> Optional[DatasetVersion]:
        orm = self.db.query(models.DatasetVersionORM).filter(
            models.DatasetVersionORM.dataset_id == dataset_id,
            models.DatasetVersionORM.file_hash == file_hash
        ).first()
        if not orm:
            return None
        return self._to_domain_version(orm)

    def get_next_version_number(self, dataset_id: str) -> int:
        max_v = self.db.query(func.max(models.DatasetVersionORM.version_number)).filter(
            models.DatasetVersionORM.dataset_id == dataset_id
        ).scalar()
        return (max_v or 0) + 1

    def create_dataset(self, dataset: Dataset) -> None:
        orm = models.DatasetORM(
            id=dataset.id,
            name=dataset.name,
            workspace_id=dataset.workspace_id,
            created_at=func.now()
        )
        self.db.add(orm)
        self.db.commit()

    def create_version(self, version: DatasetVersion) -> None:
        orm_v = models.DatasetVersionORM(
            id=version.id,
            dataset_id=version.dataset_id,
            version_number=version.version_number,
            file_hash=version.file_hash,
            file_size=version.file_size,
            storage_path=version.storage_path,
            format=version.format,
            row_count=version.row_count,
            created_at=version.created_at
        )
        self.db.add(orm_v)

        if hasattr(version, 'profile') and version.profile:
            orm_p = models.ProfileORM(
                dataset_version=orm_v,
                row_count=version.profile.row_count
            )
            self.db.add(orm_p)
            
            if hasattr(version.profile, 'columns'):
                for cp in version.profile.columns.values():
                    orm_cp = models.ColumnProfileORM(
                        profile=orm_p,
                        column=cp.name,
                        physical_type=cp.type,
                        row_count=version.profile.row_count,
                        null_count=cp.null_count,
                        null_fraction=cp.null_fraction,
                        unique_count=cp.unique_count or 0,
                        unique_fraction=cp.unique_fraction or 0.0,
                        min_value=json.dumps(cp.min_value) if cp.min_value is not None else None,
                        max_value=json.dumps(cp.max_value) if cp.max_value is not None else None,
                        mean=json.dumps(cp.mean) if cp.mean is not None else None
                    )
                    self.db.add(orm_cp)

        self.db.commit()

    def _to_domain_dataset(self, orm: models.DatasetORM) -> Dataset:
        versions = [self._to_domain_version(v) for v in orm.versions]
        return Dataset(id=orm.id, name=orm.name, workspace_id=orm.workspace_id, versions=versions)

    def _to_domain_version(self, orm: models.DatasetVersionORM) -> DatasetVersion:
        stats = None
        if orm.profile:
            cols = {}
            import json
            for cp in orm.profile.column_profiles:
                cols[cp.column] = {
                    "type": cp.physical_type,
                    "null_count": cp.null_count,
                    "null_fraction": cp.null_fraction,
                    "unique_count": cp.unique_count,
                    "unique_fraction": cp.unique_fraction,
                    "min_value": json.loads(cp.min_value) if cp.min_value else None,
                    "max_value": json.loads(cp.max_value) if cp.max_value else None,
                    "mean": json.loads(cp.mean) if cp.mean else None
                }
            stats = {"row_count": orm.profile.row_count, "columns": cols}

        return DatasetVersion(
            id=orm.id,
            dataset_id=orm.dataset_id,
            version_number=orm.version_number,
            file_hash=orm.file_hash,
            file_size=orm.file_size,
            storage_path=orm.storage_path,
            format=orm.format,
            schema={},
            row_count=orm.row_count,
            created_at=orm.created_at,
            stats=stats
        )

    def delete(self, id: str, workspace_id: str) -> None:
        orm = self.db.query(models.DatasetORM).filter(
            models.DatasetORM.id == id,
            models.DatasetORM.workspace_id == workspace_id
        ).first()
        if orm:
            self.db.delete(orm)
            self.db.commit()
