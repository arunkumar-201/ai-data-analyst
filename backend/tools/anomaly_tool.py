"""
Anomaly detection tool using Z-score, IQR, and Isolation Forest
"""
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from typing import Dict, Any, List, Optional, Tuple
from backend.data.registry import DatasetRegistry
from backend.utils.errors import ExecutionError
import logging
import json

logger = logging.getLogger(__name__)


class AnomalyTool:
    """Tool for detecting anomalies in datasets"""

    METHODS = ["zscore", "iqr", "isolation_forest"]

    def __init__(self, registry: DatasetRegistry):
        self.registry = registry

    def execute(
        self,
        dataset_id: str,
        column: str,
        method: str = "zscore",
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Detect anomalies in a column"""
        try:
            df = self.registry.get_dataframe(dataset_id)

            if column not in df.columns:
                raise ExecutionError(f"Column '{column}' not found in dataset")

            series = df[column].dropna()

            if len(series) < 10:
                raise ExecutionError("Not enough data for anomaly detection (need at least 10 non-null values)")

            if not pd.api.types.is_numeric_dtype(series):
                raise ExecutionError(f"Column '{column}' is not numeric. Anomaly detection requires numeric data.")

            if method == "zscore":
                return self._detect_zscore(df, column, series, threshold or 3.0)
            elif method == "iqr":
                return self._detect_iqr(df, column, series, threshold or 1.5)
            elif method == "isolation_forest":
                return self._detect_isolation_forest(df, column, series, threshold or 0.01)
            else:
                raise ExecutionError(f"Unknown method: {method}. Available: {self.METHODS}")

        except ExecutionError:
            raise
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            raise ExecutionError(f"Anomaly detection failed: {str(e)}")

    def _detect_zscore(self, df: pd.DataFrame, column: str, series: pd.Series, threshold: float) -> Dict[str, Any]:
        """Detect anomalies using Z-score method"""
        mean = series.mean()
        std = series.std()

        if std == 0:
            return {
                "success": True,
                "method": "zscore",
                "column": column,
                "anomalies": [],
                "statistics": {"mean": mean, "std": std, "threshold": threshold},
                "message": "No variation in data (std=0), no anomalies detected"
            }

        z_scores = np.abs((series - mean) / std)
        anomaly_mask = z_scores > threshold
        anomaly_indices = series.index[anomaly_mask].tolist()

        anomalies = []
        for idx in anomaly_indices:
            value = series.loc[idx]
            z = z_scores.loc[idx]
            direction = "above" if value > mean else "below"
            anomalies.append({
                "index": int(idx),
                "column": column,
                "value": float(value),
                "z_score": round(float(z), 2),
                "mean": round(float(mean), 2),
                "std": round(float(std), 2),
                "direction": direction,
                "severity": "high" if z > 4 else "medium" if z > 3 else "low",
                "reason": f"Value is {z:.2f} standard deviations {direction} the mean ({mean:.2f})"
            })

        return {
            "success": True,
            "method": "zscore",
            "column": column,
            "anomalies": anomalies,
            "statistics": {
                "mean": round(float(mean), 4),
                "std": round(float(std), 4),
                "threshold": threshold,
                "total_checked": len(series),
                "anomaly_count": len(anomalies),
                "anomaly_percentage": round(len(anomalies) / len(series) * 100, 2)
            }
        }

    def _detect_iqr(self, df: pd.DataFrame, column: str, series: pd.Series, multiplier: float) -> Dict[str, Any]:
        """Detect anomalies using IQR method"""
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1

        if IQR == 0:
            return {
                "success": True,
                "method": "iqr",
                "column": column,
                "anomalies": [],
                "statistics": {"Q1": Q1, "Q3": Q3, "IQR": IQR, "multiplier": multiplier},
                "message": "No variation in data (IQR=0), no anomalies detected"
            }

        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR

        anomaly_mask = (series < lower_bound) | (series > upper_bound)
        anomaly_indices = series.index[anomaly_mask].tolist()

        anomalies = []
        for idx in anomaly_indices:
            value = series.loc[idx]
            if value < lower_bound:
                direction = "below"
                bound = lower_bound
                deviation = (lower_bound - value) / IQR
            else:
                direction = "above"
                bound = upper_bound
                deviation = (value - upper_bound) / IQR

            anomalies.append({
                "index": int(idx),
                "column": column,
                "value": float(value),
                "lower_bound": round(float(lower_bound), 2),
                "upper_bound": round(float(upper_bound), 2),
                "direction": direction,
                "deviation_iqr": round(float(deviation), 2),
                "severity": "high" if deviation > 3 else "medium" if deviation > 1.5 else "low",
                "reason": f"Value is {deviation:.2f} IQRs {direction} the {direction} bound ({bound:.2f})"
            })

        return {
            "success": True,
            "method": "iqr",
            "column": column,
            "anomalies": anomalies,
            "statistics": {
                "Q1": round(float(Q1), 4),
                "Q3": round(float(Q3), 4),
                "IQR": round(float(IQR), 4),
                "lower_bound": round(float(lower_bound), 4),
                "upper_bound": round(float(upper_bound), 4),
                "multiplier": multiplier,
                "total_checked": len(series),
                "anomaly_count": len(anomalies),
                "anomaly_percentage": round(len(anomalies) / len(series) * 100, 2)
            }
        }

    def _detect_isolation_forest(
        self,
        df: pd.DataFrame,
        column: str,
        series: pd.Series,
        contamination: float
    ) -> Dict[str, Any]:
        """Detect anomalies using Isolation Forest"""
        # Reshape for sklearn
        X = series.values.reshape(-1, 1)

        # Fit Isolation Forest
        iso_forest = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        predictions = iso_forest.fit_predict(X)
        scores = iso_forest.decision_function(X)

        # -1 indicates anomaly
        anomaly_mask = predictions == -1
        anomaly_indices = series.index[anomaly_mask].tolist()

        anomalies = []
        for idx in anomaly_indices:
            value = series.loc[idx]
            score = scores[series.index.get_loc(idx)]
            # Normalize score: lower (more negative) = more anomalous
            normalized_score = (score - scores.min()) / (scores.max() - scores.min()) if scores.max() > scores.min() else 0
            severity = "high" if normalized_score < 0.2 else "medium" if normalized_score < 0.5 else "low"

            anomalies.append({
                "index": int(idx),
                "column": column,
                "value": float(value),
                "anomaly_score": round(float(score), 4),
                "normalized_score": round(float(normalized_score), 4),
                "severity": severity,
                "reason": f"Isolation Forest anomaly score: {score:.4f} (lower = more anomalous)"
            })

        return {
            "success": True,
            "method": "isolation_forest",
            "column": column,
            "anomalies": anomalies,
            "statistics": {
                "contamination": contamination,
                "total_checked": len(series),
                "anomaly_count": len(anomalies),
                "anomaly_percentage": round(len(anomalies) / len(series) * 100, 2),
                "score_range": [round(float(scores.min()), 4), round(float(scores.max()), 4)]
            }
        }

    def detect_multivariate(
        self,
        dataset_id: str,
        columns: List[str],
        contamination: float = 0.01
    ) -> Dict[str, Any]:
        """Detect multivariate anomalies using Isolation Forest"""
        try:
            df = self.registry.get_dataframe(dataset_id)

            # Validate columns
            for col in columns:
                if col not in df.columns:
                    raise ExecutionError(f"Column '{col}' not found")
                if not pd.api.types.is_numeric_dtype(df[col]):
                    raise ExecutionError(f"Column '{col}' is not numeric")

            # Prepare data
            X = df[columns].dropna()
            if len(X) < 10:
                raise ExecutionError("Not enough data for multivariate anomaly detection")

            # Fit Isolation Forest
            iso_forest = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            predictions = iso_forest.fit_predict(X)
            scores = iso_forest.decision_function(X)

            anomaly_mask = predictions == -1
            anomaly_indices = X.index[anomaly_mask].tolist()

            anomalies = []
            for idx in anomaly_indices:
                row = X.loc[idx]
                score = scores[X.index.get_loc(idx)]
                normalized_score = (score - scores.min()) / (scores.max() - scores.min()) if scores.max() > scores.min() else 0
                severity = "high" if normalized_score < 0.2 else "medium" if normalized_score < 0.5 else "low"

                anomalies.append({
                    "index": int(idx),
                    "values": {col: float(row[col]) for col in columns},
                    "anomaly_score": round(float(score), 4),
                    "normalized_score": round(float(normalized_score), 4),
                    "severity": severity,
                    "reason": f"Multivariate anomaly score: {score:.4f}"
                })

            return {
                "success": True,
                "method": "isolation_forest_multivariate",
                "columns": columns,
                "anomalies": anomalies,
                "statistics": {
                    "contamination": contamination,
                    "total_checked": len(X),
                    "anomaly_count": len(anomalies),
                    "anomaly_percentage": round(len(anomalies) / len(X) * 100, 2)
                }
            }

        except ExecutionError:
            raise
        except Exception as e:
            logger.error(f"Multivariate anomaly detection failed: {e}")
            raise ExecutionError(f"Multivariate anomaly detection failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM"""
        return {
            "name": "detect_anomalies",
            "description": "Detect anomalies in a numeric column using statistical methods",
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string"},
                    "column": {"type": "string"},
                    "method": {
                        "type": "string",
                        "enum": self.METHODS
                    },
                    "threshold": {"type": "number"}
                },
                "required": ["dataset_id", "column", "method"]
            }
        }