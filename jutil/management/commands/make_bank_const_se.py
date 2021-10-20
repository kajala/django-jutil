# pylint: disable=too-many-branches,too-many-nested-blocks,too-many-locals
import csv
import re
from copy import copy
from typing import Any

from django.core.management.base import CommandParser
from jutil.command import SafeCommand
from jutil.bank_const_se import SE_BANK_CLEARING_LIST


def se_iban_load_map(filename: str) -> list:
    """
    Loads Swedish monetary institution codes in CSV format.
    :param filename: CSV file name of the BIC definitions.
    Columns: Institution Name, Range Begin-Range End (inclusive), Account digits count
    :return: List of (bank name, clearing code begin, clearing code end, account digits)
    """
    out = []
    name_repl = {
        "BNP Paribas Fortis SA/NV, Bankfilial Sverige": "BNP Paribas Fortis SA/NV",
        "Citibank International Plc, Sweden Branch": "Citibank",
        "Santander Consumer Bank AS (deltar endast i Dataclearingen)": "Santander Consumer Bank AS",
        "Nordax Bank AB (deltar endast i Dataclearingen)": "Nordax Bank AB",
        "Swedbank och fristående Sparbanker, t ex Leksands Sparbank och Roslagsbanken.": "Swedbank",
        "Ålandsbanken Abp (Finland),svensk filial": "Ålandsbanken Abp",
        "SBAB (deltar endast i Dataclearingen)": "SBAB Bank AB",
        "SBAB deltar endast i Dataclearingen": "SBAB Bank AB",
        "DNB Bank ASA, filial Sverige": "Den Norske Bank",
        "Länsförsäkringar Bank Aktiebolag": "Länsförsäkringar Bank AB",
        "MedMera Bank AB": "Med Mera Bank AB",
    }
    with open(filename, "rt", encoding="utf-8") as fp:
        for row in csv.reader(fp):
            if len(row) == 3:
                name, series, acc_digits = row
                # pprint([name, series, acc_digits])

                # clean up name
                name = re.sub(r"\n.*", "", name)
                name = name_repl.get(name, name)

                # clean up series
                ml_acc_digits = acc_digits.split("\n")
                for i, ser in enumerate(series.split("\n")):
                    begin, end = None, None
                    res = re.match(r"^(\d+)-(\d+).*$", ser)
                    if res:
                        begin, end = res.group(1), res.group(2)
                    if begin is None:
                        res = re.match(r"^(\d{4}).*$", ser)
                        if res:
                            begin = res.group(1)
                            end = begin

                    if begin and end:
                        digits: Any = None
                        try:
                            digits = int(acc_digits)
                        except ValueError:
                            pass
                        if digits is None:
                            try:
                                digits = int(ml_acc_digits[i])
                            except ValueError:
                                digits = "?"
                            except IndexError:
                                digits = "?"

                        out.append([name.strip(), begin.strip(), end.strip(), digits])
                        # print('OK!')
    return out


class Command(SafeCommand):
    help = "Generates Python file with Swedish bank info as constants"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--filename", type=str)
        parser.add_argument("--php", action="store_true")

    def do(self, *args, **kw):
        new_bank_list = se_iban_load_map(kw["filename"]) if kw["filename"] else []
        # pprint(bank_list)

        bank_list = list(copy(SE_BANK_CLEARING_LIST))
        for name, begin, end, acc_digits in new_bank_list:
            exists = False
            # pylint: disable=unused-variable
            for name0, begin0, end0, acc_digits0 in bank_list:
                if begin0 == begin and end0 == end:
                    exists = True
                    break
            # pylint: enable=unused-variable
            if not exists:
                bank_list.append((name, begin, end, acc_digits))

        if kw["php"]:
            print("<?php")
            print("")
            print("global $SE_BANK_CLEARING_LIST;")
            print("$SE_BANK_CLEARING_LIST = array(")
            errors = False
            for name, begin, end, acc_digits in bank_list:
                print("    ['{}', '{}', '{}', {}],".format(name, begin, end, acc_digits))
                if acc_digits == "?":
                    errors = True
            print(");")
            if errors:
                print("")
                print('// TODO: fix errors from above marked with "?"')
            print("")
        else:
            print("SE_BANK_CLEARING_LIST = (  # " + str(len(bank_list)))
            errors = False
            for name, begin, end, acc_digits in bank_list:
                print("    ('{}', '{}', '{}', {}),".format(name, begin, end, acc_digits))
                if acc_digits == "?":
                    errors = True
            print(")")
            if errors:
                print("")
                print('# TODO: fix errors from above marked with "?"')
            print("")
