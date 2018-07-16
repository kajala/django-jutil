import json
from datetime import datetime, timedelta
from os.path import join
from pprint import pprint
import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.timezone import now
from jutil.command import get_date_range_by_name
from jutil.request import get_ip_info
from jutil.urls import url_equals, url_mod, url_host
from jutil.xml import xml_to_dict, dict_to_element
from rest_framework.test import APIClient
from jutil.dates import add_month, per_delta, per_month, this_week, next_month, next_week, this_month, last_month, \
    last_year, last_week, yesterday
from jutil.format import format_full_name, format_xml
from jutil.parse import parse_datetime
from jutil.validators import fi_payment_reference_number, se_ssn_validator, se_ssn_filter, fi_iban_validator, \
    se_iban_validator, iban_filter_readable, email_filter,iban_validator, iban_bank_info, fi_company_reg_id_validator


class Tests(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_payment_reference(self):
        self.assertEqual(fi_payment_reference_number('100'), '1009')

    def test_format(self):
        samples = [
            ('Short', 'Full Name', 'Short Full Name'),
            ('Short Middle Name Is Quite Long', 'Full Name', 'Short Full Name'),
            ('Short-Middle Name Is Quite Long', 'Full Name', 'Short Full Name'),
            ('Olga Demi', 'Serpuhovitinova-Miettinen', 'Olga Serpuhovitinova'),
            ('Olga-Anne Demi', 'Serpuhovitinovatsko', 'Olga S'),
        ]
        for v in samples:
            limited = format_full_name(v[0], v[1], 20)
            # print('{} {} -> {} (was: {})'.format(v[0], v[1], v[2], limited))
            self.assertEqual(v[2], limited)

    def test_add_month(self):
        t = parse_datetime('2016-06-12T01:00:00')
        self.assertEqual(t.isoformat(), '2016-06-12T01:00:00+00:00')
        t2 = add_month(t)
        self.assertEqual(t2.isoformat(), '2016-07-12T01:00:00+00:00')
        t3 = add_month(t, 7)
        self.assertEqual(t3.isoformat(), '2017-01-12T01:00:00+00:00')
        t4 = add_month(t, -1)
        self.assertEqual(t4.isoformat(), '2016-05-12T01:00:00+00:00')

    def test_se_ssn(self):
        se_ssn_validator('811228-9874')
        se_ssn_validator('670919-9530')
        with self.assertRaises(ValidationError):
            se_ssn_validator('811228-9873')

    def test_iban(self):
        iban_validator('FI2112345600000785')
        iban_validator('SE4550000000058398257466')
        fi_iban_validator('FI2112345600000785')
        se_iban_validator('SE4550000000058398257466')
        with self.assertRaises(ValidationError):
            fi_iban_validator('FI2112345600000784')
        with self.assertRaises(ValidationError):
            se_iban_validator('SE4550000000058398257465')
        iban = 'FI8847304720017517'
        self.assertEqual(iban_filter_readable(iban), 'FI88 4730 4720 0175 17')

    def test_urls(self):
        url = 'http://yle.fi/uutiset/3-8045550?a=123&b=456'
        self.assertEqual(url_host(url), 'yle.fi')
        self.assertTrue(url_equals('http://yle.fi/uutiset/3-8045550?a=123&b=456', 'http://yle.fi/uutiset/3-8045550?b=456&a=123'))
        self.assertTrue(url_equals(url_mod('http://yle.fi/uutiset/3-8045550?a=123&b=456', {'b': '123', 'a': '456'}), 'http://yle.fi/uutiset/3-8045550?b=123&a=456'))

    def test_email_filter(self):
        emails = [
            (' Asdsa@a-a.com ', 'asdsa@a-a.com'),
            ('1asdsa@a-a2.com', '1asdsa@a-a2.com'),
        ]
        for i, o in emails:
            # print('email_filter({}) -> {}'.format(i, email_filter(i)))
            self.assertEqual(email_filter(i), o)

    def test_ip_info(self):
        ip, cc, host = get_ip_info('213.214.146.142')
        self.assertEqual(ip, '213.214.146.142')
        if cc:
            self.assertEqual(cc, 'FI')
        if host:
            self.assertEqual(host, '213214146142.edelkey.net')

    def test_parse_xml(self):
        # finvoice_201_example1.xml
        xml_bytes = open(join(settings.BASE_DIR, 'data/finvoice_201_example1.xml'), 'rb').read()
        data = xml_to_dict(xml_bytes, value_key='value', attribute_prefix='_')
        # pprint(data)
        self.assertEqual(data['_Version'], '2.01')
        self.assertEqual(data['InvoiceRow'][0]['ArticleIdentifier'], '12345')
        self.assertEqual(data['InvoiceRow'][0]['DeliveredQuantity']['value'], '2')
        self.assertEqual(data['InvoiceRow'][0]['DeliveredQuantity']['_QuantityUnitCode'], 'kpl')
        self.assertEqual(data['InvoiceRow'][1]['ArticleIdentifier'], '123456')

        # parse_xml1.xml
        xml_str = open(join(settings.BASE_DIR, 'data/parse_xml1.xml'), 'rt').read()
        data = xml_to_dict(xml_str)
        # pprint(data)
        ref_data = {'@version': '1.2',
                    'A': [{'@class': 'x', 'B': {'@': 'hello', '@class': 'x2'}},
                          {'@class': 'y', 'B': {'@': 'world', '@class': 'y2'}}],
                    'C': 'value node'}
        self.assertEqual(ref_data, data)

        # parse_xml1.xml / no attributes
        xml_str = open(join(settings.BASE_DIR, 'data/parse_xml1.xml'), 'rt').read()
        data = xml_to_dict(xml_str, parse_attributes=False)
        # pprint(data)
        ref_data = {'A': [{'B': 'hello'}, {'B': 'world'}], 'C': 'value node'}
        self.assertEqual(ref_data, data)

        # parse_xml2.xml / no attributes
        xml_str = open(join(settings.BASE_DIR, 'data/parse_xml2.xml'), 'rt').read()
        data = xml_to_dict(xml_str, ['VastausLoki', 'LuottoTietoMerkinnat'], parse_attributes=False)
        # pprint(data)
        ref_data = {'VastausLoki': {'KysyttyHenkiloTunnus': '020685-1234',
                    'PaluuKoodi': 'Palveluvastaus onnistui',
                    'SyyKoodi': '1'}}
        self.assertEqual(ref_data, data)

    def test_dict_to_xml(self):
        from xml.etree.ElementTree import Element
        from xml.etree import ElementTree as ET

        data = {
            'Doc': {
                '@version': '1.2',
                'A': [{'@class': 'x', 'B': {'@': 'hello', '@class': 'x2'}},
                      {'@class': 'y', 'B': {'@': 'world', '@class': 'y2'}}],
                'C': 'value node',
             }
        }
        el = dict_to_element(data)
        assert isinstance(el, Element)
        xml_str = ET.tostring(el, encoding='utf8', method='xml').decode()
        # print(xml_str)  # <Doc version="1.2"><C>value node</C><A class="x"><B class="x2">hello</B></A><A class="y"><B class="y2">world</B></A></Doc>
        data2 = xml_to_dict(xml_str, document_tag=True)
        # print(data)
        # print(data2)
        self.assertEqual(data2, data)

    def test_per_delta(self):
        begin = datetime(2017, 9, 17, 11, 42)
        end = begin + timedelta(days=4)
        ref = [(datetime(2017, 9, 17, 11, 42), datetime(2017, 9, 18, 11, 42)),
               (datetime(2017, 9, 18, 11, 42), datetime(2017, 9, 19, 11, 42)),
               (datetime(2017, 9, 19, 11, 42), datetime(2017, 9, 20, 11, 42)),
               (datetime(2017, 9, 20, 11, 42), datetime(2017, 9, 21, 11, 42))]
        res = per_delta(begin, end, timedelta(days=1))
        self.assertEqual(list(res), ref)

    def test_per_month(self):
        begin = datetime(2017, 9, 1, 0, 0)
        res = list(per_month(begin, begin+timedelta(days=32)))
        ref = [(datetime(2017, 9, 1, 0, 0), datetime(2017, 10, 1, 0, 0)),
               (datetime(2017, 10, 1, 0, 0), datetime(2017, 11, 1, 0, 0))]
        self.assertEqual(list(res), ref)

    def test_dates(self):
        t = datetime(2018, 1, 30)
        b, e = this_week(t)
        self.assertEqual(b, pytz.utc.localize(datetime(2018, 1, 29)))
        self.assertEqual(e, pytz.utc.localize(datetime(2018, 2, 5)))
        b, e = this_month(t)
        self.assertEqual(b, pytz.utc.localize(datetime(2018, 1, 1)))
        self.assertEqual(e, pytz.utc.localize(datetime(2018, 2, 1)))
        b, e = next_week(t)
        self.assertEqual(b, pytz.utc.localize(datetime(2018, 2, 5)))
        self.assertEqual(e, pytz.utc.localize(datetime(2018, 2, 12)))

    def test_named_date_ranges(self):
        t = datetime(2018, 5, 31)
        t_tz = pytz.utc.localize(t)
        named_ranges = [
            ('last_month', last_month(t)),
            ('last_year', last_year(t)),
            ('this_month', this_month(t)),
            ('last_week', last_week(t)),
            ('yesterday', yesterday(t)),
            ('today', yesterday(t + timedelta(hours=24))),
        ]
        day_ranges = [7, 15, 30, 60, 90]
        for days in day_ranges:
            named_ranges.append(('plus_minus_{}d'.format(days), (t_tz - timedelta(days=days), t_tz + timedelta(days=days))))
            named_ranges.append(('prev_{}d'.format(days), (t_tz - timedelta(days=days), t_tz)))
            named_ranges.append(('next_{}d'.format(days), (t_tz, t_tz + timedelta(days=days))))
        for name, res in named_ranges:
            # print('testing', name)
            self.assertEqual(get_date_range_by_name(name, t), res)

    def test_bank_info(self):
        ac = 'FI8847304720017517'
        inf = iban_bank_info(ac)
        self.assertEqual(inf[0], 'POPFFI22')
        self.assertEqual(inf[1], 'POP-Pankki')

        ac = ''
        inf = iban_bank_info(ac)
        self.assertEqual(inf[0], None)
        self.assertEqual(inf[1], None)

    def test_reg_id_fi(self):
        valids = [
            'FI01098230',
            'FI-01098230',
            '0109823-0',
            '2084069-9',
        ]
        invalids = [
            '2084069-1',
        ]
        for valid in valids:
            # print('test_reg_id_fi:', valid, 'should be valid...', end=' ')
            fi_company_reg_id_validator(valid)
            # print('ok')
        for invalid in invalids:
            try:
                # print('test_reg_id_fi:', invalid, 'should be invalid', end=' ')
                fi_company_reg_id_validator(invalid)
                self.assertTrue(False)
            except ValidationError:
                # print('ok')
                pass
