from enum import Enum
from dataclasses import dataclass

class PhysicalType(str, Enum):
    INTEGER = "INTEGER"
    DOUBLE = "DOUBLE"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    DATETIME = "DATETIME"
    UNKNOWN = "UNKNOWN"

class SemanticRole(str, Enum):
    IDENTIFIER = "IDENTIFIER"
    MEASURE = "MEASURE"
    CATEGORY = "CATEGORY"
    DATETIME = "DATETIME"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    UNKNOWN = "UNKNOWN"

class Sensitivity(str, Enum):
    PII = "PII"
    NON_PII = "NON_PII"

@dataclass
class ColumnSemantics:
    column_name: str
    physical_type: PhysicalType
    semantic_role: SemanticRole
    sensitivity: Sensitivity
