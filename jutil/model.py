from django.utils.encoding import force_text
from jutil.dict import choices_label


def get_object_or_none(cls, **kwargs):
    """
    Returns model instance or None if not found.
    :param cls: Class or queryset
    :param kwargs: Filters for get() call
    :return: Object or None
    """
    from django.shortcuts import _get_queryset
    qs = _get_queryset(cls)
    try:
        return qs.get(**kwargs)
    except qs.model.DoesNotExist:
        return None


def get_model_field_label_and_value(instance, field_name) -> (str, str):
    """
    Returns model field label and value.
    :param instance: Model instance
    :param field_name: Model attribute name
    :return: (label, value) tuple
    """
    label = field_name
    value = str(getattr(instance, field_name))
    for f in instance._meta.fields:
        if f.attname == field_name:
            label = f.verbose_name
            if hasattr(f, 'choices') and len(f.choices) > 0:
                value = choices_label(f.choices, value)
            break
    return label, force_text(value)


def clone_model(instance, cls, commit: bool=True, exclude_fields: tuple=('id',), base_class_suffix: str='_ptr', **kw):
    """
    Assigns model fields to new object. Ignores exclude_fields list and
    attributes ending with pointer suffix (default '_ptr')
    :param instance: Instance to copy
    :param cls: Class name
    :param commit: Save or not
    :param exclude_fields: List of fields to exclude
    :param base_class_suffix: End of name for base class pointers, e.g. model Car(Vehicle) has implicit vehicle_ptr
    :return: New instance
    """
    keys = [f.name for f in cls._meta.fields if f.name not in exclude_fields and not f.name.endswith(base_class_suffix)]
    new_instance = cls()
    for k in keys:
        v = getattr(instance, k)
        setattr(new_instance, k, v)
    for k, v in kw.items():
        setattr(new_instance, k, v)
    if commit:
        new_instance.save()
    return new_instance
