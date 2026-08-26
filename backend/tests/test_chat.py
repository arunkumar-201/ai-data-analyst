"""
Tests for chat functionality
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.services.memory_service import MemoryService, ConversationSession, ConversationMessage
from backend.agent.state import AgentState
from backend.agent.router import AgentRouter
from backend.tools.sql_tool import SQLTool
from backend.tools.pandas_tool import PandasTool
from backend.tools.chart_tool import ChartTool
from backend.tools.anomaly_tool import AnomalyTool
from backend.tools.quality_tool import QualityTool
from backend.tools.profiling_tool import ProfilingTool
from backend.services.llm_service import LLMService, LLMResponse
from backend.services.duckdb_service import DuckDBService
from backend.data.registry import DatasetRegistry
import tempfile
import os


class TestMemoryService:
    """Test conversation memory service"""

    @pytest.fixture
    def memory_service(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        service = MemoryService(storage_path=temp_path)
        yield service
        os.unlink(temp_path)

    def test_create_session(self, memory_service):
        """Test session creation"""
        session = memory_service.create_session("dataset_123")
        assert session.session_id is not None
        assert session.dataset_id == "dataset_123"
        assert len(session.messages) == 0

    def test_add_message(self, memory_service):
        """Test adding messages to session"""
        session = memory_service.create_session("dataset_123")
        message = memory_service.add_message(
            session.session_id,
            "user",
            "Hello, world!",
            metadata={"test": "data"}
        )
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.metadata == {"test": "data"}

        session = memory_service.get_session(session.session_id)
        assert len(session.messages) == 1

    def test_get_history(self, memory_service):
        """Test getting conversation history"""
        session = memory_service.create_session("dataset_123")
        memory_service.add_message(session.session_id, "user", "Message 1")
        memory_service.add_message(session.session_id, "assistant", "Response 1")
        memory_service.add_message(session.session_id, "user", "Message 2")

        history = memory_service.get_history(session.session_id, limit=2)
        assert len(history) == 2
        assert history[0].content == "Response 1"
        assert history[1].content == "Message 2"

    def test_get_history_for_llm(self, memory_service):
        """Test getting history formatted for LLM"""
        session = memory_service.create_session("dataset_123")
        memory_service.add_message(session.session_id, "user", "Hello")
        memory_service.add_message(session.session_id, "assistant", "Hi there!")

        history = memory_service.get_history_for_llm(session.session_id)
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "assistant", "content": "Hi there!"}

    def test_update_context(self, memory_service):
        """Test updating session context"""
        session = memory_service.create_session("dataset_123")
        memory_service.update_context(session.session_id, {"last_topic": "sales", "entities": {"region": "North"}})

        context = memory_service.get_context(session.session_id)
        assert context["last_topic"] == "sales"
        assert context["entities"]["region"] == "North"

    def test_list_sessions(self, memory_service):
        """Test listing sessions"""
        session1 = memory_service.create_session("dataset_1")
        session2 = memory_service.create_session("dataset_2")
        session3 = memory_service.create_session("dataset_1")

        all_sessions = memory_service.list_sessions()
        assert len(all_sessions) == 3

        dataset1_sessions = memory_service.list_sessions("dataset_1")
        assert len(dataset1_sessions) == 2

    def test_delete_session(self, memory_service):
        """Test session deletion"""
        session = memory_service.create_session("dataset_123")
        memory_service.delete_session(session.session_id)

        sessions = memory_service.list_sessions()
        assert len(sessions) == 0

    def test_persistence(self, memory_service):
        """Test that sessions persist to disk"""
        session = memory_service.create_session("dataset_123")
        memory_service.add_message(session.session_id, "user", "Test message")
        session_id = session.session_id

        # Create new service with same storage
        new_service = MemoryService(storage_path=memory_service.storage_path)
        loaded_session = new_service.get_session(session_id)

        assert loaded_session.session_id == session_id
        assert len(loaded_session.messages) == 1
        assert loaded_session.messages[0].content == "Test message"


class TestAgentState:
    """Test agent state management"""

    def test_initial_state(self):
        """Test initial state creation"""
        state = AgentState(dataset_id="test_123", question="What is the average salary?")
        assert state.dataset_id == "test_123"
        assert state.question == "What is the average salary?"
        assert state.sql is None
        assert state.pandas_code is None
        assert state.chart is None
        assert state.results == []
        assert state.trace == []
        assert state.error is None

    def test_add_trace_step(self):
        """Test adding trace steps"""
        state = AgentState(dataset_id="test", question="test")
        state.add_trace_step("step1", {"detail": "info"})
        state.add_trace_step("step2", {"detail": "more"})

        assert len(state.trace) == 2
        assert state.trace[0]["step"] == "step1"
        assert state.trace[1]["step"] == "step2"

    def test_add_tool_call(self):
        """Test adding tool call records"""
        state = AgentState(dataset_id="test", question="test")
        state.add_tool_call("execute_sql", {"sql": "SELECT 1"}, {"success": True, "data": []})

        assert len(state.tools_called) == 1
        assert state.tools_called[0]["tool"] == "execute_sql"
        assert state.tools_called[0]["args"]["sql"] == "SELECT 1"

    def test_add_result(self):
        """Test adding results"""
        state = AgentState(dataset_id="test", question="test")
        result = {"success": True, "data": [{"a": 1}], "columns": ["a"], "row_count": 1}
        state.results.append(result)

        assert len(state.results) == 1
        assert state.results[0]["row_count"] == 1


class TestAgentRouter:
    """Test agent router (with mocked dependencies)"""

    @pytest.fixture
    def mock_services(self):
        """Create mocked services"""
        llm = MagicMock(spec=LLMService)
        memory = MagicMock(spec=MemoryService)
        registry = MagicMock(spec=DatasetRegistry)
        duckdb = MagicMock(spec=DuckDBService)
        sql_tool = MagicMock(spec=SQLTool)
        pandas_tool = MagicMock(spec=PandasTool)
        chart_tool = MagicMock(spec=ChartTool)
        anomaly_tool = MagicMock(spec=AnomalyTool)
        quality_tool = MagicMock(spec=QualityTool)
        profiling_tool = MagicMock(spec=ProfilingTool)

        return {
            'llm': llm,
            'memory': memory,
            'registry': registry,
            'duckdb': duckdb,
            'sql_tool': sql_tool,
            'pandas_tool': pandas_tool,
            'chart_tool': chart_tool,
            'anomaly_tool': anomaly_tool,
            'quality_tool': quality_tool,
            'profiling_tool': profiling_tool
        }

    @pytest.fixture
    def agent_router(self, mock_services):
        return AgentRouter(
            llm_service=mock_services['llm'],
            memory_service=mock_services['memory'],
            registry=mock_services['registry'],
            duckdb_service=mock_services['duckdb'],
            sql_tool=mock_services['sql_tool'],
            pandas_tool=mock_services['pandas_tool'],
            chart_tool=mock_services['chart_tool'],
            anomaly_tool=mock_services['anomaly_tool'],
            quality_tool=mock_services['quality_tool'],
            profiling_tool=mock_services['profiling_tool']
        )

    @pytest.mark.asyncio
    async def test_process_question_basic(self, agent_router, mock_services):
        """Test basic question processing"""
        # Setup mocks
        mock_services['registry'].get_schema_info.return_value = {
            "test_table": {"columns": [{"name": "id", "type": "int"}, {"name": "value", "type": "float"}], "rows": 100}
        }
        mock_services['registry'].get_dataset.return_value = MagicMock(table_name="test_table")
        mock_services['llm'].detect_intent = AsyncMock(return_value={
            "intent": "AGGREGATION",
            "tools_needed": ["execute_sql"],
            "visualization_type": "bar",
            "target_columns": ["value"]
        })
        mock_services['llm'].generate_sql = AsyncMock(return_value="SELECT AVG(value) FROM test_table")
        mock_services['sql_tool'].execute.return_value = {
            "success": True,
            "data": [{"avg": 50.0}],
            "columns": ["avg"],
            "row_count": 1
        }
        mock_services['llm'].explain_results = AsyncMock(return_value="The average value is 50.")

        state = await agent_router.process_question("What is the average value?", "test_dataset")

        assert state.error is None
        assert state.sql == "SELECT AVG(value) FROM test_table"
        assert len(state.results) == 1
        assert state.explanation == "The average value is 50."

    @pytest.mark.asyncio
    async def test_process_question_with_session(self, agent_router, mock_services):
        """Test question processing with session memory"""
        mock_services['memory'].resolve_references.return_value = "What is the average value in North region?"
        mock_services['memory'].get_history_for_llm.return_value = [
            {"role": "user", "content": "Show me sales in North region"},
            {"role": "assistant", "content": "Here are the sales..."}
        ]

        mock_services['registry'].get_schema_info.return_value = {
            "test_table": {"columns": [{"name": "region", "type": "varchar"}, {"name": "sales", "type": "float"}], "rows": 100}
        }
        mock_services['registry'].get_dataset.return_value = MagicMock(table_name="test_table")
        mock_services['llm'].detect_intent = AsyncMock(return_value={
            "intent": "AGGREGATION",
            "tools_needed": ["execute_sql"],
            "visualization_type": "bar",
            "target_columns": ["sales"]
        })
        mock_services['llm'].generate_sql = AsyncMock(return_value="SELECT AVG(sales) FROM test_table WHERE region = 'North'")
        mock_services['sql_tool'].execute.return_value = {
            "success": True,
            "data": [{"avg": 1000.0}],
            "columns": ["avg"],
            "row_count": 1
        }
        mock_services['llm'].explain_results = AsyncMock(return_value="Average sales in North region is 1000.")

        state = await agent_router.process_question(
            "What is the average there?",
            "test_dataset",
            session_id="session_123"
        )

        # Verify reference resolution was called
        mock_services['memory'].resolve_references.assert_called_once()
        assert state.error is None


class TestLLMService:
    """Test LLM service (mocked)"""

    @pytest.fixture
    def llm_service(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            service = LLMService()
            service.client = AsyncMock()
            return service

    @pytest.mark.asyncio
    async def test_chat_completion(self, llm_service):
        """Test chat completion"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"), finish_reason="stop")]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_response.model = "gpt-4o-mini"

        llm_service.client.chat.completions.create = AsyncMock(return_value=mock_response)

        response = await llm_service.chat_completion([{"role": "user", "content": "Hello"}])

        assert response.content == "Test response"
        assert response.usage["total_tokens"] == 30

    @pytest.mark.asyncio
    async def test_chat_completion_no_client(self, llm_service):
        """Test chat completion without client"""
        llm_service.client = None
        with pytest.raises(Exception):
            await llm_service.chat_completion([{"role": "user", "content": "Hello"}])

    def test_get_tools_schema(self, llm_service):
        """Test getting tools schema"""
        tools = llm_service.get_tools_schema()
        assert len(tools) == 6
        tool_names = [t["function"]["name"] for t in tools]
        assert "execute_sql" in tool_names
        assert "execute_pandas" in tool_names
        assert "generate_chart" in tool_names
        assert "detect_anomalies" in tool_names
        assert "run_data_quality_check" in tool_names
        assert "profile_dataset" in tool_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])