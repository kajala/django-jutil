import re
import tempfile
from datetime import timedelta
from decimal import Decimal
import subprocess
from django.conf import settings
import xml.dom.minidom


def format_full_name(first_name: str, last_name: str, max_length: int = 20):
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


def format_timedelta(dt: timedelta, include_seconds: bool = True) -> str:
    """
    Formats timedelta to readable format, e.g. 1h30min15s.
    :param dt: timedelta
    :param include_seconds: If seconds should be included in formatted string. Default is True.
    :return: str
    """
    seconds = int(dt.total_seconds())
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    s = ""
    if days > 0:
        s += str(days) + "d"
    if hours > 0:
        s += str(hours) + "h"
    if minutes > 0:
        s += str(minutes) + "min"
    if seconds > 0 and include_seconds:
        s += str(seconds) + "s"
    if s == "":
        s = "0min"
    return s


def format_xml(content: str or bytes, encoding: str = 'UTF-8', exceptions: bool = False) -> str:
    """
    Formats XML document as human-readable plain text.
    If settings.XMLLINT_PATH is defined xmllint is used for formatting (higher quality). Otherwise minidom toprettyxml is used.
    :param content: XML data as str or bytes
    :param encoding: XML file encoding
    :param exceptions: Raise exceptions on error
    :return: str (Formatted XML str)
    """
    try:
        if hasattr(settings, 'XMLLINT_PATH') and settings.XMLLINT_PATH:
            if isinstance(content, str):
                content = content.encode(encoding=encoding)
            with tempfile.NamedTemporaryFile() as fp:
                fp.write(content)
                fp.flush()
                out = subprocess.check_output([settings.XMLLINT_PATH, '--format', fp.name])
                return out.decode()
        if isinstance(content, bytes):
            content = content.decode(encoding=encoding)
        return xml.dom.minidom.parseString(content).toprettyxml()
    except Exception:
        if exceptions:
            raise
        return content.decode() if isinstance(content, bytes) else content


def format_xml_bytes(content: str or bytes, encoding: str = 'UTF-8', exceptions: bool = False) -> bytes:
    """
    Formats XML document as human-readable plain text and returns result in bytes.
    If settings.XMLLINT_PATH is defined xmllint is used for formatting (higher quality). Otherwise minidom toprettyxml is used.
    :param content: XML data as str or bytes
    :param encoding: XML file encoding
    :param exceptions: Raise exceptions on error
    :return: bytes (Formatted XML as bytes)
    """
    try:
        if hasattr(settings, 'XMLLINT_PATH') and settings.XMLLINT_PATH:
            if isinstance(content, str):
                content = content.encode(encoding=encoding)
            with tempfile.NamedTemporaryFile() as fp:
                fp.write(content)
                fp.flush()
                out = subprocess.check_output([settings.XMLLINT_PATH, '--format', fp.name])
                return out
        if isinstance(content, bytes):
            content = content.decode(encoding=encoding)
        return xml.dom.minidom.parseString(content).toprettyxml(encoding=encoding)
    except Exception:
        if exceptions:
            raise
        return content.encode(encoding=encoding) if isinstance(content, str) else content


def format_xml_file(full_path: str, encoding: str = 'UTF-8', exceptions: bool = False) -> bytes:
    """
    Formats XML file as human-readable plain text and returns result in bytes.
    Tries to format XML file first, if formatting fails the file content is returned as is.
    If the file does not exist empty bytes is returned.
    If settings.XMLLINT_PATH is defined xmllint is used for formatting (higher quality). Otherwise minidom toprettyxml is used.
    :param full_path: Full path to XML file
    :param encoding: XML file encoding
    :param exceptions: Raise exceptions on error
    :return: bytes
    """
    try:
        if hasattr(settings, 'XMLLINT_PATH') and settings.XMLLINT_PATH:
            return subprocess.check_output([settings.XMLLINT_PATH, '--format', full_path])
        with open(full_path, 'rb') as fp:
            return xml.dom.minidom.parse(fp).toprettyxml(encoding=encoding)
    except Exception:
        if exceptions:
            raise
    try:
        with open(full_path, 'rb') as fp:
            return fp.read()
    except Exception:
        pass
    return b''


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
