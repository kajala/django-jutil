import json
import logging
from typing import Optional, Dict, Any

from ipware import get_client_ip
from rest_framework.request import Request


logger = logging.getLogger(__name__)


def log_event(name: str, request: Optional[Request] = None, data: Optional[Dict[str, Any]] = None, ip: str = ''):
    """
    Logs consistent event for easy parsing/analysis.
    Format: EVENT_<UPPERCASE_NAME>: <JSON object>
    :param name: Name of the event. Will be logged as EVENT_XXX with XXX in capitals.
    :param request: Django REST framework Request (optional)
    :param data: Even data (optional)
    :param ip: Even IP (optional)
    """
    log_data: Dict[str, Any] = {}
    if not ip and request:
        ip = get_client_ip(request)[0]
    if ip:
        log_data['ip'] = ip
    if data:
        log_data['data'] = data
    logger.info('EVENT_%s: %s', name.upper(), json.dumps(log_data))
