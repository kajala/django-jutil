# pylint: disable=too-many-branches
from django.core.exceptions import ValidationError
from django.core.management.base import CommandParser
from jutil.command import SafeCommand
from jutil.dict import sorted_dict
from jutil.bank_const_fi import FI_BIC_BY_ACCOUNT_NUMBER, FI_BANK_NAME_BY_BIC


def fi_iban_load_map(filename: str) -> dict:
    """
    Loads Finnish monetary institution codes and BICs in CSV format.
    Map which is based on 3 digits as in FIXX<3 digits>.
    Can be used to map Finnish IBAN number to bank information.
    Format: dict('<3 digits': (BIC, name), ...)
    :param filename: CSV file name of the BIC definitions. Columns: National ID, BIC Code, Institution Name
    """
    out = {}
    with open(filename, "rt") as fp:
        lines = [line.strip().split(",") for line in fp.readlines()]
        lines.pop(0)  # ver
        head = lines.pop(0)
        if head != ["National ID", "BIC Code", "Financial Institution Name"]:
            raise ValidationError("Incompatible file content in {}".format(filename))
        for line in lines:
            if len(line) == 3 and line[0]:
                nat_id = str(line[0]).strip()
                bic_code = line[1].strip()
                name = line[2].strip()
                out[nat_id] = (bic_code, name)
    return out


class Command(SafeCommand):
    help = "Generates Python file with Finnish bank info as constants"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--filename", type=str)
        parser.add_argument("--php", action="store_true")

    def do(self, *args, **kw):
        iban_map = fi_iban_load_map(kw["filename"]) if kw["filename"] else {}
        bic_by_acc = FI_BIC_BY_ACCOUNT_NUMBER
        for acc, bank in iban_map.items():
            bic_by_acc[acc] = bank[0]
        bic_map = FI_BANK_NAME_BY_BIC
        for acc, bank in iban_map.items():
            if bank[0] not in bic_map:
                bic_map[bank[0]] = bank[1]
        bic_by_acc = sorted_dict(bic_by_acc)
        bic_map = sorted_dict(bic_map)

        if kw["php"]:
            print("<?php")
            print("")
            print("global $FI_BIC_BY_ACCOUNT_NUMBER;")
            print("$FI_BIC_BY_ACCOUNT_NUMBER = array(")
            for acc, bank in iban_map.items():
                print("    '{}' => '{}',".format(acc, bank[0]))
            print(");")
            print("")
            print("global $FI_BANK_NAME_BY_BIC;")
            print("$FI_BANK_NAME_BY_BIC = array(")
            for bic, bank in bic_map.items():
                print("    '{}' => '{}',".format(bic, bank))
            print(");")
            print("")
        else:
            print("FI_BIC_BY_ACCOUNT_NUMBER = {  # " + str(len(bic_by_acc.items())))
            for acc, bic in bic_by_acc.items():
                print("    '{}': '{}',".format(acc, bic))
            print("}\n")
            print("FI_BANK_NAME_BY_BIC = {  # " + str(len(bic_map.items())))
            for bic, name in bic_map.items():
                print("    '{}': '{}',".format(bic, name))
            print("}")
            print("")
