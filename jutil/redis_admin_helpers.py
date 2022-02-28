import logging
from typing import List, Tuple
from django.contrib.admin import SimpleListFilter
from jutil.redis_helpers import redis_get_json, redis_set_json

logger = logging.getLogger(__name__)


class RedisCachedSimpleListFilter(SimpleListFilter):
    """
    Simple list filter which caches lookup-options to Redis.
    """

    redis_key_name = ""
    redis_key_expires = 3600

    def generate_lookups(self, request, model_admin):
        """
        Implement this method in derived class.
        :return: Same format return as lookups(), i.e. list of filter option (value, label) pairs.
        """
        raise Exception("generate_lookups() must be implemented in RedisCachedSimpleListFilter derived class")

    def get_redis_key_name(self) -> str:
        return self.redis_key_name if self.redis_key_name else f"{self.__class__.__name__}"

    def lookups(self, request, model_admin):
        key_name = self.get_redis_key_name()
        try:
            return redis_get_json(key_name)
        except Exception as exc:
            logger.error(exc)
        out: List[Tuple[str, str]] = []
        try:
            out = self.generate_lookups(request, model_admin)
            redis_set_json(key_name, out, ex=self.redis_key_expires)
            logger.debug("%s cache refreshed", key_name)
        except Exception as exc:
            logger.error(exc)
        return out
