from django.db import models
from django.utils.html import strip_tags


class SafeCharField(models.CharField):
    """
    CharField which strips HTML tags from form data on save.
    """

    def save_form_data(self, instance, data):
        setattr(instance, self.name, strip_tags(str(data)) if data else data)


class SafeTextField(models.TextField):
    """
    TextField which strips HTML tags from form data on save.
    """

    def save_form_data(self, instance, data):
        setattr(instance, self.name, strip_tags(str(data)) if data else data)
