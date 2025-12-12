import asyncio
from collections import defaultdict
from typing import AsyncGenerator
from uuid import UUID

from loguru import logger


class Broadcaster:
    def __init__(self):
        # Map user_id -> set of queues
        self.subscribers: defaultdict[UUID, set[asyncio.Queue]] = defaultdict(set)

    async def subscribe(self, user_id: UUID, user_name: str | None = None) -> AsyncGenerator[str, None]:
        queue = asyncio.Queue()
        self.subscribers[user_id].add(queue)
        logger.debug(
            "User with id {user_id} and name {user_name} subscribed to sse stream",
            user_id=user_id,
            user_name=user_name or "unknown username",
        )

        try:
            while True:
                message = await queue.get()
                yield f"data: {message}\n\n"
        except Exception as e:
            logger.error(
                f"Encountered error on SSE stream for user with id {user_id} and name {user_name}. Error: {e}",
                user_id=user_id,
                user_name=user_name or "unknown username",
                e=e,
            )
        finally:
            self.subscribers[user_id].remove(queue)
            if not self.subscribers[user_id]:
                del self.subscribers[user_id]

    async def publish(self, user_id: UUID, message: str):
        if user_id not in self.subscribers:
            return

        # Iterate in case user has multiple tabs. Convert to list to avoid potential "set changed size during iteration" error
        for queue in list(self.subscribers[user_id]):
            await queue.put(message)


sse_broadcaster = Broadcaster()
