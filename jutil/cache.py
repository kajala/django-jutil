import logging
from django.utils.timezone import now


logger = logging.getLogger(__name__)


class CachedFieldsMixin(object):
    """
    Cached fields mixin. Usage:
    1) List cached field names in cached_fields list
    2) Implement get_xxx functions where xxx is cached field name
    3) Call update_cached_fields() to refresh
    4) Optionally call update_cached_fields_pre_save() on pre_save signal for objects (to automatically refresh on save)
    """
    cached_fields = []

    def is_cache_update(self, update_fields: list) -> bool:
        """
        Returns True if specified field update list matches exactly cached fields update
        :param update_fields: List of fields saved in this update
        :return: bool
        """
        return update_fields and sorted(list(update_fields)) == sorted(list(self.cached_fields))

    def update_cached_fields(self, commit: bool=True, exceptions: bool=True):
        try:
            """
            :param updated_fields: List of fields to update. Pass None for all.
            :param commit: Save update fields to DB
            """
            for k in self.cached_fields:
                f = 'get_' + k
                if not hasattr(self, f):
                    raise Exception('Field {} marked as cached in {} but function get_{}() does not exist'.format(k, self, k))
                v = self.__getattribute__(f)()
                setattr(self, k, v)
            if commit:
                self.save(update_fields=self.cached_fields)
        except Exception as e:
            logger.error('{}.update_cached_fields: {}'.format(self.__class__, e))
            if exceptions:
                raise e

    def update_cached_fields_pre_save(self, update_fields: list):
        if self.id and update_fields is None:
            self.update_cached_fields(commit=False, exceptions=False)


def update_cached_fields(*args):
    """
    Calls update_cached_fields() for each object passed in as argument.
    Supports also iterable objects by checking __iter__ attribute.
    :param args: List of objects
    :return: None
    """
    for a in args:
        if a is not None:
            if hasattr(a, '__iter__'):
                for e in a:
                    e.update_cached_fields()
            else:
                a.update_cached_fields()
