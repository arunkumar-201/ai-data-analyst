"""
Charts API endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from backend.tools.chart_tool import ChartTool
from backend.data.registry import DatasetRegistry
from backend.utils.errors import NotFoundError, ExecutionError
import pandas as pd
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_chart_tool(request: Request) -> ChartTool:
    return request.app.state.chart_tool


def get_registry(request: Request) -> DatasetRegistry:
    return request.app.state.registry


class ChartRequest(BaseModel):
    dataset_id: str
    chart_type: str  # bar, line, scatter, histogram, pie, box, heatmap, area
    x_column: str
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    title: Optional[str] = None


class AutoChartRequest(BaseModel):
    dataset_id: str
    x_column: str
    y_column: Optional[str] = None


@router.post("/charts/generate")
async def generate_chart(request: ChartRequest, http_request: Request):
    """Generate a chart from dataset"""
    registry = get_registry(http_request)
    tool = get_chart_tool(http_request)

    try:
        registry.get_dataset(request.dataset_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_id}' not found")

    df = registry.get_dataframe(request.dataset_id)

    if request.x_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{request.x_column}' not found")

    if request.y_column and request.y_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{request.y_column}' not found")

    # Prepare data
    if request.y_column:
        data = {
            "x": df[request.x_column].tolist(),
            "y": df[request.y_column].tolist()
        }
        if request.color_column and request.color_column in df.columns:
            data["color"] = df[request.color_column].tolist()
    else:
        data = {
            "values": df[request.x_column].tolist()
        }

    title = request.title or f"{request.y_column or 'Count'} by {request.x_column}"

    try:
        result = tool.execute(
            chart_type=request.chart_type,
            data=data,
            title=title,
            x_label=request.x_column,
            y_label=request.y_column or "Count"
        )
        return result
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chart generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/charts/auto")
async def auto_chart(request: AutoChartRequest, http_request: Request):
    """Automatically select and generate appropriate chart"""
    registry = get_registry(http_request)
    tool = get_chart_tool(http_request)

    try:
        registry.get_dataset(request.dataset_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_id}' not found")

    df = registry.get_dataframe(request.dataset_id)

    if request.x_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{request.x_column}' not found")

    if request.y_column and request.y_column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column '{request.y_column}' not found")

    try:
        result = tool.auto_chart(df, request.x_column, request.y_column)
        return result
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Auto chart failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/charts/types")
async def get_chart_types(http_request: Request):
    """Get available chart types"""
    tool = get_chart_tool(http_request)
    return {
        "chart_types": [
            {"id": k, "name": v} for k, v in tool.CHART_TYPES.items()
        ]
    }