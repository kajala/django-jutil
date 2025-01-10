import json
import logging
from collections import OrderedDict
from decimal import Decimal
from typing import Optional, Sequence, List, Dict, Any, Union
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User, AnonymousUser
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import QuerySet
from django.http import HttpRequest
from django.urls import reverse, resolve
from django.utils import translation
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.models import CHANGE, ADDITION
from django.template.response import TemplateResponse
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.utils.text import capfirst
from django.utils.encoding import force_str
from django.contrib.admin.models import LogEntry
from jutil.model import get_model_field_label

logger = logging.getLogger(__name__)


def get_admin_log(instance: object) -> QuerySet:
    """Returns admin log (LogEntry QuerySet) of the object."""
    return LogEntry.objects.filter(
        content_type_id=get_content_type_for_model(instance).pk,  # type: ignore
        object_id=instance.pk,  # type: ignore  # pytype: disable=attribute-error
    )


def admin_log_system_user():
    """Returns admin log system user (username either settings.DJANGO_SYSTEM_USER, default value "system")"""
    username = settings.DJANGO_SYSTEM_USER if hasattr(settings, "DJANGO_SYSTEM_USER") else "system"  # type: ignore
    return get_user_model().objects.get_or_create(username=username)[0]


def admin_log(instances: Sequence[object], msg: str, who: Optional[Union[User, AnonymousUser]] = None, action_flag: int = CHANGE, **kwargs):
    """Logs an entry to admin logs of model(s).

    Args:
        instances: Model instance or list of instances (None values are ignored)
        msg: Message to log
        who: Who did the change. If who is None then User with username of settings.DJANGO_SYSTEM_USER (default: 'system') will be used
        action_flag: ADDITION / CHANGE / DELETION action flag. Default CHANGED.
        **kwargs: Optional key-value attributes to append to message

    Returns:
        None
    """
    # use system user if 'who' is missing
    if who is None:
        who = admin_log_system_user()

    # allow passing individual instance
    if not isinstance(instances, list) and not isinstance(instances, tuple):
        instances = [instances]  # type: ignore

    # append extra context if any
    extra_context: List[str] = []
    for k, v in kwargs.items():
        extra_context.append(str(k) + "=" + str(v))
    if extra_context:
        msg += " | " + ", ".join(extra_context)

    for instance in instances:
        if instance:
            LogEntry.objects.log_action(  # type: ignore
                user_id=who.pk if who is not None else None,  # type: ignore
                content_type_id=get_content_type_for_model(instance).pk,  # type: ignore
                object_id=instance.pk,  # type: ignore  # pytype: disable=attribute-error
                object_repr=force_str(instance),
                action_flag=action_flag,
                change_message=msg,
            )


def admin_obj_is_related_manager(val: object) -> bool:
    """
    Checks if django model instance field value is RelatedManager type (e.g. ManyToMany field).
    Note that we have to check this indirectly like this since RelatedManager class is created dynamically by create_forward_many_to_many_manager.

    Args:
        val: object

    Returns: True if object is Django model RelatedManger type
    """
    return hasattr(val, "__class__") and hasattr(val, "all") and callable(getattr(val, "all")) and val.__class__.__name__ == "ManyRelatedManager"  # type: ignore  # noqa


def admin_obj_serialize_fields(
    obj: object, field_names: Sequence[str], cls: Any = DjangoJSONEncoder, max_serialized_field_length: Optional[int] = None
) -> str:
    """JSON serializes (changed) fields of a model instance for logging purposes.
    Referenced objects with primary key (pk) attribute are formatted using only that field as value.

    Args:
        obj: Model instance
        field_names: List of field names to store
        cls: Serialization class. Default DjangoJSONEncoder.
        max_serialized_field_length: Optional maximum length for individual serialized str value. Longer fields are cut with terminating [...]

    Returns:
        str
    """
    out: Dict[str, Any] = {}
    for k in field_names:
        val = getattr(obj, k) if hasattr(obj, k) else None
        try:
            if val is not None:
                if admin_obj_is_related_manager(val):
                    val_list = []
                    for sub_val in val.all():
                        val_list.append({"pk": sub_val.pk, "str": str(sub_val)})
                    val = val_list
                elif hasattr(val, "pk"):
                    val = {"pk": val.pk, "str": str(val)}
                elif not isinstance(val, (Decimal, float, int, bool)):
                    val = str(val)
                elif max_serialized_field_length is not None and isinstance(val, str) and len(val) > max_serialized_field_length:
                    val = val[:max_serialized_field_length] + " [...]"
        except Exception as exc:
            logger.warning("Failed to serialize object %s field %s value %s: %s", obj, k, val, exc)
            val = str(val)[:max_serialized_field_length]
        out[k] = val
    return json.dumps(out, cls=cls)


