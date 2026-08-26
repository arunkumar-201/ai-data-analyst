"""
Chart generation tool using Plotly
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from backend.utils.errors import ExecutionError
import logging
import json

logger = logging.getLogger(__name__)


class ChartTool:
    """Tool for generating Plotly charts"""

    CHART_TYPES = {
        "bar": "Bar chart",
        "horizontal_bar": "Horizontal bar chart",
        "line": "Line chart",
        "area": "Area chart",
        "pie": "Pie chart",
        "scatter": "Scatter plot",
        "histogram": "Histogram",
        "box": "Box plot",
        "heatmap": "Heatmap"
    }

    def __init__(self):
        pass

    def execute(
        self,
        chart_type: str,
        data: Dict[str, Any],
        title: str,
        x_label: str = "",
        y_label: str = "",
        color: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a chart"""
        try:
            fig = self._create_chart(chart_type, data, title, x_label, y_label, color)

            # Convert to JSON for frontend
            chart_json = fig.to_json()

            return {
                "success": True,
                "chart_json": chart_json,
                "chart_type": chart_type,
                "title": title
            }

        except Exception as e:
            logger.error(f"Chart generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _create_chart(
        self,
        chart_type: str,
        data: Dict[str, Any],
        title: str,
        x_label: str,
        y_label: str,
        color: Optional[str]
    ) -> go.Figure:
        """Create the appropriate chart type"""

        if chart_type == "bar":
            return self._create_bar(data, title, x_label, y_label, color, horizontal=False)
        elif chart_type == "horizontal_bar":
            return self._create_bar(data, title, x_label, y_label, color, horizontal=True)
        elif chart_type == "line":
            return self._create_line(data, title, x_label, y_label, color)
        elif chart_type == "area":
            return self._create_area(data, title, x_label, y_label, color)
        elif chart_type == "pie":
            return self._create_pie(data, title)
        elif chart_type == "scatter":
            return self._create_scatter(data, title, x_label, y_label, color)
        elif chart_type == "histogram":
            return self._create_histogram(data, title, x_label, y_label)
        elif chart_type == "box":
            return self._create_box(data, title, x_label, y_label, color)
        elif chart_type == "heatmap":
            return self._create_heatmap(data, title)
        else:
            raise ExecutionError(f"Unknown chart type: {chart_type}")

    def _create_bar(self, data, title, x_label, y_label, color, horizontal=False):
        """Create bar chart"""
        x = data.get("x", [])
        y = data.get("y", [])

        if horizontal:
            fig = go.Figure(go.Bar(x=y, y=x, orientation='h', marker_color=color or '#3498db'))
            fig.update_layout(xaxis_title=y_label, yaxis_title=x_label)
        else:
            fig = go.Figure(go.Bar(x=x, y=y, marker_color=color or '#3498db'))
            fig.update_layout(xaxis_title=x_label, yaxis_title=y_label)

        fig.update_layout(title=title, template="plotly_white")
        return fig

    def _create_line(self, data, title, x_label, y_label, color):
        """Create line chart"""
        x = data.get("x", [])
        y = data.get("y", [])

        if color and color in data:
            # Multiple lines
            fig = go.Figure()
            for name, vals in data[color].items():
                fig.add_trace(go.Scatter(x=x, y=vals, mode='lines+markers', name=name))
        else:
            fig = go.Figure(go.Scatter(x=x, y=y, mode='lines+markers', line=dict(color=color or '#3498db')))

        fig.update_layout(title=title, xaxis_title=x_label, yaxis_title=y_label, template="plotly_white")
        return fig

    def _create_area(self, data, title, x_label, y_label, color):
        """Create area chart"""
        x = data.get("x", [])
        y = data.get("y", [])

        fig = go.Figure(go.Scatter(
            x=x, y=y,
            fill='tozeroy',
            mode='lines',
            line=dict(color=color or '#3498db')
        ))

        fig.update_layout(title=title, xaxis_title=x_label, yaxis_title=y_label, template="plotly_white")
        return fig

    def _create_pie(self, data, title):
        """Create pie chart"""
        labels = data.get("labels", data.get("x", []))
        values = data.get("values", data.get("y", []))

        fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.3))
        fig.update_layout(title=title, template="plotly_white")
        return fig

    def _create_scatter(self, data, title, x_label, y_label, color):
        """Create scatter plot"""
        x = data.get("x", [])
        y = data.get("y", [])

        if color and color in data:
            fig = px.scatter(x=x, y=y, color=data[color], title=title)
        else:
            fig = go.Figure(go.Scatter(
                x=x, y=y,
                mode='markers',
                marker=dict(color=color or '#3498db', size=8, opacity=0.7)
            ))
            fig.update_layout(title=title, xaxis_title=x_label, yaxis_title=y_label, template="plotly_white")
        return fig

    def _create_histogram(self, data, title, x_label, y_label):
        """Create histogram"""
        values = data.get("values", data.get("y", data.get("x", [])))

        fig = go.Figure(go.Histogram(x=values, nbinsx=30, marker_color='#3498db'))
        fig.update_layout(title=title, xaxis_title=x_label, yaxis_title=y_label or "Count", template="plotly_white")
        return fig

    def _create_box(self, data, title, x_label, y_label, color):
        """Create box plot"""
        y = data.get("y", data.get("values", []))
        x = data.get("x", [])

        if x:
            fig = go.Figure(go.Box(x=x, y=y, marker_color=color or '#3498db'))
            fig.update_layout(xaxis_title=x_label)
        else:
            fig = go.Figure(go.Box(y=y, marker_color=color or '#3498db'))

        fig.update_layout(title=title, yaxis_title=y_label, template="plotly_white")
        return fig

    def _create_heatmap(self, data, title):
        """Create heatmap"""
        z = data.get("z", [])
        x = data.get("x", [])
        y = data.get("y", [])

        fig = go.Figure(go.Heatmap(z=z, x=x, y=y, colorscale='Viridis'))
        fig.update_layout(title=title, template="plotly_white")
        return fig

    def auto_chart(self, df: pd.DataFrame, x_col: str, y_col: Optional[str] = None) -> Dict[str, Any]:
        """Automatically select and create appropriate chart"""
        # Determine chart type based on data types
        x_dtype = df[x_col].dtype

        if y_col:
            y_dtype = df[y_col].dtype

            if pd.api.types.is_datetime64_any_dtype(x_dtype) and pd.api.types.is_numeric_dtype(y_dtype):
                chart_type = "line"
            elif pd.api.types.is_object_dtype(x_dtype) and pd.api.types.is_numeric_dtype(y_dtype):
                chart_type = "bar"
            elif pd.api.types.is_numeric_dtype(x_dtype) and pd.api.types.is_numeric_dtype(y_dtype):
                chart_type = "scatter"
            else:
                chart_type = "bar"
        else:
            # Single column
            if pd.api.types.is_numeric_dtype(x_dtype):
                chart_type = "histogram"
            else:
                # Categorical - bar chart of value counts
                chart_type = "bar"
                value_counts = df[x_col].value_counts().head(20)
                df = value_counts.reset_index()
                df.columns = [x_col, 'count']
                x_col = x_col
                y_col = 'count'

        # Prepare data
        if chart_type in ["bar", "horizontal_bar"]:
            data = {"x": df[x_col].tolist(), "y": df[y_col].tolist()}
        elif chart_type == "line":
            data = {"x": df[x_col].tolist(), "y": df[y_col].tolist()}
        elif chart_type == "scatter":
            data = {"x": df[x_col].tolist(), "y": df[y_col].tolist()}
        elif chart_type == "histogram":
            data = {"values": df[x_col].tolist()}
        elif chart_type == "pie":
            data = {"labels": df[x_col].tolist(), "values": df[y_col].tolist()}
        else:
            data = {"x": df[x_col].tolist(), "y": df[y_col].tolist()}

        return self.execute(chart_type, data, f"{y_col or 'Count'} by {x_col}", x_col, y_col or "Count")

    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM"""
        return {
            "name": "generate_chart",
            "description": "Generate a Plotly chart from data",
            "parameters": {
                "type": "object",
                "properties": {
                    "chart_type": {
                        "type": "string",
                        "enum": list(self.CHART_TYPES.keys())
                    },
                    "data": {
                        "type": "object",
                        "description": "Chart data with x, y, values, labels arrays as appropriate"
                    },
                    "title": {"type": "string"},
                    "x_label": {"type": "string"},
                    "y_label": {"type": "string"}
                },
                "required": ["chart_type", "data", "title"]
            }
        }