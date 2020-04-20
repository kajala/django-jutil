import json
import logging
from typing import Optional

from ipware.ip import get_real_ip  # pytype: disable=import-error
from rest_framework.request import Request


logger = logging.getLogger(__name__)


def log_event(name: str, request: Optional[Request] = None, data: Optional[dict] = None, ip: str = ''):
    """
    Logs consistent event for easy parsing/analysis.
    Format: EVENT_<UPPERCASE_NAME>: <JSON object>
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
    logger.info('EVENT_%s: %s', name.upper(), json.dumps(log_data))