def admin_log_has_field_values(instance) -> bool:  # pylint: disable=too-many-nested-blocks
    """Returns True if the instance has any field values stored as JSON in the admin log.
    See: admin_construct_change_message_ex, admin_log_field_values
    """
    content_type_id = get_content_type_for_model(instance).pk
    qs = LogEntry.objects.filter(content_type_id=content_type_id, object_id=instance.pk)
    for e in qs.order_by("id").distinct():  # pylint: disable=too-many-nested-blocks
        assert isinstance(e, LogEntry)
        try:
            change_message = json.loads(e.change_message)  # type: ignore  # noqa
        except json.JSONDecodeError:
            continue
        if isinstance(change_message, list):
            for msg in change_message:
                if isinstance(msg, dict):
                    added_or_changed = msg.get("added") or msg.get("changed") or {}
                    if added_or_changed:
                        values = added_or_changed.get("values") or {}
                        if values and isinstance(values, dict):
                            return True
    return False


def admin_log_field_values(
    instance, changed_data: Optional[List[str]] = None, who: Optional[User] = None, cls=DjangoJSONEncoder, max_serialized_field_length: int = 1000
) -> LogEntry:  # noqa
    """Logs instance field values as JSON in the admin log.

    Args:
        instance: Model instance
        changed_data: List of changed field names. If None then ADDITION is assumed as action.
        who: User who did the change. Default is system user.
        cls: JSON encoder. Default: Django implementation
        max_serialized_field_length: Max length for long text fields.

    Returns:
        LogEntry
    """
    from jutil.model import get_model_field_names  # type: ignore  # noqa

    if changed_data:
        action_flag = CHANGE
        field_names = changed_data
    else:
        action_flag = ADDITION
        field_names = get_model_field_names(instance)

    values_str = admin_obj_serialize_fields(instance, field_names, cls, max_serialized_field_length)
    values = json.loads(values_str) if values_str else {}
    with translation.override(None):
        if changed_data:
            changed_field_labels = [str(get_model_field_label(instance, k)) for k in changed_data]
            change_message = [
                {"changed": {"name": str(instance._meta.verbose_name), "object": str(instance), "fields": changed_field_labels, "values": values}}
            ]
        else:
            change_message = [
                {
                    "added": {
                        "name": str(instance._meta.verbose_name),
                        "object": str(instance),
                        "values": values,
                    }
                }
            ]
    # use system user if 'who' is missing
    if who is None:
        who = admin_log_system_user()
    content_type_id = get_content_type_for_model(instance).pk
    return LogEntry.objects.log_action(  # type: ignore
        user_id=who.pk,
        content_type_id=content_type_id,
        object_id=instance.pk,
        object_repr=str(instance),
        action_flag=action_flag,
        change_message=change_message,
    )


def admin_construct_change_message_ex(request, form, formsets, add, cls=DjangoJSONEncoder, max_serialized_field_length: int = 1000) -> List[Any]:  # noqa
    from ipware import get_client_ip  # type: ignore  # noqa
    from django.contrib.admin.utils import _get_changed_field_labels_from_form  # type: ignore  # noqa
    from jutil.model import get_model_field_names  # noqa

    changed_data = form.changed_data
    with translation.override(None):
        changed_field_labels = _get_changed_field_labels_from_form(form, changed_data)

    ip = get_client_ip(request)[0]
    instance = form.instance if hasattr(form, "instance") and form.instance is not None else None
    values_str = admin_obj_serialize_fields(form.instance, changed_data, cls, max_serialized_field_length) if instance is not None else ""
    values = json.loads(values_str) if values_str else {}
    change_message = []
    if add:
        change_message.append({"added": {"values": values, "ip": ip}})
    elif form.changed_data:
        change_message.append({"changed": {"fields": changed_field_labels, "values": values, "ip": ip}})
    if formsets:
        with translation.override(None):
            for formset in formsets:
                for added_object in formset.new_objects:
                    values = json.loads(admin_obj_serialize_fields(added_object, get_model_field_names(added_object), cls, max_serialized_field_length))
                    change_message.append(
                        {
                            "added": {
                                "name": str(added_object._meta.verbose_name),
                                "object": str(added_object),
                                "values": values,
                                "ip": ip,
                            }
                        }
                    )
                for changed_object, changed_fields in formset.changed_objects:
                    values = json.loads(admin_obj_serialize_fields(changed_object, changed_fields, cls, max_serialized_field_length))
                    change_message.append(
                        {
                            "changed": {
                                "name": str(changed_object._meta.verbose_name),
                                "object": str(changed_object),
                                "fields": _get_changed_field_labels_from_form(formset.forms[0], changed_fields),
                                "values": values,
                                "ip": ip,
                            }
                        }
                    )
                for deleted_object in formset.deleted_objects:
                    change_message.append(
                        {
                            "deleted": {
                                "name": str(deleted_object._meta.verbose_name),
                                "object": str(deleted_object),
                                "ip": ip,
                            }
                        }
                    )
    return change_message


