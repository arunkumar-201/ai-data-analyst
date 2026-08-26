"""
Data Quality API endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from backend.tools.quality_tool import QualityTool
from backend.data.registry import DatasetRegistry
from backend.utils.errors import NotFoundError, ExecutionError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_quality_tool(request: Request) -> QualityTool:
    return request.app.state.quality_tool


def get_registry(request: Request) -> DatasetRegistry:
    return request.app.state.registry


@router.get("/quality/{dataset_id}")
async def get_data_quality(dataset_id: str, http_request: Request):
    """Get data quality report for a dataset"""
    registry = get_registry(http_request)
    tool = get_quality_tool(http_request)

    try:
        registry.get_dataset(dataset_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")

    try:
        result = tool.execute(dataset_id)
        return result
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quality check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/{dataset_id}/summary")
async def get_quality_summary(dataset_id: str, http_request: Request):
    """Get quality summary metrics"""
    registry = get_registry(http_request)

    try:
        registry.get_dataset(dataset_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")

    tool = get_quality_tool(http_request)
    result = tool.execute(dataset_id)

    # Extract summary metrics
    issues = result.get("issues", [])

    # Calculate dimension scores
    completeness_issues = [i for i in issues if i["issue"] == "Missing values"]
    validity_issues = [i for i in issues if "Invalid" in i["issue"]]
    consistency_issues = [i for i in issues if "Inconsistent" in i["issue"] or "date" in i["issue"].lower()]
    uniqueness_issues = [i for i in issues if "Duplicate" in i["issue"]]

    def calc_score(issue_list):
        if not issue_list:
            return 100.0
        total_pct = sum(i["percentage"] for i in issue_list)
        return max(0, 100 - total_pct)

    return {
        "dataset_id": dataset_id,
        "overall_score": result.get("quality_score", 0),
        "dimensions": {
            "completeness": round(calc_score(completeness_issues), 2),
            "validity": round(calc_score(validity_issues), 2),
            "consistency": round(calc_score(consistency_issues), 2),
            "uniqueness": round(calc_score(uniqueness_issues), 2)
        },
        "issue_counts": {
            "total": len(issues),
            "high": len([i for i in issues if i["severity"] == "high"]),
            "medium": len([i for i in issues if i["severity"] == "medium"]),
            "low": len([i for i in issues if i["severity"] == "low"]),
            "info": len([i for i in issues if i["severity"] == "info"])
        },
        "top_issues": sorted(issues, key=lambda x: x["percentage"], reverse=True)[:10]
    }