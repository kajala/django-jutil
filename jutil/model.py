from datetime import timedelta, datetime
from django.db.models.fields import Field
from django.utils.encoding import force_str
from time import sleep
from typing import Type, List, Tuple, Any, Optional, Sequence
from django.db.models import Model
from django.utils.timezone import now
from jutil.format import choices_label


def get_object_or_none(cls: Any, **kwargs) -> Any:
    """
    Returns model instance or None if not found.
    :param cls: Class or queryset
    :param kwargs: Filters for get() call
    :return: Object or None
    """
    try:
        qs = cls._default_manager.all() if hasattr(cls, "_default_manager") else cls  # pylint: disable=protected-access
        return qs.get(**kwargs)
    except Exception:
        return None


def wait_object_or_none(cls: Any, timeout: float = 5.0, sleep_interval: float = 1.0, **kwargs) -> Any:
    """
    Returns model instance or None if not found after specified timeout.
    Waits timeout before returning if no object available.
    Waiting is done by sleeping specified intervals.
    :param cls: Class or queryset
    :param timeout: Timeout in seconds
    :param sleep_interval: Sleep interval in seconds
    :param kwargs: Filters for get() call
    :return: Object or None
    """
    t0: Optional[datetime] = None
    t1: Optional[datetime] = None
    qs0 = cls._default_manager if hasattr(cls, "_default_manager") else cls  # pylint: disable=protected-access
    while t0 is None or t0 < t1:  # type: ignore
        obj = qs0.all().filter(**kwargs).first()
        if obj is not None:
            return obj
        t0 = now()
        if t1 is None:
            t1 = t0 + timedelta(seconds=timeout)
        sleep(sleep_interval)
    return qs0.all().filter(**kwargs).first()


def get_model_field_or_none(instance, field_name: str) -> Optional[Field]:
    """
    Returns model field.
    :param instance: Model instance
    :param field_name: Model attribute name
    :return: Optional[Field]
    """
    for f in instance._meta.fields:
        if f.attname == field_name:
            return f
    return None


def get_model_field(instance, field_name: str) -> Field:
    """
    Returns model field.
    :param instance: Model instance
    :param field_name: Model attribute name
    :return: Field
    """
    f = get_model_field_or_none(instance, field_name)
    if f is None:
        raise Exception(f"Field {field_name} not found from {instance}")
    return f


def get_model_field_label(instance, field_name: str) -> str:
    """
    Returns model field label.
    Resolves also function / property short_description meta fields.
    :param instance: Model instance
    :param field_name: Model attribute name
    :return: label str
    """
    for f in instance._meta.fields:
        if f.name == field_name or f.attname == field_name:
            return f.verbose_name
    try:
        return getattr(getattr(getattr(instance.__class__, field_name), "fget"), "short_description")
    except AttributeError:
        pass
    try:
        return getattr(getattr(instance.__class__, field_name), "short_description")
    except AttributeError:
        pass
    return field_name


def get_model_field_label_and_value(instance, field_name: str) -> Tuple[str, str]:
    """
    Returns model field label and value as str.
    :param instance: Model instance
    :param field_name: Model attribute name
    :return: (label, value) tuple
    """
    label = get_model_field_label(instance, field_name)
    value = str(getattr(instance, field_name)) if hasattr(instance, field_name) else None
    for f in instance._meta.fields:
        if f.attname == field_name or f.name == field_name:
            if hasattr(f, "choices") and f.choices:
                value = choices_label(f.choices, value)
            break
    if value is None:
        value = ""
    val = force_str(value)
    return label, val


def is_model_field_changed(instance, field_name: str) -> bool:
    """
    Compares model instance field value to value stored in DB.
    If object has not been stored in DB (yet) field is considered unchanged.
    :param instance: Model instance
    :param field_name: Model attribute name
    :return: True if field value has been changed compared to value stored in DB.
    """
    assert hasattr(instance, field_name)
    if not hasattr(instance, "pk") or instance.pk is None:
        return False
    qs = instance.__class__.objects.all()
    params = {"pk": instance.pk, field_name: getattr(instance, field_name)}
    return not qs.filter(**params).exists()


def get_model_keys(instance, cls: Optional[Type[Model]] = None, exclude_fields: Sequence[str] = ("id",), base_class_suffix: str = "_ptr") -> List[str]:
    if cls is None:
        cls = instance.__class__
    return [f.name for f in cls._meta.fields if f.name not in exclude_fields and not f.name.endswith(base_class_suffix)]


def clone_model(
    instance, cls: Optional[Type[Model]] = None, commit: bool = True, exclude_fields: Sequence[str] = ("id",), base_class_suffix: str = "_ptr", **kw
):
    """
    Assigns model fields to new object. Ignores exclude_fields list and
    attributes ending with pointer suffix (default '_ptr')
    :param instance: Instance to copy
    :param cls: Class (opt)
    :param commit: Save or not
    :param exclude_fields: List of fields to exclude
    :param base_class_suffix: End of name for base class pointers, e.g. model Car(Vehicle) has implicit vehicle_ptr
    :return: New instance
    """
    if cls is None:
        cls = instance.__class__
    keys = get_model_keys(instance, cls=cls, exclude_fields=exclude_fields, base_class_suffix=base_class_suffix)
    new_instance = cls()
    for k in keys:
        setattr(new_instance, k, getattr(instance, k))
    for k, v in kw.items():
        setattr(new_instance, k, v)
    if commit:
        new_instance.save()
    return new_instance
