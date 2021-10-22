import csv
import html
import json
import logging
import os
import re
import tempfile
from collections import OrderedDict
from datetime import timedelta
from decimal import Decimal
import subprocess
from io import StringIO
from typing import List, Any, Optional, Union, Dict, Sequence, Tuple, TypeVar
from django.conf import settings
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.utils.functional import lazy
import xml.dom.minidom  # type: ignore
from django.utils.safestring import mark_safe
from django.utils.text import capfirst

logger = logging.getLogger(__name__)

S = TypeVar("S")


def format_full_name(first_name: str, last_name: str, max_length: int = 20) -> str:
    """
    Limits name length to specified length. Tries to keep name as human-readable an natural as possible.
    :param first_name: First name
    :param last_name: Last name
    :param max_length: Maximum length
    :return: Full name of shortened version depending on length
    """
    # dont allow commas in limited names
    first_name = first_name.replace(",", " ")
    last_name = last_name.replace(",", " ")

    # accept short full names as is
    original_full_name = first_name + " " + last_name
    if len(original_full_name) <= max_length:
        return original_full_name

    # drop middle names
    first_name = first_name.split(" ")[0]
    full_name = first_name + " " + last_name
    if len(full_name) <= max_length:
        return full_name

    # drop latter parts of combined first names
    first_name = re.split(r"[\s\-]", first_name)[0]
    full_name = first_name + " " + last_name
    if len(full_name) <= max_length:
        return full_name

    # drop latter parts of multi part last names
    last_name = re.split(r"[\s\-]", last_name)[0]
    full_name = first_name + " " + last_name
    if len(full_name) <= max_length:
        return full_name

    # shorten last name to one letter
    last_name = last_name[:1]

    full_name = first_name + " " + last_name
    if len(full_name) > max_length:
        raise Exception("Failed to shorten name {}".format(original_full_name))
    return full_name


def format_timedelta(dt: timedelta, days_label: str = "d", hours_label: str = "h", minutes_label: str = "min", seconds_label: str = "s") -> str:
    """
    Formats timedelta to readable format, e.g. 1h30min15s.
    :param dt: timedelta
    :param days_label: Label for days. Leave empty '' if value should be skipped / ignored.
    :param hours_label: Label for hours. Leave empty '' if value should be skipped / ignored.
    :param minutes_label: Label for minutes. Leave empty '' if value should be skipped / ignored.
    :param seconds_label: Label for seconds. Leave empty '' if value should be skipped / ignored.
    :return: str
    """
    parts = (
        (86400, days_label),
        (3600, hours_label),
        (60, minutes_label),
        (1, seconds_label),
    )
    out = ""
    seconds_f = dt.total_seconds()
    seconds = int(seconds_f)
    for n_secs, label in parts:
        n, remainder = divmod(seconds, n_secs)
        if n > 0 and label:
            out += str(n) + label
            seconds = remainder
    out_str = out.strip()
    if not out_str:
        if seconds_f >= 0.001:
            out_str = "{:0.3f}".format(int(seconds_f * 1000.0) * 0.001) + seconds_label
        else:
            out_str = "0" + seconds_label
    return out_str.strip()


def format_xml(content: str, encoding: str = "UTF-8", exceptions: bool = False) -> str:
    """
    Formats XML document as human-readable plain text.
    If settings.XMLLINT_PATH is defined xmllint is used for formatting (higher quality). Otherwise minidom toprettyxml is used.
    :param content: XML data as str
    :param encoding: XML file encoding
    :param exceptions: Raise exceptions on error
    :return: str (Formatted XML str)
    """
    assert isinstance(content, str)
    try:
        if hasattr(settings, "XMLLINT_PATH") and settings.XMLLINT_PATH:
            with tempfile.NamedTemporaryFile() as fp:
                fp.write(content.encode(encoding=encoding))
                fp.flush()
                out = subprocess.check_output([settings.XMLLINT_PATH, "--format", fp.name])
                return out.decode(encoding=encoding)
        return xml.dom.minidom.parseString(content).toprettyxml()
    except Exception as e:
        logger.error("format_xml failed: %s", e)
        if exceptions:
            raise
        return content


