from typing import Any
from redis.asyncio import Redis


async def set_key_to_cache(redis: Redis, name: str, value: str, ex: int) -> None:
    await redis.set(name=name, value=value, ex=ex)


async def get_del_cached_value(redis: Redis, name: str) -> Any:
    return await redis.getdel(name=name)
