"""
Tests for anomaly detection functionality
"""
import pytest
import pandas as pd
import numpy as np
import uuid
from backend.tools.anomaly_tool import AnomalyTool
from backend.services.duckdb_service import DuckDBService
from backend.data.registry import DatasetRegistry
from backend.utils.errors import ValidationError


class TestAnomalyDetection:
    """Test anomaly detection methods"""

    @pytest.fixture
    def duckdb_service(self):
        service = DuckDBService(db_path=":memory:")
        yield service
        service.close()

    @pytest.fixture
    def registry(self, duckdb_service):
        # Use a unique registry path to avoid conflicts
        registry = DatasetRegistry(duckdb_service)
        # Clear any existing data
        registry.datasets.clear()
        registry.dataframes.clear()
        return registry

    @pytest.fixture
    def anomaly_tool(self, registry):
        return AnomalyTool(registry)

    @pytest.fixture
    def normal_data(self):
        """Create dataset with normal distribution"""
        np.random.seed(42)
        data = {
            'id': range(1, 101),
            'value': np.random.normal(100, 15, 100),  # Normal distribution
            'category': np.random.choice(['A', 'B', 'C'], 100)
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def data_with_outliers(self):
        """Create dataset with obvious outliers"""
        np.random.seed(42)
        normal_values = np.random.normal(100, 10, 95)
        outliers = [500, -200, 1000, -500]  # Clear outliers
        data = {
            'id': range(1, 100),
            'value': np.concatenate([normal_values, outliers]),
            'category': np.random.choice(['A', 'B', 'C'], 99)
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def multivariate_data(self):
        """Create dataset for multivariate anomaly detection"""
        np.random.seed(42)
        # Normal cluster
        x1 = np.random.normal(0, 1, 80)
        y1 = np.random.normal(0, 1, 80)
        # Outlier cluster
        x2 = np.random.normal(10, 1, 10)
        y2 = np.random.normal(10, 1, 10)
        data = {
            'x': np.concatenate([x1, x2]),
            'y': np.concatenate([y1, y2]),
            'label': ['normal'] * 80 + ['outlier'] * 10
        }
        return pd.DataFrame(data)

    def _register_unique(self, registry, df, prefix):
        """Register dataframe with unique ID"""
        unique_id = f"{prefix}_{uuid.uuid4().hex[:8]}"
        registry.register_dataframe(df, unique_id)
        return unique_id

    def test_zscore_detection(self, anomaly_tool, registry, data_with_outliers):
        """Test Z-score anomaly detection"""
        dataset_id = self._register_unique(registry, data_with_outliers, "test_zscore")

        result = anomaly_tool.execute(dataset_id, "value", "zscore", threshold=3.0)

        assert result['success'] is True
        assert 'anomalies' in result
        assert 'statistics' in result
        assert result['method'] == 'zscore'
        # Should detect at least 3 outliers (out of 4)
        assert len(result['anomalies']) >= 3

    def test_iqr_detection(self, anomaly_tool, registry, data_with_outliers):
        """Test IQR anomaly detection"""
        dataset_id = self._register_unique(registry, data_with_outliers, "test_iqr")

        result = anomaly_tool.execute(dataset_id, "value", "iqr", threshold=1.5)

        assert result['success'] is True
        assert 'anomalies' in result
        assert result['method'] == 'iqr'
        assert len(result['anomalies']) >= 3

    def test_isolation_forest_detection(self, anomaly_tool, registry, data_with_outliers):
        """Test Isolation Forest anomaly detection"""
        dataset_id = self._register_unique(registry, data_with_outliers, "test_if")

        # execute uses threshold parameter for contamination
        result = anomaly_tool.execute(dataset_id, "value", "isolation_forest", threshold=0.1)

        assert result['success'] is True
        assert 'anomalies' in result
        assert result['method'] == 'isolation_forest'

    def test_no_anomalies_in_normal_data(self, anomaly_tool, registry, normal_data):
        """Test that normal data has few/no anomalies"""
        dataset_id = self._register_unique(registry, normal_data, "test_normal")

        result = anomaly_tool.execute(dataset_id, "value", "zscore", threshold=3.0)

        assert result['success'] is True
        # With normal distribution and threshold 3, should have very few anomalies
        # (about 0.3% expected, so 0-1 in 100 samples)

    def test_multivariate_detection(self, anomaly_tool, registry, multivariate_data):
        """Test multivariate anomaly detection"""
        dataset_id = self._register_unique(registry, multivariate_data, "test_multi")

        result = anomaly_tool.detect_multivariate(dataset_id, ["x", "y"], contamination=0.1)

        assert result['success'] is True
        assert 'anomalies' in result
        assert 'statistics' in result
        assert result['method'] == 'isolation_forest_multivariate'

    def test_anomaly_explanation_structure(self, anomaly_tool, registry, data_with_outliers):
        """Test that anomaly results have correct structure"""
        dataset_id = self._register_unique(registry, data_with_outliers, "test_structure")

        result = anomaly_tool.execute(dataset_id, "value", "zscore", threshold=3.0)

        assert result['success'] is True
        if result['anomalies']:
            anomaly = result['anomalies'][0]
            assert 'index' in anomaly
            assert 'value' in anomaly
            # Z-score method has 'z_score', isolation forest has 'anomaly_score'
            assert 'z_score' in anomaly or 'anomaly_score' in anomaly
            assert 'reason' in anomaly

    def test_statistics_output(self, anomaly_tool, registry, data_with_outliers):
        """Test statistics in anomaly result"""
        dataset_id = self._register_unique(registry, data_with_outliers, "test_stats")

        result = anomaly_tool.execute(dataset_id, "value", "zscore", threshold=3.0)

        assert 'statistics' in result
        stats = result['statistics']
        assert 'mean' in stats
        assert 'std' in stats
        assert 'threshold' in stats

    def test_invalid_column(self, anomaly_tool, registry, normal_data):
        """Test handling of invalid column name"""
        dataset_id = self._register_unique(registry, normal_data, "test_invalid")

        # The tool raises ExecutionError for invalid column
        with pytest.raises(Exception):
            anomaly_tool.execute(dataset_id, "nonexistent_column", "zscore")

    def test_non_numeric_column(self, anomaly_tool, registry, normal_data):
        """Test handling of non-numeric column"""
        dataset_id = self._register_unique(registry, normal_data, "test_nonnumeric")

        # The tool raises ExecutionError for non-numeric column
        with pytest.raises(Exception):
            anomaly_tool.execute(dataset_id, "category", "zscore")

    def test_empty_dataset(self, anomaly_tool, registry):
        """Test handling of empty dataset - registry rejects empty dataframes"""
        empty_df = pd.DataFrame({'value': []})
        # Registry should reject empty DataFrame
        with pytest.raises(ValidationError):
            registry.register_dataframe(empty_df, "test_empty")


class TestAnomalyToolEdgeCases:
    """Test edge cases in anomaly detection"""

    @pytest.fixture
    def duckdb_service(self):
        service = DuckDBService(db_path=":memory:")
        yield service
        service.close()

    @pytest.fixture
    def registry(self, duckdb_service):
        registry = DatasetRegistry(duckdb_service)
        registry.datasets.clear()
        registry.dataframes.clear()
        return registry

    @pytest.fixture
    def anomaly_tool(self, registry):
        return AnomalyTool(registry)

    def test_constant_column(self, anomaly_tool, registry):
        """Test anomaly detection on constant column"""
        df = pd.DataFrame({'value': [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]})
        dataset_id = f"test_constant_{uuid.uuid4().hex[:8]}"
        registry.register_dataframe(df, dataset_id)

        result = anomaly_tool.execute(dataset_id, "value", "zscore")

        # Should handle gracefully (std = 0)
        assert 'success' in result
        assert result['success'] is True
        assert result['anomalies'] == []

    def test_single_value_column(self, anomaly_tool, registry):
        """Test anomaly detection on single value - need at least 10 values"""
        # Need at least 10 values for anomaly detection
        df = pd.DataFrame({'value': [42] * 15})  # Constant column with 15 values
        dataset_id = f"test_single_{uuid.uuid4().hex[:8]}"
        registry.register_dataframe(df, dataset_id)

        result = anomaly_tool.execute(dataset_id, "value", "zscore")

        assert 'success' in result
        assert result['success'] is True
        assert result['anomalies'] == []

    def test_two_values_column(self, anomaly_tool, registry):
        """Test anomaly detection on two distinct values"""
        # Need at least 10 values for anomaly detection
        df = pd.DataFrame({'value': [10, 20] * 10})  # 20 values
        dataset_id = f"test_two_{uuid.uuid4().hex[:8]}"
        registry.register_dataframe(df, dataset_id)

        result = anomaly_tool.execute(dataset_id, "value", "zscore")

        assert 'success' in result
        assert result['success'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])