def admin_obj_url(obj: Optional[object], route: str = "", base_url: str = "") -> str:
    """Returns admin URL to object. If object is standard model with default route name, the function
    can deduct the route name as in "admin:<app>_<class-lowercase>_change".

    Args:
        obj: Object
        route: Empty for default route
        base_url: Base URL if you want absolute URLs, e.g. https://example.com

    Returns:
        URL to admin object change view
    """
    if obj is None:
        return ""
    if not route:
        route = "admin:{}_{}_change".format(obj._meta.app_label, obj._meta.model_name)  # type: ignore
    path = reverse(route, args=[obj.id])  # type: ignore
    return base_url + path


def admin_obj_link(obj: Optional[object], label: str = "", route: str = "", base_url: str = "") -> str:
    """Returns safe-marked admin link to object. If object is standard model with default route name, the function
    can deduct the route name as in "admin:<app>_<class-lowercase>_change".

    Args:
        obj: Object
        label: Optional label. If empty uses str(obj)
        route: Empty for default route
        base_url: Base URL if you want absolute URLs, e.g. https://example.com

    Returns:
        HTML link marked safe
    """
    if obj is None:
        return ""
    url = mark_safe(admin_obj_url(obj, route, base_url))  # nosec
    return format_html("<a href='{}'>{}</a>", url, str(obj) if not label else label)


def admin_update_model_instance(  # pylint: disable=too-many-locals,too-many-arguments,too-many-positional-arguments
    instance: object,
    changes: Dict[str, Any],
    note: str = "",
    who: Optional[Union[User, AnonymousUser]] = None,
    cls: Any = DjangoJSONEncoder,
    commit: bool = True,
) -> LogEntry:
    """
    Changes object field values and writes a structured message about the change with optional free-form text about the change to object's admin history log.

    Args:
        instance: Model instance
        changes: Key-value pairs of fields to change.
        note: Free text note what the change is about (optional)
        who: Who made the change (optional)
        cls: Serialization class. Default DjangoJSONEncoder.
        commit: Save instance to database at the end of change

    Returns:
        LogEntry
    """
    from jutil.model import get_model_field_names  # type: ignore  # noqa

    action_flag = CHANGE
    field_names: List[str] = []
    for k, v in changes.items():
        if not hasattr(instance, k):
            raise ValueError(f"{instance}: Model has no field name {k}")
        if v != getattr(instance, k):
            field_names.append(k)
    change_message: List[Union[dict, str]] = []
    if field_names:
        old_values_str = admin_obj_serialize_fields(instance, field_names, cls=cls)
        old_values = json.loads(old_values_str) if old_values_str else {}
        for k in field_names:
            setattr(instance, k, changes[k])  # type: ignore
        instance.save(update_fields=field_names)  # type: ignore
        values_str = admin_obj_serialize_fields(instance, field_names, cls=cls)
        values = json.loads(values_str) if values_str else {}
        with translation.override(None):
            changed_field_labels = [str(get_model_field_label(instance, k)) for k in field_names]
            change_message.append(
                {
                    "changed": {
                        "name": str(instance._meta.verbose_name),  # type: ignore
                        "object": str(instance),
                        "fields": changed_field_labels,
                        "values": values,
                        "old_values": old_values,
                    }
                }
            )
    if note:
        change_message.append(note)
    if not change_message:
        change_message.append(str(_("No fields changed.")))
    if who is None:
        who = admin_log_system_user()
    content_type_id = get_content_type_for_model(instance).pk  # type: ignore
    for k, v in changes.items():
        setattr(instance, k, v)
    if commit:
        instance.save()  # type: ignore
    return LogEntry.objects.log_action(  # type: ignore
        user_id=who.pk,  # type: ignore
        content_type_id=content_type_id,
        object_id=instance.pk,  # type: ignore
        object_repr=str(instance),
        action_flag=action_flag,
        change_message=change_message,
    )


