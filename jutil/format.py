import re
from datetime import timedelta
from decimal import Decimal


def format_full_name(first_name: str, last_name: str, max_length: int=20):
    """
    Limits name length to specified length. Tries to keep name as human-readable an natural as possible.
    :param first_name: First name
    :param last_name: Last name
    :param max_length: Maximum length
    :return: Full name of shortened version depending on length
    """
    # dont allow commas in limited names
    first_name = first_name.replace(',', ' ')
    last_name = last_name.replace(',', ' ')
    # accept short full names as is
    original_full_name = first_name + ' ' + last_name
    if len(original_full_name) <= max_length:
        return original_full_name
    # drop middle names
    first_name = first_name.split(' ')[0]
    full_name = first_name + ' ' + last_name
    if len(full_name) <= max_length:
        return full_name
    # drop latter parts of combined first names
    first_name = re.split(r'[\s\-]', first_name)[0]
    full_name = first_name + ' ' + last_name
    if len(full_name) <= max_length:
        return full_name
    # drop latter parts of multi part last names
    last_name = re.split(r'[\s\-]', last_name)[0]
    full_name = first_name + ' ' + last_name
    if len(full_name) <= max_length:
        return full_name
    # shorten last name to one letter
    last_name = last_name[:1]

    full_name = first_name + ' ' + last_name
    if len(full_name) > max_length:
        raise Exception('Failed to shorten name {}'.format(original_full_name))
    return full_name


def format_timedelta(dt: timedelta) -> str:
    """
    Formats timedelta to readable format, e.g. 1h30min.
    :param dt: timedelta
    :return: str
    """
    seconds = int(dt.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    s = ""
    if hours > 0:
        s += str(hours) + "h"
    if minutes > 0:
        s += str(minutes) + "min"
    if s == "":
        s = "0min"
    return s


def format_xml(xml_str: str, exceptions: bool=False):
    """
    Formats XML document as human-readable plain text.
    :param xml_str: str (Input XML str)
    :param exceptions: Raise exceptions on error
    :return: str (Formatted XML str)
    """
    try:
        import xml.dom.minidom
        return xml.dom.minidom.parseString(xml_str).toprettyxml()
    except Exception:
        if exceptions:
            raise
        return xml_str


def dec1(a) -> Decimal:
    """
    Converts number to Decimal with 1 decimal digits.
    :param a: Number
    :return: Decimal with 1 decimal digits
    """
    return Decimal(a).quantize(Decimal('1.0'))


def dec2(a) -> Decimal:
    """
    Converts number to Decimal with 2 decimal digits.
    :param a: Number
    :return: Decimal with 2 decimal digits
    """
    return Decimal(a).quantize(Decimal('1.00'))


def dec3(a) -> Decimal:
    """
    Converts number to Decimal with 3 decimal digits.
    :param a: Number
    :return: Decimal with 3 decimal digits
    """
    return Decimal(a).quantize(Decimal('1.000'))


def dec4(a) -> Decimal:
    """
    Converts number to Decimal with 4 decimal digits.
    :param a: Number
    :return: Decimal with 4 decimal digits
    """
    return Decimal(a).quantize(Decimal('1.0000'))


def dec5(a) -> Decimal:
    """
    Converts number to Decimal with 5 decimal digits.
    :param a: Number
    :return: Decimal with 4 decimal digits
    """
    return Decimal(a).quantize(Decimal('1.00000'))


def dec6(a) -> Decimal:
    """
    Converts number to Decimal with 6 decimal digits.
    :param a: Number
    :return: Decimal with 4 decimal digits
    """
    return Decimal(a).quantize(Decimal('1.000000'))
