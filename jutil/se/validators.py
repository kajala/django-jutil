import re
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _


STRIP_NON_NUMBERS = re.compile(r'[^0-9]')
SE_SSN_FILTER = re.compile(r'[^-0-9]')
SE_SSN_VALIDATOR = re.compile(r'^\d{6}[-]\d{3}[\d]$')


def se_iban_validator(v: str):
    from jutil.validators import validate_country_iban
    validate_country_iban(v, 'SE', 24)


def se_ssn_filter(v: str) -> str:
    return SE_SSN_FILTER.sub('', v.upper())


def se_ssn_validator(v: str):
    v = se_ssn_filter(v)
    if not SE_SSN_VALIDATOR.fullmatch(v):
        raise ValidationError(_('Invalid personal identification number')+' (SE.1): {}'.format(v), code='invalid_ssn')
    v = STRIP_NON_NUMBERS.sub('', v)
    dsum = 0
    for i in range(9):
        x = int(v[i])
        if i & 1 == 0:
            x += x
        # print('summing', v[i], 'as', x)
        xsum = x % 10 + int(x/10) % 10
        # print(v[i], 'xsum', xsum)
        dsum += xsum
    # print('sum', dsum)
    rem = dsum % 10
    # print('rem', rem)
    checksum = 10 - rem
    if checksum == 10:
        checksum = 0
    # print('checksum', checksum)
    if int(v[-1:]) != checksum:
        raise ValidationError(_('Invalid personal identification number')+' (SE.2): {}'.format(v), code='invalid_ssn')
