import uvicorn
import os
from a2a.types import AgentSkill, AgentCard, AgentCapabilities
from a2a.server.request_handlers import DefaultRequestHandler
from descope import DescopeClient
from descope.exceptions import AuthException
from src.agents.OrchestratorAgent.agent_executor import OrchestratorAgentExecutor
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
from src.common.logger.logger import get_logger
from src.common.auth.auth import Auth
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


logger = get_logger("OrchAgent-M2M_Validation")
descope_client = DescopeClient(project_id=Auth.Descope.DESCOPE_PROJECT_KEY)
host = os.getenv("AGENT_HOST", "0.0.0.0")
port = int(os.getenv("AGENT_PORT", "10000"))
public_url = os.getenv("PUBLIC_URL", f"http://{host}:{port}")


class M2MMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify Machine-to-Machine (M2M) Bearer tokens
    """

    def __init__(self, app, required_scope: str = "orch_agent"):
        super().__init__(app)
        self.required_scope = required_scope

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/.well-known"):
            logger.info("Accessing public endpoint: %s", request.url.path)
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.info("Missing or invalid Authorization header")
            raise HTTPException(status_code=401, detail="Missing bearer token")

        token = auth_header.split(" ", 1)[1].strip()
        logger.info("Received token, validating...")

        try:
            claims = descope_client._auth._validate_token(
                token, audience=Auth.Descope.DESCOPE_PROJECT_KEY
            )
            logger.info("VALID M2M token for Agent: %s", self.required_scope)
        except AuthException as e:
            logger.info("Invalid M2M token: %s", e)
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

        # Check required scope
        token_scope = claims.get("scope", "")
        if isinstance(token_scope, str):
            token_scope = token_scope.split()

        if self.required_scope not in token_scope:
            logger.info(
                "Token missing required scope '%s', token scopes: %s",
                self.required_scope,
                token_scope,
            )
            raise HTTPException(
                status_code=403, detail=f"Missing required scope: {self.required_scope}"
            )

        logger.info("Token scope verified, continuing request")
        return await call_next(request)


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
        url=public_url,
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
    app.add_middleware(M2MMiddleware)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
