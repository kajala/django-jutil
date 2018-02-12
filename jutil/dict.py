from collections import OrderedDict


def sorted_dict(d: dict):
    """
    Returns OrderedDict sorted by ascending key
    :param d: dict
    :return: OrderedDict
    """
    return OrderedDict(sorted(d.items()))


def choices_label(choices: tuple, value) -> str:
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


def _dict_to_html_r(data: dict, margin: str='') -> str:
    if not isinstance(data, dict):
        return '{}{}\n'.format(margin, data)
    out = ''
    for k, v in sorted_dict(data).items():
        if isinstance(v, dict):
            out += '{}{}:\n'.format(margin, k)
            out += _dict_to_html_r(v, margin+'    ')
        elif isinstance(v, list):
            for v2 in v:
                out += '{}{}:\n'.format(margin, k)
                out += _dict_to_html_r(v2, margin+'    ')
        else:
            out += '{}{}: {}\n'.format(margin, k, v)
    return out


def dict_to_html(data: dict) -> str:
    """
    Formats dict to simple pre-formatted html (<pre> tag).
    :param data: dict
    :return: str (html)
    """
    return '<pre>' + _dict_to_html_r(data) + '</pre>'
