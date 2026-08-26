"""
Agent state management
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class AgentState:
    """Current state of the agent during analysis"""
    dataset_id: str
    question: str
    intent: Optional[str] = None
    tools_called: List[Dict[str, Any]] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)
    sql: Optional[str] = None
    pandas_code: Optional[str] = None
    chart: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    trace: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_trace_step(self, step: str, details: Dict[str, Any]):
        """Add a step to the analysis trace"""
        self.trace.append({
            "step": step,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })

    def add_tool_call(self, tool: str, args: Dict, result: Dict):
        """Record a tool call"""
        self.tools_called.append({
            "tool": tool,
            "args": args,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "dataset_id": self.dataset_id,
            "question": self.question,
            "intent": self.intent,
            "tools_called": self.tools_called,
            "results": self.results,
            "sql": self.sql,
            "pandas_code": self.pandas_code,
            "chart": self.chart,
            "explanation": self.explanation,
            "trace": self.trace,
            "error": self.error,
            "created_at": self.created_at
        }