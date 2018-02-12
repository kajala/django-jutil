import json
import logging
from ipware.ip import get_real_ip
from rest_framework.request import Request


logger = logging.getLogger(__name__)


def log_event(name: str, request: Request=None, data=None, ip=None):
    """
    Logs consistent event for easy parsing/analysis.
    :param name: Name of the event. Will be logged as EVENT_XXX with XXX in capitals.
    :param request: Django REST framework Request (optional)
    :param data: Even data (optional)
    :param ip: Even IP (optional)
    """
    log_data = {}
    if not ip and request:
        ip = get_real_ip(request)
    if ip:
        log_data['ip'] = ip
    if data:
        log_data['data'] = data

    msg = 'EVENT_{}: {}'.format(name.upper(), json.dumps(log_data))
    logger.info(msg)
