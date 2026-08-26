"""
Upload API endpoints
"""
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import JSONResponse
from backend.data.loader import DataLoader
from backend.data.registry import DatasetRegistry
from backend.utils.errors import ValidationError, FileError
from backend.utils.security import validate_file_extension, validate_file_size, sanitize_filename, generate_dataset_id
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Temporary upload directory
UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def get_registry(request: Request) -> DatasetRegistry:
    """Get the dataset registry from app state"""
    return request.app.state.registry


@router.post("/upload")
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(...),
    dataset_ids: List[str] = Form(default=None)
):
    """
    Upload one or more CSV files
    """
    registry = get_registry(request)
    loader = DataLoader()

    if not files:
        raise ValidationError("No files provided")

    if len(files) > 10:
        raise ValidationError("Maximum 10 files per upload")

    results = []
    errors = []

    for i, file in enumerate(files):
        storage_path = None
        try:
            # Validate file
            validate_file_extension(file.filename)
            content = await file.read()
            validate_file_size(len(content))

            # Sanitize filename
            safe_filename = sanitize_filename(file.filename)

            # Determine dataset ID
            dataset_id = None
            if dataset_ids and i < len(dataset_ids) and dataset_ids[i]:
                dataset_id = dataset_ids[i]
            else:
                dataset_id = generate_dataset_id(safe_filename)

            if dataset_id in registry.datasets:
                raise ValidationError(
                    f"Dataset with ID '{dataset_id}' already exists"
                )

            # Save to persistent upload storage so datasets can be
            # restored into memory after a backend restart.
            storage_path = UPLOAD_DIR / f"{dataset_id}_{safe_filename}"
            with open(storage_path, "wb") as f:
                f.write(content)

            # Register dataset
            info = registry.register_dataset(storage_path, dataset_id)

            results.append({
                **info.to_dict(),
                # Keep the legacy keys for older clients.
                "filename": info.original_filename,
                "quality_score": info.validation_report.quality_score if info.validation_report else 0,
            })

            logger.info(f"Uploaded: {safe_filename} -> {dataset_id}")

        except ValidationError as e:
            errors.append({"filename": file.filename, "error": e.message, "details": e.details})
        except FileError as e:
            errors.append({"filename": file.filename, "error": e.message, "details": e.details})
        except Exception as e:
            logger.error(f"Upload failed for {file.filename}: {e}")
            errors.append({"filename": file.filename, "error": str(e)})
            if storage_path:
                storage_path.unlink(missing_ok=True)

    return {
        "success": len(results) > 0,
        "uploaded": results,
        "errors": errors,
        "total_uploaded": len(results),
        "total_failed": len(errors)
    }


@router.post("/upload/preview")
async def preview_file(file: UploadFile = File(...), nrows: int = 100):
    """
    Preview a CSV file without registering it
    """
    validate_file_extension(file.filename)
    content = await file.read()
    validate_file_size(len(content))

    # Save to temp location
    safe_filename = sanitize_filename(file.filename)
    temp_path = UPLOAD_DIR / safe_filename
    with open(temp_path, "wb") as f:
        f.write(content)

    try:
        loader = DataLoader()
        df = loader.get_preview(temp_path, nrows=nrows)

        # Get basic info
        info = loader.get_file_info(temp_path)

        # Clean up
        temp_path.unlink(missing_ok=True)

        return {
            "filename": file.filename,
            "info": info,
            "preview": df.head(nrows).to_dict(orient="records"),
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "shape": df.shape
        }

    except Exception as e:
        temp_path.unlink(missing_ok=True)
        raise FileError(f"Preview failed: {str(e)}")
