"""
Conversation memory service for maintaining context across questions
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """A single message in the conversation"""
    id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConversationSession:
    """A conversation session with memory"""
    session_id: str
    dataset_id: Optional[str]
    messages: List[ConversationMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "dataset_id": self.dataset_id,
            "messages": [m.to_dict() for m in self.messages],
            "context": self.context,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class MemoryService:
    """Manages conversation memory and context"""

    def __init__(self, storage_path: str = "./data/conversations.json"):
        self.storage_path = Path(storage_path)
        self.sessions: Dict[str, ConversationSession] = {}
        self.max_messages_per_session = 50
        self._load_sessions()

    def _load_sessions(self):
        """Load sessions from disk"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                for session_data in data.get("sessions", []):
                    session = ConversationSession(
                        session_id=session_data["session_id"],
                        dataset_id=session_data.get("dataset_id"),
                        messages=[
                            ConversationMessage(**m) for m in session_data.get("messages", [])
                        ],
                        context=session_data.get("context", {}),
                        created_at=session_data.get("created_at", datetime.utcnow().isoformat()),
                        updated_at=session_data.get("updated_at", datetime.utcnow().isoformat())
                    )
                    self.sessions[session.session_id] = session
                logger.info(f"Loaded {len(self.sessions)} conversation sessions")
            except Exception as e:
                logger.warning(f"Failed to load conversations: {e}")

    def _save_sessions(self):
        """Save sessions to disk"""
        try:
            data = {
                "sessions": [s.to_dict() for s in self.sessions.values()]
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save conversations: {e}")

    def create_session(self, dataset_id: Optional[str] = None) -> ConversationSession:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())[:8]
        session = ConversationSession(
            session_id=session_id,
            dataset_id=dataset_id
        )
        self.sessions[session_id] = session
        self._save_sessions()
        return session

    def get_session(self, session_id: str) -> ConversationSession:
        """Get session by ID"""
        if session_id not in self.sessions:
            raise KeyError(f"Session '{session_id}' not found")
        return self.sessions[session_id]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Add a message to the session"""
        session = self.get_session(session_id)

        message = ConversationMessage(
            id=str(uuid.uuid4())[:8],
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )

        session.messages.append(message)
        session.updated_at = datetime.utcnow().isoformat()

        # Trim old messages if too many
        if len(session.messages) > self.max_messages_per_session:
            session.messages = session.messages[-self.max_messages_per_session:]

        self._save_sessions()
        return message

    def update_context(self, session_id: str, context: Dict[str, Any]):
        """Update session context (entities, last intent, etc.)"""
        session = self.get_session(session_id)
        session.context.update(context)
        session.updated_at = datetime.utcnow().isoformat()
        self._save_sessions()

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context"""
        session = self.get_session(session_id)
        return session.context.copy()

    def get_history(self, session_id: str, limit: int = 10) -> List[ConversationMessage]:
        """Get recent conversation history"""
        session = self.get_session(session_id)
        return session.messages[-limit:]

    def get_history_for_llm(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get history formatted for LLM"""
        messages = self.get_history(session_id, limit)
        return [{"role": m.role, "content": m.content} for m in messages]

    def resolve_references(self, question: str, session_id: str) -> str:
        """Resolve pronouns and references using conversation context"""
        context = self.get_context(session_id)
        entities = context.get("entities", {})

        # Simple reference resolution
        resolved = question
        for entity_type, value in entities.items():
            # Replace common references
            resolved = resolved.replace("its", value)
            resolved = resolved.replace("it", value)
            resolved = resolved.replace("them", value)
            resolved = resolved.replace("they", value)

        return resolved

    def extract_entities(self, question: str, answer: str, result_data: Any) -> Dict[str, Any]:
        """Extract entities from Q&A for context"""
        entities = {}

        # This is a simplified version - in production, use NER
        # For now, extract from common patterns
        import re

        # Look for proper nouns in answer that might be entities
        # e.g., "West region", "Product A", etc.
        patterns = [
            r"(?:the|in|for|of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+)\s+(?:region|customer|product|category|segment)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, answer, re.IGNORECASE)
            for match in matches:
                if len(match) > 2:  # Avoid short words
                    entities["last_entity"] = match

        # Store last result summary
        if hasattr(result_data, 'shape'):
            entities["last_result_shape"] = f"{result_data.shape[0]} rows x {result_data.shape[1]} cols"
        elif isinstance(result_data, list):
            entities["last_result_count"] = len(result_data)

        return entities

    def delete_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()

    def list_sessions(self, dataset_id: Optional[str] = None) -> List[ConversationSession]:
        """List all sessions, optionally filtered by dataset"""
        sessions = list(self.sessions.values())
        if dataset_id:
            sessions = [s for s in sessions if s.dataset_id == dataset_id]
        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions