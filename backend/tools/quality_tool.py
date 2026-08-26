"""
Data quality check tool
"""
from typing import Dict, Any
from backend.data.validator import validate_dataframe, ValidationReport
from backend.data.registry import DatasetRegistry
from backend.utils.errors import ExecutionError
import logging

logger = logging.getLogger(__name__)


class QualityTool:
    """Tool for running data quality checks"""

    def __init__(self, registry: DatasetRegistry):
        self.registry = registry

    def execute(self, dataset_id: str) -> Dict[str, Any]:
        """Run data quality checks on a dataset"""
        try:
            df = self.registry.get_dataframe(dataset_id)
            report = validate_dataframe(df, dataset_id)
            return report.to_dict()
        except Exception as e:
            logger.error(f"Quality check failed for {dataset_id}: {e}")
            raise ExecutionError(f"Quality check failed: {str(e)}")

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM"""
        return {
            "name": "run_data_quality_check",
            "description": "Run comprehensive data quality checks on a dataset",
            "parameters": {
                "type": "object",
                "properties": {
                    "dataset_id": {
                        "type": "string",
                        "description": "ID of the dataset to check"
                    }
                },
                "required": ["dataset_id"]
            }
        }