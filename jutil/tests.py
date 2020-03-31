from datetime import datetime, timedelta, date
from decimal import Decimal
from os.path import join
import pytz
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import CommandParser
from django.test import TestCase
from django.utils import translation
from django.utils.translation import override, gettext as _, gettext_lazy
from jutil.admin import admin_log, admin_obj_url, admin_obj_link
from jutil.command import get_date_range_by_name, add_date_range_arguments, parse_date_range_arguments
from jutil.dict import dict_to_html
from jutil.model import is_model_field_changed, clone_model, get_model_field_label_and_value, get_object_or_none
from jutil.request import get_ip_info
from jutil.sftp import parse_sftp_connection
from jutil.testing import DefaultTestSetupMixin
from jutil.urls import url_equals, url_mod, url_host
from jutil.xml import xml_to_dict, dict_to_element
from rest_framework.test import APIClient
from jutil.dates import add_month, per_delta, per_month, this_week, next_month, next_week, this_month, last_month, \
    last_year, last_week, yesterday
from jutil.format import format_full_name, format_xml, format_xml_bytes, format_timedelta, dec1, dec2, dec3, dec4, dec5, \
    dec6, format_table, ucfirst_lazy
from jutil.parse import parse_datetime, parse_bool
from jutil.validators import fi_payment_reference_number, se_ssn_validator, se_ssn_filter, fi_iban_validator, \
    se_iban_validator, iban_filter_readable, email_filter, iban_validator, iban_bank_info, fi_company_org_id_validator, \
    email_validator, fi_payment_reference_validator, iso_payment_reference_validator, fi_ssn_age, \
    se_clearing_code_bank_info, ascii_filter, ee_iban_validator, be_iban_validator, dk_iban_validator, \
    dk_iban_bank_info, dk_clearing_code_bank_name, country_code_sanitizer, phone_sanitizer, email_sanitizer, \
    fi_company_org_id_generator


