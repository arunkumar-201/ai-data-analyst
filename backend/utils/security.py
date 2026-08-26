"""
Security utilities for file validation, SQL sanitization, etc.
"""
import os
import re
import hashlib
from pathlib import Path
from typing import List, Set
from backend.utils.errors import SecurityError, ValidationError


# Allowed file extensions
ALLOWED_EXTENSIONS: Set[str] = {"csv"}

# Maximum file size (default 200MB)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "200"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Maximum files per upload
MAX_FILES_PER_UPLOAD = int(os.getenv("MAX_FILES_PER_UPLOAD", "10"))

# SQL keywords that are forbidden (write operations)
FORBIDDEN_SQL_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
    "TRUNCATE", "REPLACE", "MERGE", "COPY", "BULK",
    "GRANT", "REVOKE", "COMMIT", "ROLLBACK",
    "EXEC", "EXECUTE", "CALL", "PREPARE"
}

# Allowed SQL keywords (read-only operations)
ALLOWED_SQL_KEYWORDS = {
    "SELECT", "WITH", "FROM", "WHERE", "GROUP BY", "ORDER BY",
    "HAVING", "LIMIT", "OFFSET", "JOIN", "LEFT", "RIGHT",
    "INNER", "OUTER", "ON", "AS", "DISTINCT", "CASE", "WHEN",
    "THEN", "ELSE", "END", "AND", "OR", "NOT", "IN", "LIKE",
    "BETWEEN", "IS", "NULL", "ASC", "DESC", "UNION", "INTERSECT",
    "EXCEPT", "OVER", "PARTITION BY", "ROW_NUMBER", "RANK",
    "DENSE_RANK", "LAG", "LEAD", "FIRST_VALUE", "LAST_VALUE"
}


def validate_file_extension(filename: str) -> None:
    """Validate file extension"""
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '.{ext}' is not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def validate_file_size(file_size: int) -> None:
    """Validate file size"""
    if file_size <= 0:
        raise ValidationError("File is empty")
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            f"File size ({file_size / (1024*1024):.1f} MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB} MB)"
        )


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    # Remove path components
    filename = os.path.basename(filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Remove special characters
    filename = re.sub(r'[^\w\-.]', '', filename)
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    return filename


def validate_sql_readonly(sql: str) -> None:
    """Validate that SQL contains only read-only operations"""
    sql_upper = sql.upper().strip()

    # Remove comments
    sql_upper = re.sub(r'--.*$', '', sql_upper, flags=re.MULTILINE)
    sql_upper = re.sub(r'/\*.*?\*/', '', sql_upper, flags=re.DOTALL)

    # Check for forbidden keywords
    for keyword in FORBIDDEN_SQL_KEYWORDS:
        # Use word boundary to avoid partial matches
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_upper):
            raise SecurityError(
                f"Forbidden SQL keyword detected: {keyword}. Only read-only queries are allowed."
            )

    # Must start with SELECT or WITH (CTE)
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        raise SecurityError("SQL must be a SELECT query or WITH clause (CTE)")


def validate_tool_arguments(tool_name: str, arguments: dict) -> None:
    """Validate tool arguments for security"""
    if tool_name == "execute_sql":
        sql = arguments.get("sql", "")
        validate_sql_readonly(sql)
    elif tool_name == "execute_pandas":
        code = arguments.get("code", "")
        # Check for dangerous patterns in Python code
        dangerous_patterns = [
            r"__import__", r"eval\(", r"exec\(", r"compile\(",
            r"open\(", r"subprocess", r"os\.system", r"os\.popen",
            r"__builtins__", r"globals\(", r"locals\(",
            r"getattr\(", r"setattr\(", r"delattr\("
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                raise SecurityError(f"Potentially dangerous code pattern detected: {pattern}")


def generate_dataset_id(filename: str) -> str:
    """Generate a unique dataset ID from filename"""
    base = Path(filename).stem
    # Sanitize to alphanumeric and underscore
    base = re.sub(r'[^\w]', '_', base)
    # Add hash for uniqueness
    hash_suffix = hashlib.md5(filename.encode()).hexdigest()[:8]
    return f"{base}_{hash_suffix}"


def validate_column_name(column: str) -> bool:
    """Validate column name (alphanumeric and underscore only)"""
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column))