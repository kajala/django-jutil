import requests
from django.conf import settings
from jutil.validators import phone_filter


def send_sms(phone: str, message: str, sender: str = '', **kw):
    """
    Sends SMS via Kajala Group SMS API. Contact info@kajala.com for access.
    :param phone: Phone number
    :param message: Message to be esnd
    :param sender: Sender (max 11 characters)
    :param kw: Variable key-value pairs to be sent to SMS API
    :return: Response from requests.post
    """
    if not hasattr(settings, 'SMS_TOKEN'):
        raise Exception('Invalid configuration: settings.SMS_TOKEN missing')
    if not sender:
        sender = settings.SMS_SENDER_NAME
    if not sender:
        raise Exception('Invalid configuration: settings.SMS_SENDER_NAME missing')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token ' + settings.SMS_TOKEN,
    }
    data = {
        'dst': phone_filter(phone),
        'msg': message,
        'src': sender,
    }
    for k, v in kw.items():
        data[k] = v
    return requests.post("https://sms.kajala.com/api/sms/", json=data, headers=headers)
