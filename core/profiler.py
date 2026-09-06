import duckdb
from typing import Dict, Any

class Profiler:
    def __init__(self):
        self.con = duckdb.connect(database=':memory:')
        
    def profile(self, location: str, format: str) -> Dict[str, Any]:
        if format == 'csv':
            table_ref = f"read_csv_auto('{location}')"
        elif format == 'parquet':
            table_ref = f"read_parquet('{location}')"
        elif format == 'json' or format == 'ndjson':
            table_ref = f"read_json_auto('{location}')"
        else:
            raise ValueError(f"Unsupported format for profiling: {format}")
            
        try:
            row_count_res = self.con.execute(f"SELECT COUNT(*) FROM {table_ref}").fetchone()
            row_count = row_count_res[0] if row_count_res else 0
            
            columns_info = self.con.execute(f"DESCRIBE SELECT * FROM {table_ref}").fetchall()
            
            stats = {
                "row_count": row_count,
                "columns": {}
            }
            
            for col_info in columns_info:
                col_name = col_info[0]
                col_type = col_info[1]
                
                is_numeric = col_type in [
                    'BIGINT', 'INTEGER', 'DOUBLE', 'FLOAT', 
                    'DECIMAL', 'HUGEINT', 'TINYINT', 'SMALLINT'
                ]
                
                query_parts = [
                    f'COUNT("{col_name}") as not_null_count',
                    f'APPROX_COUNT_DISTINCT("{col_name}") as unique_count'
                ]
                
                if is_numeric:
                    query_parts.extend([
                        f'MIN("{col_name}") as min_val',
                        f'MAX("{col_name}") as max_val',
                        f'AVG("{col_name}") as mean_val'
                    ])
                    
                query = f"SELECT {', '.join(query_parts)} FROM {table_ref}"
                res = self.con.execute(query).fetchone()
                
                not_null_count = res[0]
                null_count = row_count - not_null_count
                unique_count = res[1]
                
                col_stats = {
                    "name": col_name,
                    "dtype": col_type,
                    "null_count": null_count,
                    "null_fraction": null_count / row_count if row_count > 0 else 0.0,
                    "unique_count": unique_count,
                }
                
                if is_numeric:
                    col_stats["min"] = res[2]
                    col_stats["max"] = res[3]
                    col_stats["mean"] = res[4]
                    
                stats["columns"][col_name] = col_stats
                
            return stats
        except Exception as e:
            raise ValueError(f"Malformed dataset file. Parser error: {str(e)}")
