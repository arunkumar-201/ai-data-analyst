"""
CSV data loader with encoding handling and validation
"""
import pandas as pd
import chardet
from pathlib import Path
from typing import Optional, List, Tuple
from backend.utils.errors import FileError, ValidationError
from backend.utils.security import validate_file_extension, validate_file_size, sanitize_filename
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Handles CSV file loading with encoding detection and validation"""

    # Common encodings to try
    ENCODINGS = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']

    def __init__(self, max_rows_preview: int = 1000):
        self.max_rows_preview = max_rows_preview

    def detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding using chardet"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(100000)  # Read first 100KB for detection
        result = chardet.detect(raw_data)
        encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0)
        logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")
        return encoding or 'utf-8'

    def load_csv(
        self,
        file_path: Path,
        encoding: Optional[str] = None,
        nrows: Optional[int] = None
    ) -> pd.DataFrame:
        """Load CSV file with encoding detection fallback"""
        validate_file_extension(file_path.name)
        validate_file_size(file_path.stat().st_size)

        # Try provided encoding first, then detected, then fallbacks
        encodings_to_try = []
        if encoding:
            encodings_to_try.append(encoding)
        encodings_to_try.append(self.detect_encoding(file_path))
        encodings_to_try.extend([e for e in self.ENCODINGS if e not in encodings_to_try])

        last_error = None
        for enc in encodings_to_try:
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=enc,
                    nrows=nrows,
                    low_memory=False,
                    on_bad_lines='skip'
                )
                logger.info(f"Successfully loaded {file_path.name} with encoding {enc}")
                return df
            except UnicodeDecodeError as e:
                last_error = e
                logger.debug(f"Failed to load with {enc}: {e}")
                continue
            except Exception as e:
                last_error = e
                logger.debug(f"Failed to load with {enc}: {e}")
                continue

        raise FileError(
            f"Could not load CSV file with any supported encoding. Last error: {last_error}"
        )

    def load_multiple_csvs(self, file_paths: List[Path]) -> dict:
        """Load multiple CSV files and return dict of dataframes"""
        if len(file_paths) > MAX_FILES_PER_UPLOAD:
            raise ValidationError(
                f"Too many files. Maximum {MAX_FILES_PER_UPLOAD} files per upload."
            )

        dataframes = {}
        for file_path in file_paths:
            df = self.load_csv(file_path)
            dataset_id = sanitize_filename(file_path.stem)
            dataframes[dataset_id] = df

        return dataframes

    def load(self, file_path: str | Path, encoding: Optional[str] = None, nrows: Optional[int] = None) -> pd.DataFrame:
        """Load CSV file (alias for load_csv that accepts string or Path)"""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return self.load_csv(file_path, encoding, nrows)

    def get_preview(self, file_path: str | Path, nrows: int = 100) -> pd.DataFrame:
        """Get preview of CSV file"""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        return self.load_csv(file_path, nrows=nrows)

    def get_file_info(self, file_path: str | Path) -> dict:
        """Get basic file information"""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        stat = file_path.stat()
        # Load first few rows to get columns and dtypes
        df = self.load_csv(file_path, nrows=5)
        return {
            "filename": file_path.name,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "rows": len(df),
            "columns": len(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }


# Module-level constants
MAX_FILES_PER_UPLOAD = int(__import__('os').getenv("MAX_FILES_PER_UPLOAD", "10"))