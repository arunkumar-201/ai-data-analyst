"""
LLM service for Google Gemini API using the OpenAI-compatible interface.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass

import pandas as pd
from openai import AsyncOpenAI
from dotenv import load_dotenv

from backend.utils.errors import LLMError


logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """LLM response with metadata"""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str


class LLMService:
    """Service for interacting with Google Gemini."""

    def __init__(self):
        load_dotenv()

        # Gemini API configuration
        self.api_key = os.getenv("GEMINI_API_KEY")

        # Gemini OpenAI-compatible endpoint
        self.base_url = os.getenv(
            "LLM_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/"
        )

        # Use a Gemini Flash model for faster responses
        self.model = os.getenv(
            "LLM_MODEL",
            "gemini-3.6-flash"
        )

        self.temperature = float(
            os.getenv("LLM_TEMPERATURE", "0.1")
        )

        self.max_tokens = int(
            os.getenv("LLM_MAX_TOKENS", "4096")
        )

        self.timeout = int(
            os.getenv("LLM_REQUEST_TIMEOUT", "60")
        )

        if not self.api_key or self.api_key in {
            "your_gemini_api_key_here",
            "your_groq_api_key_here",
            "your_openai_api_key_here",
        }:
            logger.warning(
                "GEMINI_API_KEY not set. "
                "LLM features will not work."
            )
            self.client = None

        else:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )

            logger.info(
                f"Gemini LLM initialized with model: {self.model}"
            )


    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Send chat completion request to Gemini."""

        if not self.client:
            raise LLMError(
                "LLM client not initialized. "
                "Set GEMINI_API_KEY in .env."
            )

        try:
            request_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": (
                    temperature
                    if temperature is not None
                    else self.temperature
                ),
                "max_tokens": (
                    max_tokens
                    if max_tokens is not None
                    else self.max_tokens
                ),
                "stream": stream,
            }

            # Only send tools when supplied
            if tools:
                request_kwargs["tools"] = tools

            # Gemini OpenAI-compatible API accepts:
            # none / auto / required
            if tool_choice in {
                "none",
                "auto",
                "required",
            }:
                request_kwargs["tool_choice"] = tool_choice

            response = await self.client.chat.completions.create(
                **request_kwargs
            )

            if stream:
                raise NotImplementedError(
                    "Streaming is not implemented yet."
                )

            choice = response.choices[0]

            usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }

            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return LLMResponse(
                content=choice.message.content or "",
                usage=usage,
                model=response.model,
                finish_reason=choice.finish_reason,
            )

        except Exception as e:
            logger.error(
                f"Gemini LLM request failed: {e}"
            )
            raise LLMError(
                f"LLM request failed: {str(e)}"
            )


    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from Gemini."""

        if not self.client:
            raise LLMError(
                "LLM client not initialized. "
                "Set GEMINI_API_KEY in .env."
            )

        try:
            request_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": (
                    temperature
                    if temperature is not None
                    else self.temperature
                ),
                "max_tokens": (
                    max_tokens
                    if max_tokens is not None
                    else self.max_tokens
                ),
                "stream": True,
            }

            if tools:
                request_kwargs["tools"] = tools

            if tool_choice in {
                "none",
                "auto",
                "required",
            }:
                request_kwargs["tool_choice"] = tool_choice

            stream = await self.client.chat.completions.create(
                **request_kwargs
            )

            async for chunk in stream:
                if (
                    chunk.choices
                    and chunk.choices[0].delta.content
                ):
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(
                f"Gemini streaming failed: {e}"
            )
            raise LLMError(
                f"LLM streaming failed: {str(e)}"
            )


    def get_tools_schema(self) -> List[Dict]:
        """Get function-calling schemas."""

        return [
            {
                "type": "function",
                "function": {
                    "name": "execute_sql",
                    "description": (
                        "Execute a read-only SQL query "
                        "on the registered datasets."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": (
                                    "SQL query to execute "
                                    "(SELECT only)."
                                ),
                            },
                            "dataset_id": {
                                "type": "string",
                                "description": (
                                    "Dataset ID to query."
                                ),
                            },
                        },
                        "required": [
                            "sql",
                            "dataset_id",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_pandas",
                    "description": (
                        "Execute Pandas code "
                        "for data analysis."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": (
                                    "Pandas code to execute."
                                ),
                            },
                            "dataset_id": {
                                "type": "string",
                                "description": (
                                    "Dataset ID to analyze."
                                ),
                            },
                        },
                        "required": [
                            "code",
                            "dataset_id",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_chart",
                    "description": (
                        "Generate a Plotly chart from data."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "chart_type": {
                                "type": "string",
                                "enum": [
                                    "bar",
                                    "line",
                                    "scatter",
                                    "histogram",
                                    "pie",
                                    "box",
                                    "heatmap",
                                    "area",
                                ],
                            },
                            "data": {
                                "type": "object",
                                "description": (
                                    "Chart data containing "
                                    "x, y, or values arrays."
                                ),
                            },
                            "title": {
                                "type": "string"
                            },
                            "x_label": {
                                "type": "string"
                            },
                            "y_label": {
                                "type": "string"
                            },
                        },
                        "required": [
                            "chart_type",
                            "data",
                            "title",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_anomalies",
                    "description": (
                        "Detect anomalies in a dataset "
                        "using statistical methods."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dataset_id": {
                                "type": "string"
                            },
                            "column": {
                                "type": "string"
                            },
                            "method": {
                                "type": "string",
                                "enum": [
                                    "zscore",
                                    "iqr",
                                    "isolation_forest",
                                ],
                            },
                            "threshold": {
                                "type": "number"
                            },
                        },
                        "required": [
                            "dataset_id",
                            "column",
                            "method",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_data_quality_check",
                    "description": (
                        "Run data quality checks "
                        "on a dataset."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dataset_id": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "dataset_id"
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "profile_dataset",
                    "description": (
                        "Get dataset profile information."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "dataset_id": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "dataset_id"
                        ],
                    },
                },
            },
        ]


    async def generate_sql(
        self,
        question: str,
        schema_info: Dict[str, Any],
        dataset_id: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> str:
        """Generate DuckDB SQL."""

        if not self.client:
            raise LLMError(
                "LLM client not initialized"
            )

        schema_desc = self._format_schema(
            schema_info,
            dataset_id,
        )

        system_prompt = f"""
