"""
Dataset registry - manages loaded datasets and DuckDB registration
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.data.loader import DataLoader
from backend.data.profiler import DataProfiler, DatasetProfile
from backend.data.validator import DataValidator, ValidationReport
from backend.utils.errors import NotFoundError, ValidationError
from backend.utils.security import generate_dataset_id, sanitize_filename


logger = logging.getLogger(__name__)


@dataclass
class DatasetInfo:
    """Metadata for a registered dataset"""

    dataset_id: str
    original_filename: str
    rows: int
    columns: int
    profile: Optional[DatasetProfile] = None
    validation_report: Optional[ValidationReport] = None
    table_name: str = ""
    created_at: str = ""
    file_size_mb: float = 0.0
    source_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "original_filename": self.original_filename,
            "rows": self.rows,
            "columns": self.columns,
            "profile": (
                self.profile.to_dict()
                if self.profile
                else None
            ),
            "validation_report": (
                self.validation_report.to_dict()
                if self.validation_report
                else None
            ),
            "table_name": self.table_name,
            "created_at": self.created_at,
            "file_size_mb": self.file_size_mb,
            "source_path": self.source_path,
        }


class DatasetRegistry:
    """Manages dataset storage, registration, and retrieval"""

    def __init__(
        self,
        duckdb_service,
        storage_path: Optional[Path] = None,
    ):
        self.duckdb_service = duckdb_service

        self.datasets: Dict[str, DatasetInfo] = {}
        self.dataframes: Dict[str, pd.DataFrame] = {}

        self.loader = DataLoader()
        self.validator = DataValidator()
        self.profiler = DataProfiler()

        self.storage_path = (
            storage_path or Path("./data/registry.json")
        )

        self._load_registry()

    def _load_registry(self):
        """
        Load registry from disk and restore datasets.

        The previous implementation only restored metadata.
        This version also attempts to reload the original CSV
        and register it back into DuckDB after a backend restart.
        """

        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)

            datasets = data.get("datasets", [])

            for item in datasets:
                try:
                    dataset_id = item["dataset_id"]

                    # Restore metadata
                    info = DatasetInfo(
                        dataset_id=dataset_id,
                        original_filename=item.get(
                            "original_filename",
                            "dataframe.csv"
                        ),
                        rows=item.get("rows", 0),
                        columns=item.get("columns", 0),
                        table_name=item.get(
                            "table_name",
                            f"tbl_{sanitize_filename(dataset_id)}"
                        ),
                        created_at=item.get(
                            "created_at",
                            ""
                        ),
                        file_size_mb=item.get(
                            "file_size_mb",
                            0.0
                        ),
                        source_path=item.get(
                            "source_path",
                            ""
                        ),
                    )

                    self.datasets[dataset_id] = info

                    # -------------------------------------------------
                    # Restore actual DataFrame / DuckDB table
                    # -------------------------------------------------

                    source_path = info.source_path

                    possible_paths = []

                    # 1. Previously saved source path
                    if source_path:
                        possible_paths.append(
                            Path(source_path)
                        )

                    # 2. Common upload/storage locations
                    possible_paths.extend(
                        [
                            Path("./data/uploads")
                            / info.original_filename,

                            Path("./uploads")
                            / info.original_filename,

                            Path("./data")
                            / info.original_filename,

                            Path(info.original_filename),
                        ]
                    )

                    loaded = False

                    for csv_path in possible_paths:

                        try:
                            if not csv_path.exists():
                                continue

                            logger.info(
                                f"Restoring dataset "
                                f"{dataset_id} "
                                f"from {csv_path}"
                            )

                            df = self.loader.load_csv(
                                csv_path
                            )

                            if len(df) == 0:
                                logger.warning(
                                    f"Dataset {dataset_id} "
                                    f"source file is empty"
                                )
                                continue

                            # Store DataFrame
                            self.dataframes[
                                dataset_id
                            ] = df

                            # Register DuckDB table
                            self.duckdb_service.register_table(
                                info.table_name,
                                df
                            )

                            # Update source path
                            info.source_path = str(
                                csv_path
                            )

                            loaded = True

                            logger.info(
                                f"Restored dataset "
                                f"{dataset_id}: "
                                f"{len(df)} rows, "
                                f"{len(df.columns)} columns"
                            )

                            break

                        except Exception as restore_error:
                            logger.warning(
                                f"Failed restoring "
                                f"{dataset_id} from "
                                f"{csv_path}: "
                                f"{restore_error}"
                            )

                    if not loaded:
                        logger.warning(
                            f"Could not restore data for "
                            f"dataset {dataset_id}. "
                            f"Metadata was loaded, but "
                            f"DataFrame/table is unavailable."
                        )

                except Exception as item_error:
                    logger.warning(
                        f"Failed loading dataset entry: "
                        f"{item_error}"
                    )

            logger.info(
                f"Loaded {len(self.datasets)} datasets "
                f"from registry"
            )

            logger.info(
                f"Restored {len(self.dataframes)} datasets "
                f"into memory"
            )

        except Exception as e:
            logger.warning(
                f"Failed to load registry: {e}"
            )

    def _save_registry(self):
        """Save registry metadata to disk"""

        try:
            self.storage_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            data = {
                "datasets": [
                    info.to_dict()
                    for info in self.datasets.values()
                ]
            }

            with open(self.storage_path, "w") as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    default=str,
                )

        except Exception as e:
            logger.error(
                f"Failed to save registry: {e}"
            )

    def register_dataset(
        self,
        file_path: str | Path,
        dataset_id: Optional[str] = None,
    ) -> DatasetInfo:
        """Register a new dataset from CSV file"""

        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise ValidationError(
                f"File not found: {file_path}"
            )

        if dataset_id is None:
            dataset_id = generate_dataset_id(
                file_path.name
            )

        if dataset_id in self.datasets:
            raise ValidationError(
                f"Dataset with ID '{dataset_id}' already exists"
            )

        # Load CSV
        df = self.loader.load_csv(file_path)

        if len(df) == 0:
            raise ValidationError(
                "CSV file contains no data rows"
            )

        if len(df.columns) == 0:
            raise ValidationError(
                "CSV file contains no columns"
            )

        # Validate
        validation_report = self.validator.validate(
            df,
            dataset_id,
        )

        # Profile
        profile = self.profiler.profile(
            df,
            dataset_id,
        )

        # Create DuckDB table name
        table_name = sanitize_filename(
            file_path.stem
        )
        table_name = f"tbl_{table_name}"

        # Register in DuckDB
        self.duckdb_service.register_table(
            table_name,
            df,
        )

        # Store dataframe in memory
        self.dataframes[dataset_id] = df

        # Create metadata
        from datetime import datetime

        info = DatasetInfo(
            dataset_id=dataset_id,
            original_filename=file_path.name,
            rows=len(df),
            columns=len(df.columns),
            profile=profile,
            validation_report=validation_report,
            table_name=table_name,
            created_at=datetime.utcnow().isoformat(),
            file_size_mb=(
                file_path.stat().st_size
                / (1024 * 1024)
            ),
            source_path=str(
                file_path.resolve()
            ),
        )

        self.datasets[dataset_id] = info

        self._save_registry()

        logger.info(
            f"Registered dataset: {dataset_id} "
            f"({len(df)} rows, {len(df.columns)} cols)"
        )

        return info

    def register_dataframe(
        self,
        df: pd.DataFrame,
        dataset_id: str,
        original_filename: str = "dataframe.csv",
    ) -> DatasetInfo:
        """Register a dataset from an existing DataFrame"""

        if dataset_id in self.datasets:
            raise ValidationError(
                f"Dataset with ID '{dataset_id}' already exists"
            )

        if len(df) == 0:
            raise ValidationError(
                "DataFrame contains no data rows"
            )

        # Validate
        validation_report = self.validator.validate(
            df,
            dataset_id,
        )

        # Profile
        profile = self.profiler.profile(
            df,
            dataset_id,
        )

        # Create DuckDB table name
        table_name = sanitize_filename(dataset_id)
        table_name = f"tbl_{table_name}"

        # Register in DuckDB
        self.duckdb_service.register_table(
            table_name,
            df,
        )

        # Store dataframe
        self.dataframes[dataset_id] = df

        # Create metadata
        from datetime import datetime

        info = DatasetInfo(
            dataset_id=dataset_id,
            original_filename=original_filename,
            rows=len(df),
            columns=len(df.columns),
            profile=profile,
            validation_report=validation_report,
            table_name=table_name,
            created_at=datetime.utcnow().isoformat(),
            file_size_mb=(
                df.memory_usage(deep=True).sum()
                / (1024 * 1024)
            ),
            source_path="",
        )

        self.datasets[dataset_id] = info

        self._save_registry()

        logger.info(
            f"Registered DataFrame as dataset: {dataset_id}"
        )

        return info

    def get_dataset(
        self,
        dataset_id: str,
    ) -> DatasetInfo:
        """Get dataset info by ID"""

        if dataset_id not in self.datasets:
            raise NotFoundError(
                f"Dataset '{dataset_id}' not found"
            )

        return self.datasets[dataset_id]

    def get_dataframe(
        self,
        dataset_id: str,
    ) -> pd.DataFrame:
        """Get dataframe by dataset ID"""

        # Already loaded
        if dataset_id in self.dataframes:
            return self.dataframes[dataset_id]

        # Try restoring lazily
        if dataset_id in self.datasets:

            info = self.datasets[dataset_id]

            possible_paths = []

            if info.source_path:
                possible_paths.append(
                    Path(info.source_path)
                )

            possible_paths.extend(
                [
                    Path("./data/uploads")
                    / info.original_filename,

                    Path("./uploads")
                    / info.original_filename,

                    Path("./data")
                    / info.original_filename,

                    Path(info.original_filename),
                ]
            )

            for csv_path in possible_paths:

                try:
                    if not csv_path.exists():
                        continue

                    df = self.loader.load_csv(
                        csv_path
                    )

                    if len(df) == 0:
                        continue

                    self.dataframes[
                        dataset_id
                    ] = df

                    self.duckdb_service.register_table(
                        info.table_name,
                        df
                    )

                    info.source_path = str(
                        csv_path
                    )

                    self._save_registry()

                    return df

                except Exception as e:
                    logger.warning(
                        f"Lazy restore failed for "
                        f"{dataset_id}: {e}"
                    )

        raise NotFoundError(
            f"Dataset '{dataset_id}' not found in memory"
        )

    def list_datasets(self) -> List[DatasetInfo]:
        """List all registered datasets"""

        return list(
            self.datasets.values()
        )

    def delete_dataset(
        self,
        dataset_id: str,
    ) -> None:
        """Delete a dataset"""

        if dataset_id not in self.datasets:
            raise NotFoundError(
                f"Dataset '{dataset_id}' not found"
            )

        info = self.datasets[dataset_id]

        # Drop from DuckDB
        try:
            self.duckdb_service.drop_table(
                info.table_name
            )
        except Exception as e:
            logger.warning(
                f"Failed dropping table "
                f"{info.table_name}: {e}"
            )

        # Remove from memory
        if dataset_id in self.dataframes:
            del self.dataframes[dataset_id]

        del self.datasets[dataset_id]

        self._save_registry()

        logger.info(
            f"Deleted dataset: {dataset_id}"
        )

    def get_table_names(self) -> List[str]:
        """Get all registered table names"""

        return [
            info.table_name
            for info in self.datasets.values()
        ]

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get schema information for all registered tables.

        Uses the in-memory DataFrame when available.
        If the DataFrame isn't loaded, it attempts to restore
        it before falling back to metadata.
        """

        schemas: Dict[str, Any] = {}

        for info in self.datasets.values():

            # -------------------------------------------------
            # 1. DataFrame already in memory
            # -------------------------------------------------
            df = self.dataframes.get(
                info.dataset_id
            )

            # -------------------------------------------------
            # 2. Try lazy restoration
            # -------------------------------------------------
            if df is None:

                try:
                    df = self.get_dataframe(
                        info.dataset_id
                    )

                except Exception as e:
                    logger.warning(
                        f"Could not restore "
                        f"{info.dataset_id}: {e}"
                    )

            # -------------------------------------------------
            # 3. DataFrame available
            # -------------------------------------------------
            if df is not None:

                schemas[info.table_name] = {
                    "columns": [
                        {
                            "name": col,
                            "type": str(
                                df[col].dtype
                            ),
                        }
                        for col in df.columns
                    ],
                    "rows": len(df),
                }

                continue

            # -------------------------------------------------
            # 4. Try DuckDB schema
            # -------------------------------------------------
            try:

                schema_df = (
                    self.duckdb_service.get_schema(
                        info.table_name
                    )
                )

                columns = []

                if isinstance(
                    schema_df,
                    pd.DataFrame
                ):

                    for _, row in schema_df.iterrows():

                        if len(row) >= 2:

                            columns.append(
                                {
                                    "name": str(
                                        row.iloc[0]
                                    ),
                                    "type": str(
                                        row.iloc[1]
                                    ),
                                }
                            )

                schemas[info.table_name] = {
                    "columns": columns,
                    "rows": info.rows,
                }

            except Exception as e:

                logger.warning(
                    f"Could not retrieve schema for "
                    f"{info.table_name}: {e}"
                )

                schemas[info.table_name] = {
                    "columns": [],
                    "rows": info.rows,
                }

        return schemas