import requests
from django.conf import settings
from jutil.validators import phone_filter


def send_sms(phone: str, message: str, sender: str = "", channel: str = "", **kw):
    """Sends SMS via Kajala Group SMS API. Contact info@kajala.com for access.

    Args:
        phone: Phone number
        message: Message to be esnd
        sender: Sender (max 11 characters)
        channel: Set delivery channel explicitly
        **kw: Variable key-value pairs to be sent to SMS API

    Returns:
        Response from requests.post
    """
    if not hasattr(settings, "SMS_TOKEN"):
        raise Exception("Invalid configuration: settings.SMS_TOKEN missing")  # noqa
    if not sender and hasattr(settings, "SMS_SENDER_NAME"):
        sender = settings.SMS_SENDER_NAME  # type: ignore
    if not sender:
        raise Exception("Invalid configuration: settings.SMS_SENDER_NAME missing and sender not set explicitly either")  # noqa
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Token " + settings.SMS_TOKEN,  # type: ignore
    }
    data = {
        "dst": phone_filter(phone),
        "msg": message,
        "src": sender,
    }
    if channel:
        data["channel"] = channel
    for k, v in kw.items():
        data[k] = v
    return requests.post("https://sms.kajala.com/api/sms/", json=data, headers=headers, timeout=15)
