import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

@dataclass
class ColumnProfile:
    name: str
    type: str
    null_count: int
    null_fraction: float
    unique_count: Optional[int] = None
    unique_fraction: Optional[float] = None
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean: Optional[float] = None
    std_dev: Optional[float] = None

@dataclass
class Profile:
    row_count: int
    columns: Dict[str, ColumnProfile]
    
@dataclass
class DatasetVersion:
    dataset_id: str
    version_number: int
    file_hash: str
    file_size: int
    storage_path: str
    format: str
    schema: Dict[str, Any]
    row_count: int = 0
    stats: Optional[Dict[str, Any]] = None
    id: str = field(default_factory=lambda: f"v_{uuid.uuid4().hex[:8]}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def profile(self) -> Profile:
        if not self.stats:
            return Profile(row_count=self.row_count, columns={})
        
        cols = {}
        for cname, cstat in self.stats.get("columns", {}).items():
            cols[cname] = ColumnProfile(
                name=cname,
                type=cstat.get("type", "unknown"),
                null_count=cstat.get("null_count", 0),
                null_fraction=cstat.get("null_fraction", 0.0),
                unique_count=cstat.get("unique_count"),
                unique_fraction=cstat.get("unique_fraction"),
                min_value=cstat.get("min_value"),
                max_value=cstat.get("max_value"),
                mean=cstat.get("mean"),
                std_dev=cstat.get("std_dev")
            )
        return Profile(row_count=self.stats.get("row_count", self.row_count), columns=cols)

@dataclass
class Dataset:
    name: str
    workspace_id: str = "ws_local_dev"
    versions: List[DatasetVersion] = field(default_factory=list)
    id: str = field(default_factory=lambda: f"ds_{uuid.uuid4().hex[:8]}")
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
