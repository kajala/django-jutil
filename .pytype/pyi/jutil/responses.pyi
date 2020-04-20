# (generated with --quick)

import io
from typing import Any, List, Type

FileResponse: Any
Http404: Any
HttpResponse: Any
StringIO: Type[io.StringIO]
_: Any
csv: module
mimetypes: module
os: module

class CsvResponse(Any):
    __doc__: str
    def __init__(self, rows: List[list], filename: str, dialect = ..., **kw) -> None: ...

class FileSystemFileResponse(Any):
    __doc__: str
    def __init__(self, full_path: str, filename: str = ..., **kw) -> None: ...

class FormattedXmlFileResponse(Any):
    def __init__(self, filename: str) -> None: ...

class FormattedXmlResponse(XmlResponse):
    def __init__(self, content: bytes, filename: str, encoding: str = ..., exceptions: bool = ...) -> None: ...

class XmlResponse(Any):
    def __init__(self, content: bytes, filename: str) -> None: ...

def format_xml_bytes(content: bytes, encoding: str = ..., exceptions: bool = ...) -> bytes: ...
def format_xml_file(full_path: str, encoding: str = ..., exceptions: bool = ...) -> bytes: ...
