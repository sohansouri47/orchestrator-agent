from google.adk.agents import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from src.common.config.prompts import AgentPrompts
from src.common.config.constants import LlmConfig
from google.adk.models.lite_llm import LiteLlm
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from collections.abc import AsyncIterable
import uuid
from src.common.agent_registry.agent_registry import AgentRegistry
from src.common.auth.auth import OAuth
from src.common.agent_registry.agent_connector import AgentConnector
import uuid
from src.common.db.Postgre import ConversationHistoryManager
import json
import re
from src.common.logger.logger import get_logger

logger = get_logger("Agent")


class OrchestratorAgent:
    def __init__(self):
        self._user_id = None
        self._agent_registry = AgentRegistry()
        self._agent_auth = OAuth()
        self._agent_connector = AgentConnector()
        self._conversation_history_manger = ConversationHistoryManager()
        self._agent = None
        self._runner = None
        self._context_id = None

    async def _initialize(self):
        """Initialize async components"""
        logger.info("Agent initialized")
        self._agent = await self._build_agent()
        self._runner = Runner(
            app_name=AgentPrompts.OrchestratorAgent.NAME,
            agent=self._agent,
            session_service=InMemorySessionService(),
        )

    async def _build_agent(self) -> LlmAgent:
        agentlist = await self._agent_registry.get_agents_list()
        agentcards = await self._agent_registry.get_context_cards()
        logger.info("Get all agentcards from the registry")
        conversation_history = await self._conversation_history_manger.fetch_last_n(
            self._context_id, 8
        )
        logger.info(f"Fetch Conversation history for context:{conversation_history}")
        agentlist_str = json.dumps(agentlist, indent=2)
        agentcards_str = json.dumps(agentcards, indent=2)
        return LlmAgent(
            name=AgentPrompts.OrchestratorAgent.NAME,
            instruction=AgentPrompts.OrchestratorAgent.INSTRUCTION.format(
                conversation_history=conversation_history,
                agentlist=agentlist_str,
                agentcards=agentcards_str,
            ),
            description=AgentPrompts.OrchestratorAgent.DESCRIPTION,
            model=LiteLlm(model=LlmConfig.Anthropic.SONET_4_MODEL),
            tools=[
                FunctionTool(self.redirect_agent),
                # FunctionTool(self.operator_handoff),
            ],
        )

    # async def operator_handoff(self):
    #     return "Handded off to operator"

    async def redirect_agent(self, agent_name: str, message: str) -> str:
        logger.info("Agent Redirected")
        try:
            cards = await self._agent_registry.load_cards()
            token = await self._agent_auth.get_m2m_token(agent_name=agent_name)
            matched_card = None
            metadata = {
                "user_id": self._user_id,
                "context_id": self._context_id,
                "role": self._role,
            }

            for card in cards:
                if card.name.lower() == agent_name.lower():
                    matched_card = card
                elif getattr(card, "id", "").lower() == agent_name.lower():
                    matched_card = card

            if matched_card is None:
                return "Agent not found"

            result = await self._agent_connector.send_task(
                matched_card=matched_card,
                message=message,
                token=token,
                metadata=metadata,
            )
            return str(result)

        except Exception as e:
            return f"Error redirecting to agent: {str(e)}"

    async def invoke(self, query: str, context_id: str) -> AsyncIterable[dict]:
        try:
            payload: dict[str, str] = json.loads(query)
            self._user_id = payload.get("user")
            self._context_id = context_id
            self._role = payload.get("role")
            user_query = payload.get("msg")
        except (json.JSONDecodeError, AttributeError):
            self._user_id = None
            self._context_id = context_id
        await self._initialize()
        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            session_id=self._context_id,
            user_id=self._user_id,
        )

        if not session:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                session_id=self._context_id,
                user_id=self._user_id,
            )

        user_content = types.Content(
            role=self._role, parts=[types.Part.from_text(text=user_query)]
        )

        async for event in self._runner.run_async(
            user_id=self._user_id, new_message=user_content, session_id=self._context_id
        ):
            if event.is_final_response():
                final_response = ""
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[-1].text
                ):
                    final_response = event.content.parts[-1].text

                if not final_response or not final_response.strip():
                    raise ValueError("Model returned empty response, cannot parse JSON")

                yield {"is_task_complete": True, "content": final_response}
