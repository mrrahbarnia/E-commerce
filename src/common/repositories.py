from typing import Any
from redis.asyncio import Redis


async def set_key_to_cache(redis: Redis, name: str, value: str, ex: int) -> None:
    await redis.set(name=name, value=value, ex=ex)


async def get_del_cached_value(redis: Redis, name: str) -> Any:
    return await redis.getdel(name=name)


async def get_value_from_cache(redis: Redis, key: str) -> str | None:
    value = await redis.get(key)
    if value is None:
        return None
    return value


async def del_cache_key_by_regex_pattern(redis: Redis, pattern: str) -> None:
    keys = await redis.keys(pattern=pattern)
    if keys:
        await redis.delete(*keys)