class ModelAdminBase(admin.ModelAdmin):
    """ModelAdmin with some customizations:
    * Customized change message which logs changed values and user IP as well (can be disabled by extended_log=False)
    * Length-limited latest-first history view (customizable by max_history_length)
    * Actions sorted alphabetically by localized description
    * Additional fill_extra_context() method which can be used to share common extra context for add_view(), change_view() and changelist_view()
    * Save-on-top enabled by default (save_on_top=True)
    """

    save_on_top = True
    extended_log = True
    max_history_length = 1000
    history_ordering = ["-action_time", "-id"]
    serialization_cls = DjangoJSONEncoder
    max_serialized_field_length = 1000

    def construct_change_message(self, request, form, formsets, add=False):
        if self.extended_log:
            return admin_construct_change_message_ex(request, form, formsets, add, self.serialization_cls, self.max_serialized_field_length)
        return super().construct_change_message(request, form, formsets, add)

    def sort_actions_by_description(self, actions: dict) -> OrderedDict:
        """
        Args:
            actions: dict of str: (callable, name, description)

        Returns:
            OrderedDict
        """
        sorted_descriptions = sorted([(k, data[2]) for k, data in actions.items()], key=lambda x: x[1])
        sorted_actions = OrderedDict()
        for k, description in sorted_descriptions:  # pylint: disable=unused-variable
            sorted_actions[k] = actions[k]
        return sorted_actions

    def get_actions(self, request):
        return self.sort_actions_by_description(super().get_actions(request))

    def fill_extra_context(self, request: HttpRequest, extra_context: Optional[Dict[str, Any]]):  # pylint: disable=unused-argument
        """Function called by customized add_view(), change_view() and kw_changelist_view()
        to supplement extra_context dictionary by custom variables.
        """
        return extra_context

    def add_view(self, request: HttpRequest, form_url="", extra_context=None):
        """Custom add_view() which calls fill_extra_context()."""
        return super().add_view(request, form_url, self.fill_extra_context(request, extra_context))

    def change_view(self, request: HttpRequest, object_id, form_url="", extra_context=None):
        """Custom change_view() which calls fill_extra_context()."""
        return super().change_view(request, object_id, form_url, self.fill_extra_context(request, extra_context))

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, self.fill_extra_context(request, extra_context))

    def kw_changelist_view(self, request: HttpRequest, extra_context=None, **kwargs):  # pylint: disable=unused-argument
        """Changelist view which allow key-value arguments and calls fill_extra_context().

        Args:
            request: HttpRequest
            extra_context: Extra context dict
            **kwargs: Key-value dict

        Returns:
            See changelist_view()
        """
        extra_context = extra_context or {}
        extra_context.update(kwargs)
        return self.changelist_view(request, self.fill_extra_context(request, extra_context))

    def history_view(self, request, object_id, extra_context=None):  # pylint: disable=too-many-locals
        from django.contrib.admin.models import LogEntry  # noqa
        from django.contrib.admin.views.main import PAGE_VAR  # noqa

        # First check if the user can see this history.
        model = self.model
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, model._meta, object_id)  # noqa

        if not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied

        # Then get the history for this object.
        opts = model._meta  # noqa
        app_label = opts.app_label
        action_list = (
            LogEntry.objects.filter(
                object_id=unquote(object_id),
                content_type=get_content_type_for_model(model),
            )
            .select_related()
            .order_by(*self.history_ordering)
        )

        max_per_page = self.max_history_length
        paginator = self.get_paginator(request, action_list, max_per_page)
        page_number = request.GET.get(PAGE_VAR, 1)  # type: ignore
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(page_obj.number)

        context = {
            **self.admin_site.each_context(request),
            "title": _("Change history: %s") % obj,
            "subtitle": None,
            "action_list": page_obj,
            "page_range": page_range,
            "page_var": PAGE_VAR,
            "pagination_required": paginator.count > max_per_page,
            "module_name": str(capfirst(opts.verbose_name_plural)),
            "object": obj,
            "opts": opts,
            "preserved_filters": self.get_preserved_filters(request),
            **(extra_context or {}),
        }

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            self.object_history_template
            or [
                "admin/%s/%s/object_history.html" % (app_label, opts.model_name),
                "admin/%s/object_history.html" % app_label,
                "jutil/admin/object_history.html",
            ],
            context,
        )


class InlineModelAdminParentAccessMixin:
    """Admin mixin for accessing parent objects to be used in InlineModelAdmin derived classes."""

    OBJECT_PK_KWARGS = ["object_id", "pk", "id"]

    def get_parent_object(self, request) -> Optional[object]:
        """
        Returns the inline admin object's parent object or None if not found.
        """
        mgr = self.parent_model.objects  # type: ignore
        resolved = resolve(request.path_info)
        if resolved.kwargs:
            for k in self.OBJECT_PK_KWARGS:
                if k in resolved.kwargs:
                    return mgr.filter(pk=resolved.kwargs[k]).first()
        if resolved.args:
            return mgr.filter(pk=resolved.args[0]).first()
        return None
