"""
SQL execution tool
"""
import pandas as pd
from typing import Dict, Any, Optional
from backend.services.duckdb_service import DuckDBService
from backend.utils.errors import ExecutionError
from backend.utils.security import validate_sql_readonly
import logging
import time

logger = logging.getLogger(__name__)


class SQLTool:
    """Tool for executing SQL queries"""

    def __init__(self, duckdb_service: DuckDBService, registry=None):
        self.duckdb = duckdb_service
        self.registry = registry

    def execute(self, sql: str, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a SQL query"""
        start_time = time.time()

        try:
            # Validate SQL
            validate_sql_readonly(sql)

            # Execute
            result_df = self.duckdb.execute(sql)

            elapsed = (time.time() - start_time) * 1000

            return {
                "success": True,
                "data": result_df.to_dict(orient="records"),
                "columns": result_df.columns.tolist(),
                "row_count": len(result_df),
                "execution_time_ms": round(elapsed, 2),
                "sql": sql
            }

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"SQL execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "sql": sql,
                "execution_time_ms": round(elapsed, 2)
            }

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM"""
        return {
            "name": "execute_sql",
            "description": "Execute a read-only SQL query on registered datasets. Use DuckDB syntax.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL SELECT query to execute"
                    },
                    "dataset_id": {
                        "type": "string",
                        "description": "Dataset ID to query (optional if table name in SQL)"
                    }
                },
                "required": ["sql"]
            }
        }

    def explain_query(self, sql: str) -> Dict[str, Any]:
        """Get query execution plan"""
        try:
            plan = self.duckdb.execute_raw(f"EXPLAIN {sql}").fetchall()
            return {
                "success": True,
                "plan": str(plan)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }