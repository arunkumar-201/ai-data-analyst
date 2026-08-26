"""
Tests for SQL functionality
"""
import pytest
import pandas as pd
from backend.services.duckdb_service import DuckDBService
from backend.tools.sql_tool import SQLTool
from backend.utils.errors import ExecutionError
from backend.utils.security import validate_sql_readonly


class TestDuckDBService:
    """Test DuckDB service functionality"""

    @pytest.fixture
    def duckdb_service(self):
        service = DuckDBService(db_path=":memory:")
        yield service
        service.close()

    @pytest.fixture
    def sample_data(self):
        """Create sample DataFrame"""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 40, 45],
            'salary': [50000, 60000, 70000, 80000, 90000],
            'department': ['Engineering', 'Sales', 'Engineering', 'Marketing', 'Sales']
        })

    def test_register_table(self, duckdb_service, sample_data):
        """Test registering a DataFrame as a table"""
        duckdb_service.register_table("employees", sample_data)
        tables = duckdb_service.get_tables()
        assert "employees" in tables

    def test_execute_simple_select(self, duckdb_service, sample_data):
        """Test executing a simple SELECT query"""
        duckdb_service.register_table("employees", sample_data)
        result = duckdb_service.execute("SELECT * FROM employees")
        assert len(result) == 5
        assert list(result.columns) == ['id', 'name', 'age', 'salary', 'department']

    def test_execute_with_where(self, duckdb_service, sample_data):
        """Test executing SELECT with WHERE clause"""
        duckdb_service.register_table("employees", sample_data)
        result = duckdb_service.execute("SELECT * FROM employees WHERE age > 30")
        assert len(result) == 3
        assert all(result['age'] > 30)

    def test_execute_aggregation(self, duckdb_service, sample_data):
        """Test executing aggregation queries"""
        duckdb_service.register_table("employees", sample_data)
        result = duckdb_service.execute("SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department")
        assert len(result) == 3
        assert 'avg_salary' in result.columns

    def test_execute_order_by_limit(self, duckdb_service, sample_data):
        """Test ORDER BY and LIMIT"""
        duckdb_service.register_table("employees", sample_data)
        result = duckdb_service.execute("SELECT * FROM employees ORDER BY salary DESC LIMIT 2")
        assert len(result) == 2
        assert result.iloc[0]['salary'] == 90000
        assert result.iloc[1]['salary'] == 80000

    def test_execute_join(self, duckdb_service):
        """Test JOIN operations"""
        df1 = pd.DataFrame({'id': [1, 2, 3], 'name': ['A', 'B', 'C'], 'dept_id': [10, 20, 10]})
        df2 = pd.DataFrame({'dept_id': [10, 20], 'dept_name': ['Engineering', 'Sales']})
        duckdb_service.register_table("employees", df1)
        duckdb_service.register_table("departments", df2)

        result = duckdb_service.execute("""
            SELECT e.name, d.dept_name
            FROM employees e
            JOIN departments d ON e.dept_id = d.dept_id
        """)
        assert len(result) == 3
        assert 'dept_name' in result.columns

    def test_get_schema(self, duckdb_service, sample_data):
        """Test getting table schema"""
        duckdb_service.register_table("employees", sample_data)
        schema = duckdb_service.get_schema("employees")
        assert len(schema) == 5
        assert 'column_name' in schema.columns
        assert 'column_type' in schema.columns

    def test_table_exists(self, duckdb_service, sample_data):
        """Test table existence check"""
        assert not duckdb_service.table_exists("employees")
        duckdb_service.register_table("employees", sample_data)
        assert duckdb_service.table_exists("employees")

    def test_drop_table(self, duckdb_service, sample_data):
        """Test dropping a table"""
        duckdb_service.register_table("employees", sample_data)
        assert duckdb_service.table_exists("employees")
        duckdb_service.drop_table("employees")
        assert not duckdb_service.table_exists("employees")


class TestSQLSecurity:
    """Test SQL security validation"""

    def test_validate_select_only(self):
        """Test that SELECT queries pass"""
        assert validate_sql_readonly("SELECT * FROM table") is None
        assert validate_sql_readonly("SELECT a, b FROM table WHERE c = 1") is None
        assert validate_sql_readonly("WITH cte AS (SELECT * FROM t) SELECT * FROM cte") is None

    def test_reject_insert(self):
        """Test that INSERT is rejected"""
        with pytest.raises(Exception):
            validate_sql_readonly("INSERT INTO table VALUES (1, 2)")

    def test_reject_update(self):
        """Test that UPDATE is rejected"""
        with pytest.raises(Exception):
            validate_sql_readonly("UPDATE table SET a = 1")

    def test_reject_delete(self):
        """Test that DELETE is rejected"""
        with pytest.raises(Exception):
            validate_sql_readonly("DELETE FROM table")

    def test_reject_drop(self):
        """Test that DROP is rejected"""
        with pytest.raises(Exception):
            validate_sql_readonly("DROP TABLE table")

    def test_reject_create(self):
        """Test that CREATE is rejected"""
        with pytest.raises(Exception):
            validate_sql_readonly("CREATE TABLE table (a INT)")

    def test_reject_alter(self):
        """Test that ALTER is rejected"""
        with pytest.raises(Exception):
            validate_sql_readonly("ALTER TABLE table ADD COLUMN b INT")


class TestSQLTool:
    """Test SQL tool functionality"""

    @pytest.fixture
    def duckdb_service(self):
        service = DuckDBService(db_path=":memory:")
        yield service
        service.close()

    @pytest.fixture
    def sql_tool(self, duckdb_service):
        return SQLTool(duckdb_service)

    @pytest.fixture
    def sample_data(self):
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
            'age': [25, 30, 35, 40, 45],
            'salary': [50000, 60000, 70000, 80000, 90000],
            'department': ['Engineering', 'Sales', 'Engineering', 'Marketing', 'Sales']
        })

    def test_execute_valid_sql(self, sql_tool, sample_data):
        """Test executing valid SQL"""
        # Register table first
        sql_tool.duckdb.register_table("employees", sample_data)
        result = sql_tool.execute("SELECT * FROM employees WHERE age > 30")
        assert result['success'] is True
        assert result['row_count'] == 3
        assert len(result['data']) == 3

    def test_execute_invalid_sql(self, sql_tool):
        """Test executing invalid SQL"""
        result = sql_tool.execute("SELECT * FROM nonexistent_table")
        assert result['success'] is False
        assert 'error' in result

    def test_execute_non_select(self, sql_tool):
        """Test that non-SELECT queries are rejected"""
        result = sql_tool.execute("INSERT INTO employees VALUES (6, 'Frank', 30, 55000, 'HR')")
        assert result['success'] is False
        assert 'error' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])