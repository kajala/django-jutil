from collections import OrderedDict
from typing import Optional, Sequence, List
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.urls import reverse, resolve
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.models import CHANGE
from django.template.response import TemplateResponse
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.utils.text import capfirst
from django.utils.encoding import force_text
from django.contrib.admin.models import LogEntry


def admin_log(instances: Sequence[object], msg: str, who: Optional[User] = None, **kw):
    """
    Logs an entry to admin logs of model(s).
    :param instances: Model instance or list of instances (None values are ignored)
    :param msg: Message to log
    :param who: Who did the change. If who is None then User with username of settings.DJANGO_SYSTEM_USER (default: 'system') will be used
    :param kw: Optional key-value attributes to append to message
    :return: None
    """
    # use system user if 'who' is missing
    if who is None:
        username = settings.DJANGO_SYSTEM_USER if hasattr(settings, "DJANGO_SYSTEM_USER") else "system"
        who = User.objects.get_or_create(username=username)[0]

    # allow passing individual instance
    if not isinstance(instances, list) and not isinstance(instances, tuple):
        instances = [instances]  # type: ignore

    # append extra keyword attributes if any
    att_str = ""
    for k, v in kw.items():
        if hasattr(v, "pk"):  # log only primary key for model instances, not whole str representation
            v = v.pk
        att_str += "{}={}".format(k, v) if not att_str else ", {}={}".format(k, v)
    if att_str:
        att_str = " [{}]".format(att_str)
    msg = str(msg) + att_str

    for instance in instances:
        if instance:
            LogEntry.objects.log_action(
                user_id=who.pk if who is not None else None,
                content_type_id=get_content_type_for_model(instance).pk,  # type: ignore
                object_id=instance.pk,  # type: ignore  # pytype: disable=attribute-error
                object_repr=force_text(instance),
                action_flag=CHANGE,
                change_message=msg,
            )


def admin_log_changed_fields(obj: object, field_names: Sequence[str], who: Optional[User] = None, **kwargs):
    """
    Logs changed fields of a model instance to admin log.
    :param obj: Model instance
    :param field_names: Field names
    :param who: Who did the change. If who is None then User with username of settings.DJANGO_SYSTEM_USER (default: 'system') will be used
    :param kwargs: Optional key-value attributes to append to message
    :return:
    """
    from jutil.model import get_model_field_label_and_value  # noqa

    fv: List[str] = []
    for k in field_names:
        label, value = get_model_field_label_and_value(obj, k)
        fv.append('{}: "{}"'.format(label, value))
    msg = ", ".join(fv)
    if "ip" in kwargs:
        msg += " (IP {ip})".format(ip=kwargs.pop("ip"))
    admin_log([obj], msg, who, **kwargs)  # type: ignore


def admin_obj_url(obj: Optional[object], route: str = "", base_url: str = "") -> str:
    """
    Returns admin URL to object. If object is standard model with default route name, the function
    can deduct the route name as in "admin:<app>_<class-lowercase>_change".
    :param obj: Object
    :param route: Empty for default route
    :param base_url: Base URL if you want absolute URLs, e.g. https://example.com
    :return: URL to admin object change view
    """
    if obj is None:
        return ""
    if not route:
        route = "admin:{}_{}_change".format(obj._meta.app_label, obj._meta.model_name)  # type: ignore
    path = reverse(route, args=[obj.id])  # type: ignore
    return base_url + path


def admin_obj_link(obj: Optional[object], label: str = "", route: str = "", base_url: str = "") -> str:
    """
    Returns safe-marked admin link to object. If object is standard model with default route name, the function
    can deduct the route name as in "admin:<app>_<class-lowercase>_change".
    :param obj: Object
    :param label: Optional label. If empty uses str(obj)
    :param route: Empty for default route
    :param base_url: Base URL if you want absolute URLs, e.g. https://example.com
    :return: HTML link marked safe
    """
    if obj is None:
        return ""
    url = mark_safe(admin_obj_url(obj, route, base_url))  # nosec
    return format_html("<a href='{}'>{}</a>", url, str(obj) if not label else label)


class ModelAdminBase(admin.ModelAdmin):
    """
    ModelAdmin with save-on-top default enabled and customized (length-limited) history view.
    """

    save_on_top = True
    max_history_length = 1000

    def sort_actions_by_description(self, actions: dict) -> OrderedDict:
        """
        :param actions: dict of str: (callable, name, description)
        :return: OrderedDict
        """
        sorted_descriptions = sorted([(k, data[2]) for k, data in actions.items()], key=lambda x: x[1])
        sorted_actions = OrderedDict()
        for k, description in sorted_descriptions:  # pylint: disable=unused-variable
            sorted_actions[k] = actions[k]
        return sorted_actions

    def get_actions(self, request):
        return self.sort_actions_by_description(super().get_actions(request))

    def kw_changelist_view(self, request: HttpRequest, extra_context=None, **kwargs):  # pylint: disable=unused-argument
        """
        Changelist view which allow key-value arguments.
        :param request: HttpRequest
        :param extra_context: Extra context dict
        :param kwargs: Key-value dict
        :return: See changelist_view()
        """
        return self.changelist_view(request, extra_context)

    def history_view(self, request, object_id, extra_context=None):
        "The 'history' admin view for this model."
        from django.contrib.admin.models import LogEntry  # noqa

        # First check if the user can see this history.
        model = self.model
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, model._meta, object_id)

        if not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied

        # Then get the history for this object.
        opts = model._meta
        app_label = opts.app_label
        action_list = (
            LogEntry.objects.filter(object_id=unquote(object_id), content_type=get_content_type_for_model(model))
            .select_related()
            .order_by("-action_time")[: self.max_history_length]
        )

        context = {
            **self.admin_site.each_context(request),
            "title": _("Change history: %s") % obj,
            "action_list": action_list,
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
                "admin/object_history.html",
            ],
            context,
        )


class InlineModelAdminParentAccessMixin:
    """
    Admin mixin for accessing parent objects to be used in InlineModelAdmin derived classes.
    """

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


class AdminLogEntryMixin:
    """
    Model mixin for logging Django admin changes of Models.
    Call fields_changed() on change events.
    """

    def fields_changed(self, field_names: Sequence[str], who: Optional[User] = None, **kwargs):
        admin_log_changed_fields(self, field_names, who, **kwargs)
