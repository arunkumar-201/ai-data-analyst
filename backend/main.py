"""
AI Data Analyst - FastAPI Backend
Main application entry point
"""
import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api import upload, chat, datasets, anomalies, charts, export, quality
from backend.services.duckdb_service import DuckDBService
from backend.services.llm_service import LLMService
from backend.services.memory_service import MemoryService
from backend.services.export_service import ExportService
from backend.utils.logger import setup_logging
from backend.utils.errors import AppError
from backend.utils.json_response import SafeJSONResponse
from backend.data.registry import DatasetRegistry
from backend.agent.router import AgentRouter
from backend.tools.sql_tool import SQLTool
from backend.tools.pandas_tool import PandasTool
from backend.tools.chart_tool import ChartTool
from backend.tools.anomaly_tool import AnomalyTool
from backend.tools.quality_tool import QualityTool
from backend.tools.profiling_tool import ProfilingTool


# Global services
duckdb_service: DuckDBService = None
llm_service: LLMService = None
memory_service: MemoryService = None
export_service: ExportService = None
dataset_registry: DatasetRegistry = None
agent_router: AgentRouter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown"""
    global duckdb_service, llm_service, memory_service, export_service, dataset_registry, agent_router

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Data Analyst backend...")

    # Create data directories
    Path("./data").mkdir(exist_ok=True)
    Path("./exports").mkdir(exist_ok=True)
    Path("./sample_data").mkdir(exist_ok=True)

    # Initialize services
    duckdb_service = DuckDBService()
    llm_service = LLMService()
    memory_service = MemoryService()
    export_service = ExportService()
    dataset_registry = DatasetRegistry(duckdb_service)

    # Initialize tools
    sql_tool = SQLTool(duckdb_service)
    pandas_tool = PandasTool(dataset_registry)
    chart_tool = ChartTool()
    anomaly_tool = AnomalyTool(dataset_registry)
    quality_tool = QualityTool(dataset_registry)
    profiling_tool = ProfilingTool(dataset_registry)

    # Initialize agent router
    agent_router = AgentRouter(
        llm_service=llm_service,
        memory_service=memory_service,
        registry=dataset_registry,
        duckdb_service=duckdb_service,
        sql_tool=sql_tool,
        pandas_tool=pandas_tool,
        chart_tool=chart_tool,
        anomaly_tool=anomaly_tool,
        quality_tool=quality_tool,
        profiling_tool=profiling_tool
    )

    # Store in app state for dependency injection
    app.state.duckdb = duckdb_service
    app.state.llm = llm_service
    app.state.memory = memory_service
    app.state.export = export_service
    app.state.registry = dataset_registry
    app.state.agent = agent_router
    app.state.anomaly_tool = anomaly_tool
    app.state.chart_tool = chart_tool
    app.state.quality_tool = quality_tool
    app.state.profiling_tool = profiling_tool

    logger.info("Backend started successfully")
    yield

    # Cleanup
    logger.info("Shutting down...")
    if duckdb_service:
        duckdb_service.close()


app = FastAPI(
    title="AI Data Analyst API",
    description="AI-powered data analysis platform with natural language querying",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=SafeJSONResponse,
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return SafeJSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger = logging.getLogger(__name__)
    logger.exception("Unhandled exception: %s", exc)
    return SafeJSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)},
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-data-analyst"}


# Include API routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(datasets.router, prefix="/api", tags=["datasets"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(anomalies.router, prefix="/api", tags=["anomalies"])
app.include_router(charts.router, prefix="/api", tags=["charts"])
app.include_router(quality.router, prefix="/api", tags=["quality"])
app.include_router(export.router, prefix="/api", tags=["export"])

# Serve static files (exported files)
app.mount("/exports", StaticFiles(directory="exports"), name="exports")
# Serve React frontend
frontend_dir = Path("/app/frontend/dist")

if frontend_dir.exists():
    app.mount(
        "/",
        StaticFiles(directory=frontend_dir, html=True),
        name="frontend"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
