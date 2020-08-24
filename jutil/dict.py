import logging
from collections import OrderedDict
from typing import Sequence, Tuple, Dict, TypeVar, Any

R = TypeVar('R')
S = TypeVar('S')

logger = logging.getLogger(__name__)


def sorted_dict(d: Dict[S, R]) -> Dict[S, R]:
    """
    Returns dict sorted by ascending key
    :param d: dict
    :return: OrderedDict
    """
    return OrderedDict(sorted(d.items()))


def choices_label(choices: Sequence[Tuple[S, str]], value: S) -> str:
    logger.warning('jutil.dict.choices_label is deprecated, use jutil.format.choices_label')
    from jutil.format import choices_label as format_choices_label  # noqa  # type: ignore
    return format_choices_label(choices, value)


def dict_to_html(data: Dict[str, Any], format_keys: bool = True) -> str:
    logger.warning('jutil.dict.dict_to_html is deprecated, use jutil.format.format_dict_as_html')
    from jutil.format import format_dict_as_html  # noqa  # type: ignore
    return format_dict_as_html(data, format_keys)
