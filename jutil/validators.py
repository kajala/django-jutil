import re
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from jutil.fi.validators import *
from jutil.se.validators import *


EMAIL_FILTER = re.compile(r'[^a-z0-9.@-]')
PHONE_FILTER = re.compile(r'[^+0-9]')
PHONE_VALIDATOR = re.compile(r'\+?\d{6,}')
PASSPORT_FILTER = re.compile(r'[^-A-Z0-9]')
STRIP_NON_NUMBERS = re.compile(r'[^0-9]')
IBAN_FILTER = re.compile(r'[^A-Z0-9]')


def phone_filter(v: str) -> str:
    return PHONE_FILTER.sub('', str(v)) if v else ''


def email_filter(v: str) -> str:
    return EMAIL_FILTER.sub('', str(v).lower()) if v else ''


def phone_validator(v: str):
    v = phone_filter(v)
    if not PHONE_VALIDATOR.fullmatch(v):
        raise ValidationError(_('Invalid phone number')+': {}'.format(v), code='invalid_phone')


def passport_filter(v: str) -> str:
    return PASSPORT_FILTER.sub('', str(v).upper()) if v else ''


def passport_validator(v: str):
    v = passport_filter(v)
    if len(v) < 5:
        raise ValidationError(_('Invalid passport number')+': {}'.format(v), code='invalid_passport')


def iban_filter(v: str) -> str:
    return IBAN_FILTER.sub('', str(v).upper()) if v else ''


def iban_filter_readable(acct) -> str:
    acct = iban_filter(acct)
    if acct:
        i = 0
        j = 4
        out = ''
        nlen = len(acct)
        while i < nlen:
            if out:
                out += ' '
            out += acct[i:j]
            i = j
            j += 4
        return out
    return acct


def iban_validator(v: str):
    v = iban_filter(v)
    digits = '0123456789'
    num = ''
    for ch in v[4:] + v[0:4]:
        if ch not in digits:
            ch = str(ord(ch) - ord('A') + 10)
        num += ch
    x = Decimal(num) % Decimal(97)
    if x != Decimal(1):
        raise ValidationError(_('Invalid IBAN account number') + ': {}'.format(v), code='invalid_iban')


def validate_country_iban(v: str, country: str, length: int):
    v = iban_filter(v)
    if len(v) != length:
        raise ValidationError(_('Invalid IBAN account number') + ' ({}.1): {}'.format(country, v), code='invalid_iban')
    if v[0:2] != country:
        raise ValidationError(_('Invalid IBAN account number') + ' ({}.2): {}'.format(country, v), code='invalid_iban')
    digits = '0123456789'
    num = ''
    for ch in v[4:] + v[0:4]:
        if ch not in digits:
            ch = str(ord(ch) - ord('A') + 10)
        num += ch
    x = Decimal(num) % Decimal(97)
    if x != Decimal(1):
        raise ValidationError(_('Invalid IBAN account number') + ' ({}.3): {}'.format(country, v), code='invalid_iban')


def iban_bank_info(v: str) -> (str, str):
    """
    Returns BIC code and bank name from IBAN number.
    :param v: IBAN account number
    :return: (BIC code, bank name) or None if not found / unsupported country
    """
    v = iban_filter(v)
    if v[:2] == 'FI':
        return fi_iban_bank_info(v)
    else:
        return None


def iban_bic(v: str) -> str:
    """
    Returns BIC code from IBAN number.
    :param v: IBAN account number
    :return: BIC code or '' if not found
    """
    info = iban_bank_info(v)
    return info[0] if info else ''
