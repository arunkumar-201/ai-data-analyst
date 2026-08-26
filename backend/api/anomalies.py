"""
Anomalies API endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from typing import Optional, List
from backend.tools.anomaly_tool import AnomalyTool
from backend.data.registry import DatasetRegistry
from backend.utils.errors import NotFoundError, ExecutionError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_anomaly_tool(request: Request) -> AnomalyTool:
    return request.app.state.anomaly_tool


def get_registry(request: Request) -> DatasetRegistry:
    return request.app.state.registry


class AnomalyRequest(BaseModel):
    dataset_id: str
    column: str
    method: str = "zscore"  # zscore, iqr, isolation_forest
    threshold: Optional[float] = None


class MultivariateAnomalyRequest(BaseModel):
    dataset_id: str
    columns: List[str]
    contamination: float = 0.01


@router.post("/anomalies/detect")
async def detect_anomalies(request: AnomalyRequest, http_request: Request):
    """Detect anomalies in a column"""
    registry = get_registry(http_request)
    tool = get_anomaly_tool(http_request)

    # Validate dataset
    try:
        registry.get_dataset(request.dataset_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_id}' not found")

    # Validate method
    valid_methods = ["zscore", "iqr", "isolation_forest"]
    if request.method not in valid_methods:
        raise HTTPException(status_code=400, detail=f"Invalid method. Choose from: {valid_methods}")

    try:
        result = tool.execute(
            request.dataset_id,
            request.column,
            request.method,
            request.threshold
        )
        return result
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anomalies/detect-multivariate")
async def detect_multivariate_anomalies(request: MultivariateAnomalyRequest, http_request: Request):
    """Detect multivariate anomalies"""
    registry = get_registry(http_request)
    tool = get_anomaly_tool(http_request)

    try:
        registry.get_dataset(request.dataset_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_id}' not found")

    try:
        result = tool.detect_multivariate(
            request.dataset_id,
            request.columns,
            request.contamination
        )
        return result
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Multivariate anomaly detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies/methods")
async def get_anomaly_methods():
    """Get available anomaly detection methods"""
    return {
        "methods": [
            {
                "id": "zscore",
                "name": "Z-Score",
                "description": "Detects outliers based on standard deviations from mean",
                "parameters": {"threshold": {"type": "number", "default": 3.0, "description": "Z-score threshold"}}
            },
            {
                "id": "iqr",
                "name": "IQR (Interquartile Range)",
                "description": "Detects outliers using the interquartile range",
                "parameters": {"multiplier": {"type": "number", "default": 1.5, "description": "IQR multiplier"}}
            },
            {
                "id": "isolation_forest",
                "name": "Isolation Forest",
                "description": "ML-based anomaly detection for multivariate data",
                "parameters": {"contamination": {"type": "number", "default": 0.01, "description": "Expected anomaly proportion"}}
            }
        ]
    }