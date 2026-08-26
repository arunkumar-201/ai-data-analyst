"""
Tests for upload functionality
"""
import pytest
import tempfile
import os
from pathlib import Path
from backend.data.loader import DataLoader
from backend.data.registry import DatasetRegistry
from backend.services.duckdb_service import DuckDBService
from backend.utils.security import validate_file_extension, validate_file_size, sanitize_filename, generate_dataset_id
from backend.utils.errors import ValidationError, FileError
import json


def create_temp_csv(content: str) -> str:
    """Create a temporary CSV file that persists until explicitly deleted."""
    fd, fname = tempfile.mkstemp(suffix='.csv', text=True)
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    return fname


class TestFileValidation:
    """Test file validation utilities"""

    def test_validate_file_extension_valid(self):
        """Test valid CSV extensions"""
        assert validate_file_extension("test.csv") is None
        assert validate_file_extension("test.CSV") is None
        assert validate_file_extension("data.Csv") is None

    def test_validate_file_extension_invalid(self):
        """Test invalid extensions"""
        with pytest.raises(ValidationError):
            validate_file_extension("test.txt")
        with pytest.raises(ValidationError):
            validate_file_extension("test.xlsx")
        with pytest.raises(ValidationError):
            validate_file_extension("test.json")

    def test_validate_file_size_valid(self):
        """Test valid file sizes"""
        assert validate_file_size(1024) is None  # 1 KB
        assert validate_file_size(10 * 1024 * 1024) is None  # 10 MB

    def test_validate_file_size_invalid(self):
        """Test invalid file sizes"""
        with pytest.raises(ValidationError):
            validate_file_size(0)
        with pytest.raises(ValidationError):
            validate_file_size(-1)

    def test_validate_file_size_too_large(self):
        """Test file size exceeding maximum"""
        # Default max is 200MB, so test with 300MB
        with pytest.raises(ValidationError):
            validate_file_size(300 * 1024 * 1024)  # 300 MB - too large

    def test_sanitize_filename(self):
        """Test filename sanitization"""
        assert sanitize_filename("normal.csv") == "normal.csv"
        assert sanitize_filename("file with spaces.csv") == "file_with_spaces.csv"
        assert sanitize_filename("file<script>.csv") == "filescript.csv"
        # os.path.basename removes path components
        assert sanitize_filename("../../../etc/passwd.csv") == "passwd.csv"

    def test_generate_dataset_id(self):
        """Test dataset ID generation"""
        id1 = generate_dataset_id("sales_data.csv")
        id2 = generate_dataset_id("sales_data.csv")
        # Should be different each time (includes hash)
        assert id1.startswith("sales_data_")
        assert id2.startswith("sales_data_")
        assert len(id1) > len("sales_data_")


class TestDataLoader:
    """Test data loading functionality"""

    @pytest.fixture
    def sample_csv(self):
        """Create a temporary CSV file for testing"""
        content = """id,name,value,category
1,Item A,100,Electronics
2,Item B,200,Clothing
3,Item C,150,Electronics
4,Item D,300,Home
5,Item E,250,Clothing"""
        fname = create_temp_csv(content)
        yield fname
        os.unlink(fname)

    @pytest.fixture
    def loader(self):
        return DataLoader()

    def test_load_csv(self, loader, sample_csv):
        """Test loading a CSV file"""
        df = loader.load(sample_csv)
        assert len(df) == 5
        assert list(df.columns) == ['id', 'name', 'value', 'category']
        assert df['value'].dtype in ['int64', 'float64']

    def test_get_preview(self, loader, sample_csv):
        """Test preview functionality"""
        df = loader.get_preview(sample_csv, nrows=3)
        assert len(df) == 3

    def test_get_file_info(self, loader, sample_csv):
        """Test file info extraction"""
        info = loader.get_file_info(sample_csv)
        assert info['rows'] == 5
        assert info['columns'] == 4
        assert info['size_bytes'] > 0
        assert 'dtypes' in info

    def test_detect_encoding(self, loader, sample_csv):
        """Test encoding detection"""
        encoding = loader.detect_encoding(sample_csv)
        assert encoding in ['utf-8', 'ascii']


class TestDatasetRegistry:
    """Test dataset registry functionality"""

    @pytest.fixture
    def duckdb_service(self):
        service = DuckDBService(db_path=":memory:")
        yield service
        service.close()

    @pytest.fixture
    def registry(self, duckdb_service, tmp_path):
        # Use a unique registry file per test
        registry = DatasetRegistry(duckdb_service)
        registry.storage_path = tmp_path / "registry.json"
        registry.datasets.clear()
        registry.dataframes.clear()
        return registry

    @pytest.fixture
    def sample_csv(self):
        """Create a temporary CSV file for testing"""
        content = """id,name,value,category,date
1,Item A,100,Electronics,2024-01-01
2,Item B,200,Clothing,2024-01-02
3,Item C,150,Electronics,2024-01-03
4,Item D,300,Home,2024-01-04
5,Item E,250,Clothing,2024-01-05"""
        fname = create_temp_csv(content)
        yield fname
        os.unlink(fname)

    def test_register_dataset(self, registry, sample_csv):
        """Test dataset registration"""
        import uuid
        dataset_id = f"test_dataset_{uuid.uuid4().hex[:8]}"
        info = registry.register_dataset(sample_csv, dataset_id)
        assert info.dataset_id == dataset_id
        assert info.rows == 5
        assert info.columns == 5
        assert info.table_name.startswith("tbl_")
        assert info.validation_report is not None

    def test_get_dataset(self, registry, sample_csv):
        """Test retrieving dataset info"""
        import uuid
        dataset_id = f"test_dataset_{uuid.uuid4().hex[:8]}"
        registry.register_dataset(sample_csv, dataset_id)
        info = registry.get_dataset(dataset_id)
        assert info.dataset_id == dataset_id
        assert info.rows == 5

    def test_list_datasets(self, registry, sample_csv):
        """Test listing datasets"""
        import uuid
        dataset_id_1 = f"test_dataset_1_{uuid.uuid4().hex[:8]}"
        dataset_id_2 = f"test_dataset_2_{uuid.uuid4().hex[:8]}"
        registry.register_dataset(sample_csv, dataset_id_1)
        registry.register_dataset(sample_csv, dataset_id_2)
        datasets = registry.list_datasets()
        assert len(datasets) == 2

    def test_delete_dataset(self, registry, sample_csv):
        """Test dataset deletion"""
        import uuid
        dataset_id = f"test_dataset_{uuid.uuid4().hex[:8]}"
        registry.register_dataset(sample_csv, dataset_id)
        registry.delete_dataset(dataset_id)
        datasets = registry.list_datasets()
        assert len(datasets) == 0

    def test_get_dataframe(self, registry, sample_csv):
        """Test getting pandas DataFrame"""
        import uuid
        dataset_id = f"test_dataset_{uuid.uuid4().hex[:8]}"
        registry.register_dataset(sample_csv, dataset_id)
        df = registry.get_dataframe(dataset_id)
        assert len(df) == 5
        assert list(df.columns) == ['id', 'name', 'value', 'category', 'date']

    def test_get_schema_info(self, registry, sample_csv):
        """Test getting schema information"""
        import uuid
        dataset_id = f"test_dataset_{uuid.uuid4().hex[:8]}"
        registry.register_dataset(sample_csv, dataset_id)
        schema = registry.get_schema_info()
        # Schema uses table names as keys
        table_names = list(schema.keys())
        assert len(table_names) == 1
        assert len(schema[table_names[0]]["columns"]) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])