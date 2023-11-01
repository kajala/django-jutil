from typing import Any, Union
from django.db import models
from django.utils.html import strip_tags


class SafeCharField(models.CharField):
    """CharField which strips HTML tags from form data on save."""

    _pyi_private_set_type: Union[str, int, models.expressions.Combinable]
    _pyi_private_get_type: str
    _pyi_lookup_exact_type: Any

    def save_form_data(self, instance, data):
        setattr(instance, self.name, strip_tags(str(data)) if data else data)


class SafeTextField(models.TextField):
    """TextField which strips HTML tags from form data on save."""

    _pyi_private_set_type: Union[str, models.expressions.Combinable]
    _pyi_private_get_type: str
    _pyi_lookup_exact_type: Any

    def save_form_data(self, instance, data):
        setattr(instance, self.name, strip_tags(str(data)) if data else data)
