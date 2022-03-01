from django.utils.formats import date_format


def formatted_date(description=None, ordering=None, fmt: str = "SHORT_DATE_FORMAT"):
    """
    Decorator for formatting date/datetime field in Django admin.
    :param description: Short description of the function (default is "short date").
    :param ordering: Admin order field (optional).
    :param fmt: Format to pass to date_format (default "SHORT_DATE_FORMAT")

    Usage example in Django Admin:

    @formatted_date(_("timestamp"), "timestamp")
    def timestamp_short(obj):
        return obj.timestamp
    """

    def wrap_func(func):
        def fmt_func(*args, **kwargs):
            val = func(*args, **kwargs)
            if not val:
                return ""
            return date_format(val, fmt)

        if description is not None:
            fmt_func.short_description = description
        if ordering is not None:
            fmt_func.admin_order_field = ordering
        return fmt_func

    return wrap_func
