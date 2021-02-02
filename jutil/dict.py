import logging
from collections import OrderedDict
from typing import Dict, TypeVar

R = TypeVar("R")
S = TypeVar("S")

logger = logging.getLogger(__name__)


def sorted_dict(d: Dict[S, R]) -> Dict[S, R]:
    """
    Returns dict sorted by ascending key
    :param d: dict
    :return: OrderedDict
    """
    return OrderedDict(sorted(d.items()))
