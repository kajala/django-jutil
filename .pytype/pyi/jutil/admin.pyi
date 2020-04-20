# (generated with --quick)

import collections
import jutil.responses
from typing import Any, List, Tuple, Type

CHANGE: Any
FileSystemFileResponse: Type[jutil.responses.FileSystemFileResponse]
Http404: Any
HttpRequest: Any
LogEntry: Any
OrderedDict: Type[collections.OrderedDict]
PermissionDenied: Any
Q: Any
TemplateResponse: Any
User: Any
_: Any
admin: module
capfirst: Any
force_text: Any
format_html: Any
get_content_type_for_model: Any
mark_safe: Any
os: module
reverse: Any
settings: Any
unquote: Any
url: Any

class AdminFileDownloadMixin:
    __doc__: str
    file_field: str
    file_fields: List[nothing]
    single_file_field: str
    upload_to: str
    def file_download_view(self, request, filename, form_url = ..., extra_context = ...) -> jutil.responses.FileSystemFileResponse: ...
    def get_download_link(self, obj, file_field: str = ..., label: str = ...) -> str: ...
    def get_download_url(self, obj, file_field: str = ...) -> str: ...
    def get_download_urls(self) -> list: ...
    def get_file_fields(self) -> List[str]: ...
    def get_object_by_filename(self, request, filename) -> Any: ...

class AdminLogEntryMixin:
    __doc__: str
    def fields_changed(self, field_names: list, who, **kw) -> None: ...

class ModelAdminBase(Any):
    __doc__: str
    max_history_length: int
    save_on_top: bool
    def get_actions(self, request) -> collections.OrderedDict: ...
    def history_view(self, request, object_id, extra_context = ...) -> Any: ...
    def kw_changelist_view(self, request, extra_context = ..., **kwargs) -> Any: ...
    def sort_actions_by_description(self, actions: dict) -> collections.OrderedDict: ...

def admin_log(instances, msg: str, who = ..., **kw) -> None: ...
def admin_obj_link(obj, label: str = ..., route: str = ..., base_url: str = ...) -> str: ...
def admin_obj_url(obj, route: str = ..., base_url: str = ...) -> str: ...
def get_model_field_label_and_value(instance, field_name: str) -> Tuple[str, str]: ...
