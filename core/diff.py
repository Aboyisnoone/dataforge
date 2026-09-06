from dataclasses import dataclass
from typing import List, Optional, Any, Dict
from core.dataset.models import DatasetVersion, Profile, ColumnProfile

@dataclass
class SchemaChange:
    column: str
    change_type: str  # 'added', 'removed', 'type_changed'
    previous_type: Optional[str] = None
    current_type: Optional[str] = None

@dataclass
class ColumnChange:
    column: str
    metric: str
    previous_value: Any
    current_value: Any
    absolute_delta: float
    relative_delta: Optional[float]
    change_type: str

@dataclass
class DatasetDiff:
    dataset_id: str
    previous_version_id: str
    current_version_id: str
    schema_changes: List[SchemaChange]
    column_changes: List[ColumnChange]
    summary: str

class HistoricalDiffEngine:
    def compare(self, v1: DatasetVersion, v2: DatasetVersion) -> DatasetDiff:
        if not v1.profile or not v2.profile:
            raise ValueError("Both dataset versions must have profiles to compare.")

        schema_changes: List[SchemaChange] = []
        column_changes: List[ColumnChange] = []

        # Map column profiles by name for quick lookup
        cp1_map: Dict[str, ColumnProfile] = v1.profile.columns
        cp2_map: Dict[str, ColumnProfile] = v2.profile.columns

        # 1. Schema Changes
        added_cols = set(cp2_map.keys()) - set(cp1_map.keys())
        removed_cols = set(cp1_map.keys()) - set(cp2_map.keys())
        common_cols = set(cp1_map.keys()).intersection(set(cp2_map.keys()))

        for col in added_cols:
            schema_changes.append(SchemaChange(
                column=col,
                change_type="added",
                current_type=cp2_map[col].type
            ))
            
        for col in removed_cols:
            schema_changes.append(SchemaChange(
                column=col,
                change_type="removed",
                previous_type=cp1_map[col].type
            ))

        for col in common_cols:
            if cp1_map[col].type != cp2_map[col].type:
                schema_changes.append(SchemaChange(
                    column=col,
                    change_type="type_changed",
                    previous_type=cp1_map[col].type,
                    current_type=cp2_map[col].type
                ))

        # 2. Row Count Changes (Dataset Level)
        if v1.profile.row_count != v2.profile.row_count:
            old_rc = v1.profile.row_count
            new_rc = v2.profile.row_count
            abs_delta = new_rc - old_rc
            rel_delta = abs_delta / old_rc if old_rc > 0 else float('inf')
            column_changes.append(ColumnChange(
                column="*dataset*",
                metric="row_count",
                previous_value=old_rc,
                current_value=new_rc,
                absolute_delta=abs_delta,
                relative_delta=rel_delta,
                change_type="row_count_shift"
            ))

        # 3. Column Stats Changes
        for col in common_cols:
            c1 = cp1_map[col]
            c2 = cp2_map[col]

                        # Null fraction
            if c1.null_fraction is not None and c2.null_fraction is not None and abs(c1.null_fraction - c2.null_fraction) > 0.0001:
                abs_delta = c2.null_fraction - c1.null_fraction
                rel_delta = abs_delta / c1.null_fraction if c1.null_fraction > 0 else float('inf')
                column_changes.append(ColumnChange(
                    column=col, metric="null_fraction",
                    previous_value=c1.null_fraction, current_value=c2.null_fraction,
                    absolute_delta=abs_delta, relative_delta=rel_delta,
                    change_type="null_rate_shift"
                ))

            # Unique fraction / cardinality
            if c1.unique_fraction is not None and c2.unique_fraction is not None and abs(c1.unique_fraction - c2.unique_fraction) > 0.0001:
                abs_delta = c2.unique_fraction - c1.unique_fraction
                rel_delta = abs_delta / c1.unique_fraction if c1.unique_fraction > 0 else float('inf')
                column_changes.append(ColumnChange(
                    column=col, metric="unique_fraction",
                    previous_value=c1.unique_fraction, current_value=c2.unique_fraction,
                    absolute_delta=abs_delta, relative_delta=rel_delta,
                    change_type="cardinality_shift"
                ))
                
            # Mean (Distribution shift)
            if c1.mean is not None and c2.mean is not None:
                try:
                    m1 = float(c1.mean)
                    m2 = float(c2.mean)
                    if abs(m1 - m2) > 0.0001:
                        abs_delta = m2 - m1
                        rel_delta = abs_delta / abs(m1) if m1 != 0 else float('inf')
                        column_changes.append(ColumnChange(
                            column=col, metric="mean",
                            previous_value=m1, current_value=m2,
                            absolute_delta=abs_delta, relative_delta=rel_delta,
                            change_type="distribution_shift"
                        ))
                except (ValueError, TypeError):
                    pass
                    
            # Min / Max
            if c1.min_value != c2.min_value and c1.min_value is not None and c2.min_value is not None:
                try:
                    m1 = float(c1.min_value)
                    m2 = float(c2.min_value)
                    abs_delta = m2 - m1
                    rel_delta = abs_delta / abs(m1) if m1 != 0 else float('inf')
                    column_changes.append(ColumnChange(
                        column=col, metric="min_value",
                        previous_value=c1.min_value, current_value=c2.min_value,
                        absolute_delta=abs_delta, relative_delta=rel_delta,
                        change_type="min_shift"
                    ))
                except (ValueError, TypeError):
                    # For non-numeric min/max, absolute/relative delta might not make sense, 
                    # but we can record it as 0.0
                    column_changes.append(ColumnChange(
                        column=col, metric="min_value",
                        previous_value=c1.min_value, current_value=c2.min_value,
                        absolute_delta=0.0, relative_delta=0.0,
                        change_type="min_shift"
                    ))
                    
            if c1.max_value != c2.max_value and c1.max_value is not None and c2.max_value is not None:
                try:
                    m1 = float(c1.max_value)
                    m2 = float(c2.max_value)
                    abs_delta = m2 - m1
                    rel_delta = abs_delta / abs(m1) if m1 != 0 else float('inf')
                    column_changes.append(ColumnChange(
                        column=col, metric="max_value",
                        previous_value=c1.max_value, current_value=c2.max_value,
                        absolute_delta=abs_delta, relative_delta=rel_delta,
                        change_type="max_shift"
                    ))
                except (ValueError, TypeError):
                    column_changes.append(ColumnChange(
                        column=col, metric="max_value",
                        previous_value=c1.max_value, current_value=c2.max_value,
                        absolute_delta=0.0, relative_delta=0.0,
                        change_type="max_shift"
                    ))

        # Generate summary
        sc_count = len(schema_changes)
        cc_count = len(column_changes)
        if sc_count == 0 and cc_count == 0:
            summary = "No changes detected."
        else:
            summary = f"Detected {sc_count} schema changes and {cc_count} column statistical changes."

        return DatasetDiff(
            dataset_id=v1.dataset_id,
            previous_version_id=v1.id,
            current_version_id=v2.id,
            schema_changes=schema_changes,
            column_changes=column_changes,
            summary=summary
        )
