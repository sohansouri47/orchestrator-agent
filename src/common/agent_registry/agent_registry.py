import json
import os
from a2a.types import AgentCard
from a2a.client import A2ACardResolver
import httpx
import json
from src.common.logger.logger import get_logger

logger = get_logger("agent_registry")


class AgentRegistry:
    """Agent registry to load agent cards from URLs"""

    def __init__(self):
        self._agent_cards = None

    async def load_cards(self, file_path: str = None) -> list[AgentCard]:
        """
        Load agent cards from registry file

        Args:
            file_path: Optional path to registry JSON file

        Returns:
            List of AgentCards
        """
        try:
            base_urls = json.loads(os.getenv("AGENT_REGISTRY", "[]"))
            logger.info(f"baseurls: {base_urls}")
        except json.JSONDecodeError:
            return []

        cards = []
        async with httpx.AsyncClient(timeout=300.0) as client:
            for base_url in base_urls:
                resolver = A2ACardResolver(
                    base_url=base_url.rstrip("/"), httpx_client=client
                )
                card = await resolver.get_agent_card()
                cards.append(card)
        return cards

    async def get_context_cards(self) -> list[dict]:
        if self._agent_cards is None:
            self._agent_cards = await self.load_cards()
        return await self.simplify_cards(self._agent_cards)

    async def get_agents_list(self) -> list[str]:
        if self._agent_cards is None:
            self._agent_cards = await self.load_cards()
        return [card.name for card in self._agent_cards]

    async def simplify_cards(self, cards: list[AgentCard]) -> list[dict]:
        """Extract only essential info for LLM selection"""
        if self._agent_cards is None:
            self._agent_cards = await self.load_cards()
        return [
            {
                "name": card.name,
                "description": card.description,
                "url": card.url,
                "skills": [
                    {"description": skill.description, "tags": skill.tags}
                    for skill in card.skills
                ],
            }
            for card in cards
        ]
