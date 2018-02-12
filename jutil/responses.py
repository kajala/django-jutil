from io import BytesIO, StringIO
from django.http import HttpResponse


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

        super().__init__(content=f.getvalue().encode('utf-8'), content_type='text/csv', **kw)
        self['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)
