import asyncpg
from app.core.config import Settings

class Database:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            host=self.settings.POSTGRES_HOST,
            port=self.settings.POSTGRES_PORT,
            database=self.settings.POSTGRES_DB,
            user=self.settings.POSTGRES_USER,
            password=self.settings.POSTGRES_PASSWORD,
            min_size=5,
            max_size=20
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def execute_transaction(self, queries: list):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for query, args in queries:
                    await conn.execute(query, *args) 