You are an expert SQL data analyst.

Generate a DuckDB-compatible SELECT query
that directly answers the user's question.

Database Schema:
{schema_desc}

Rules:
- Only generate SELECT queries.
- Never generate INSERT, UPDATE, DELETE, DROP,
  ALTER, CREATE, or other write operations.
- Use DuckDB syntax.
- Use the actual table name from the schema.
- For "first N rows", use SELECT * ... LIMIT N.
- For row count, use COUNT(*).
- For averages, use AVG(column).
- Return ONLY SQL.
- Do not return markdown.
- Do not explain the SQL.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ]

        if conversation_history:
            for msg in conversation_history[-5:]:
                messages.insert(-1, msg)

        response = await self.chat_completion(
            messages,
            temperature=0,
        )

        sql = response.content.strip()

        # Remove accidental markdown fences
        if sql.startswith("```"):
            sql = sql.replace("```sql", "")
            sql = sql.replace("```", "")
            sql = sql.strip()

        return sql


    async def generate_pandas_code(
        self,
        question: str,
        schema_info: Dict[str, Any],
        dataset_id: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> str:
        """Generate Pandas analysis code."""

        if not self.client:
            raise LLMError(
                "LLM client not initialized"
            )

        schema_desc = self._format_schema(
            schema_info,
            dataset_id,
        )

        system_prompt = f"""
You are an expert Python Pandas data analyst.

Generate Pandas code to answer the user's question.

Dataset:
{schema_desc}

Rules:
- The DataFrame variable is named df.
- Use only pandas/numpy operations.
- Store the final answer in a variable named result.
- For "first N rows", use df.head(N).
- For row count, use len(df).
- For averages, use df["column"].mean().
- Do not use print().
- Do not use display().
- Return ONLY Python code.
- Do not return markdown.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ]

        if conversation_history:
            for msg in conversation_history[-5:]:
                messages.insert(-1, msg)

        response = await self.chat_completion(
            messages,
            temperature=0,
        )

        code = response.content.strip()

        if code.startswith("```"):
            code = code.replace("```python", "")
            code = code.replace("```", "")
            code = code.strip()

        return code


    async def explain_results(
        self,
        question: str,
        results: Any,
        sql: Optional[str] = None,
        pandas_code: Optional[str] = None,
        chart_data: Optional[Dict] = None,
    ) -> str:
        """Generate a concise explanation of actual results."""

        if not self.client:
            raise LLMError(
                "LLM client not initialized"
            )

        system_prompt = """
You are an AI data analyst.

Explain ONLY the actual supplied analysis results.

IMPORTANT:
- Never invent rows.
- Never invent statistics.
- Never claim values that are not present in Results.
- Do not assume missing data.
- Keep the answer concise.
- If the user asks to see rows, show the actual returned rows.
- If results are empty, clearly say the result is empty.
- If SQL or Pandas code is supplied, it is supporting context only.
"""

        results_str = self._format_results(results)

        user_prompt = f"""
Question:
{question}

Actual Results:
{results_str}
"""

        if sql:
            user_prompt += f"""

SQL Used:
{sql}
"""

        if pandas_code:
            user_prompt += f"""

Pandas Code Used:
{pandas_code}
"""

        if chart_data:
            user_prompt += f"""

Chart Data:
{json.dumps(chart_data, default=str)}
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        response = await self.chat_completion(
            messages,
            temperature=0.2,
        )

        return response.content.strip()


    async def detect_intent(
        self,
        question: str,
        schema_info: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Detect user intent."""

        if not self.client:
            raise LLMError(
                "LLM client not initialized"
            )

        schema_desc = self._format_schema(
            schema_info,
            list(schema_info.keys())[0]
            if schema_info
            else "",
        )

        system_prompt = f"""
Analyze the user's data-analysis question.

Available intents:
- AGGREGATION
- FILTERING
- GROUPING
- COMPARISON
- TREND_ANALYSIS
- DISTRIBUTION
- CORRELATION
- ANOMALY_DETECTION
- DATA_QUALITY
- SQL_GENERATION
- PANDAS_GENERATION
- VISUALIZATION
- SUMMARY

Dataset Schema:
{schema_desc}

Rules:
- "Show first N rows" -> SQL_GENERATION
- "How many rows" -> AGGREGATION
- "Average/sum/min/max" -> AGGREGATION
- Filtering rows -> FILTERING
- Group by city/category -> GROUPING
- Trends over time -> TREND_ANALYSIS
- Find outliers -> ANOMALY_DETECTION
- Data quality -> DATA_QUALITY

For normal data questions, prefer execute_sql.

Return ONLY valid JSON:
{{
  "intent": "AGGREGATION",
  "tools_needed": ["execute_sql"],
  "visualization_type": null,
  "target_columns": []
}}
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ]

        if conversation_history:
            for msg in conversation_history[-5:]:
                messages.insert(-1, msg)

        response = await self.chat_completion(
            messages,
            temperature=0,
        )

        content = response.content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        try:
            return json.loads(content)

        except json.JSONDecodeError:
            logger.warning(
                "Gemini returned invalid intent JSON. "
                "Using safe fallback."
            )

            return {
                "intent": "AGGREGATION",
                "tools_needed": ["execute_sql"],
                "visualization_type": None,
                "target_columns": [],
            }


    async def generate_anomaly_explanation(
        self,
        anomalies: List[Dict],
        column: str,
        method: str,
        stats: Dict,
    ) -> str:
        """Explain detected anomalies."""

        if not self.client:
            raise LLMError(
                "LLM client not initialized"
            )

        system_prompt = """
You are a data analyst.

Explain detected anomalies using ONLY
the supplied statistical evidence.

Do not invent values.
Be concise and specific.
"""

        user_prompt = f"""
Column:
{column}

Method:
{method}

Anomalies:
{json.dumps(anomalies, indent=2, default=str)}

Statistics:
{json.dumps(stats, indent=2, default=str)}
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        response = await self.chat_completion(
            messages,
            temperature=0.2,
        )

        return response.content.strip()


    def _format_schema(
        self,
        schema_info: Dict[str, Any],
        dataset_id: str,
    ) -> str:
        """Format schema information."""

        lines = []

        for table_name, info in schema_info.items():

            lines.append(
                f"Table: {table_name}"
            )

            for col in info.get(
                "columns",
                [],
            ):
                lines.append(
                    f"  - {col['name']}: "
                    f"{col['type']}"
                )

            lines.append(
                f"  Rows: "
                f"{info.get('rows', 'unknown')}"
            )

        return "\n".join(lines)


    def _format_results(
        self,
        results: Any,
    ) -> str:
        """Format actual results for the LLM."""

        if isinstance(results, pd.DataFrame):

            if len(results) > 20:
                return (
                    f"DataFrame: "
                    f"{len(results)} rows x "
                    f"{len(results.columns)} cols\n"
                    f"Top 20 rows:\n"
                    f"{results.head(20).to_string()}"
                )

            return results.to_string()

        if isinstance(results, list):
            return json.dumps(
                results[:50],
                indent=2,
                default=str,
            )

        if isinstance(results, dict):
            return json.dumps(
                results,
                indent=2,
                default=str,
            )

        return str(results)