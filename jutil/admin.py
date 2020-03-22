import os
from collections import OrderedDict
from typing import List
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpRequest, Http404
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from jutil.model import get_model_field_label_and_value
from django.utils.translation import gettext_lazy as _
from jutil.responses import FileSystemFileResponse
from django.contrib.admin.models import CHANGE
from django.template.response import TemplateResponse
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.utils.text import capfirst
from django.utils.encoding import force_text
from django.contrib.admin.models import LogEntry


def admin_log(instances, msg: str, who: User or None = None, **kw):
    """
    Logs an entry to admin logs of model(s).
    :param instances: Model instance or list of instances
    :param msg: Message to log
    :param who: Who did the change. If who is None then User with username of settings.DJANGO_SYSTEM_USER (default: 'system') will be used
    :param kw: Optional key-value attributes to append to message
    :return: None
    """
    # use system user if 'who' is missing
    if not who:
        username = settings.DJANGO_SYSTEM_USER if hasattr(settings, 'DJANGO_SYSTEM_USER') else 'system'
        who = User.objects.get_or_create(username=username)[0]

    # append extra keyword attributes if any
    att_str = ''
    for k, v in kw.items():
        if hasattr(v, 'pk'):  # log only primary key for model instances, not whole str representation
            v = v.pk
        att_str += '{}={}'.format(k, v) if not att_str else ', {}={}'.format(k, v)
    if att_str:
        att_str = ' [{}]'.format(att_str)
    msg = str(msg) + att_str

    if not isinstance(instances, list) and not isinstance(instances, tuple):
        instances = [instances]
    for instance in instances:
        if instance:
            LogEntry.objects.log_action(
                user_id=who.pk,
                content_type_id=get_content_type_for_model(instance).pk,
                object_id=instance.pk,
                object_repr=force_text(instance),
                action_flag=CHANGE,
                change_message=msg,
            )


def admin_obj_url(obj, route: str = '', base_url: str = '') -> str:
    """
    Returns admin URL to object. If object is standard model with default route name, the function
    can deduct the route name as in "admin:<app>_<class-lowercase>_change".
    :param obj: Object
    :param route: Empty for default route
    :param base_url: Base URL if you want absolute URLs, e.g. https://example.com
    :return: URL to admin object change view
    """
    if obj is None:
        return ''
    if not route:
        o = type(obj)
        model_path = o.__module__.split('.')
        route = 'admin:' + ".".join(['.'.join(model_path[:-1]), o.__name__]).lower().replace('.', '_') + '_change'
    return base_url + reverse(route, args=[obj.id])


def admin_obj_link(obj, label: str = '', route: str = '', base_url: str = '') -> str:
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
        return ''
    url = admin_obj_url(obj, route, base_url)
    return format_html("<a href='{}'>{}</a>", mark_safe(url), str(obj) if not label else label)


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
        # pylint:disable=unused-variable
        sorted_descriptions = sorted([(k, data[2]) for k, data in actions.items()], key=lambda x: x[1])
        sorted_actions = OrderedDict()
        for k, description in sorted_descriptions:
            sorted_actions[k] = actions[k]
        # pylint:enable=unused-variable
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
        # First check if the user can see this history.
        model = self.model
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, model._meta, object_id)

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        # Then get the history for this object.
        opts = model._meta
        app_label = opts.app_label
        action_list = LogEntry.objects.filter(
            object_id=unquote(object_id),
            content_type=get_content_type_for_model(model)
        ).select_related().order_by('-action_time')[:self.max_history_length]

        context = dict(
            self.admin_site.each_context(request),
            title=_('Change history: %s') % force_text(obj),
            action_list=action_list,
            module_name=capfirst(force_text(opts.verbose_name_plural)),
            object=obj,
            opts=opts,
            preserved_filters=self.get_preserved_filters(request),
        )
        context.update(extra_context or {})

        request.current_app = self.admin_site.name

        return TemplateResponse(request, self.object_history_template or [
            "admin/%s/%s/object_history.html" % (app_label, opts.model_name),
            "admin/%s/object_history.html" % app_label,
            "admin/object_history.html"
        ], context)
        # pylint:enable=too-many-arguments,too-many-locals


