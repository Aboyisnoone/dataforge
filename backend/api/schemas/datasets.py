from pydantic import BaseModel
from typing import Dict, Any

class ProfileRequest(BaseModel):
    name: str
    filepath: str

class ProfileResponse(BaseModel):
    version_id: str
    format: str
    row_count: int
    columns: Dict[str, Any]
