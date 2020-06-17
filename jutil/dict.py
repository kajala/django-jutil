import re
from collections import OrderedDict
from typing import List, Sequence, Tuple, Any, Dict, TypeVar
from django.utils.text import capfirst


R = TypeVar('R')
S = TypeVar('S')


def sorted_dict(d: Dict[Any, R]) -> Dict[Any, R]:
    """
    Returns OrderedDict sorted by ascending key
    :param d: dict
    :return: OrderedDict
    """
    return OrderedDict(sorted(d.items()))


def choices_label(choices: Sequence[Tuple[S, str]], value: S) -> str:
    """
    Iterates (value,label) list and returns label matching the choice
    :param choices: [(choice1, label1), (choice2, label2), ...]
    :param value: Value to find
    :return: label or None
    """
    for key, label in choices:
        if key == value:
            return label
    return ''


def _dict_to_html_format_key(k: str) -> str:
    if k.startswith('@'):
        k = k[1:]
    k = k.replace('_', ' ')
    k = re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', k)
    parts = k.split(' ')
    out: List[str] = [str(capfirst(parts[0].strip()))]
    for p in parts[1:]:
        p2 = p.strip().lower()
        if p2:
            out.append(p2)
    return ' '.join(out)


def _dict_to_html_r(data: Dict[str, Any], margin: str = '', format_keys: bool = True) -> str:
    if not isinstance(data, dict):
        return '{}{}\n'.format(margin, data)
    out = ''
    for k, v in sorted_dict(data).items():
        if isinstance(v, dict):
            out += '{}{}:\n'.format(margin, _dict_to_html_format_key(k) if format_keys else k)
            out += _dict_to_html_r(v, margin + '    ', format_keys=format_keys)
            out += '\n'
        elif isinstance(v, list):
            for v2 in v:
                out += '{}{}:\n'.format(margin, _dict_to_html_format_key(k) if format_keys else k)
                out += _dict_to_html_r(v2, margin + '    ', format_keys=format_keys)
            out += '\n'
        else:
            out += '{}{}: {}\n'.format(margin, _dict_to_html_format_key(k) if format_keys else k, v)
    return out


def dict_to_html(data: Dict[str, Any], format_keys: bool = True) -> str:
    """
    Formats dict to simple pre-formatted html (<pre> tag).
    :param data: dict
    :param format_keys: Re-format 'additionalInfo' and 'additional_info' type of keys as 'Additional info'
    :return: str (html)
    """
    return '<pre>' + _dict_to_html_r(data, format_keys=format_keys) + '</pre>'
