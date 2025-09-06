import uvicorn

from a2a.types import AgentSkill, AgentCard, AgentCapabilities
import click
from a2a.server.request_handlers import DefaultRequestHandler

from src.agents.OrchestratorAgent.agent_executor import OrchestratorAgentExecutor
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication


def main():
    """
    Main function to create and run the orchestrator agent.
    """
    skills = [
        AgentSkill(
            id="task_delegation",
            name="Delegate Tasks",
            description="Analyze requests and delegate to appropriate specialized agents",
            tags=["coordination", "routing", "delegation", "emergency"],
            examples=[
                "Route fire emergency to FireAgent",
                "Delegate minor injury to MinorCallsAgent",
                "Coordinate agent responses",
            ],
        ),
        AgentSkill(
            id="general_assistance",
            name="General Information",
            description="Provide general information and non-emergency assistance",
            tags=["information", "general", "assistance", "help"],
            examples=[
                "Answer general questions",
                "Provide information about services",
                "Handle non-emergency inquiries",
            ],
        ),
        AgentSkill(
            id="emergency_triage",
            name="Emergency Triage",
            description="Assess emergency severity and route to appropriate agents",
            tags=["triage", "emergency", "assessment", "safety"],
            examples=[
                "Assess emergency severity levels",
                "Route fire emergencies appropriately",
                "Triage minor vs major emergencies",
            ],
        ),
    ]

    agent_card = AgentCard(
        name="orchestrator_agent",
        description="Central coordination agent that delegates tasks to specialized agents and handles general inquiries. Built using agent development framework for emergency response coordination.",
        url="http://localhost:10000/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=skills,
        capabilities=AgentCapabilities(streaming=True),
    )

    request_handler = DefaultRequestHandler(
        agent_executor=OrchestratorAgentExecutor(), task_store=InMemoryTaskStore()
    )

    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )

    app = server.build()
    uvicorn.run(app, host="0.0.0.0", port=10000)


if __name__ == "__main__":
    main()
