import sqlite3
import time
import logging
import os
import tempfile
from typing import List, Dict, Any, Tuple
import polars as pl
from core.storage import get_storage_service
from core.investigation.experiment import ExperimentResult

logger = logging.getLogger(__name__)

class ExperimentExecutionEngine:
    def __init__(self, dataset_path: str, table_name: str = "dataset"):
        self.dataset_path = dataset_path
        self.table_name = table_name

    def _load_data(self, conn: sqlite3.Connection, actual_path: str):
        logger.info(f"Loading {self.dataset_path} into in-memory SQLite table {self.table_name}")
        ext = os.path.splitext(self.dataset_path)[1].lower()
        if ext == '.parquet':
            df = pl.read_parquet(actual_path)
        elif ext == '.json':
            df = pl.read_json(actual_path)
        elif ext == '.ndjson':
            df = pl.read_ndjson(actual_path)
        else:
            df = pl.read_csv(actual_path)
        schema = df.schema
        
        cols = []
        for name, dtype in schema.items():
            if dtype in (pl.Int64, pl.Int32, pl.Int16, pl.Int8, pl.UInt64, pl.UInt32, pl.UInt16, pl.UInt8):
                sql_type = "INTEGER"
            elif dtype in (pl.Float64, pl.Float32):
                sql_type = "REAL"
            elif dtype == pl.Boolean:
                sql_type = "BOOLEAN"
            else:
                sql_type = "TEXT"
            cols.append(f'{name} {sql_type}')
            
        create_stmt = f"CREATE TABLE {self.table_name} ({', '.join(cols)})"
        
        cursor = conn.cursor()
        cursor.execute(create_stmt)
        
        placeholders = ", ".join(["?"] * len(schema))
        insert_stmt = f"INSERT INTO {self.table_name} VALUES ({placeholders})"
        
        cursor.executemany(insert_stmt, df.rows())
        conn.commit()

    def _authorizer(self, action, arg1, arg2, dbname, trigger_name):
        if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION):
            return sqlite3.SQLITE_OK
            
        if action in (sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE, 
                      sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_DROP_INDEX, sqlite3.SQLITE_DROP_VTABLE,
                      sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_CREATE_TABLE):
            return sqlite3.SQLITE_DENY
            
        blacklist = [
            sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
            sqlite3.SQLITE_ALTER_TABLE, sqlite3.SQLITE_DROP_TABLE,
            sqlite3.SQLITE_DROP_VTABLE, sqlite3.SQLITE_DROP_INDEX,
            sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_CREATE_INDEX,
            sqlite3.SQLITE_CREATE_TEMP_TABLE, sqlite3.SQLITE_DROP_TEMP_TABLE,
            sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH
        ]
        if action in blacklist:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    def execute_query(self, query: str, sample_limit: int = 50) -> ExperimentResult:
        start_time = time.time()
        conn = sqlite3.connect(":memory:")
        
        storage = get_storage_service()
        ext = os.path.splitext(self.dataset_path)[1].lower()
        
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp_path = tmp.name
            
        try:
            storage.download_file(self.dataset_path, tmp_path)
            self._load_data(conn, tmp_path)
            conn.set_authorizer(self._authorizer)
            
            cursor = conn.cursor()
            cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            
            rows = cursor.fetchall()
            row_count = len(rows)
            
            sample_data = [dict(zip(columns, row)) for row in rows[:sample_limit]]
            
            execution_time = time.time() - start_time
            
            return ExperimentResult(
                row_count=row_count,
                columns=list(sample_data[0].keys()) if sample_data else [],
                sample_rows=sample_data,
                execution_time_ms=execution_time * 1000
            )
            
        except sqlite3.DatabaseError as e:
            return ExperimentResult(
                row_count=0,
                columns=[],
                sample_rows=[],
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return ExperimentResult(
                row_count=0,
                columns=[],
                sample_rows=[],
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
        finally:
            conn.close()
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
