from db import redis
from redis.typing import EncodableT, ResponseT


def get_value(key: str) -> ResponseT:
    return redis.get(key)


def set_value(key: str, value: EncodableT, expire_time: int = 3600 * 24):
    redis.set(key, value, ex=expire_time)
