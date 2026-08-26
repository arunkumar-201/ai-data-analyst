"""
Datasets API endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Request
from backend.data.registry import DatasetRegistry
from backend.utils.errors import NotFoundError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_registry(request: Request) -> DatasetRegistry:
    return request.app.state.registry


@router.get("/datasets")
async def list_datasets(request: Request):
    """List all registered datasets"""
    registry = get_registry(request)
    datasets = registry.list_datasets()
    return {
        "datasets": [d.to_dict() for d in datasets],
        "count": len(datasets)
    }


@router.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str, request: Request):
    """Get dataset information"""
    registry = get_registry(request)
    try:
        info = registry.get_dataset(dataset_id)
        return info.to_dict()
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/datasets/{dataset_id}/profile")
async def get_dataset_profile(dataset_id: str, request: Request):
    """Get dataset profile"""
    registry = get_registry(request)
    try:
        info = registry.get_dataset(dataset_id)
        if info.profile:
            return info.profile.to_dict()
        else:
            # Generate profile if not exists
            from backend.data.profiler import profile_dataframe
            df = registry.get_dataframe(dataset_id)
            profile = profile_dataframe(df, dataset_id)
            info.profile = profile
            return profile.to_dict()
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/datasets/{dataset_id}/quality")
async def get_dataset_quality(dataset_id: str, request: Request):
    """Get dataset quality report"""
    registry = get_registry(request)
    try:
        info = registry.get_dataset(dataset_id)
        if info.validation_report:
            return info.validation_report.to_dict()
        else:
            from backend.data.validator import validate_dataframe
            df = registry.get_dataframe(dataset_id)
            report = validate_dataframe(df, dataset_id)
            info.validation_report = report
            return report.to_dict()
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/datasets/{dataset_id}/preview")
async def preview_dataset(dataset_id: str, nrows: int = Query(100, ge=1, le=1000), request: Request = None):
    """Preview dataset rows"""
    registry = get_registry(request)
    try:
        df = registry.get_dataframe(dataset_id)
        preview_df = df.head(nrows)
        return {
            "dataset_id": dataset_id,
            "rows": len(df),
            "columns": df.columns.tolist(),
            "preview": preview_df.to_dict(orient="records"),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/datasets/{dataset_id}/schema")
async def get_dataset_schema(dataset_id: str, request: Request):
    """Get dataset schema"""
    registry = get_registry(request)
    try:
        info = registry.get_dataset(dataset_id)
        df = registry.get_dataframe(dataset_id)
        return {
            "dataset_id": dataset_id,
            "table_name": info.table_name,
            "columns": [
                {"name": col, "type": str(df[col].dtype)}
                for col in df.columns
            ],
            "rows": len(df)
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str, request: Request):
    """Delete a dataset"""
    registry = get_registry(request)
    try:
        registry.delete_dataset(dataset_id)
        return {"success": True, "message": f"Dataset {dataset_id} deleted"}
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/schema")
async def get_all_schemas(request: Request):
    """Get schema for all registered tables"""
    registry = get_registry(request)
    return registry.get_schema_info()