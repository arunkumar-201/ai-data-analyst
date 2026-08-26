"""
Data validation pipeline for uploaded datasets
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from backend.utils.errors import ValidationError
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents a data validation issue"""
    column: str
    issue: str
    count: int
    percentage: float
    severity: str  # "high", "medium", "low"
    recommendation: str


@dataclass
class ValidationReport:
    """Complete validation report for a dataset"""
    dataset_id: str
    rows: int
    columns: int
    issues: List[ValidationIssue] = field(default_factory=list)
    quality_score: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "rows": self.rows,
            "columns": self.columns,
            "issues": [
                {
                    "column": i.column,
                    "issue": i.issue,
                    "count": i.count,
                    "percentage": round(i.percentage, 2),
                    "severity": i.severity,
                    "recommendation": i.recommendation
                }
                for i in self.issues
            ],
            "quality_score": round(self.quality_score, 2)
        }


class DataValidator:
    """Validates dataset quality and identifies issues"""

    def __init__(self):
        self.high_cardinality_threshold = 0.95  # 95% unique values
        self.constant_threshold = 1  # Only 1 unique value
        self.missing_high_threshold = 0.5  # 50% missing

    def validate(self, df: pd.DataFrame, dataset_id: str) -> ValidationReport:
        """Run complete validation pipeline"""
        report = ValidationReport(
            dataset_id=dataset_id,
            rows=len(df),
            columns=len(df.columns)
        )

        # Run all validation checks
        self._check_empty_rows(df, report)
        self._check_empty_columns(df, report)
        self._check_duplicate_columns(df, report)
        self._check_missing_values(df, report)
        self._check_duplicate_rows(df, report)
        self._check_invalid_numeric(df, report)
        self._check_invalid_dates(df, report)
        self._check_inconsistent_types(df, report)
        self._check_high_cardinality(df, report)
        self._check_constant_columns(df, report)
        self._check_potential_identifiers(df, report)
        self._check_suspicious_outliers(df, report)

        # Calculate quality score
        report.quality_score = self._calculate_quality_score(report, df)

        return report

    def _add_issue(
        self,
        report: ValidationReport,
        column: str,
        issue: str,
        count: int,
        percentage: float,
        severity: str,
        recommendation: str
    ):
        """Add an issue to the report"""
        if count > 0:
            report.issues.append(ValidationIssue(
                column=column,
                issue=issue,
                count=count,
                percentage=percentage,
                severity=severity,
                recommendation=recommendation
            ))

    def _check_empty_rows(self, df: pd.DataFrame, report: ValidationReport):
        """Check for completely empty rows"""
        empty_rows = df.isnull().all(axis=1).sum()
        if empty_rows > 0:
            pct = (empty_rows / len(df)) * 100
            self._add_issue(report, "_row", "Empty rows", empty_rows, pct, "medium",
                          "Consider removing rows with no data")

    def _check_empty_columns(self, df: pd.DataFrame, report: ValidationReport):
        """Check for completely empty columns"""
        empty_cols = df.columns[df.isnull().all()].tolist()
        for col in empty_cols:
            pct = 100.0
            self._add_issue(report, col, "Empty column", len(df), pct, "high",
                          f"Column '{col}' contains no data. Consider dropping it.")

    def _check_duplicate_columns(self, df: pd.DataFrame, report: ValidationReport):
        """Check for duplicate column names"""
        dup_cols = df.columns[df.columns.duplicated()].tolist()
        for col in set(dup_cols):
            count = list(df.columns).count(col)
            self._add_issue(report, col, "Duplicate column name", count, 0, "high",
                          f"Column '{col}' appears {count} times. Rename duplicates.")

    def _check_missing_values(self, df: pd.DataFrame, report: ValidationReport):
        """Check for missing values in each column"""
        for col in df.columns:
            missing = df[col].isnull().sum()
            if missing > 0:
                pct = (missing / len(df)) * 100
                severity = "high" if pct > 50 else "medium" if pct > 10 else "low"
                self._add_issue(report, col, "Missing values", int(missing), pct, severity,
                              f"Column has {pct:.1f}% missing values. Consider imputation or removal.")

    def _check_duplicate_rows(self, df: pd.DataFrame, report: ValidationReport):
        """Check for duplicate rows"""
        dup_count = df.duplicated().sum()
        if dup_count > 0:
            pct = (dup_count / len(df)) * 100
            self._add_issue(report, "_row", "Duplicate rows", int(dup_count), pct, "medium",
                          f"Found {dup_count} duplicate rows. Consider deduplication.")

    def _check_invalid_numeric(self, df: pd.DataFrame, report: ValidationReport):
        """Check for invalid numeric values"""
        for col in df.select_dtypes(include=[np.number]).columns:
            # Check for inf values
            inf_count = np.isinf(df[col]).sum()
            if inf_count > 0:
                pct = (inf_count / len(df)) * 100
                self._add_issue(report, col, "Infinite values", int(inf_count), pct, "high",
                              "Column contains infinite values. Replace with NaN or valid numbers.")

    def _check_invalid_dates(self, df: pd.DataFrame, report: ValidationReport):
        """Check for invalid date values"""
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to parse as dates
                try:
                    parsed = pd.to_datetime(df[col], errors='coerce')
                    invalid = parsed.isnull().sum() - df[col].isnull().sum()
                    if invalid > 0:
                        pct = (invalid / len(df)) * 100
                        self._add_issue(report, col, "Invalid date format", int(invalid), pct, "medium",
                                      "Some values could not be parsed as dates. Check date format consistency.")
                except Exception:
                    pass

    def _check_inconsistent_types(self, df: pd.DataFrame, report: ValidationReport):
        """Check for inconsistent data types in object columns"""
        for col in df.select_dtypes(include=['object']).columns:
            # Sample non-null values and check type consistency
            non_null = df[col].dropna()
            if len(non_null) == 0:
                continue
            sample = non_null.head(1000)
            types = sample.apply(type).unique()
            if len(types) > 1:
                self._add_issue(report, col, "Inconsistent data types", len(df), 0, "medium",
                              f"Column contains mixed types: {[t.__name__ for t in types]}. Standardize data types.")

    def _check_high_cardinality(self, df: pd.DataFrame, report: ValidationReport):
        """Check for extremely high cardinality columns"""
        for col in df.columns:
            unique_count = df[col].nunique()
            total_count = len(df) - df[col].isnull().sum()
            if total_count > 0:
                cardinality = unique_count / total_count
                if cardinality > self.high_cardinality_threshold and unique_count > 100:
                    pct = cardinality * 100
                    self._add_issue(report, col, "High cardinality", unique_count, pct, "low",
                                  f"Column has {unique_count} unique values ({pct:.1f}% cardinality). May be an identifier.")

    def _check_constant_columns(self, df: pd.DataFrame, report: ValidationReport):
        """Check for constant columns (single unique value)"""
        for col in df.columns:
            unique_count = df[col].nunique()
            if unique_count <= self.constant_threshold:
                pct = 100.0
                self._add_issue(report, col, "Constant column", len(df), pct, "low",
                              f"Column has only {unique_count} unique value(s). Consider dropping.")

    def _check_potential_identifiers(self, df: pd.DataFrame, report: ValidationReport):
        """Check for potential identifier columns"""
        for col in df.columns:
            unique_count = df[col].nunique()
            total_count = len(df) - df[col].isnull().sum()
            if total_count > 0 and unique_count == total_count and unique_count > 1:
                # Could be an ID column
                col_lower = col.lower()
                if any(kw in col_lower for kw in ['id', 'key', 'code', 'number', 'num']):
                    self._add_issue(report, col, "Potential identifier", unique_count, 100, "info",
                                  f"Column appears to be a unique identifier. Verify if it should be used as index.")

    def _check_suspicious_outliers(self, df: pd.DataFrame, report: ValidationReport):
        """Check for suspicious outliers using IQR method"""
        for col in df.select_dtypes(include=[np.number]).columns:
            non_null = df[col].dropna()
            if len(non_null) < 10:
                continue
            Q1 = non_null.quantile(0.25)
            Q3 = non_null.quantile(0.75)
            IQR = Q3 - Q1
            if IQR == 0:
                continue
            lower = Q1 - 3 * IQR  # Using 3*IQR for extreme outliers
            upper = Q3 + 3 * IQR
            outliers = ((non_null < lower) | (non_null > upper)).sum()
            if outliers > 0:
                pct = (outliers / len(non_null)) * 100
                if pct > 1:  # Only flag if > 1% are extreme outliers
                    self._add_issue(report, col, "Suspicious outliers", int(outliers), pct, "medium",
                                  f"Found {outliers} extreme outliers (3*IQR). Review for data entry errors.")

    def _calculate_quality_score(self, report: ValidationReport, df: pd.DataFrame) -> float:
        """Calculate overall data quality score (0-100)"""
        if len(df) == 0 or len(df.columns) == 0:
            return 0.0

        # Base score
        score = 100.0

        # Deduct for each issue based on severity
        severity_weights = {"high": 10, "medium": 5, "low": 2, "info": 1}
        for issue in report.issues:
            weight = severity_weights.get(issue.severity, 5)
            # Scale by percentage
            deduction = weight * (issue.percentage / 100)
            score -= deduction

        # Ensure score doesn't go below 0
        return max(0.0, min(100.0, score))


def validate_dataframe(df: pd.DataFrame, dataset_id: str) -> ValidationReport:
    """Convenience function to validate a dataframe"""
    validator = DataValidator()
    return validator.validate(df, dataset_id)