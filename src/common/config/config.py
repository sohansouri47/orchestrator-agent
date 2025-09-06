import os
from dotenv import load_dotenv
import uuid

load_dotenv()


class LLMProviders:
    class Anthropic:
        API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    class Google:
        API_KEY = os.getenv("GOOGLE_API_KEY", "")


class Auth:
    class Descope:
        DESCOPE_PROJECT_KEY = os.getenv("DESCOPE_PROJECT_KEY", "")
        DESCOPE_TOKEN_URL = os.getenv(
            "DESCOPE_TOKEN_URL", "https://api.descope.com/oauth2/v1/apps/token"
        )
        DESCOPE_CLIENT_ID = os.getenv("DESCOPE_CLIENT_ID", "")
        DESCOPE_CLIENT_SECRET = os.getenv("DESCOPE_CLIENT_SECRET", "")


class AgenticSystemConfig:
    ORCH_AGENT_URL = os.getenv("ORCH_AGENT_URL", "")
    PUBLIC_AGENT_CARD_PATH = os.getenv("PUBLIC_AGENT_CARD_PATH", "")


class ConversationConfig:
    CONTEXT_ID = os.getenv("CONTEXT_ID", str(uuid.uuid4()))
    USER_ID = os.getenv("USER_ID", str(uuid.uuid4()))
