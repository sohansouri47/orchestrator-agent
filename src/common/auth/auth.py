import os
import logging
import ssl
import certifi
import aiohttp
import redis.asyncio as redis
from src.common.config.config import Auth
from src.common.logger.logger import get_logger

logger = get_logger("DESCOPE AUTH")

TOKEN_BUFFER_SECONDS = 300


# Initialize async Redis client
redis_client = redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True
)


class OAuth:
    def __init__(self):
        pass

    async def get_m2m_token(self, agent_name: str) -> str:
        """
        Request a machine-to-machine (M2M) OAuth2 access token for an agent.

        This function performs a client_credentials grant flow against Descope's
        authorization server. The scope used in the request is derived from the
        given agent name, which defines what resources or permissions the token
        should grant.

        Args:
            agent_name (str): The logical name or identifier of the agent.
                This is mapped to one or more OAuth2 scopes that determine
                the level of access granted.

        Returns:
            str: A valid access token string if the request succeeds.
        """
        cache_key = f"m2m_token:{agent_name}"

        # Check cache first
        logger.info("check for existing token")
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info("Cache hit for agent '%s'", agent_name)
            return cached

        logger.info("Cache miss for agent '%s'. Requesting new token...", agent_name)

        # Prepare token request data
        data = {
            "grant_type": "client_credentials",
            "client_id": Auth.Descope.DESCOPE_CLIENT_ID,
            "client_secret": Auth.Descope.DESCOPE_CLIENT_SECRET,
            "scope": {agent_name},
        }

        # Make async HTTP request with SSL context
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        timeout = aiohttp.ClientTimeout(total=20)
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        logger.info(f"Fetch new token from descope for agent:{agent_name}")
        async with aiohttp.ClientSession(
            timeout=timeout, connector=connector
        ) as session:
            async with session.post(Auth.Descope.DESCOPE_TOKEN_URL, data=data) as resp:
                resp.raise_for_status()
                res = await resp.json()
        # Extract token and expiration
        token = res.get("access_token")
        logger.info("fetched token successfully")
        expires_in = int(res.get("expires_in", 3600))

        if not token:
            logger.error("Failed to obtain M2M token for agent '%s'", agent_name)
            raise ValueError("Failed to obtain M2M token")

        # Cache with TTL (subtract buffer to prevent expired token usage)
        ttl = max(0, expires_in - TOKEN_BUFFER_SECONDS)
        await redis_client.set(cache_key, token, ex=ttl)

        logger.info(
            "Stored new token for agent '%s' in Redis with TTL=%s seconds",
            agent_name,
            ttl,
        )
        return token
