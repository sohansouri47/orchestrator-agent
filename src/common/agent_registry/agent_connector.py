from typing import Any
from uuid import uuid4
from a2a.types import SendMessageRequest, MessageSendParams
import httpx
from a2a.client import A2AClient
from src.common.logger.logger import get_logger
import json

logger = get_logger("Agent Router")


class AgentConnector:
    """
    Connects to a remote A2A agent and provides a uniform method to delegate tasks
    """

    def __init__(self):
        pass

    async def send_task(
        self, matched_card, message: str, token: str, metadata: dict
    ) -> str:
        """
        Send a task to the agent and return the Task object

        Args:
            message (str): The message to send to the agent
            session_id (str): The session ID for tracking the task
            token(str): Auth token

        Returns:
            Task: The Task object containing the response from the agent
        """
        logger.info(
            f"message:{message},mathchedcard:{matched_card},metadata:{metadata}"
        )
        async with httpx.AsyncClient(
            headers={"Authorization": f"Bearer {token}"}, timeout=300.0
        ) as httpx_client:
            a2a_client = A2AClient(
                httpx_client=httpx_client,
                agent_card=matched_card,
            )
            send_message_payload: dict[str, Any] = {
                "message": {
                    "role": metadata["role"],
                    "messageId": str(uuid4()),
                    "parts": [
                        {
                            "text": (message),
                            "kind": "text",
                        }
                    ],
                    "metadata": {"user_id": metadata["user_id"]},
                    "context_id": metadata["context_id"],
                }
            }

            request = SendMessageRequest(
                id=str(uuid4()), params=MessageSendParams(**send_message_payload)
            )
            logger.info("Request sennt to subagent")
            response = await a2a_client.send_message(request=request)
            logger.info(f"Response recieved from subagent:{response}")
            response_data = response.model_dump(mode="json", exclude_none=True)

            try:
                agent_response = response_data["result"]["status"]["message"]["parts"][
                    0
                ]["text"]

            except (KeyError, IndexError):
                agent_response = "No response from agent"

            return agent_response
