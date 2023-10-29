import logging
from typing import List, Tuple
from django.utils.translation import get_language, gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from jutil.redis_helpers import redis_get_json, redis_set_json

logger = logging.getLogger(__name__)


class RedisCachedSimpleListFilter(SimpleListFilter):
    """
    Simple list filter which caches lookup-options to Redis.
    Use as SimpleListFilter but implement lookups(self, request, model_admin) method in generate_lookups(self, request, model_admin) instead.
    SimpleListFilter queryset(self, request, queryset) should be implemented as normal.
    """

    redis_key_name = ""  # Redis key to store data. Default is class name.
    redis_key_expires = 3600  # Redis data expiration in seconds
    parameter_value_refresh_trigger = "_refresh"  # special querystring parameter name which causes cache to be refreshed by force
    refresh_link_in_lookups = False  # if refresh link should be included in list of lookups
    refresh_link_label = _("Refresh")

    def generate_lookups(self, request, model_admin):
        """
        Implement this method in derived class.
        :return: Same format return as lookups(), i.e. list of filter option (value, label) pairs.
        """
        raise Exception("generate_lookups() must be implemented in RedisCachedSimpleListFilter derived class")  # noqa

    def get_redis_key_name(self) -> str:
        base_name = self.redis_key_name if self.redis_key_name else str(self.__class__.__name__)
        return base_name + "." + (get_language() or "")

    def refresh_lookups(self, request, model_admin) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        try:
            out = self.generate_lookups(request, model_admin)
            key_name = self.get_redis_key_name()
            redis_set_json(key_name, out, ex=self.redis_key_expires)
            logger.debug("%s cache refreshed", key_name)
        except Exception as exc:
            logger.error(exc)
        return out

    def lookups(self, request, model_admin):
        try:
            parameter_value = request.GET.get(self.parameter_name)
            if parameter_value and str(parameter_value) == self.parameter_value_refresh_trigger:
                results = self.refresh_lookups(request, model_admin)
            else:
                results = redis_get_json(self.get_redis_key_name())
            if self.refresh_link_in_lookups:
                results.append((self.parameter_value_refresh_trigger, str(self.refresh_link_label)))
            return results
        except Exception as exc:
            logger.error(exc)
        return self.refresh_lookups(request, model_admin)