def format_xml_bytes(content: bytes, encoding: str = "UTF-8", exceptions: bool = False) -> bytes:
    """
    Formats XML document as human-readable plain text and returns result in bytes.
    If settings.XMLLINT_PATH is defined xmllint is used for formatting (higher quality). Otherwise minidom toprettyxml is used.
    :param content: XML data as bytes
    :param encoding: XML file encoding
    :param exceptions: Raise exceptions on error
    :return: bytes (Formatted XML as bytes)
    """
    assert isinstance(content, bytes)
    try:
        if hasattr(settings, "XMLLINT_PATH") and settings.XMLLINT_PATH:
            with tempfile.NamedTemporaryFile() as fp:
                fp.write(content)
                fp.flush()
                out = subprocess.check_output([settings.XMLLINT_PATH, "--format", fp.name])
                return out
        return xml.dom.minidom.parseString(content.decode(encoding=encoding)).toprettyxml(encoding=encoding)
    except Exception as e:
        logger.error("format_xml_bytes failed: %s", e)
        if exceptions:
            raise
        return content


def format_xml_file(full_path: str, encoding: str = "UTF-8", exceptions: bool = False) -> bytes:
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
        if hasattr(settings, "XMLLINT_PATH") and settings.XMLLINT_PATH:
            return subprocess.check_output([settings.XMLLINT_PATH, "--format", full_path])
        with open(full_path, "rb") as fp:
            return xml.dom.minidom.parse(fp).toprettyxml(encoding=encoding)  # type: ignore
    except Exception as e:
        logger.error("format_xml_file failed (1): %s", e)
        if exceptions:
            raise
    try:
        with open(full_path, "rb") as fp:
            return fp.read()
    except Exception as e:
        logger.error("format_xml_file failed (2): %s", e)
    return b""


def format_as_html_json(value: Any) -> str:
    """
    Returns value as JSON-formatted value in HTML.
    :param value: Any value which can be converted to JSON by json.dumps
    :return: str
    """
    return mark_safe(html.escape(json.dumps(value, indent=4)).replace("\n", "<br/>").replace(" ", "&nbsp;"))


def _format_dict_as_html_key(k: str) -> str:
    if k.startswith("@"):
        k = k[1:]
    k = k.replace("_", " ")
    k = re.sub(r"((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))", r" \1", k)
    parts = k.split(" ")
    out: List[str] = [str(capfirst(parts[0].strip()))]
    for p in parts[1:]:
        p2 = p.strip().lower()
        if p2:
            out.append(p2)
    return " ".join(out)


def _format_dict_as_html_r(data: Dict[str, Any], margin: str = "", format_keys: bool = True) -> str:
    if not isinstance(data, dict):
        return "{}{}\n".format(margin, data)
    out = ""
    for k, v in OrderedDict(sorted(data.items())).items():
        if isinstance(v, dict):
            out += "{}{}:\n".format(margin, _format_dict_as_html_key(k) if format_keys else k)
            out += _format_dict_as_html_r(v, margin + "    ", format_keys=format_keys)
            out += "\n"
        elif isinstance(v, list):
            for v2 in v:
                out += "{}{}:\n".format(margin, _format_dict_as_html_key(k) if format_keys else k)
                out += _format_dict_as_html_r(v2, margin + "    ", format_keys=format_keys)
            out += "\n"
        else:
            out += "{}{}: {}\n".format(margin, _format_dict_as_html_key(k) if format_keys else k, v)
    return out


def format_dict_as_html(data: Dict[str, Any], format_keys: bool = True) -> str:
    """
    Formats dict to simple human readable pre-formatted html (<pre> tag).
    :param data: dict
    :param format_keys: Re-format 'additionalInfo' and 'additional_info' type of keys as 'Additional info'
    :return: str (html)
    """
    return "<pre>" + _format_dict_as_html_r(data, format_keys=format_keys) + "</pre>"


def format_csv(rows: List[List[Any]], dialect: str = "excel") -> str:
    """
    Formats rows to CSV string content.
    :param rows: List[List[Any]]
    :param dialect: See csv.writer dialect
    :return: str
    """
    f = StringIO()
    writer = csv.writer(f, dialect=dialect)
    for row in rows:
        writer.writerow(row)
    return f.getvalue()


