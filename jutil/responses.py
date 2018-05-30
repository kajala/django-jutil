import mimetypes
import os
from io import StringIO
from django.http import HttpResponse, FileResponse, Http404
from django.utils.translation import ugettext as _


class FileSystemFileResponse(FileResponse):
    """
    File system download HTTP response.
    :param full_path: Full path to file
    """
    def __init__(self, full_path: str, **kw):
        filename = os.path.basename(full_path)
        if not os.path.isfile(full_path):
            raise Http404(_("File {} not found").format(full_path))
        content_type = mimetypes.guess_type(filename)[0]
        super().__init__(open(full_path, 'rb'), **kw)
        self['Content-Type'] = content_type
        self['Content-Length'] = os.path.getsize(full_path)
        self['Content-Disposition'] = "attachment; filename={}".format(filename)


class CsvFileResponse(HttpResponse):
    """
    CSV file download HTTP response.
    """
    def __init__(self, rows: list, filename: str, dialect='excel', **kw):
        """
        Returns CSV response.
        :param rows: List of column lists
        :param filename: Download response file name
        :param dialect: csv.writer dialect
        :param kw: Parameters to be passed to HttpResponse __init__
        """
        import csv

        f = StringIO()
        writer = csv.writer(f, dialect=dialect)
        for row in rows:
            writer.writerow(row)

        buf = f.getvalue().encode('utf-8')
        super().__init__(content=buf, content_type='text/csv', **kw)
        self['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)
