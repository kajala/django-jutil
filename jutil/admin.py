import mimetypes
import os
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.models import User
from django.http import HttpRequest, Http404, FileResponse
from django.utils.timezone import now
from jutil.format import format_timedelta
from jutil.model import get_model_field_label_and_value
from django.utils.translation import ugettext_lazy as _
from jutil.responses import FileSystemFileResponse


def admin_log(instances, msg: str, who: User=None, **kw):
    """
    Logs an entry to admin logs of model(s).
    :param instances: Model instance or list of instances
    :param msg: Message to log
    :param who: Who did the change
    :param kw: Optional key-value attributes to append to message
    :return: None
    """

    from django.contrib.admin.models import LogEntry, CHANGE
    from django.contrib.admin.options import get_content_type_for_model
    from django.utils.encoding import force_text

    # use system user if 'who' is missing
    if not who:
        username = settings.DJANGO_SYSTEM_USER if hasattr(settings, 'DJANGO_SYSTEM_USER') else 'system'
        who, created = User.objects.get_or_create(username=username)

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


class ModelAdminBase(admin.ModelAdmin):
    """
    ModelAdmin with save-on-top default enabled and customized (length-limited) history view.
    """
    save_on_top = True
    max_history_length = 1000

    def kw_changelist_view(self, request: HttpRequest, extra_context=None, **kw):
        """
        Changelist view which allow key-value arguments.
        :param request: HttpRequest
        :param extra_context: Extra context dict
        :param kw: Key-value dict
        :return: See changelist_view()
        """
        return self.changelist_view(request, extra_context)

    def history_view(self, request, object_id, extra_context=None):
        from django.template.response import TemplateResponse
        from django.contrib.admin.options import get_content_type_for_model
        from django.contrib.admin.utils import unquote
        from django.core.exceptions import PermissionDenied
        from django.utils.text import capfirst
        from django.utils.encoding import force_text
        from django.utils.translation import ugettext as _

        "The 'history' admin view for this model."
        from django.contrib.admin.models import LogEntry
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


class AdminLogEntryMixin(object):
    """
    Mixin for logging Django admin changes of models.
    Call fields_changed() on change events.
    """

    def fields_changed(self, field_names: list, who: User, **kw):
        from django.utils.translation import ugettext as _

        fv_str = ''
        for k in field_names:
            label, value = get_model_field_label_and_value(self, k)
            fv_str += '{}={}'.format(label, value) if not fv_str else ', {}={}'.format(label, value)

        msg = "{class_name} id={id}: {fv_str}".format(class_name=self._meta.verbose_name.title(), id=self.id, fv_str=fv_str)
        admin_log([who, self], msg, who, **kw)


class AdminFileDownloadMixin(object):
    """
    Model Admin mixin for downloading uploaded files. Checks object permission before allowing download.
    """
    upload_to = 'uploads'
    file_field = 'file'

    def get_object_by_filename(self, request, filename):
        """
        Returns owner object by filename (to be downloaded).
        This can be used to implement custom permission checks.
        :param request: HttpRequest
        :param filename: File name of the downloaded object.
        :return: owner object
        """
        kw = dict()
        kw[self.file_field] = filename
        obj = self.get_queryset(request).filter(**kw).first()
        if not obj:
            raise Http404(_('File {} not found').format(filename))
        return self.get_object(request, obj.id)  # for permission check

    def file_download_view(self, request, filename, form_url='', extra_context=None):
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
            url(r'^.+(' + self.upload_to + '/.+)/$', self.file_download_view, name='%s_%s_file_download' % info),
        ]
