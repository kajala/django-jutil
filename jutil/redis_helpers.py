import json
import logging
from datetime import timedelta
from functools import lru_cache
from typing import Any, Optional, Union
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

try:
    import redis  # type: ignore

    if int(redis.__version__.split(".", maxsplit=1)[0]) < 4:  # type: ignore
        raise Exception("Invalid version")  # noqa
except Exception as err:
    raise Exception("Using jutil.redis_helpers requires redis>=4.0.0 installed") from err  # noqa

logger = logging.getLogger(__name__)


@lru_cache()
def redis_connection_pool(connection_str: str) -> redis.ConnectionPool:
    """
    Returns cached Redis connection pool.
    :param connection_str: str
    :return: redis.ConnectionPool
    """
    return redis.ConnectionPool.from_url(connection_str)


@lru_cache()
def redis_instance(connection_str: str = "") -> redis.Redis:
    """Returns cached Redis instance using settings.REDIS_URL connection string.
    If no connection string is provided, AND settings.REDIS_URL is empty or missing, then
    localhost with default Redis settings (no password) is assumed.

    Args:
        connection_str: Default connection string is settings.REDIS_URL or 'redis://:@localhost:6379/1?max_connections=50'.
    """
    if not connection_str:
        connection_str = settings.REDIS_URL if hasattr(settings, "REDIS_URL") else "redis://:@localhost:6379/1?max_connections=50"  # type: ignore
    return redis.Redis(connection_pool=redis_connection_pool(connection_str))


def redis_prefix_key(name: str) -> str:
    """Returns name prefixed with default DB name separated with dot.
    For example, if Django default DB name is "my_db"
    then "my_key" is returned as "my_db.my_key".

    Args:
        name: Key name without prefix

    Returns:
        Key name with prefix
    """
    return str(settings.DATABASES["default"]["NAME"]) + "." + name


def redis_set_bytes(name: str, value: bytes, ex: Optional[Union[int, timedelta]] = None, nx: bool = False):
    """Sets value of the key as bytes to Redis.

    Uses default DB name as a key prefix. For example, if default DB name is "my_db"
    then key "my_key" is stored in Redis as "my_db.my_key".

    Args:
        name: Key name without DB name prefix
        value: bytes
        ex: Optional expire time either in seconds or timedelta
        nx: Set only if value does not exist in Redis. See Redis docs for details.
    """
    return redis_instance().set(redis_prefix_key(name), value, ex=ex, nx=nx)


def redis_get_bytes_or_none(name: str) -> Optional[bytes]:
    """Returns value of the key as bytes from Redis or None if value missing.

    Uses default DB name as a key prefix. For example, if default DB name is "my_db"
    then key "my_key" is stored in Redis as "my_db.my_key".

    Args:
        name: Key name without DB name prefix

    Returns:
        bytes or None if value missing
    """
    return redis_instance().get(redis_prefix_key(name))  # type: ignore


def redis_get_bytes(name: str) -> bytes:
    """Returns value of the key as bytes from Redis. Raise Exception if value is missing.

    Uses default DB name as a key prefix. For example, if default DB name is "my_db"
    then key "my_key" is stored in Redis as "my_db.my_key".

    Args:
        name: Key name without DB name prefix

    Returns:
        bytes
    """
    buf = redis_get_bytes_or_none(name)
    if buf is None:
        raise Exception(f"{redis_prefix_key(name)} not in Redis")  # noqa
    return buf


def redis_set_json(name: str, value: Any, ex: Optional[Union[int, timedelta]] = None, nx: bool = False, cls=DjangoJSONEncoder):
    """Sets value of the key as JSON to Redis.

    Uses default DB name as a key prefix. For example, if default DB name is "my_db"
    then key "my_key" is stored in Redis as "my_db.my_key".

    Stored value is assumed to be JSON and it is serialized before sending.

    Args:
        name: Key name without DB name prefix
        value: Any value that will be serialized as JSON
        ex: Optional expire time either in seconds or timedelta
        nx: Set only if value does not exist in Redis. See Redis docs for details.
        cls: JSON encoder class (default is DjangoJSONEncoder from Django)
    """
    value_bytes = json.dumps(value, cls=cls).encode()
    return redis_instance().set(redis_prefix_key(name), value_bytes, ex=ex, nx=nx)


def redis_get_json_or_none(name: str) -> Any:
    """Returns value of the key as JSON from Redis or None if value missing.

    Uses default DB name as a key prefix. For example, if default DB name is "my_db"
    then key "my_key" is stored in Redis as "my_db.my_key".

    Stored value is assumed to be JSON and it is deserialized before returning.

    Args:
        name: Key name without DB name prefix

    Returns:
        bytes deserialized as JSON or None
    """
    try:
        buf = redis_instance().get(redis_prefix_key(name))
        if buf is not None:
            return json.loads(buf)  # type: ignore
    except Exception as exc:
        logger.error("redis_get_json(%s) failed: %s", name, exc)
    return None


def redis_get_json(name: str) -> Any:
    """Returns value of the key as JSON from Redis. Raise Exception if value is missing.

    Uses default DB name as a key prefix. For example, if default DB name is "my_db"
    then key "my_key" is stored in Redis as "my_db.my_key".

    Stored value is assumed to be JSON and it is deserialized before returning.

    Args:
        name: Key name without DB name prefix

    Returns:
        bytes deserialized as JSON
    """
    buf = redis_instance().get(redis_prefix_key(name))
    if buf is None:
        raise Exception(f"{redis_prefix_key(name)} not in Redis")  # noqa
    return json.loads(buf)  # type: ignore


def redis_delete(name: str):
    """Deletes key-value pair from from Redis.

    Uses default DB name as a key prefix. For example, if default DB name is "my_db"
    then key "my_key" is stored in Redis as "my_db.my_key".

    Args:
        name: Key name without DB name prefix
    """
    return redis_instance().delete(redis_prefix_key(name))
