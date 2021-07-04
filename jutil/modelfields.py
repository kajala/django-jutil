from typing import Any
from django.db import models
from django.utils.html import strip_tags


class SafeCharField(models.CharField):
    """
    CharField which strips HTML tags from form data on save.
    """

    _pyi_private_set_type: str  # for mypy_django_plugin
    _pyi_private_get_type: str  # for mypy_django_plugin
    _pyi_lookup_exact_type: Any  # for mypy_django_plugin

    def save_form_data(self, instance, data):
        setattr(instance, self.name, strip_tags(str(data)) if data else data)


class SafeTextField(models.TextField):
    """
    TextField which strips HTML tags from form data on save.
    """

    _pyi_private_set_type: str  # for mypy_django_plugin
    _pyi_private_get_type: str  # for mypy_django_plugin
    _pyi_lookup_exact_type: Any  # for mypy_django_plugin

    def save_form_data(self, instance, data):
        setattr(instance, self.name, strip_tags(str(data)) if data else data)
