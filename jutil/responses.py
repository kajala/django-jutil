import mimetypes
import os
from typing import Any, List
from django.http import HttpResponse, FileResponse, Http404
from django.utils.translation import gettext as _
from jutil.format import format_xml_file, format_xml_bytes, format_csv


class FileSystemFileResponse(FileResponse):
    """
    File system download HTTP response.
    :param full_path: Full path to file
    :param filename: Filename (optional) passed to client. Defaults to basename of the full path.
    """

    def __init__(self, full_path: str, filename: str = "", **kw):
        if not os.path.isfile(full_path):
            raise Http404(_("File {} not found").format(full_path))
        if not filename:
            filename = os.path.basename(full_path)
        content_type = mimetypes.guess_type(filename)[0]
        super().__init__(open(full_path, "rb"), **kw)
        if content_type:
            self["Content-Type"] = content_type
        self["Content-Length"] = os.path.getsize(full_path)
        self["Content-Disposition"] = "attachment; filename={}".format(filename)


class CsvResponse(HttpResponse):
    """
    CSV download HTTP response.
    """

    def __init__(self, rows: List[List[Any]], filename: str, dialect="excel", **kw):
        """
        Returns CSV response.
        :param rows: List of column lists
        :param filename: Download response file name
        :param dialect: See csv.writer dialect
        :param kw: Parameters to be passed to HttpResponse __init__
        """
        buf = format_csv(rows, dialect=dialect).encode("utf-8")
        super().__init__(content=buf, content_type="text/csv", **kw)
        self["Content-Disposition"] = 'attachment;filename="{}"'.format(filename)


class FormattedXmlFileResponse(HttpResponse):
    def __init__(self, filename: str):
        content = format_xml_file(filename)
        super().__init__(content)
        self["Content-Type"] = "application/xml"
        self["Content-Length"] = len(content)
        self["Content-Disposition"] = "attachment; filename={}".format(os.path.basename(filename))


class XmlResponse(HttpResponse):
    def __init__(self, content: bytes, filename: str):
        super().__init__(content)
        self["Content-Type"] = "application/xml"
        self["Content-Length"] = len(content)
        self["Content-Disposition"] = "attachment; filename={}".format(os.path.basename(filename))


class FormattedXmlResponse(XmlResponse):
    def __init__(self, content: bytes, filename: str, encoding: str = "UTF-8", exceptions: bool = True):
        super().__init__(format_xml_bytes(content, encoding=encoding, exceptions=exceptions), filename)
