from typing import (
    Any,
    TypeVar,
    Union,
)
from django.db.models import CharField, TextField, Field
from django.db.models.expressions import Combinable

_T = TypeVar("_T", bound=Field)
_ST = TypeVar("_ST", contravariant=True)
_GT = TypeVar("_GT", covariant=True)


class SafeCharField(CharField[_ST, _GT]):
    _pyi_private_set_type: Union[str, int, Combinable]
    _pyi_private_get_type: str
    _pyi_lookup_exact_type: Any


class SafeTextField(TextField[_ST, _GT]):
    _pyi_private_set_type: Union[str, Combinable]
    _pyi_private_get_type: str
    _pyi_lookup_exact_type: Any
