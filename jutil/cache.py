import logging
from typing import Optional, TYPE_CHECKING, Any, Sequence, List

logger = logging.getLogger(__name__)


class CachedFieldsMixin:
    """
    Cached fields mixin. Usage:
    1) List cached field names in cached_fields list
    2) Implement get_xxx functions where xxx is cached field name
    3) Call update_cached_fields() to refresh
    4) Optionally call update_cached_fields_pre_save() on pre_save signal for objects (to automatically refresh on save)
    """

    cached_fields: Sequence[str] = []

    if TYPE_CHECKING:
        pk: Any = None

        def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
            pass

    def update_cached_fields(
        self, commit: bool = True, exceptions: bool = True, updated_fields: Optional[Sequence[str]] = None, force: bool = False
    ) -> List[str]:
        """
        Updates cached fields using get_xxx calls for each cached field (in cached_fields list).
        :param commit: Save update fields to DB
        :param exceptions: Raise exceptions or not
        :param updated_fields: List of cached fields to update. Pass None for all cached fields.
        :param force: Force commit of all cached fields even if nothing changed
        :return: List of changed fields
        """
        changed_fields: List[str] = []
        try:
            fields = updated_fields or self.cached_fields
            for k in fields:
                f = "get_" + k
                if not hasattr(self, f):
                    raise Exception("Field {k} marked as cached in {obj} but function get_{k}() does not exist".format(k=k, obj=self))
                v = self.__getattribute__(f)()
                if force or getattr(self, k) != v:
                    setattr(self, k, v)
                    changed_fields.append(k)
            if commit and changed_fields:
                self.save(update_fields=changed_fields)  # pytype: disable=attribute-error
            return changed_fields
        except Exception as err:
            logger.warning("%s update_cached_fields failed for %s: %s", self.__class__.__name__, self, err)
            if exceptions:
                raise err
            return changed_fields

    def update_cached_fields_pre_save(self, update_fields: Optional[Sequence[str]]) -> List[str]:
        """
        Call on pre_save signal for objects (to automatically refresh on save).
        :param update_fields: list of fields to update
        :return: List of changed fields
        """
        if hasattr(self, "pk") and self.pk and update_fields is None:
            return self.update_cached_fields(commit=False, exceptions=False)
        return []


def update_cached_fields(*args):
    """
    Calls update_cached_fields() for each object passed in as argument.
    Supports also iterable objects by checking __iter__ attribute.
    :param args: List of objects
    :return: None
    """
    for a in args:
        if a is not None:
            if hasattr(a, "__iter__"):
                for e in a:
                    if e is not None:
                        e.update_cached_fields()
            else:
                a.update_cached_fields()
