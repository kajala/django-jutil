import csv
import re
from pprint import pprint
from django.core.exceptions import ValidationError
from django.core.management.base import CommandParser
from jutil.command import SafeCommand
from jutil.dict import sorted_dict
from jutil.fi_bank_const import FI_BIC_BY_ACCOUNT_NUMBER, FI_BANK_NAME_BY_BIC


def se_iban_load_map(filename: str) -> list:
    """
    Loads Swedish monetary institution codes in CSV format.
    :param filename: CSV file name of the BIC definitions.
    Columns: Institution Name, Range Begin-Range End (inclusive), Account digits count
    :return: List of (bank name, clearing code begin, clearing code end, account digits)
    """
    out = []
    name_repl = {
        'BNP Paribas Fortis SA/NV, Bankfilial Sverige': 'BNP Paribas Fortis SA/NV',
        'Citibank International Plc, Sweden Branch': 'Citibank International Plc',
        'Santander Consumer Bank AS (deltar endast i Dataclearingen)': 'Santander Consumer Bank AS',
        'Nordax Bank AB (deltar endast i Dataclearingen)': 'Nordax Bank AB',
        'Swedbank och fristående Sparbanker, t ex Leksands Sparbank och Roslagsbanken.': 'Swedbank',
        'Ålandsbanken Abp (Finland),svensk filial': 'Ålandsbanken Abp',
    }
    with open(filename) as fp:
        for row in csv.reader(fp):
            if len(row) == 3:
                name, series, acc_digits = row
                # pprint([name, series, acc_digits])

                # clean up name
                name = re.sub(r'\n.*', '', name)
                if name in name_repl:
                    name = name_repl[name]

                # clean up series
                ml_acc_digits = acc_digits.split('\n')
                for i, ser in enumerate(series.split('\n')):
                    begin, end = None, None
                    res = re.match(r'^(\d+)-(\d+).*$', ser)
                    if res:
                        begin, end = res.group(1), res.group(2)
                    if begin is None:
                        res = re.match(r'^(\d{4}).*$', ser)
                        if res:
                            begin = res.group(1)
                            end = begin

                    if begin and end:
                        digits = None
                        try:
                            digits = int(acc_digits)
                        except ValueError:
                            pass
                        if digits is None:
                            try:
                                digits = int(ml_acc_digits[i])
                            except ValueError:
                                digits = '?'
                            except IndexError:
                                digits = '?'

                        out.append([name, begin, end, digits])
                        # print('OK!')
    return out


class Command(SafeCommand):
    help = 'Generates Python file with Swedish bank info as constants'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('filename', type=str)

    def do(self, *args, **kw):
        bank_list = se_iban_load_map(kw['filename'])
        # pprint(bank_list)

        print('SE_BANK_CLEARING_LIST = (  # ' + str(len(bank_list)))
        errors = False
        for name, begin, end, acc_digits in bank_list:
            print("    ('{}', '{}', '{}', {}),".format(name, begin, end, acc_digits))
            if acc_digits == '?':
                errors = True
        print(')')
        if errors:
            print('')
            print('# TODO: fix errors from above marked with "?"')
        print('')
