from datetime import datetime, date
from decimal import Decimal
from django.http import HttpResponse
from django.utils.html import strip_tags
from typing import Any, List, Optional
import os

try:
    import openpyxl  # type: ignore

    if int(openpyxl.__version__.split(".", maxsplit=1)[0]) < 3:
        raise Exception("Invalid version")
except Exception as err:
    raise Exception("Using jutil.openpyxl_helpers requires openpyxl>3.0 installed") from err

from openpyxl import Workbook  # type: ignore
from openpyxl.styles import Alignment, NamedStyle  # type: ignore
from openpyxl.worksheet.worksheet import Worksheet  # type: ignore
from openpyxl.writer.excel import save_virtual_workbook  # type: ignore


class CellConfig:
    decimal_format: str = "0.00"
    int_format: str = "0"
    float_format: str = "0.0"
    number_alignment = Alignment(horizontal="right")
    date_style = NamedStyle(name="datetime", number_format="YYYY-MM-DD")


class ExcelResponse(HttpResponse):
    def __init__(self, book: Workbook, filename: str, disposition: str = "", content_type: str = ""):
        if not disposition:
            disposition = "filename=" + os.path.basename(filename)
        if not content_type:
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        super().__init__(
            content=save_virtual_workbook(book),
            content_type=content_type,
        )
        self["Content-Disposition"] = disposition


def set_cell_value(sheet: Worksheet, row_index: int, column_index: int, val: Any, config: Optional[CellConfig] = None):
    if config is None:
        config = CellConfig()
    c = sheet.cell(row_index + 1, column_index + 1)
    if isinstance(val, Decimal):
        c.number_format = config.decimal_format
        c.alignment = config.number_alignment
    elif isinstance(val, int):
        c.number_format = config.int_format
        c.alignment = config.number_alignment
    elif isinstance(val, float):
        c.number_format = config.float_format
        c.alignment = config.number_alignment
    elif isinstance(val, (datetime, date)):
        c.style = config.date_style
        if isinstance(val, datetime):
            val = val.replace(tzinfo=None)
    else:
        val = strip_tags(str(val if val else ""))
    c.value = val
    return c


def rows_to_sheet(sheet: Worksheet, rows: List[List[Any]], config: Optional[CellConfig]):
    if config is None:
        config = CellConfig()
    for row_ix, row in enumerate(list(rows)):
        for col_ix, val in enumerate(list(row)):
            set_cell_value(sheet, row_ix, col_ix, val, config)


def rows_to_workbook(rows: List[List[Any]], config: Optional[CellConfig] = None) -> Workbook:
    if config is None:
        config = CellConfig()
    book = Workbook()
    sheet = book.active
    assert isinstance(sheet, Worksheet)
    rows_to_sheet(sheet, rows, config)
    return book