def format_table(  # noqa
    rows: List[List[Any]],
    max_col: Optional[int] = None,
    max_line: Optional[int] = 200,
    col_sep: str = "|",
    row_sep: str = "-",
    row_begin: str = "|",
    row_end: str = "|",
    has_label_row: bool = False,
    left_align: Optional[List[int]] = None,
    center_align: Optional[List[int]] = None,
) -> str:
    """
    Formats "ASCII-table" rows by padding column widths to longest column value, optionally limiting column widths.
    Optionally separates colums with ' | ' character and header row with '-' characters.
    Supports left, right and center alignment. Useful for console apps / debugging.

    :param rows: List[List[Any]]
    :param max_col: Max column value width. Pass None for unlimited length.
    :param max_line: Maximum single line length. Exceeding columns truncated. Pass None for unlimited length.
    :param col_sep: Column separator string.
    :param row_sep: Row separator character used before first row, end, after first row (if has_label_row).
    :param row_begin: Row begin string, inserted before each row.
    :param row_end: Row end string, appended after each row.
    :param has_label_row: Set to True if table starts with column label row.
    :param left_align: Indexes of left-aligned columns. By default all are right aligned.
    :param center_align: Indexes of center-aligned columns. By default all are right aligned.
    :return: str
    """
    # validate parameters
    assert max_col is None or max_col > 2
    if left_align is None:
        left_align = []
    if center_align is None:
        center_align = []
    if left_align:
        if set(left_align) & set(center_align):
            raise ValidationError("Left align columns {} overlap with center align {}".format(left_align, center_align))

    # find out number of columns
    ncols = 0
    for row in rows:
        ncols = max(ncols, len(row))

    # find out full-width column lengths
    col_lens0: List[int] = [0] * ncols
    for row in rows:
        for ix, v in enumerate(row):
            v = str(v)
            col_lens0[ix] = max(col_lens0[ix], len(v))

    # adjust max_col if needed
    if max_line and (not max_col or sum(col_lens0) > max_line):
        max_col = max_line // ncols

    # length limited lines and final column lengths
    col_lens = [0] * ncols
    lines: List[List[str]] = []
    for row in rows:
        line = []
        for ix, v in enumerate(row):
            v = str(v)
            if max_col and len(v) > max_col:
                v = v[: max_col - 2] + ".."
            line.append(v)
            col_lens[ix] = max(col_lens[ix], len(v))
        while len(line) < ncols:
            line.append("")
        lines.append(line)

    # padded lines
    lines2: List[List[str]] = []
    for line in lines:
        line2 = []
        for ix, v in enumerate(line):
            col_len = col_lens[ix]
            if len(v) < col_len:
                if ix in left_align:
                    v = v + " " * (col_len - len(v))
                elif ix in center_align:
                    pad = col_len - len(v)
                    lpad = int(pad / 2)
                    rpad = pad - lpad
                    v = " " * lpad + v + " " * rpad
                else:
                    v = " " * (col_len - len(v)) + v
            line2.append(v)
        lines2.append(line2)

    # calculate max number of columns and max line length
    max_line_len = 0
    col_sep_len = len(col_sep)
    ncols0 = ncols
    for line in lines2:
        if max_line is not None:
            line_len = len(row_begin) + sum(len(v) + col_sep_len for v in line[:ncols]) - col_sep_len + len(row_end)
            while line_len > max_line:
                ncols -= 1
                line_len = len(row_begin) + sum(len(v) + col_sep_len for v in line[:ncols]) - col_sep_len + len(row_end)
            max_line_len = max(max_line_len, line_len)

    # find out how we should terminate lines/rows
    line_term = ""
    row_sep_term = ""
    if ncols0 > ncols:
        line_term = ".."
        row_sep_term = row_sep * int(2 / len(row_sep))

    # final output with row and column separators
    lines3 = []
    if row_sep:
        lines3.append(row_sep * max_line_len + row_sep_term)
    for line_ix, line in enumerate(lines2):
        while len(line) > ncols:
            line.pop()
        line_out = col_sep.join(line)
        lines3.append(row_begin + line_out + row_end + line_term)
        if line_ix == 0 and row_sep and has_label_row:
            lines3.append(row_sep * max_line_len + row_sep_term)
    if row_sep:
        lines3.append(row_sep * max_line_len + row_sep_term)
    return "\n".join(lines3)


def _capfirst_lazy(x):
    """
    capfirst() keeping lazy strings lazy.
    """
    return x[0:1].upper() + x[1:] if x else ""


capfirst_lazy = lazy(_capfirst_lazy, str)


def dec0(a: Union[float, int, Decimal, str]) -> Decimal:
    """
    Converts number to Decimal with 0 decimal digits.
    :param a: Number
    :return: Decimal with 0 decimal digits
    """
    return Decimal(a).quantize(Decimal("1"))


