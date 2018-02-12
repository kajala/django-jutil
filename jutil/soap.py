import ssl
from pprint import pprint
from suds.client import Client
from suds.plugin import MessagePlugin
from xml.etree import ElementTree as ET


class SoapStore(MessagePlugin):
    """
    Stores SOAP request and responses as text.
    """
    def __init__(self):
        self.request = ''
        self.response = ''

    def sending(self, cx):
        self.request = str(cx.envelope.decode('utf-8'))

    def received(self, cx):
        self.response = str(cx.reply.decode('utf-8'))


class SoapContext(object):
    """
    SOAP context which support last request and response access.
    """
    def __init__(self, wsdl_url: str):
        self.wsdl_url = wsdl_url
        self.store = SoapStore()
        # ssl._create_default_https_context = ssl._create_unverified_context
        self.client = Client(url=self.wsdl_url, plugins=[self.store])

    @property
    def last_request(self):
        """
        :return: Last request as text
        """
        return self.store.request

    @property
    def last_response(self):
        """
        :return: Last response as text
        """
        return self.store.response

    def soap_call(self, func: str, args: dict):
        """
        Calls SOAP function with specified arguments.
        :param func: Function name
        :param args: Function args
        :return: Result object
        """
        return getattr(self.client.service, func)(**args)
