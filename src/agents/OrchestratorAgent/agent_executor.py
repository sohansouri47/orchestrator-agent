from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater

from src.agents.OrchestratorAgent.agent import OrchestratorAgent
from a2a.utils import new_task, new_agent_text_message

from a2a.utils.errors import ServerError

from a2a.types import Task, TaskState, UnsupportedOperationError
import json
import asyncio
from src.common.db.Postgre import ConversationHistoryManager
from src.common.logger.logger import get_logger

logger = get_logger("ORCH_AGENT_EXCUTOR")


class OrchestratorAgentExecutor(AgentExecutor):
    """
    Implements the AgentExecutor interface to integrate the
    website builder simple agent with the A2A framework.
    """

    def __init__(self):
        self.agent = OrchestratorAgent()
        self.manager = ConversationHistoryManager()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Executes the agent with the provided context and event queue.
        """
        message = context.message
        logger.info(f"METADATA:{message}")
        metadata = message.metadata if message else {}
        user_id = metadata.get("user_id")
        role = message.role.value if message and message.role else None
        query = context.get_user_input()
        input_payload = {
            "user": user_id,
            "role": role,
            "msg": query,
        }
        input_payload_str = json.dumps(input_payload)
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        store_payload = {"role": "user", "query": query}
        await self.manager.store(
            conversation_id=task.context_id,
            username=user_id,
            conversation=str(store_payload),
        )
        logger.info("Stored question to conversation history")
        updater = TaskUpdater(event_queue, task.id, task.context_id)

        try:
            async for item in self.agent.invoke(input_payload_str, task.context_id):
                is_task_complete = item.get("is_task_complete", False)

                if not is_task_complete:
                    message = item.get(
                        "updates", "The Agent is still working on your request."
                    )
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(message, task.context_id, task.id),
                    )
                else:
                    logger.info(item)
                    final_result = item.get("content", "no result received")
                    await updater.update_status(
                        TaskState.completed,
                        new_agent_text_message(final_result, task.context_id, task.id),
                    )
                    logger.info(f"Final Rsponse from Orch Agent:{final_result}")
                    await self.manager.store(
                        conversation_id=task.context_id,
                        username=user_id,
                        conversation=str(final_result),
                    )
                    logger.info("Stored response to conversation history")
                    await asyncio.sleep(0.1)

                    break

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(error_message, task.context_id, task.id),
            )
            raise

    async def cancel(
        self, request: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