class Tests(TestCase, DefaultTestSetupMixin):
    def setUp(self):
        self.add_test_user()

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
        ee_iban_validator('EE38 2200 2210 2014 5685')
        be_iban_validator('BE68 5390 0754 7034')
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

    def test_email_filter_and_validation(self):
        emails = [
            (' Asdsa@a-a.com ', 'asdsa@a-a.com', True),
            ('1asdsa@a-a2.com', '1asdsa@a-a2.com', True),
            (' Asdsa@a-a ', 'asdsa@a-a', False),
            (' @a-a2.com', '@a-a2.com', False),
            (' a-a2.com', 'a-a2.com', False),
            ('ää-a2@ää-a2.com', 'ää-a2@ää-a2.com', False),
        ]
        for i, o, is_valid in emails:
            # print('email_filter({}) -> {}'.format(i, email_filter(i)))
            self.assertEqual(email_filter(i), o)
            if is_valid:
                email_validator(o)
            else:
                fail = False
                try:
                    email_validator(o)
                except ValidationError:
                    fail = True
                self.assertTrue(fail, '{} is not valid email but passed validation'.format(o))

    def test_ip_info(self):
        ip, cc, host = get_ip_info('213.214.146.142')
        self.assertEqual(ip, '213.214.146.142')
        if cc:
            self.assertEqual(cc, 'FI')
        if host:
            self.assertEqual(host, '213214146142.edelkey.net')

    def test_parse_xml(self):
        # finvoice_201_example1.xml
        xml_bytes = open(join(settings.BASE_DIR, 'data/fi/finvoice_201_example1.xml'), 'rb').read()
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
                'D': 123,
                'E': ['abc'],
             }
        }
        el = dict_to_element(data)
        assert isinstance(el, Element)
        xml_str = ET.tostring(el, encoding='utf8', method='xml').decode()
        # print(xml_str)  # <Doc version="1.2"><C>value node</C><A class="x"><B class="x2">hello</B></A><A class="y"><B class="y2">world</B></A></Doc>
        data2 = xml_to_dict(xml_str, document_tag=True, array_tags=['E'], int_tags=['D'])
        # print('')
        # pprint(data)
        # pprint(data2)
        self.assertEqual(data2, data)

    def test_xml_to_dict(self):
        from xml.etree.ElementTree import Element
        from xml.etree import ElementTree as ET

        xml_str = """<?xml version="1.0" encoding="utf-8"?>
<Document>
  <TxsSummry>
    <TtlNtries>
      <NbOfNtries>12</NbOfNtries>
    </TtlNtries>
    <TtlCdtNtries>
      <NbOfNtries>34</NbOfNtries>
      <Sum>1234.56</Sum>
    </TtlCdtNtries>
    <TtlDbtNtries>
      <NbOfNtries>0</NbOfNtries>
      <Sum>0</Sum>
    </TtlDbtNtries>
  </TxsSummry>
</Document>"""
        data = xml_to_dict(xml_str, document_tag=True, array_tags=[], int_tags=['NbOfNtries'])
        # print('')
        # pprint(data)
        self.assertEqual(data['Document']['TxsSummry']['TtlNtries']['NbOfNtries'], 12)
        self.assertEqual(data['Document']['TxsSummry']['TtlCdtNtries']['NbOfNtries'], 34)

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
        self.assertEqual(inf[0], '')
        self.assertEqual(inf[1], '')

        ac= 'BE75270187592710'
        inf = iban_bank_info(ac)
        self.assertEqual(inf[0], 'GEBABEBB')
        self.assertEqual(inf[1], 'BNP Paribas Fortis')
        ac= 'BE58465045170210'
        inf = iban_bank_info(ac)
        self.assertEqual(inf[0], 'KREDBEBB')
        self.assertEqual(inf[1], 'KBC Bank')
        ac= 'BE11000123456748'
        inf = iban_bank_info(ac)
        self.assertEqual(inf[0], 'BPOTBEB1')
        self.assertEqual(inf[1], 'bpost bank')

    def test_org_id_fi(self):
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
            # print('test_org_id_fi:', valid, 'should be valid...', end=' ')
            fi_company_org_id_validator(valid)
            # print('ok')
        for invalid in invalids:
            try:
                # print('test_org_id_fi:', invalid, 'should be invalid', end=' ')
                fi_company_org_id_validator(invalid)
                self.assertTrue(False)
            except ValidationError:
                # print('ok')
                pass
        for n in range(10):
            v0 = fi_company_org_id_generator()
            # print(v0)
            fi_company_org_id_validator(v0)

    def test_reference_number_validators(self):
        valid_fi_refs = [
            '302300',
            '202196',
            '302290',
        ]
        for ref_no in valid_fi_refs:
            fi_payment_reference_validator(ref_no)

        invalid_fi_refs = [
            '302301',
            '202195',
            '302291',
        ]
        for ref_no in invalid_fi_refs:
            try:
                fi_payment_reference_validator(ref_no)
                self.assertFalse(True, '{} should have failed validation'.format(ref_no))
            except ValidationError:
                pass

        valid_iso_refs = [
            'RF92 1229',
            'RF11 1232',
            'RF48 1245',
        ]
        for ref_no in valid_iso_refs:
            iso_payment_reference_validator(ref_no)

    def test_fi_ssn_age(self):
        samples = [
            (date(2018, 12, 20), '231298-965X', 19),
            (date(2018, 12, 22), '231298-965X', 19),
            (date(2018, 12, 23), '231298-965X', 20),
            (date(2018, 12, 24), '231298-965X', 20),
        ]
        for date_now, ssn, age in samples:
            self.assertEqual(fi_ssn_age(ssn, date_now), age, msg='{} age is {} on {} but fi_ssn_age result was {}'.format(ssn, age, date_now, fi_ssn_age(ssn, date_now)))

    def test_se_banks(self):
        self.assertEqual(se_clearing_code_bank_info('6789'), ('Handelsbanken', 9))
        se_iban_validator('SE45 5000 0000 0583 9825 7466')
        self.assertEqual(se_clearing_code_bank_info('9500'), ('Nordea AB', 10))
        an = '957033025420'
        bank_name, acc_digits = se_clearing_code_bank_info(an)
        self.assertEqual(bank_name, 'Sparbanken Syd')
        self.assertGreaterEqual(len(an)-4, acc_digits)

    def test_dk_banks(self):
        an = 'DK50 0040 0440 1162 43'
        dk_iban_validator(an)
        bic, name = dk_iban_bank_info(an)
        self.assertEqual(name, 'Nordea')
        an = '8114 0008874093'
        name = dk_clearing_code_bank_name(an)
        self.assertEqual(name, 'Nykredit Bank')
        an = 'DK2520006893703029'
        name = dk_clearing_code_bank_name(an)
        self.assertEqual(name, 'Nordea')

    def test_ascii_filter(self):
        pairs = [
            ('Åke va Källe o Öring', 'Ake va Kalle o Oring'),
            ('Tôi đang đi mua sắm', 'Toi ang i mua sam'),
            ('HELÉN FRANZÉN', 'HELEN FRANZEN'),
        ]
        for a, b in pairs:
            self.assertEqual(ascii_filter(a), b, 'ascii_filter("{}") != "{}"'.format(b, ascii_filter(a)))

    def test_l10n(self):
        from rest_framework.exceptions import ValidationError

        with override('fi'):
            msg = _("“%(value)s” value has an invalid format. It must be in YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ] format.")
            if 'muoto ei kelpaa' not in msg:
                print(msg)
            self.assertTrue('muoto ei kelpaa' in msg)

            try:
                parse_bool('hello')
            except ValidationError as e:
                self.assertEqual(str(e), "[ErrorDetail(string='hello ei ole yksi valittavissa olevista arvoista', code='invalid')]")

    def test_sanitizers(self):
        self.assertEqual(country_code_sanitizer('kods'), '')
        self.assertEqual(country_code_sanitizer('fi'), 'FI')
        self.assertEqual(phone_sanitizer('+13146094459'), '+13146094459')
        self.assertEqual(phone_sanitizer('13146094459'), '13146094459')
        self.assertEqual(phone_sanitizer('+13146094459A'), '+13146094459')
        self.assertEqual(email_sanitizer('test@example.com'), 'test@example.com')
        self.assertEqual(email_sanitizer('testexample.com'), '')

    def test_dict_to_html(self):
        a = {'b': 1, 'c': {'@testVariable': '123'}}
        res = '<pre>B: 1\nC:\n    Test variable: 123\n\n</pre>'
        self.assertEqual(dict_to_html(a), res)

    def test_format_xml(self):
        assert settings.XMLLINT_PATH, 'add e.g. XMLLINT_PATH = "/usr/bin/xmllint" to settings.py'
        src = '<ApplicationRequest> <CustomerId>1</CustomerId>  <Command>DownloadFileList</Command><Timestamp>2019-11-27T04:32:18.613452+02:00</Timestamp><Environment>PRODUCTION</Environment></ApplicationRequest>'
        dst_ref = '<?xml version="1.0"?>\n<ApplicationRequest>\n  <CustomerId>1</CustomerId>\n  <Command>DownloadFileList</Command>\n  <Timestamp>2019-11-27T04:32:18.613452+02:00</Timestamp>\n  <Environment>PRODUCTION</Environment>\n</ApplicationRequest>\n'
        dst = format_xml(src)
        self.assertEqual(dst, dst_ref)
        dst = format_xml_bytes(src)
        self.assertEqual(dst, dst_ref.encode())

    def test_parse_sftp(self):
        test_cases = [
            ('jani@kajala.com', ['jani', '', 'kajala.com', '']),
            ('jani.kajala:1231!@kajala.com', ['jani.kajala', '1231!', 'kajala.com', '']),
            ('jani:1231!@kajala.com:/my/dir', ['jani', '1231!', 'kajala.com', '/my/dir']),
            ('jani.kajala:1231!@kajala.com:my/dir', ['jani.kajala', '1231!', 'kajala.com', 'my/dir']),
            ('user=jani;host=kajala.com', ['jani', '', 'kajala.com', '']),
            ('user=jani.kajala;pass=1231!;host=kajala.com', ['jani.kajala', '1231!', 'kajala.com', '']),
            ('user=jani;pass=1231!;host=kajala.com;path=/my/dir', ['jani', '1231!', 'kajala.com', '/my/dir']),
            ('user=jani.kajala;pass=1231!;host=kajala.com;path=my/dir', ['jani.kajala', '1231!', 'kajala.com', 'my/dir']),
        ]
        for connection, ref_res in test_cases:
            res = parse_sftp_connection(connection)
            self.assertListEqual(list(res), ref_res, 'SFTP connection string "{}" parsed incorrectly'.format(connection))

    def test_admin(self):
        obj = self.user
        admin_log([obj], 'Hello, world')
        e = LogEntry.objects.all().filter(object_id=obj.id).last()
        self.assertIsNotNone(e)
        assert isinstance(e, LogEntry)
        self.assertEqual(e.change_message, 'Hello, world')
        self.assertEqual(admin_obj_url(obj, 'admin:auth_user_change'), '/admin/auth/user/{}/change/'.format(obj.id))
        link = admin_obj_link(obj, 'User', 'admin:auth_user_change')
        self.assertEqual(link, "<a href='/admin/auth/user/{}/change/'>User</a>".format(obj.id))

    def test_cmd_parser(self):
        parser = CommandParser()
        add_date_range_arguments(parser)
        argv = parser.parse_args(['--begin', '2019-06-25', '--end', '2020-02-01'])
        options = argv.__dict__
        begin, end, steps = parse_date_range_arguments(options)
        self.assertEqual(begin, pytz.utc.localize(datetime(2019, 6, 25)))
        self.assertEqual(end, pytz.utc.localize(datetime(2020, 2, 1)))

    def test_format_timedelta(self):
        self.assertEqual(format_timedelta(timedelta(seconds=90), include_seconds=True), '1min30s')
        self.assertEqual(format_timedelta(timedelta(seconds=90), include_seconds=False), '1min')

    def test_dec123456(self):
        self.assertEqual(dec1(Decimal('1.2345678')), Decimal('1.2'))
        self.assertEqual(dec2(Decimal('1.2345678')), Decimal('1.23'))
        self.assertEqual(dec3(Decimal('1.2345678')), Decimal('1.235'))
        self.assertEqual(dec4(Decimal('1.2345678')), Decimal('1.2346'))
        self.assertEqual(dec5(Decimal('1.2345678')), Decimal('1.23457'))
        self.assertEqual(dec6(Decimal('1.2345678')), Decimal('1.234568'))

    def test_model_funcs(self):
        admin_log([self.user], 'test msg 1')
        obj = LogEntry.objects.all().order_by('-pk').last()
        assert isinstance(obj, LogEntry)
        self.assertFalse(is_model_field_changed(obj, 'change_message'))
        obj.change_message = 'hello world'
        self.assertTrue(is_model_field_changed(obj, 'change_message'))
        obj.save()
        self.assertFalse(is_model_field_changed(obj, 'change_message'))
        obj2 = clone_model(obj)
        assert isinstance(obj2, LogEntry)
        self.assertEqual(obj.change_message, obj2.change_message)
        self.assertGreater(obj2.pk, obj.pk)
        label, val = get_model_field_label_and_value(obj, 'action_time')
        self.assertEqual(label, _('action time'))
        self.assertEqual(str(obj.action_time), val)
        obj_b = get_object_or_none(obj.__class__, id=obj.id)
        self.assertEqual(obj_b.id, obj.id)
        obj_b = get_object_or_none(obj.__class__, id=-1)
        self.assertIsNone(obj_b)

    def test_format_table(self):
        a = [
            ['date', 'description', 'count', 'unit price', 'total price'],
            [date(2019, 12, 15), 'oranges', 1000, dec2('0.99'), dec2('990.00')],
            [date(2020, 1, 3), 'apples', 4, dec2('1.10'), dec2('4.40')],
            [date(2020, 11, 3), 'apples', 5, dec2('10.10'), dec2('50.50')],
        ]
        out = format_table(a, has_label_row=True, max_col=10)
        out_ref = """
---------------------------------------------------
|      date|descript..|count|unit price|total pr..|
---------------------------------------------------
|2019-12-15|   oranges| 1000|      0.99|    990.00|
|2020-01-03|    apples|    4|      1.10|      4.40|
|2020-11-03|    apples|    5|     10.10|     50.50|
---------------------------------------------------
            """.strip()
        self.assertEqual(out, out_ref)

        out = format_table(a, has_label_row=True, max_col=20)
        out_ref = """
-----------------------------------------------------
|      date|description|count|unit price|total price|
-----------------------------------------------------
|2019-12-15|    oranges| 1000|      0.99|     990.00|
|2020-01-03|     apples|    4|      1.10|       4.40|
|2020-11-03|     apples|    5|     10.10|      50.50|
-----------------------------------------------------
            """.strip()
        self.assertEqual(out, out_ref)

        out = format_table(a, has_label_row=True, max_col=20, col_sep=' | ')
        out_ref = """
-------------------------------------------------------------
|      date | description | count | unit price | total price|
-------------------------------------------------------------
|2019-12-15 |     oranges |  1000 |       0.99 |      990.00|
|2020-01-03 |      apples |     4 |       1.10 |        4.40|
|2020-11-03 |      apples |     5 |      10.10 |       50.50|
-------------------------------------------------------------
            """.strip()
        self.assertEqual(out, out_ref)

        out = format_table(a, has_label_row=True, max_col=20, col_sep=' | ', left_align=[1])
        out_ref = """
-------------------------------------------------------------
|      date | description | count | unit price | total price|
-------------------------------------------------------------
|2019-12-15 | oranges     |  1000 |       0.99 |      990.00|
|2020-01-03 | apples      |     4 |       1.10 |        4.40|
|2020-11-03 | apples      |     5 |      10.10 |       50.50|
-------------------------------------------------------------
            """.strip()
        self.assertEqual(out, out_ref)

        out = format_table(a, has_label_row=True, max_col=20, col_sep=' | ', left_align=[1], max_line=50)
        out_ref = """
-------------------------------------------------
|      date | description | count | unit price|..
-------------------------------------------------
|2019-12-15 | oranges     |  1000 |       0.99|..
|2020-01-03 | apples      |     4 |       1.10|..
|2020-11-03 | apples      |     5 |      10.10|..
-------------------------------------------------
            """.strip()
        self.assertEqual(out, out_ref)

        out = format_table(a, left_align=[1], center_align=[0,2,3,4], max_col=50)
        out_ref = """
-----------------------------------------------------
|   date   |description|count|unit price|total price|
|2019-12-15|oranges    |1000 |   0.99   |  990.00   |
|2020-01-03|apples     |  4  |   1.10   |   4.40    |
|2020-11-03|apples     |  5  |  10.10   |   50.50   |
-----------------------------------------------------
            """.strip()
        self.assertEqual(out, out_ref)

    def test_ucfirst_lazy(self):
        s = gettext_lazy(ucfirst_lazy("missing value"))
        s_ref = gettext_lazy("Missing value")
        s_en = "Missing value"
        s_fi = "Puuttuva arvo"
        with override('fi'):
            self.assertEqual(s, s_fi)
            self.assertEqual(s, s_ref)
        with override('en'):
            self.assertEqual(s, s_en)
            self.assertEqual(s, s_ref)
