from django.utils.formats import date_format


def formatted_date(short_description=None, admin_order_field=None, fmt: str = "SHORT_DATE_FORMAT"):
    """
    Decorator for formatting date/datetime field in Django admin.
    :param short_description: Short description of the function (default is "short date").
    :param admin_order_field: Admin order field (optional).
    :param fmt: Format to pass to date_format (default "SHORT_DATE_FORMAT")

    Usage example in Django Admin:

    @date_format_short_date(_("timestamp"), "timestamp")
    def timestamp_short(obj):
        return obj.timestamp
    """

    def wrap_func(func):
        def short_date(*args, **kwargs):
            val = func(*args, **kwargs)
            if not val:
                return ""
            return date_format(val, fmt)

        if short_description is not None:
            short_date.short_description = short_description
        if admin_order_field is not None:
            short_date.admin_order_field = admin_order_field
        return short_date

    return wrap_func
