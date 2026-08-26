"""
Profiling tool for dataset profiling
"""
from typing import Dict, Any
from backend.data.profiler import profile_dataframe, DatasetProfile
from backend.data.registry import DatasetRegistry
from backend.utils.errors import ExecutionError, NotFoundError
import logging

logger = logging.getLogger(__name__)


class ProfilingTool:
    """Tool for dataset profiling"""

    def __init__(self, registry: DatasetRegistry):
        self.registry = registry

    def execute(self, dataset_id: str) -> Dict[str, Any]:
        """Profile a dataset"""
        try:
            df = self.registry.get_dataframe(dataset_id)
            profile = profile_dataframe(df, dataset_id)
            return profile.to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Profiling failed for {dataset_id}: {e}")
            raise ExecutionError(f"Profiling failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM"""
        return {
            "name": "profile_dataset",
            "description": "Get comprehensive profile of a dataset including column statistics, data types, missing values, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "string",
                        "description": "ID of the dataset to profile"
                    }
                },
                "required": ["dataset_id"]
            }
        }