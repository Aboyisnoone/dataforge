import re
from typing import Dict, Any
from .models import ColumnSemantics, PhysicalType, SemanticRole, Sensitivity

class SemanticClassifier:
    
    def _map_physical_type(self, dtype: str) -> PhysicalType:
        dtype = dtype.upper()
        if dtype in ('BIGINT', 'INTEGER', 'TINYINT', 'SMALLINT', 'HUGEINT'):
            return PhysicalType.INTEGER
        elif dtype in ('DOUBLE', 'FLOAT', 'DECIMAL'):
            return PhysicalType.DOUBLE
        elif dtype in ('VARCHAR', 'STRING'):
            return PhysicalType.STRING
        elif dtype == 'BOOLEAN':
            return PhysicalType.BOOLEAN
        elif 'DATE' in dtype or 'TIMESTAMP' in dtype or 'TIME' in dtype:
            return PhysicalType.DATETIME
        return PhysicalType.UNKNOWN

    def _infer_semantic_role(self, col_name: str, phys_type: PhysicalType, stats: Dict[str, Any], total_rows: int) -> SemanticRole:
        name_lower = col_name.lower()
        
        # Datetime
        if phys_type == PhysicalType.DATETIME or name_lower.endswith('_at') or name_lower.endswith('_date'):
            return SemanticRole.DATETIME
            
        # Identifier heuristics
        if name_lower == 'id' or name_lower.endswith('_id'):
            return SemanticRole.IDENTIFIER
        
        # High uniqueness on a relatively large set could be an identifier
        if total_rows > 0:
            unique_ratio = stats.get('unique_count', 0) / total_rows
            if unique_ratio > 0.95 and phys_type in (PhysicalType.INTEGER, PhysicalType.STRING):
                if stats.get('null_fraction', 1.0) < 0.05:
                    return SemanticRole.IDENTIFIER
        
        # Boolean
        if phys_type == PhysicalType.BOOLEAN or name_lower.startswith('is_') or name_lower.startswith('has_'):
            return SemanticRole.BOOLEAN
            
        # Category vs Measure for Numeric
        if phys_type in (PhysicalType.INTEGER, PhysicalType.DOUBLE):
            if phys_type == PhysicalType.DOUBLE:
                return SemanticRole.MEASURE
            
            # If it's an integer but has very low cardinality compared to total rows
            if total_rows > 100 and stats.get('unique_count', 0) < 10:
                return SemanticRole.CATEGORY
            
            return SemanticRole.MEASURE
            
        # Category vs Text for String
        if phys_type == PhysicalType.STRING:
            if total_rows > 0:
                unique_ratio = stats.get('unique_count', 0) / total_rows
                if unique_ratio < 0.05 or stats.get('unique_count', 0) < 100:
                    return SemanticRole.CATEGORY
            return SemanticRole.TEXT
            
        return SemanticRole.UNKNOWN

    def _infer_sensitivity(self, col_name: str, semantic_role: SemanticRole) -> Sensitivity:
        name_lower = col_name.lower()
        pii_keywords = {'email', 'ssn', 'phone', 'address', 'ip_address', 'credit_card', 'password', 'first_name', 'last_name'}
        
        if any(kw in name_lower for kw in pii_keywords):
            return Sensitivity.PII
            
        if name_lower == 'email': # Explicit coverage
            return Sensitivity.PII
            
        return Sensitivity.NON_PII

    def classify(self, col_name: str, col_stats: Dict[str, Any], total_rows: int) -> ColumnSemantics:
        phys_type = self._map_physical_type(col_stats.get('dtype', ''))
        sem_role = self._infer_semantic_role(col_name, phys_type, col_stats, total_rows)
        sensitivity = self._infer_sensitivity(col_name, sem_role)
        
        return ColumnSemantics(
            column_name=col_name,
            physical_type=phys_type,
            semantic_role=sem_role,
            sensitivity=sensitivity
        )
