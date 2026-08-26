"""
DuckDB service for analytical SQL queries
"""
import duckdb
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
from backend.utils.errors import ExecutionError
from backend.utils.security import validate_sql_readonly
import logging
import time

logger = logging.getLogger(__name__)


class DuckDBService:
    """Manages DuckDB connection and query execution"""

    def __init__(self, db_path: str = "./data/analytics.duckdb"):
        self.db_path = db_path
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        self._connect()

    def _connect(self):
        """Initialize DuckDB connection"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(self.db_path)
        # Set pragmas for better performance
        self.conn.execute("PRAGMA threads=4")
        self.conn.execute("PRAGMA memory_limit='2GB'")
        logger.info(f"DuckDB connected to {self.db_path}")

    def register_table(self, table_name: str, df: pd.DataFrame) -> None:
        """Register a pandas DataFrame as a DuckDB table"""
        if self.conn is None:
            self._connect()

        # Drop if exists (both table and view)
        self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        self.conn.execute(f"DROP VIEW IF EXISTS {table_name}")

        # Register DataFrame properly - use a temp view then create table
        temp_view = f"temp_{table_name}"
        self.conn.execute(f"DROP VIEW IF EXISTS {temp_view}")
        self.conn.register(temp_view, df)
        # Create actual table for persistence
        try:
            self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {temp_view}")
        finally:
            self.conn.execute(f"DROP VIEW IF EXISTS {temp_view}")
        logger.info(f"Registered table: {table_name} ({len(df)} rows)")

    def drop_table(self, table_name: str) -> None:
        """Drop a table or view"""
        if self.conn is None:
            return
        try:
            # Drop both table and view to handle all cases
            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.conn.execute(f"DROP VIEW IF EXISTS {table_name}")
            logger.info(f"Dropped table/view: {table_name}")
        except Exception as e:
            logger.warning(f"Failed to drop table/view {table_name}: {e}")

    def execute(self, sql: str, params: Optional[List] = None) -> pd.DataFrame:
        """Execute a read-only SQL query and return results as DataFrame"""
        if self.conn is None:
            self._connect()

        # Validate SQL is read-only
        validate_sql_readonly(sql)

        start_time = time.time()
        try:
            result = self.conn.execute(sql, params or []).fetchdf()
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"SQL executed in {elapsed:.2f}ms, returned {len(result)} rows")
            logger.debug(f"SQL: {sql[:500]}")
            return result
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"SQL execution failed after {elapsed:.2f}ms: {e}")
            logger.debug(f"Failed SQL: {sql[:500]}")
            raise ExecutionError(f"Query execution failed: {str(e)}")

    def execute_raw(self, sql: str) -> Any:
        """Execute raw SQL (for DDL operations)"""
        if self.conn is None:
            self._connect()
        return self.conn.execute(sql)

    def get_tables(self) -> List[str]:
        """Get list of all tables"""
        if self.conn is None:
            self._connect()
        result = self.conn.execute("SHOW TABLES").fetchdf()
        return result['name'].tolist() if len(result) > 0 else []

    def get_schema(self, table_name: str) -> pd.DataFrame:
        """Get schema for a table"""
        if self.conn is None:
            self._connect()
        return self.conn.execute(f"DESCRIBE {table_name}").fetchdf()

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        if self.conn is None:
            self._connect()
        try:
            self.conn.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
            return True
        except Exception:
            return False

    def close(self):
        """Close the connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("DuckDB connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()