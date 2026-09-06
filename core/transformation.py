from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import polars as pl
import os

@dataclass
class Transformation:
    type_name: str
    parameters: Dict[str, Any]
    input_fingerprint: str
    output_fingerprint: str
    timestamp: datetime
    affected_columns: List[str]
    generated_code: str
    
class TransformationEngine:
    """
    Applies transformations to datasets and tracks the operation metadata.
    In this spike, we use Polars to execute the transformations eagerly.
    """
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def _read_file(self, filepath: str) -> pl.DataFrame:
        if filepath.endswith('.csv'):
            return pl.read_csv(filepath)
        elif filepath.endswith('.parquet'):
            return pl.read_parquet(filepath)
        raise ValueError("Unsupported format")

    def _write_and_track(self, result_df: pl.DataFrame, type_name: str, params: Dict[str, Any], 
                         input_fp: str, affected: List[str], code: str) -> Tuple[str, Transformation]:
        timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
        out_file = os.path.join(self.output_dir, f"transformed_{timestamp_str}.csv")
        result_df.write_csv(out_file)
        
        # For the spike, the output fingerprint is just a timestamp mock. 
        # In reality, this would trigger the fingerprinting engine.
        output_fp = f"fp_out_{timestamp_str}"
        
        t = Transformation(
            type_name=type_name,
            parameters=params,
            input_fingerprint=input_fp,
            output_fingerprint=output_fp,
            timestamp=datetime.now(timezone.utc),
            affected_columns=affected,
            generated_code=code
        )
        return out_file, t

    def apply_drop_duplicates(self, filepath: str, subset: List[str], input_fingerprint: str) -> Tuple[str, Transformation]:
        df = self._read_file(filepath)
        result_df = df.unique(subset=subset, maintain_order=True)
        
        subset_str = ", ".join(f"'{s}'" for s in subset)
        code = f"df = df.unique(subset=[{subset_str}], maintain_order=True)"
        
        return self._write_and_track(
            result_df, 
            type_name="drop_duplicates", 
            params={"subset": subset}, 
            input_fp=input_fingerprint, 
            affected=subset, 
            code=code
        )
        
    def apply_fill_nulls(self, filepath: str, column: str, value: Any, input_fingerprint: str) -> Tuple[str, Transformation]:
        df = self._read_file(filepath)
        result_df = df.with_columns(pl.col(column).fill_null(value))
        
        if isinstance(value, str):
            code = f"df = df.with_columns(pl.col('{column}').fill_null('{value}'))"
        else:
            code = f"df = df.with_columns(pl.col('{column}').fill_null({value}))"
            
        return self._write_and_track(
            result_df, 
            type_name="fill_nulls", 
            params={"column": column, "value": value}, 
            input_fp=input_fingerprint, 
            affected=[column], 
            code=code
        )
