from typing import Tuple, Any


def _split_obj_attr_path(obj, key: str, exceptions: bool = True) -> Tuple[Any, str]:
    obj0 = obj
    key0 = key
    key_parts = key.split('.')
    key_path = key_parts[:-1]
    key_name = key_parts[-1]
    for next_obj in key_path:
        if not hasattr(obj, next_obj):
            if exceptions:
                raise AttributeError('{} not in {}'.format(key0, obj0))
            return None, ''
        obj = getattr(obj, next_obj)
    return obj, key_name


def set_obj_attr(obj, key: str, val: Any):
    """
    Set object property. Support '.' separate path to sub-objects, for example
    set_key_value(user, 'profile.address', 'Lapinrinne 1') sets user.profile.address as 'Lapinrinne 1'.
    :param obj: Object
    :param key: Attribute name
    :param val: New attribute value
    :return: None
    """
    obj, key_name = _split_obj_attr_path(obj, key)
    setattr(obj, key_name, val)


def get_obj_attr(obj, key: str, default: Any = None, exceptions: bool = True) -> Any:
    """
    Get object property. Support '.' separate path to sub-objects, for example
    get_key_value(user, 'profile.address') gets user.profile.address field value.
    :param obj: Object
    :param key: Attribute name
    :param default: Default return value if exceptions=False
    :param exceptions: Raise AttributeError or not. Default is True.
    :return: Attribute value
    """
    obj, key_name = _split_obj_attr_path(obj, key, exceptions=exceptions)
    return getattr(obj, key_name) if obj is not None else default
