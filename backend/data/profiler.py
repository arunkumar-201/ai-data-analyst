"""
Data profiling engine - generates detailed column statistics and dataset overview
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from backend.utils.errors import ValidationError
import logging

logger = logging.getLogger(__name__)


@dataclass
class ColumnProfile:
    """Profile for a single column"""
    name: str
    dtype: str
    inferred_type: str  # "numeric", "categorical", "datetime", "boolean", "text"
    missing_count: int
    missing_percentage: float
    unique_count: int
    cardinality: float  # unique / non-null

    # Numeric stats
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    q1: Optional[float] = None
    q3: Optional[float] = None
    iqr: Optional[float] = None
    skewness: Optional[float] = None
    kurtosis: Optional[float] = None

    # Categorical stats
    top_values: Optional[List[Dict[str, Any]]] = None  # [{"value": ..., "count": ...}]
    value_counts: Optional[Dict[str, int]] = None

    # Datetime stats
    min_date: Optional[str] = None
    max_date: Optional[str] = None
    date_range_days: Optional[int] = None

    # Distribution
    histogram: Optional[Dict[str, Any]] = None  # bins and counts

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DatasetProfile:
    """Complete dataset profile"""
    dataset_id: str
    rows: int
    columns: int
    missing_values: int
    missing_percentage: float
    duplicate_rows: int
    duplicate_percentage: float
    numeric_columns: int
    categorical_columns: int
    datetime_columns: int
    boolean_columns: int
    text_columns: int
    column_profiles: List[ColumnProfile] = field(default_factory=list)
    memory_usage_mb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "rows": self.rows,
            "columns": self.columns,
            "missing_values": self.missing_values,
            "missing_percentage": round(self.missing_percentage, 2),
            "duplicate_rows": self.duplicate_rows,
            "duplicate_percentage": round(self.duplicate_percentage, 2),
            "numeric_columns": self.numeric_columns,
            "categorical_columns": self.categorical_columns,
            "datetime_columns": self.datetime_columns,
            "boolean_columns": self.boolean_columns,
            "text_columns": self.text_columns,
            "column_profiles": [cp.to_dict() for cp in self.column_profiles],
            "memory_usage_mb": round(self.memory_usage_mb, 2)
        }


class DataProfiler:
    """Generates comprehensive data profiles"""

    def __init__(self, sample_size: int = 10000):
        self.sample_size = sample_size

    def profile(self, df: pd.DataFrame, dataset_id: str) -> DatasetProfile:
        """Generate complete dataset profile"""
        # Use sample for large datasets to speed up profiling
        profile_df = df
        if len(df) > self.sample_size:
            profile_df = df.sample(n=self.sample_size, random_state=42)
            logger.info(f"Profiling using sample of {self.sample_size} rows")

        # Basic dataset stats
        total_rows = len(df)
        total_cols = len(df.columns)
        missing_values = int(df.isnull().sum().sum())
        missing_pct = (missing_values / (total_rows * total_cols)) * 100 if total_rows * total_cols > 0 else 0
        duplicate_rows = int(df.duplicated().sum())
        duplicate_pct = (duplicate_rows / total_rows) * 100 if total_rows > 0 else 0
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)

        # Profile each column
        column_profiles = []
        numeric_count = 0
        categorical_count = 0
        datetime_count = 0
        boolean_count = 0
        text_count = 0

        for col in df.columns:
            cp = self._profile_column(df[col], col)
            column_profiles.append(cp)

            # Count by inferred type
            if cp.inferred_type == "numeric":
                numeric_count += 1
            elif cp.inferred_type == "categorical":
                categorical_count += 1
            elif cp.inferred_type == "datetime":
                datetime_count += 1
            elif cp.inferred_type == "boolean":
                boolean_count += 1
            else:
                text_count += 1

        return DatasetProfile(
            dataset_id=dataset_id,
            rows=total_rows,
            columns=total_cols,
            missing_values=missing_values,
            missing_percentage=missing_pct,
            duplicate_rows=duplicate_rows,
            duplicate_percentage=duplicate_pct,
            numeric_columns=numeric_count,
            categorical_columns=categorical_count,
            datetime_columns=datetime_count,
            boolean_columns=boolean_count,
            text_columns=text_count,
            column_profiles=column_profiles,
            memory_usage_mb=memory_mb
        )

    def _profile_column(self, series: pd.Series, name: str) -> ColumnProfile:
        """Profile a single column"""
        missing_count = int(series.isnull().sum())
        non_null = series.dropna()
        unique_count = int(non_null.nunique())
        total_count = len(series)
        missing_pct = (missing_count / total_count) * 100 if total_count > 0 else 0
        cardinality = unique_count / len(non_null) if len(non_null) > 0 else 0

        # Infer type
        inferred_type = self._infer_type(series, non_null)

        # Base profile
        profile = ColumnProfile(
            name=name,
            dtype=str(series.dtype),
            inferred_type=inferred_type,
            missing_count=missing_count,
            missing_percentage=missing_pct,
            unique_count=unique_count,
            cardinality=cardinality
        )

        # Type-specific profiling
        if inferred_type == "numeric":
            self._profile_numeric(profile, non_null)
        elif inferred_type == "categorical":
            self._profile_categorical(profile, non_null)
        elif inferred_type == "datetime":
            self._profile_datetime(profile, non_null)
        elif inferred_type == "boolean":
            self._profile_boolean(profile, non_null)
        else:
            self._profile_text(profile, non_null)

        return profile

    def _infer_type(self, series: pd.Series, non_null: pd.Series) -> str:
        """Infer semantic type of column"""
        if len(non_null) == 0:
            return "text"

        # Check boolean
        unique_vals = set(str(v).lower() for v in non_null.unique()[:20])
        bool_vals = {'true', 'false', 'yes', 'no', '1', '0', 't', 'f', 'y', 'n'}
        if unique_vals.issubset(bool_vals) and len(unique_vals) <= 2:
            return "boolean"

        # Check numeric
        if pd.api.types.is_numeric_dtype(series):
            return "numeric"

        # Check datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"

        # Try to parse as datetime
        if series.dtype == 'object':
            try:
                parsed = pd.to_datetime(non_null.head(100), errors='coerce')
                if parsed.notna().sum() / len(parsed) > 0.8:
                    return "datetime"
            except Exception:
                pass

            # Check if categorical (low cardinality)
            if len(non_null) > 0:
                cardinality = non_null.nunique() / len(non_null)
                if cardinality < 0.05 and non_null.nunique() < 100:
                    return "categorical"

        return "text"

    def _profile_numeric(self, profile: ColumnProfile, series: pd.Series):
        """Profile numeric column"""
        if len(series) == 0:
            return

        profile.mean = float(series.mean())
        profile.median = float(series.median())
        profile.std = float(series.std())
        profile.min = float(series.min())
        profile.max = float(series.max())
        profile.q1 = float(series.quantile(0.25))
        profile.q3 = float(series.quantile(0.75))
        profile.iqr = profile.q3 - profile.q1
        profile.skewness = float(series.skew())
        profile.kurtosis = float(series.kurtosis())

        # Histogram
        hist, bins = np.histogram(series.dropna(), bins=20)
        profile.histogram = {
            "bins": bins.tolist(),
            "counts": hist.tolist()
        }

    def _profile_categorical(self, profile: ColumnProfile, series: pd.Series):
        """Profile categorical column"""
        if len(series) == 0:
            return

        value_counts = series.value_counts().head(20)
        profile.top_values = [
            {"value": str(idx), "count": int(count)}
            for idx, count in value_counts.items()
        ]
        profile.value_counts = {str(k): int(v) for k, v in value_counts.items()}

    def _profile_datetime(self, profile: ColumnProfile, series: pd.Series):
        """Profile datetime column"""
        if len(series) == 0:
            return

        try:
            parsed = pd.to_datetime(series, errors='coerce').dropna()
            if len(parsed) > 0:
                profile.min_date = parsed.min().isoformat()
                profile.max_date = parsed.max().isoformat()
                profile.date_range_days = (parsed.max() - parsed.min()).days
        except Exception:
            pass

    def _profile_boolean(self, profile: ColumnProfile, series: pd.Series):
        """Profile boolean column"""
        if len(series) == 0:
            return

        value_counts = series.value_counts()
        profile.top_values = [
            {"value": str(idx), "count": int(count)}
            for idx, count in value_counts.items()
        ]

    def _profile_text(self, profile: ColumnProfile, series: pd.Series):
        """Profile text column"""
        if len(series) == 0:
            return

        # Get top values
        value_counts = series.value_counts().head(20)
        profile.top_values = [
            {"value": str(idx), "count": int(count)}
            for idx, count in value_counts.items()
        ]

        # Basic text stats
        lengths = series.astype(str).str.len()
        profile.mean = float(lengths.mean())
        profile.min = float(lengths.min())
        profile.max = float(lengths.max())


def profile_dataframe(df: pd.DataFrame, dataset_id: str) -> DatasetProfile:
    """Convenience function to profile a dataframe"""
    profiler = DataProfiler()
    return profiler.profile(df, dataset_id)