def dec1(a: Union[float, int, Decimal, str]) -> Decimal:
    """
    Converts number to Decimal with 1 decimal digits.
    :param a: Number
    :return: Decimal with 1 decimal digits
    """
    return Decimal(a).quantize(Decimal("1.0"))


def dec2(a: Union[float, int, Decimal, str]) -> Decimal:
    """
    Converts number to Decimal with 2 decimal digits.
    :param a: Number
    :return: Decimal with 2 decimal digits
    """
    return Decimal(a).quantize(Decimal("1.00"))


def dec3(a: Union[float, int, Decimal, str]) -> Decimal:
    """
    Converts number to Decimal with 3 decimal digits.
    :param a: Number
    :return: Decimal with 3 decimal digits
    """
    return Decimal(a).quantize(Decimal("1.000"))


def dec4(a: Union[float, int, Decimal, str]) -> Decimal:
    """
    Converts number to Decimal with 4 decimal digits.
    :param a: Number
    :return: Decimal with 4 decimal digits
    """
    return Decimal(a).quantize(Decimal("1.0000"))


def dec5(a: Union[float, int, Decimal, str]) -> Decimal:
    """
    Converts number to Decimal with 5 decimal digits.
    :param a: Number
    :return: Decimal with 4 decimal digits
    """
    return Decimal(a).quantize(Decimal("1.00000"))


def dec6(a: Union[float, int, Decimal, str]) -> Decimal:
    """
    Converts number to Decimal with 6 decimal digits.
    :param a: Number
    :return: Decimal with 4 decimal digits
    """
    return Decimal(a).quantize(Decimal("1.000000"))


def is_media_full_path(file_path: str) -> bool:
    """
    Checks if file path is under (settings) MEDIA_ROOT.
    """
    if not hasattr(settings, "MEDIA_ROOT") or not settings.MEDIA_ROOT:
        raise ImproperlyConfigured("MEDIA_ROOT not defined")
    full_path = os.path.abspath(file_path)
    return full_path.startswith(str(settings.MEDIA_ROOT))


def strip_media_root(file_path: str) -> str:
    """
    If file path starts with (settings) MEDIA_ROOT,
    the MEDIA_ROOT part gets stripped and only relative path is returned.
    Otherwise file path is returned as is. This enabled stored file names in more
    portable format for different environment / storage.
    If MEDIA_ROOT is missing or empty, the filename is returned as is.
    Reverse operation of this is get_media_full_path().
    :param file_path: str
    :return: str
    """
    if not hasattr(settings, "MEDIA_ROOT") or not settings.MEDIA_ROOT:
        raise ImproperlyConfigured("MEDIA_ROOT not defined")
    full_path = os.path.abspath(file_path)
    if not full_path.startswith(str(settings.MEDIA_ROOT)):
        raise ValueError("Path {} not under MEDIA_ROOT".format(file_path))
    file_path = full_path[len(str(settings.MEDIA_ROOT)) :]
    if file_path.startswith("/"):
        return file_path[1:]
    return file_path


def get_media_full_path(file_path: str) -> str:
    """
    Returns the absolute path from a (relative) path to (settings) MEDIA_ROOT.
    This enabled stored file names in more portable format for different environment / storage.
    If MEDIA_ROOT is missing or non-media path is passed to function, exception is raised.
    Reverse operation of this is strip_media_root().
    :param file_path: str
    :return: str
    """
    if not hasattr(settings, "MEDIA_ROOT") or not settings.MEDIA_ROOT:
        raise ImproperlyConfigured("MEDIA_ROOT not defined")
    full_path = os.path.abspath(file_path) if os.path.isabs(file_path) else os.path.join(settings.MEDIA_ROOT, file_path)
    if not full_path.startswith(str(settings.MEDIA_ROOT)):
        raise ValueError("Path {} not under MEDIA_ROOT".format(file_path))
    return full_path


def camel_case_to_underscore(s: str) -> str:
    """
    Converts camelCaseWord to camel_case_word.
    :param s: str
    :return: str
    """
    if s:
        s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
        s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
        s = s.replace("-", "_")
    return s.lower()


def underscore_to_camel_case(s: str) -> str:
    """
    Converts under_score_word to underScoreWord.
    :param s: str
    :return: str
    """
    if s:
        p = s.split("_")
        s = p[0] + "".join([capfirst(w) or "" for w in p[1:]])
    return s


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
    return ""
