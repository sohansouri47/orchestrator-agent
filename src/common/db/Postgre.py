import psycopg
import psycopg.rows
import json
import os
from typing import List, Dict, Optional


class ConversationHistoryManager:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.table_name = os.getenv("CONVERSATION_TABLE", "conversationss")

    async def _create_table(self):
        """Create conversation table"""
        async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        username VARCHAR(255) NOT NULL,
                        conversation_id VARCHAR(255) NOT NULL,
                        conversation JSONB NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (conversation_id)
                    );
                    """
                )
            await conn.commit()

    async def store(self, username: str, conversation_id: str, conversation):
        """Store/update conversation with automatic str->dict handling"""
        if isinstance(conversation, str):
            try:
                conversation = json.loads(conversation)
            except json.JSONDecodeError:
                conversation = {"text": conversation}

        async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"SELECT conversation FROM {self.table_name} WHERE conversation_id = %s",
                    (conversation_id,),
                )
                result = await cur.fetchone()

                if result:
                    try:
                        existing_data = json.loads(result[0])
                    except Exception:
                        existing_data = []

                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]

                    existing_data.append(conversation)

                    await cur.execute(
                        f"""
                        UPDATE {self.table_name} 
                        SET conversation = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE conversation_id = %s
                        """,
                        (json.dumps(existing_data), conversation_id),
                    )
                else:
                    await cur.execute(
                        f"""
                        INSERT INTO {self.table_name} (username, conversation_id, conversation)
                        VALUES (%s, %s, %s)
                        """,
                        (username, conversation_id, json.dumps([conversation])),
                    )
            await conn.commit()

    async def fetch(self, conversation_id: str) -> Optional[Dict]:
        """Fetch conversation by ID"""
        async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
            async with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                await cur.execute(
                    f"""
                    SELECT username, conversation_id, conversation 
                    FROM {self.table_name} 
                    WHERE conversation_id = %s
                    """,
                    (conversation_id,),
                )
                result = await cur.fetchone()
                if result:
                    try:
                        result["conversation"] = json.loads(result["conversation"])
                    except Exception:
                        pass
                return result

    async def fetch_last_n(self, conversation_id: str, n: int = 10) -> List[Dict]:
        """Fetch last n interactions from a conversation with safe str->dict handling"""
        async with await psycopg.AsyncConnection.connect(self.database_url) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"""
                    SELECT conversation
                    FROM {self.table_name} 
                    WHERE conversation_id = %s
                    """,
                    (conversation_id,),
                )
                result = await cur.fetchone()

                if not result or not result[0]:
                    return []

                raw_data = result[0]

                def safe_load(data):
                    """Recursively decode JSON strings until we get a list/dict"""
                    while isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except Exception:
                            break
                    if isinstance(data, dict):
                        return [data]
                    if isinstance(data, list):
                        flattened = []
                        for item in data:
                            if isinstance(item, str):
                                try:
                                    loaded = json.loads(item)
                                    if isinstance(loaded, list):
                                        flattened.extend(loaded)
                                    else:
                                        flattened.append(loaded)
                                except Exception:
                                    flattened.append({"text": item})
                            elif isinstance(item, dict):
                                flattened.append(item)
                            else:
                                flattened.append({"value": item})
                        return flattened
                    return []

                all_interactions = safe_load(raw_data)
                return all_interactions[-n:]
