"""
Agent router - orchestrates tool calling and analysis workflow
"""

import logging
import re
from typing import Dict, Any, List, Optional

import pandas as pd

from backend.agent.state import AgentState
from backend.services.llm_service import LLMService
from backend.services.memory_service import MemoryService
from backend.data.registry import DatasetRegistry

from backend.tools.sql_tool import SQLTool
from backend.tools.pandas_tool import PandasTool
from backend.tools.chart_tool import ChartTool
from backend.tools.anomaly_tool import AnomalyTool
from backend.tools.quality_tool import QualityTool
from backend.tools.profiling_tool import ProfilingTool


logger = logging.getLogger(__name__)


class AgentRouter:
    """Routes questions to appropriate tools and orchestrates analysis"""

    def __init__(
        self,
        llm_service: LLMService,
        memory_service: MemoryService,
        registry: DatasetRegistry,
        duckdb_service,
        sql_tool: SQLTool,
        pandas_tool: PandasTool,
        chart_tool: ChartTool,
        anomaly_tool: AnomalyTool,
        quality_tool: QualityTool,
        profiling_tool: ProfilingTool
    ):
        self.llm = llm_service
        self.memory = memory_service
        self.registry = registry
        self.duckdb = duckdb_service
        self.sql_tool = sql_tool
        self.pandas_tool = pandas_tool
        self.chart_tool = chart_tool
        self.anomaly_tool = anomaly_tool
        self.quality_tool = quality_tool
        self.profiling_tool = profiling_tool

    async def process_question(
        self,
        question: str,
        dataset_id: str,
        session_id: Optional[str] = None
    ) -> AgentState:
        """Process a natural language question and return analysis state"""

        state = AgentState(
            dataset_id=dataset_id,
            question=question
        )

        try:
            # Resolve references using conversation memory
            if session_id:
                question = self.memory.resolve_references(
                    question,
                    session_id
                )
                state.question = question

            # Add trace step
            state.add_trace_step(
                "question_received",
                {"question": question}
            )

            # Get schema information
            schema_info = self.registry.get_schema_info()
            dataset_info = self.registry.get_dataset(dataset_id)
            selected_schema_info = {
                dataset_info.table_name: schema_info.get(
                    dataset_info.table_name,
                    {"columns": [], "rows": dataset_info.rows}
                )
            }

            state.add_trace_step(
                "schema_retrieved",
                {
                    "tables": list(selected_schema_info.keys())
                }
            )

            # Detect intent
            intent_result = await self._detect_intent(
                question,
                selected_schema_info,
                session_id
            )

            state.intent = intent_result.get(
                "intent",
                "AGGREGATION"
            )

            state.add_trace_step(
                "intent_detected",
                intent_result
            )

            # Execute tools
            await self._execute_tools(
                state,
                intent_result,
                selected_schema_info,
                dataset_id,
                session_id
            )

            # Generate explanation
            state.explanation = await self._generate_explanation(
                state
            )

            state.add_trace_step(
                "explanation_generated",
                {
                    "length": len(state.explanation)
                }
            )

            # Update memory context
            if session_id and state.results:
                entities = self.memory.extract_entities(
                    question,
                    state.explanation,
                    state.results[0]
                )

                self.memory.update_context(
                    session_id,
                    {
                        "entities": entities
                    }
                )

            return state

        except Exception as e:
            logger.error(
                f"Agent processing failed: {e}"
            )

            state.error = str(e)

            state.add_trace_step(
                "error",
                {
                    "error": str(e)
                }
            )

            return state

    async def _detect_intent(
        self,
        question: str,
        schema_info: Dict,
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """Detect user intent using LLM"""

        try:
            conversation_history = []

            if session_id:
                conversation_history = (
                    self.memory.get_history_for_llm(
                        session_id
                    )
                )

            result = await self.llm.detect_intent(
                question,
                schema_info,
                conversation_history
            )

            return result

        except Exception as e:
            logger.warning(
                f"Intent detection failed, using fallback: {e}"
            )

            return {
                "intent": "AGGREGATION",
                "tools_needed": [
                    "execute_sql"
                ],
                "visualization_type": "bar",
                "target_columns": []
            }

    async def _execute_tools(
        self,
        state: AgentState,
        intent_result: Dict,
        schema_info: Dict,
        dataset_id: str,
        session_id: Optional[str]
    ):
        """
        Execute tools based on detected intent.

        The LLM can return either execution-style names such as
        ``execute_sql`` or generation-style names such as
        ``SQL_GENERATION``. Normalize both forms before execution.
        """

        tools_needed = intent_result.get(
            "tools_needed",
            ["execute_sql"]
        )

        target_columns = intent_result.get(
            "target_columns",
            []
        )

        # Get dataset information
        dataset_info = self.registry.get_dataset(
            dataset_id
        )

        table_name = dataset_info.table_name

        # Normalize tool names returned by the LLM.
        normalized_tools = []

        for raw_tool_name in tools_needed:

            tool_name = str(
                raw_tool_name
            ).strip().upper()

            if tool_name in {
                "EXECUTE_SQL",
                "SQL_GENERATION",
                "GENERATE_SQL",
                "SQL"
            }:
                if "execute_sql" not in normalized_tools:
                    normalized_tools.append(
                        "execute_sql"
                    )

            elif tool_name in {
                "EXECUTE_PANDAS",
                "PANDAS_GENERATION",
                "GENERATE_PANDAS",
                "PANDAS"
            }:
                if "execute_pandas" not in normalized_tools:
                    normalized_tools.append(
                        "execute_pandas"
                    )

            elif tool_name in {
                "GENERATE_CHART",
                "CHART"
            }:
                if "generate_chart" not in normalized_tools:
                    normalized_tools.append(
                        "generate_chart"
                    )

            elif tool_name in {
                "DETECT_ANOMALIES",
                "ANOMALY_DETECTION",
                "ANOMALIES"
            }:
                if "detect_anomalies" not in normalized_tools:
                    normalized_tools.append(
                        "detect_anomalies"
                    )

            elif tool_name in {
                "RUN_DATA_QUALITY_CHECK",
                "DATA_QUALITY",
                "QUALITY_CHECK"
            }:
                if "run_data_quality_check" not in normalized_tools:
                    normalized_tools.append(
                        "run_data_quality_check"
                    )

            elif tool_name in {
                "PROFILE_DATASET",
                "PROFILE"
            }:
                if "profile_dataset" not in normalized_tools:
                    normalized_tools.append(
                        "profile_dataset"
                    )

            else:
                logger.warning(
                    f"Unknown tool requested by LLM: "
                    f"{raw_tool_name}"
                )

        # Safe fallback.
        # If the LLM returned an unsupported or empty tool list,
        # use SQL for normal data questions.
        if not normalized_tools:
            normalized_tools.append(
                "execute_sql"
            )

        logger.info(
            f"Requested tools: {tools_needed}"
        )

        logger.info(
            f"Normalized tools: {normalized_tools}"
        )

        # Execute normalized tools
        for tool_name in normalized_tools:

            if tool_name == "execute_sql":

                await self._execute_sql_tool(
                    state,
                    question=state.question,
                    table_name=table_name,
                    schema_info=schema_info,
                    session_id=session_id
                )

            elif tool_name == "execute_pandas":

                await self._execute_pandas_tool(
                    state,
                    question=state.question,
                    dataset_id=dataset_id,
                    schema_info=schema_info,
                    session_id=session_id
                )

            elif tool_name == "generate_chart":

                await self._execute_chart_tool(
                    state,
                    intent_result,
                    dataset_id
                )

            elif tool_name == "detect_anomalies":

                await self._execute_anomaly_tool(
                    state,
                    target_columns,
                    dataset_id
                )

            elif tool_name == "run_data_quality_check":

                await self._execute_quality_tool(
                    state,
                    dataset_id
                )

            elif tool_name == "profile_dataset":

                await self._execute_profiling_tool(
                    state,
                    dataset_id
                )

    async def _execute_sql_tool(
        self,
        state: AgentState,
        question: str,
        table_name: str,
        schema_info: Dict,
        session_id: Optional[str]
    ):
        """Generate and execute SQL"""

        try:
            conversation_history = []

            if session_id:
                conversation_history = (
                    self.memory.get_history_for_llm(
                        session_id
                    )
                )

            try:
                sql = await self.llm.generate_sql(
                    question,
                    schema_info,
                    state.dataset_id,
                    conversation_history
                )
            except Exception as generation_error:
                sql = self._fallback_sql(
                    question,
                    table_name,
                    schema_info
                )
                if not sql:
                    raise generation_error

                state.add_trace_step(
                    "sql_fallback_generated",
                    {
                        "reason": str(generation_error),
                        "sql": sql
                    }
                )

            # Safety cleanup
            sql = sql.strip()

            if sql.startswith("```"):
                sql = sql.replace(
                    "```sql",
                    ""
                )
                sql = sql.replace(
                    "```",
                    ""
                )
                sql = sql.strip()

            state.sql = sql

            state.add_trace_step(
                "sql_generated",
                {
                    "sql": sql
                }
            )

            logger.info(
                f"Generated SQL for {state.dataset_id}: {sql}"
            )

            # Execute SQL
            result = self.sql_tool.execute(
                sql
            )

            if not result.get("success"):
                fallback_sql = self._fallback_sql(
                    question,
                    table_name,
                    schema_info
                )

                if fallback_sql and fallback_sql != sql:
                    fallback_result = self.sql_tool.execute(
                        fallback_sql
                    )

                    state.add_trace_step(
                        "sql_fallback_executed",
                        {
                            "original_error": result.get("error"),
                            "sql": fallback_sql,
                            "success": fallback_result.get("success")
                        }
                    )

                    if fallback_result.get("success"):
                        sql = fallback_sql
                        state.sql = fallback_sql
                        result = fallback_result

            state.add_tool_call(
                "execute_sql",
                {
                    "sql": sql
                },
                result
            )

            if result.get("success"):

                state.results.append(
                    result
                )

                state.add_trace_step(
                    "sql_executed",
                    {
                        "rows": result.get(
                            "row_count",
                            0
                        )
                    }
                )

            else:

                state.add_trace_step(
                    "sql_failed",
                    {
                        "error": result.get(
                            "error"
                        )
                    }
                )

        except Exception as e:

            logger.error(
                f"SQL tool failed: {e}"
            )

            state.add_trace_step(
                "sql_error",
                {
                    "error": str(e)
                }
            )

    def _fallback_sql(
        self,
        question: str,
        table_name: str,
        schema_info: Dict[str, Any]
    ) -> Optional[str]:
        """Generate SQL for simple factual questions when the LLM is unavailable."""

        question_lower = question.lower()
        quoted_table = self._quote_identifier(table_name)

        if (
            "first" in question_lower
            or "top" in question_lower
            or "sample" in question_lower
            or "preview" in question_lower
            or "show me" in question_lower and "row" in question_lower
        ):
            limit_match = re.search(r"\b(\d{1,4})\b", question_lower)
            limit = int(limit_match.group(1)) if limit_match else 10
            limit = max(1, min(limit, 1000))
            return f"SELECT * FROM {quoted_table} LIMIT {limit}"

        if (
            "how many row" in question_lower
            or "number of row" in question_lower
            or "row count" in question_lower
            or "count rows" in question_lower
        ):
            return f"SELECT COUNT(*) AS row_count FROM {quoted_table}"

        if any(term in question_lower for term in ["average", "avg", "mean"]):
            column = self._match_numeric_column(
                question_lower,
                table_name,
                schema_info
            )

            if column:
                alias_suffix = re.sub(r"\W+", "_", column).strip("_")
                alias = f"avg_{alias_suffix or 'value'}"
                return (
                    f"SELECT AVG({self._quote_identifier(column)}) "
                    f"AS {self._quote_identifier(alias)} FROM {quoted_table}"
                )

        return None

    def _match_numeric_column(
        self,
        question_lower: str,
        table_name: str,
        schema_info: Dict[str, Any]
    ) -> Optional[str]:
        numeric_markers = (
            "int",
            "float",
            "double",
            "decimal",
            "numeric",
            "number",
            "bigint",
            "smallint",
            "tinyint",
        )

        columns = schema_info.get(table_name, {}).get("columns", [])
        numeric_columns = [
            col["name"]
            for col in columns
            if any(
                marker in str(col.get("type", "")).lower()
                for marker in numeric_markers
            )
        ]

        if not numeric_columns:
            return None

        for column in numeric_columns:
            normalized = re.sub(r"[_\W]+", " ", column.lower()).strip()
            if normalized and normalized in question_lower:
                return column

        for preferred in ("score", "value", "amount", "sales", "revenue", "salary"):
            for column in numeric_columns:
                if preferred in column.lower():
                    return column

        return numeric_columns[0]

    def _quote_identifier(self, identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

    async def _execute_pandas_tool(
        self,
        state: AgentState,
        question: str,
        dataset_id: str,
        schema_info: Dict,
        session_id: Optional[str]
    ):
        """Generate and execute Pandas code"""

        try:
            conversation_history = []

            if session_id:
                conversation_history = (
                    self.memory.get_history_for_llm(
                        session_id
                    )
                )

            code = await self.llm.generate_pandas_code(
                question,
                schema_info,
                dataset_id,
                conversation_history
            )

            # Remove accidental markdown fences
            code = code.strip()

            if code.startswith("```"):
                code = code.replace(
                    "```python",
                    ""
                )
                code = code.replace(
                    "```",
                    ""
                )
                code = code.strip()

            state.pandas_code = code

            state.add_trace_step(
                "pandas_generated",
                {
                    "code": code[:500]
                }
            )

            result = self.pandas_tool.execute(
                code,
                dataset_id
            )

            state.add_tool_call(
                "execute_pandas",
                {
                    "code": code
                },
                result
            )

            if result.get("success"):

                state.results.append(
                    result
                )

                state.add_trace_step(
                    "pandas_executed",
                    {
                        "rows": result.get(
                            "row_count",
                            0
                        )
                    }
                )

            else:

                state.add_trace_step(
                    "pandas_failed",
                    {
                        "error": result.get(
                            "error"
                        )
                    }
                )

        except Exception as e:

            logger.error(
                f"Pandas tool failed: {e}"
            )

            state.add_trace_step(
                "pandas_error",
                {
                    "error": str(e)
                }
            )

    async def _execute_chart_tool(
        self,
        state: AgentState,
        intent_result: Dict,
        dataset_id: str
    ):
        """Generate chart from results"""

        try:
            if not state.results:
                return

            result = state.results[0]

            data = result.get(
                "data",
                []
            )

            columns = result.get(
                "columns",
                []
            )

            if not data:
                return

            df = pd.DataFrame(
                data
            )

            chart_type = intent_result.get(
                "visualization_type",
                "bar"
            )

            if chart_type == "auto" or not chart_type:
                chart_type = self._auto_select_chart(
                    df,
                    columns
                )

            if len(columns) >= 2:

                chart_data = {
                    "x": [
                        row.get(
                            columns[0]
                        )
                        for row in data
                    ],
                    "y": [
                        row.get(
                            columns[1]
                        )
                        for row in data
                    ]
                }

            elif len(columns) == 1:

                chart_data = {
                    "values": [
                        row.get(
                            columns[0]
                        )
                        for row in data
                    ]
                }

            else:
                return

            chart_result = self.chart_tool.execute(
                chart_type=chart_type,
                data=chart_data,
                title=(
                    f"{columns[1] if len(columns) > 1 else 'Count'} "
                    f"by {columns[0]}"
                ),
                x_label=(
                    columns[0]
                    if columns
                    else ""
                ),
                y_label=(
                    columns[1]
                    if len(columns) > 1
                    else "Count"
                )
            )

            if chart_result.get("success"):

                state.chart = chart_result

                state.add_tool_call(
                    "generate_chart",
                    {
                        "chart_type": chart_type
                    },
                    chart_result
                )

                state.add_trace_step(
                    "chart_generated",
                    {
                        "type": chart_type
                    }
                )

        except Exception as e:

            logger.error(
                f"Chart tool failed: {e}"
            )

            state.add_trace_step(
                "chart_error",
                {
                    "error": str(e)
                }
            )

    def _auto_select_chart(
        self,
        df: pd.DataFrame,
        columns: List[str]
    ) -> str:
        """Automatically select chart type based on data"""

        if len(columns) < 2:

            col = (
                columns[0]
                if columns
                else None
            )

            if (
                col
                and pd.api.types.is_numeric_dtype(
                    df[col]
                )
            ):
                return "histogram"

            return "bar"

        x_col = columns[0]
        y_col = columns[1]

        x_dtype = df[x_col].dtype
        y_dtype = df[y_col].dtype

        if (
            pd.api.types.is_datetime64_any_dtype(
                x_dtype
            )
            and pd.api.types.is_numeric_dtype(
                y_dtype
            )
        ):
            return "line"

        elif (
            (
                pd.api.types.is_object_dtype(
                    x_dtype
                )
                or pd.api.types.is_categorical_dtype(
                    x_dtype
                )
            )
            and pd.api.types.is_numeric_dtype(
                y_dtype
            )
        ):
            return "bar"

        elif (
            pd.api.types.is_numeric_dtype(
                x_dtype
            )
            and pd.api.types.is_numeric_dtype(
                y_dtype
            )
        ):
            return "scatter"

        else:
            return "bar"

    async def _execute_anomaly_tool(
        self,
        state: AgentState,
        target_columns: List[str],
        dataset_id: str
    ):
        """Execute anomaly detection"""

        try:
            df = self.registry.get_dataframe(
                dataset_id
            )

            numeric_cols = (
                df.select_dtypes(
                    include=["number"]
                )
                .columns
                .tolist()
            )

            if not target_columns:
                target_columns = numeric_cols[:1]

            for column in target_columns:

                if column not in df.columns:
                    continue

                if not pd.api.types.is_numeric_dtype(
                    df[column]
                ):
                    continue

                result = self.anomaly_tool.execute(
                    dataset_id,
                    column,
                    "zscore"
                )

                state.add_tool_call(
                    "detect_anomalies",
                    {
                        "column": column,
                        "method": "zscore"
                    },
                    result
                )

                if (
                    result.get("success")
                    and result.get("anomalies")
                ):

                    state.add_trace_step(
                        "anomalies_detected",
                        {
                            "column": column,
                            "method": "zscore",
                            "count": len(
                                result["anomalies"]
                            )
                        }
                    )

                    explanation = (
                        await self.llm.generate_anomaly_explanation(
                            result["anomalies"],
                            column,
                            "zscore",
                            result["statistics"]
                        )
                    )

                    result["explanation"] = explanation

                    state.results.append(
                        result
                    )

                    break

        except Exception as e:

            logger.error(
                f"Anomaly tool failed: {e}"
            )

            state.add_trace_step(
                "anomaly_error",
                {
                    "error": str(e)
                }
            )

    async def _execute_quality_tool(
        self,
        state: AgentState,
        dataset_id: str
    ):
        """Execute data quality check"""

        try:
            result = self.quality_tool.execute(
                dataset_id
            )

            state.add_tool_call(
                "run_data_quality_check",
                {
                    "dataset_id": dataset_id
                },
                result
            )

            if result.get("success"):
                state.results.append(
                    result
                )

            state.add_trace_step(
                "quality_check_completed",
                {
                    "quality_score": result.get(
                        "quality_score",
                        0
                    )
                }
            )

        except Exception as e:

            logger.error(
                f"Quality tool failed: {e}"
            )

            state.add_trace_step(
                "quality_error",
                {
                    "error": str(e)
                }
            )

    async def _execute_profiling_tool(
        self,
        state: AgentState,
        dataset_id: str
    ):
        """Execute dataset profiling"""

        try:
            result = self.profiling_tool.execute(
                dataset_id
            )

            state.add_tool_call(
                "profile_dataset",
                {
                    "dataset_id": dataset_id
                },
                result
            )

            if result.get("success"):
                state.results.append(
                    result
                )

            state.add_trace_step(
                "profile_completed",
                {
                    "columns": len(
                        result.get(
                            "column_profiles",
                            []
                        )
                    )
                }
            )

        except Exception as e:

            logger.error(
                f"Profiling tool failed: {e}"
            )

            state.add_trace_step(
                "profiling_error",
                {
                    "error": str(e)
                }
            )

    async def _generate_explanation(
        self,
        state: AgentState
    ) -> str:
        """Generate natural language explanation of results"""

        try:
            results_str = (
                self._format_results_for_llm(
                    state.results
                )
            )

            explanation = await self.llm.explain_results(
                question=state.question,
                results=results_str,
                sql=state.sql,
                pandas_code=state.pandas_code,
                chart_data=state.chart
            )

            return explanation

        except Exception as e:

            logger.error(
                f"Explanation generation failed: {e}"
            )

            return (
                f"Analysis completed. "
                f"{len(state.results)} result(s) generated."
            )

    def _format_results_for_llm(
        self,
        results: List[Dict]
    ) -> str:
        """Format complete query results for the LLM."""

        if not results:
            return "No results"

        formatted = []

        for i, result in enumerate(results):

            if not result.get("success"):
                formatted.append(
                    f"Result {i + 1}: "
                    f"Error - {result.get('error', 'Unknown error')}"
                )
                continue

            data = result.get(
                "data",
                []
            )

            if not data:
                formatted.append(
                    f"Result {i + 1}: Empty result"
                )
                continue

            formatted.append(
                f"Result {i + 1}: {len(data)} rows"
            )

            # Include all returned rows.
            # This is important for questions such as:
            # "Show me the first 10 rows"
            for row_number, row in enumerate(
                data,
                start=1
            ):
                formatted.append(
                    f"Row {row_number}: {row}"
                )

        return "\n".join(formatted)