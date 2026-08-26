"""
Chat API endpoints
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from backend.agent.router import AgentRouter
from backend.agent.state import AgentState
from backend.services.memory_service import MemoryService, ConversationSession
from backend.data.registry import DatasetRegistry
from backend.utils.errors import NotFoundError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def get_agent(request: Request) -> AgentRouter:
    return request.app.state.agent


def get_memory(request: Request) -> MemoryService:
    return request.app.state.memory


def get_registry(request: Request) -> DatasetRegistry:
    return request.app.state.registry


class ChatRequest(BaseModel):
    dataset_id: str
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool
    session_id: str
    answer: str
    explanation: Optional[str] = None
    sql: Optional[str] = None
    pandas_code: Optional[str] = None
    chart: Optional[dict] = None
    trace: List[dict] = []
    results: List[dict] = []
    error: Optional[str] = None


class SessionRequest(BaseModel):
    dataset_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    """Process a natural language question"""
    agent = get_agent(http_request)
    memory = get_memory(http_request)
    registry = get_registry(http_request)

    # Validate dataset exists
    try:
        registry.get_dataset(request.dataset_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Dataset '{request.dataset_id}' not found")

    # Get or create session
    session_id = request.session_id
    if not session_id:
        session = memory.create_session(request.dataset_id)
        session_id = session.session_id
    else:
        try:
            session = memory.get_session(session_id)
        except KeyError:
            session = memory.create_session(request.dataset_id)
            session_id = session.session_id

    # Add user message to history
    memory.add_message(session_id, "user", request.message)

    # Process question
    state = await agent.process_question(request.message, request.dataset_id, session_id)

    # Prepare response
    response_data = {
        "success": state.error is None,
        "session_id": session_id,
        "answer": state.explanation or "Analysis completed.",
        "explanation": state.explanation,
        "sql": state.sql,
        "pandas_code": state.pandas_code,
        "chart": state.chart,
        "trace": state.trace,
        "results": state.results,
        "error": state.error
    }

    # Add assistant response to history
    memory.add_message(
        session_id,
        "assistant",
        state.explanation or "Analysis completed.",
        metadata={
            "sql": state.sql,
            "pandas_code": state.pandas_code,
            "chart_type": state.chart.get("chart_type") if state.chart else None,
            "chart": state.chart,
            "intent": state.intent,
            "trace": state.trace,
            "results": state.results
        }
    )

    return response_data


@router.post("/sessions")
async def create_session(request: SessionRequest, http_request: Request):
    """Create a new conversation session"""
    memory = get_memory(http_request)
    session = memory.create_session(request.dataset_id)
    return {"session_id": session.session_id, "dataset_id": session.dataset_id}


@router.get("/sessions")
async def list_sessions(dataset_id: Optional[str] = None, http_request: Request = None):
    """List all conversation sessions"""
    memory = get_memory(http_request)
    sessions = memory.list_sessions(dataset_id)
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "dataset_id": s.dataset_id,
                "messages": [m.to_dict() for m in s.messages],
                "context": s.context,
                "message_count": len(s.messages),
                "created_at": s.created_at,
                "updated_at": s.updated_at
            }
            for s in sessions
        ],
        "count": len(sessions)
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, http_request: Request):
    """Get session details"""
    memory = get_memory(http_request)
    try:
        session = memory.get_session(session_id)
        return session.to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 20, http_request: Request = None):
    """Get conversation history for a session"""
    memory = get_memory(http_request)
    try:
        history = memory.get_history(session_id, limit)
        return {
            "session_id": session_id,
            "messages": [m.to_dict() for m in history]
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, http_request: Request):
    """Delete a conversation session"""
    memory = get_memory(http_request)
    memory.delete_session(session_id)
    return {"success": True, "message": f"Session {session_id} deleted"}
