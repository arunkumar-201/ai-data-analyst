"""
Pandas execution tool
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from backend.data.registry import DatasetRegistry
from backend.utils.errors import ExecutionError
from backend.utils.security import validate_tool_arguments
import logging
import time
import traceback

logger = logging.getLogger(__name__)


class PandasTool:
    """Tool for executing Pandas code"""

    def __init__(self, registry: DatasetRegistry):
        self.registry = registry

    def execute(self, code: str, dataset_id: str) -> Dict[str, Any]:
        """Execute Pandas code on a dataset"""
        start_time = time.time()

        try:
            # Validate code for security
            validate_tool_arguments("execute_pandas", {"code": code})

            # Get the dataframe
            df = self.registry.get_dataframe(dataset_id)

            # Prepare execution environment
            local_vars = {
                "df": df.copy(),
                "pd": pd,
                "np": np,
            }

            # Execute the code
            exec(code, {"pd": pd, "np": np}, local_vars)

            # Get result
            result = local_vars.get("result", None)

            elapsed = (time.time() - start_time) * 1000

            # Format result
            if isinstance(result, pd.DataFrame):
                data = result.to_dict(orient="records")
                columns = result.columns.tolist()
                row_count = len(result)
            elif isinstance(result, pd.Series):
                data = result.reset_index().to_dict(orient="records")
                columns = result.reset_index().columns.tolist()
                row_count = len(result)
            elif isinstance(result, (int, float, str, bool)):
                data = [{"value": result}]
                columns = ["value"]
                row_count = 1
            elif isinstance(result, (list, tuple)):
                data = [{"value": v} for v in result]
                columns = ["value"]
                row_count = len(result)
            elif result is None:
                data = []
                columns = []
                row_count = 0
            else:
                data = [{"value": str(result)}]
                columns = ["value"]
                row_count = 1

            return {
                "success": True,
                "data": data,
                "columns": columns,
                "row_count": row_count,
                "execution_time_ms": round(elapsed, 2),
                "code": code
            }

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"Pandas execution failed: {e}\n{traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "code": code,
                "execution_time_ms": round(elapsed, 2)
            }

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM"""
        return {
            "name": "execute_pandas",
            "description": "Execute Pandas code for data analysis. The DataFrame is available as 'df'. Assign result to 'result' variable.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Pandas code to execute. Use 'df' for the DataFrame. Assign result to 'result' variable."
                    },
                    "dataset_id": {
                        "type": "string",
                        "description": "Dataset ID to analyze"
                    }
                },
                "required": ["code", "dataset_id"]
            }
        }