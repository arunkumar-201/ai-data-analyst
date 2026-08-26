"""
Export service for CSV, Excel, PDF, PNG, HTML exports
"""
import pandas as pd
import json
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
import plotly.io as pio
import plotly.graph_objects as go
from backend.utils.errors import ExecutionError
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    """Result of an export operation"""
    format: str
    file_path: str
    file_size: int
    download_url: str


class ExportService:
    """Handles exporting analysis results to various formats"""

    def __init__(self, export_dir: str = "./exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_dataframe(
        self,
        df: pd.DataFrame,
        format: str,
        filename: Optional[str] = None
    ) -> ExportResult:
        """Export DataFrame to specified format"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}"

        if format == "csv":
            return self._export_csv(df, filename)
        elif format == "excel":
            return self._export_excel(df, filename)
        elif format == "json":
            return self._export_json(df, filename)
        else:
            raise ExecutionError(f"Unsupported data export format: {format}")

    def export_chart(
        self,
        fig: go.Figure,
        format: str,
        filename: Optional[str] = None
    ) -> ExportResult:
        """Export Plotly chart to specified format"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chart_{timestamp}"

        if format == "png":
            return self._export_png(fig, filename)
        elif format == "html":
            return self._export_html(fig, filename)
        elif format == "pdf":
            return self._export_pdf(fig, filename)
        else:
            raise ExecutionError(f"Unsupported chart export format: {format}")

    def export_report(
        self,
        report_data: Dict[str, Any],
        format: str,
        filename: Optional[str] = None
    ) -> ExportResult:
        """Export analysis report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}"

        if format == "pdf":
            return self._export_report_pdf(report_data, filename)
        elif format == "html":
            return self._export_report_html(report_data, filename)
        elif format == "json":
            return self._export_report_json(report_data, filename)
        else:
            raise ExecutionError(f"Unsupported report format: {format}")

    def _export_csv(self, df: pd.DataFrame, filename: str) -> ExportResult:
        file_path = self.export_dir / f"{filename}.csv"
        df.to_csv(file_path, index=False)
        return ExportResult(
            format="csv",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            download_url=f"/exports/{file_path.name}"
        )

    def _export_excel(self, df: pd.DataFrame, filename: str) -> ExportResult:
        file_path = self.export_dir / f"{filename}.xlsx"
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        return ExportResult(
            format="excel",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            download_url=f"/exports/{file_path.name}"
        )

    def _export_json(self, df: pd.DataFrame, filename: str) -> ExportResult:
        file_path = self.export_dir / f"{filename}.json"
        df.to_json(file_path, orient='records', indent=2, date_format='iso')
        return ExportResult(
            format="json",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            download_url=f"/exports/{file_path.name}"
        )

    def _export_png(self, fig: go.Figure, filename: str) -> ExportResult:
        file_path = self.export_dir / f"{filename}.png"
        try:
            fig.write_image(str(file_path), width=1200, height=800, scale=2)
        except Exception as e:
            # Fallback: try with kaleido
            try:
                import kaleido
                fig.write_image(str(file_path), width=1200, height=800, scale=2)
            except Exception:
                raise ExecutionError(f"PNG export failed: {str(e)}. Install kaleido for PNG support.")
        return ExportResult(
            format="png",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            download_url=f"/exports/{file_path.name}"
        )

    def _export_html(self, fig: go.Figure, filename: str) -> ExportResult:
        file_path = self.export_dir / f"{filename}.html"
        fig.write_html(str(file_path), include_plotlyjs='cdn')
        return ExportResult(
            format="html",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            download_url=f"/exports/{file_path.name}"
        )

    def _export_pdf(self, fig: go.Figure, filename: str) -> ExportResult:
        file_path = self.export_dir / f"{filename}.pdf"
        try:
            fig.write_image(str(file_path), width=1200, height=800)
        except Exception as e:
            raise ExecutionError(f"PDF export failed: {str(e)}. Install kaleido for PDF support.")
        return ExportResult(
            format="pdf",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            download_url=f"/exports/{file_path.name}"
        )

    def _export_report_pdf(self, report_data: Dict, filename: str) -> ExportResult:
        """Export report as PDF using HTML -> PDF conversion"""
        file_path = self.export_dir / f"{filename}.pdf"
        html_content = self._generate_report_html(report_data)

        # Write HTML first, then convert
        html_path = self.export_dir / f"{filename}.html"
        with open(html_path, 'w') as f:
            f.write(html_content)

        try:
            # Try using weasyprint if available
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(str(file_path))
        except ImportError:
            # Fallback: just return HTML
            logger.warning("weasyprint not installed, returning HTML instead of PDF")
            return ExportResult(
                format="html",
                file_path=str(html_path),
                file_size=html_path.stat().st_size,
                download_url=f"/exports/{html_path.name}"
            )
        except Exception as e:
            raise ExecutionError(f"PDF report generation failed: {str(e)}")

        return ExportResult(
            format="pdf",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            download_url=f"/exports/{file_path.name}"
        )

    def _export_report_html(self, report_data: Dict, filename: str) -> ExportResult:
        file_path = self.export_dir / f"{filename}.html"
        html_content = self._generate_report_html(report_data)
        with open(file_path, 'w') as f:
            f.write(html_content)
        return ExportResult(
            format="html",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            download_url=f"/exports/{file_path.name}"
        )

    def _export_report_json(self, report_data: Dict, filename: str) -> ExportResult:
        file_path = self.export_dir / f"{filename}.json"
        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        return ExportResult(
            format="json",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            download_url=f"/exports/{file_path.name}"
        )

    def _generate_report_html(self, report_data: Dict) -> str:
        """Generate HTML report from report data"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Data Analyst Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
        h3 {{ color: #2980b9; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 10px 20px; background: #ecf0f1; border-radius: 5px; }}
        .metric-label {{ font-weight: bold; color: #2c3e50; }}
        .metric-value {{ color: #2980b9; font-size: 1.2em; }}
        .chart {{ text-align: center; margin: 20px 0; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        code {{ background: #f8f9fa; padding: 2px 5px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>AI Data Analyst Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <h2>Dataset Summary</h2>
    {self._format_dataset_summary(report_data.get('dataset_summary', {}))}

    <h2>Questions & Answers</h2>
    {self._format_qa(report_data.get('qa_pairs', []))}

    <h2>Charts</h2>
    {self._format_charts(report_data.get('charts', []))}

    <h2>SQL Queries</h2>
    {self._format_sql(report_data.get('sql_queries', []))}

    <h2>Pandas Code</h2>
    {self._format_pandas(report_data.get('pandas_code', []))}

    <h2>Anomalies</h2>
    {self._format_anomalies(report_data.get('anomalies', []))}

    <h2>Data Quality</h2>
    {self._format_quality(report_data.get('data_quality', {}))}

    <h2>Recommendations</h2>
    {self._format_recommendations(report_data.get('recommendations', []))}
</body>
</html>
"""
        return html

    def _format_dataset_summary(self, summary: Dict) -> str:
        if not summary:
            return "<p>No dataset summary available.</p>"
        rows = []
        for key, value in summary.items():
            rows.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
        return f"<table><tr><th>Property</th><th>Value</th></tr>{''.join(rows)}</table>"

    def _format_qa(self, qa_pairs: List) -> str:
        if not qa_pairs:
            return "<p>No questions asked.</p>"
        html = ""
        for i, qa in enumerate(qa_pairs, 1):
            html += f"<h3>Q{i}: {qa.get('question', '')}</h3>"
            html += f"<p><strong>Answer:</strong> {qa.get('answer', '')}</p>"
            if qa.get('explanation'):
                html += f"<p><strong>Explanation:</strong> {qa.get('explanation')}</p>"
        return html

    def _format_charts(self, charts: List) -> str:
        if not charts:
            return "<p>No charts generated.</p>"
        html = ""
        for chart in charts:
            html += f"<div class='chart'><h3>{chart.get('title', 'Chart')}</h3>"
            if chart.get('image_base64'):
                html += f"<img src='data:image/png;base64,{chart['image_base64']}' style='max-width: 100%;'/>"
            html += "</div>"
        return html

    def _format_sql(self, sql_queries: List) -> str:
        if not sql_queries:
            return "<p>No SQL queries generated.</p>"
        html = ""
        for sql in sql_queries:
            html += f"<pre><code>{sql}</code></pre>"
        return html

    def _format_pandas(self, pandas_code: List) -> str:
        if not pandas_code:
            return "<p>No Pandas code generated.</p>"
        html = ""
        for code in pandas_code:
            html += f"<pre><code>{code}</code></pre>"
        return html

    def _format_anomalies(self, anomalies: List) -> str:
        if not anomalies:
            return "<p>No anomalies detected.</p>"
        rows = []
        for a in anomalies:
            rows.append(f"<tr><td>{a.get('index', '')}</td><td>{a.get('column', '')}</td><td>{a.get('value', '')}</td><td>{a.get('reason', '')}</td><td>{a.get('severity', '')}</td></tr>")
        return f"<table><tr><th>Index</th><th>Column</th><th>Value</th><th>Reason</th><th>Severity</th></tr>{''.join(rows)}</table>"

    def _format_quality(self, quality: Dict) -> str:
        if not quality:
            return "<p>No data quality information.</p>"
        rows = []
        for key, value in quality.items():
            rows.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
        return f"<table><tr><th>Metric</th><th>Value</th></tr>{''.join(rows)}</table>"

    def _format_recommendations(self, recommendations: List) -> str:
        if not recommendations:
            return "<p>No recommendations.</p>"
        items = "".join(f"<li>{r}</li>" for r in recommendations)
        return f"<ul>{items}</ul>"