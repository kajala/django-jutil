# pylint: disable=too-many-branches
import csv
from copy import copy
from django.core.management.base import CommandParser
from jutil.command import SafeCommand
from jutil.bank_const_dk import DK_BANK_CLEARING_MAP


def is_int(x) -> bool:
    try:
        int(x)
        return True
    except Exception:
        return False


def dk_iban_load_map(filename: str) -> list:
    """
    Loads Denmark monetary institution codes in CSV format.
    :param filename: CSV file name of the BIC definitions.
    Columns: 4-digit code, bank name, ...
    :return: list of (code, name)
    """
    data_list = []
    with open(filename) as fp:
        for row in csv.reader(fp):
            if len(row) >= 2 and is_int(row[0]) and row[1]:
                data_list.append((row[0], row[1]))
    return data_list


class Command(SafeCommand):
    help = 'Generates Python file with Denmark bank info as constants'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('--filename', type=str)
        parser.add_argument('--php', action='store_true')

    def do(self, *args, **kw):
        new_bank_list = dk_iban_load_map(kw['filename']) if kw['filename'] else []

        bank_data = dict(copy(DK_BANK_CLEARING_MAP))
        for code, name in new_bank_list:
            if code not in bank_data:
                bank_data[code] = name

        if kw['php']:
            print('<?php')
            print('')
            print('global $DK_BANK_CLEARING_MAP;')
            print('$DK_BANK_CLEARING_MAP = array(')
            errors = False
            for code, name in bank_data.items():
                print("    '{}' => '{}',".format(code, name))
            print(');')
            if errors:
                print('')
                print('// TODO: fix errors from above marked with "?"')
            print('')
        else:
            print('DK_BANK_CLEARING_MAP = {  # ' + str(len(bank_data)))
            errors = False
            for code, name in bank_data.items():
                print("    '{}': '{}',".format(code, name))
            print('}')
            if errors:
                print('')
                print('# TODO: fix errors from above marked with "?"')
            print('')
