"""
Export API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from backend.services.export_service import ExportService
from backend.data.registry import DatasetRegistry
from backend.services.memory_service import MemoryService
from backend.utils.errors import NotFoundError, ExecutionError
import pandas as pd
import plotly.graph_objects as go
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_export_service(request: Request) -> ExportService:
    return request.app.state.export


def get_registry(request: Request) -> DatasetRegistry:
    return request.app.state.registry


def get_memory(request: Request) -> MemoryService:
    return request.app.state.memory


class ExportDataRequest(BaseModel):
    dataset_id: str
    format: str  # csv, excel, json
    filename: Optional[str] = None


class ExportChartRequest(BaseModel):
    chart_json: Dict[str, Any]
    format: str  # png, html, pdf
    filename: Optional[str] = None


class ExportReportRequest(BaseModel):
    session_id: str
    format: str  # pdf, html, json
    filename: Optional[str] = None


@router.post("/export/data")
async def export_data(request: ExportDataRequest, http_request: Request):
    """Export dataset to CSV, Excel, or JSON"""
    registry = get_registry(http_request)
    export = get_export_service(http_request)

    try:
        registry.get_dataset(request.dataset_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_id}' not found")

    if request.format not in ["csv", "excel", "json"]:
        raise HTTPException(status_code=400, detail="Format must be csv, excel, or json")

    df = registry.get_dataframe(request.dataset_id)

    try:
        result = export.export_dataframe(df, request.format, request.filename)
        return {
            "success": True,
            "format": result.format,
            "file_path": result.file_path,
            "file_size": result.file_size,
            "download_url": result.download_url
        }
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Data export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/chart")
async def export_chart(request: ExportChartRequest, http_request: Request):
    """Export chart to PNG, HTML, or PDF"""
    export = get_export_service(http_request)

    if request.format not in ["png", "html", "pdf"]:
        raise HTTPException(status_code=400, detail="Format must be png, html, or pdf")

    try:
        # Reconstruct figure from JSON
        fig = go.Figure(json.loads(json.dumps(request.chart_json)))

        result = export.export_chart(fig, request.format, request.filename)
        return {
            "success": True,
            "format": result.format,
            "file_path": result.file_path,
            "file_size": result.file_size,
            "download_url": result.download_url
        }
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chart export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/report")
async def export_report(request: ExportReportRequest, http_request: Request):
    """Export analysis report"""
    memory = get_memory(http_request)
    export = get_export_service(http_request)

    if request.format not in ["pdf", "html", "json"]:
        raise HTTPException(status_code=400, detail="Format must be pdf, html, or json")

    try:
        session = memory.get_session(request.session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{request.session_id}' not found")

    # Build report data from session
    report_data = _build_report_data(session, http_request)

    try:
        result = export.export_report(report_data, request.format, request.filename)
        return {
            "success": True,
            "format": result.format,
            "file_path": result.file_path,
            "file_size": result.file_size,
            "download_url": result.download_url
        }
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Report export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/formats")
async def get_export_formats():
    """Get available export formats"""
    return {
        "data": ["csv", "excel", "json"],
        "chart": ["png", "html", "pdf"],
        "report": ["pdf", "html", "json"]
    }


def _build_report_data(session, http_request: Request) -> Dict[str, Any]:
    """Build report data from conversation session"""
    dataset_summary = {}
    if session.dataset_id:
        registry = get_registry(http_request)
        try:
            info = registry.get_dataset(session.dataset_id)
            if info.profile:
                dataset_summary = {
                    "rows": info.rows,
                    "columns": info.columns,
                    "missing_percentage": info.profile.missing_percentage,
                    "quality_score": info.validation_report.quality_score if info.validation_report else 0
                }
        except Exception:
            pass

    qa_pairs = []
    charts = []
    sql_queries = []
    pandas_code = []
    anomalies = []

    for msg in session.messages:
        if msg.role == "user":
            qa_pairs.append({"question": msg.content, "answer": ""})
        elif msg.role == "assistant" and qa_pairs:
            qa_pairs[-1]["answer"] = msg.content
            qa_pairs[-1]["explanation"] = msg.content
            if msg.metadata:
                if msg.metadata.get("sql"):
                    sql_queries.append(msg.metadata["sql"])
                if msg.metadata.get("pandas_code"):
                    pandas_code.append(msg.metadata["pandas_code"])
                if msg.metadata.get("chart_type"):
                    charts.append({"title": f"Chart ({msg.metadata['chart_type']})", "type": msg.metadata["chart_type"]})

    return {
        "dataset_summary": dataset_summary,
        "qa_pairs": qa_pairs,
        "charts": charts,
        "sql_queries": sql_queries,
        "pandas_code": pandas_code,
        "anomalies": anomalies,
        "data_quality": {},
        "recommendations": []
    }