class AdminLogEntryMixin:
    """
    Mixin for logging Django admin changes of models.
    Call fields_changed() on change events.
    """

    def fields_changed(self, field_names: list, who: User, **kw):
        fv_str = ''
        for k in field_names:
            label, value = get_model_field_label_and_value(self, k)
            fv_str += '{}={}'.format(label, value) if not fv_str else ', {}={}'.format(label, value)

        msg = "{class_name} id={id}: {fv_str}".format(class_name=self._meta.verbose_name.title(), id=self.id, fv_str=fv_str)
        admin_log([who, self], msg, who, **kw)


class AdminFileDownloadMixin:
    """
    Model Admin mixin for downloading uploaded files. Checks object permission before allowing download.
    """
    upload_to = 'uploads'
    file_field = 'file'
    file_fields = []

    def get_file_fields(self) -> List[str]:
        if self.file_fields and self.file_field:
            raise AssertionError('AdminFileDownloadMixin cannot have both file_fields and '
                                 'file_field set ({})'.format(self.__class__))
        out = set()
        for f in self.file_fields or [self.file_field]:
            if f:
                out.add(f)
        if not out:
            raise AssertionError('AdminFileDownloadMixin must have either file_fields or '
                                 'file_field set ({})'.format(self.__class__))
        return list(out)

    @property
    def single_file_field(self) -> str:
        out = self.get_file_fields()
        if len(out) != 1:
            raise AssertionError('AdminFileDownloadMixin has multiple file fields, '
                                 'you need to specify field explicitly ({})'.format(self.__class__))
        return out[0]

    def get_object_by_filename(self, request, filename):
        """
        Returns owner object by filename (to be downloaded).
        This can be used to implement custom permission checks.
        :param request: HttpRequest
        :param filename: File name of the downloaded object.
        :return: owner object
        """
        query = None
        for k in self.get_file_fields():
            query_params = {k: filename}
            if query is None:
                query = Q(**query_params)
            else:
                query = query | Q(**query_params)
        objs = self.get_queryset(request).filter(query)
        for obj in objs:
            try:
                return self.get_object(request, obj.id)  # for permission check
            except Exception:
                pass
        raise Http404(_('File {} not found').format(filename))

    def get_download_url(self, obj, file_field: str = '') -> str:
        obj_id = obj.pk
        filename = getattr(obj, self.single_file_field if not file_field else file_field).name
        info = self.model._meta.app_label, self.model._meta.model_name
        return reverse('admin:{}_{}_change'.format(*info), args=(str(obj_id),)) + filename

    def get_download_link(self, obj, file_field: str = '', label: str = '') -> str:
        label = str(label or getattr(obj, self.single_file_field if not file_field else file_field))
        return mark_safe(format_html('<a href="{}">{}</a>', self.get_download_url(obj, file_field), label))

    def file_download_view(self, request, filename, form_url='', extra_context=None):  # pylint: disable=unused-argument
        full_path = os.path.join(settings.MEDIA_ROOT, filename)
        obj = self.get_object_by_filename(request, filename)
        if not obj:
            raise Http404(_('File {} not found').format(filename))
        return FileSystemFileResponse(full_path)

    def get_download_urls(self):
        """
        Use like this:
            def get_urls(self):
                return self.get_download_urls() + super().get_urls()

        Returns: File download URLs for this model.
        """
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            url(r'^\d+/change/(' + self.upload_to + '/.+)/$', self.file_download_view, name='%s_%s_file_download' % info),
            url(r'^(' + self.upload_to + '/.+)/$', self.file_download_view, name='%s_%s_file_download_changelist' % info),
        ]
