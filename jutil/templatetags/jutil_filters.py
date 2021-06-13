from django.template.defaultfilters import register


@register.filter
def ucfirst(v: str) -> str:
    """
    Converts first character of the string to uppercase.
    :param v: str
    :return: str
    """
    return v[0:1].upper() + v[1:]
