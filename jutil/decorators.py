from django.utils.formats import date_format


def date_format_short_date(short_description=None, admin_order_field=None):
    """
    Formats date/datetime as SHORT_DATE_FORMAT.
    :param short_description: Short description of the function (optional, default is "short date").
    :param short_description: Admin order field (optional).

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
            return date_format(val, "SHORT_DATE_FORMAT")

        if short_description is not None:
            short_date.short_description = short_description
        if admin_order_field is not None:
            short_date.admin_order_field = admin_order_field
        return short_date

    return wrap_func
