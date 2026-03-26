from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from jutil.dates import add_month, as_datetime
from jutil.format import dec2, dec6


def calc_fully_amortized_loan_payment(principal_amount: Decimal, term: int, interest_rate: Decimal) -> Decimal:
    """
    Calculates fully amortized (annuity) loan payment.
    =(interest_rate/100)*principal_amount/(1-(1+(interest_rate/100))^-term)

    Args:
        principal_amount: Total loan amount
        term: Loan term units, e.g. months
        interest_rate: Interest rate per time unit, e.g. 12.5/12

    Returns:
        Payment/time unit with six decimals
    """
    if term < 1:
        raise ValidationError(_("Loan term cannot be less than a month"))
    if principal_amount < Decimal("0.00"):
        raise ValidationError(_("Loan principal cannot be negative"))
    if interest_rate < Decimal("0.00"):
        raise ValidationError(_("Interest rate cannot be negative"))
    r = Decimal(interest_rate) * Decimal("0.01")
    n = Decimal(term)
    p = Decimal(principal_amount)
    amt = r * p / (Decimal(1) - (Decimal(1) + r) ** -n)
    return dec6(amt)


def calc_simple_interest(principal_amount: Decimal, term: int, interest_rate: Decimal) -> Decimal:
    """
    Calculates simple interest.

    Args:
        principal_amount: Principal amount
        term: Number of time units, e.g. days
        interest_rate: Interest rate per time unit, e.g. %/day

    Returns:
        Interest amount for the period with 6 decimals
    """
    r = Decimal(interest_rate) * Decimal("0.01")
    n = Decimal(term)
    p = Decimal(principal_amount)
    return dec6(p * r * n)


@dataclass(kw_only=True)
class PaymentScheduleData:
    due_date: date
    due_amount: Decimal
    due_interest: Decimal
    due_principal: Decimal
    interest_days: int
    total_paid_principal: Decimal
    total_paid_interest: Decimal
    balance: Decimal

    def __str__(self) -> str:
        return (
            f"PaymentScheduleEntry("
            f"due_date={self.due_date}, "
            f"due_amount={self.due_amount}, "
            f"principal={self.due_principal}, "
            f"interest={self.due_interest}, "
            f"interest_days={self.interest_days}, "
            f"total_paid_principal={self.total_paid_principal}, "
            f"total_paid_interest={self.total_paid_interest}, "
            f"balance={self.balance}"
            f")"
        )

    @staticmethod
    def field_names() -> List[str]:
        return [
            "due_date",
            "due_amount",
            "due_interest",
            "due_principal",
            "interest_days",
            "total_paid_principal",
            "total_paid_interest",
            "balance",
        ]

    @staticmethod
    def csv_header(separator: str = ",") -> str:
        return separator.join(PaymentScheduleData.field_names())

    def to_csv(self, separator: str = ",") -> str:
        out = ""
        for k in PaymentScheduleData.field_names():
            out += f"{getattr(self, k)}{separator}"
        return out


def calc_fully_amortized_loan_monthly_payment_schedule(
    *,  # noqa
    principal_amount: Decimal,
    term_months: int,
    interest_rate: Decimal,
    monthly_payment: Decimal,
    loan_drawn_date: date,
    repayments_begin_date: date,
    days_in_year: int = 365,
) -> List[PaymentScheduleData]:
    """
    Calculates fully amortized installment loan payment schedule.

    Args:
        principal_amount:
        term_months:
        interest_rate:
        monthly_payment:
        loan_drawn_date:
        repayments_begin_date:
        days_in_year:

    Returns:
        Payment schedule entries
    """
    interest_rate_daily = interest_rate / Decimal(days_in_year)
    repayments_begin = as_datetime(repayments_begin_date)
    assert isinstance(repayments_begin, datetime)
    out: List[PaymentScheduleData] = []
    current_date: date = loan_drawn_date
    balance = principal_amount
    total_paid_principal = Decimal("0.00")
    total_paid_interest = Decimal("0.00")
    for month_ix in range(term_months - 1):
        due_date = add_month(repayments_begin, month_ix).date()
        interest_days = (due_date - current_date).days
        due_interest = dec2(calc_simple_interest(balance, interest_days, interest_rate_daily))
        due_principal = max(monthly_payment - due_interest, Decimal("0.00"))
        balance -= due_principal
        total_paid_principal += due_principal
        total_paid_interest += due_interest
        current_date = due_date

        entry = PaymentScheduleData(
            due_date=due_date,
            due_amount=monthly_payment,
            due_interest=due_interest,
            due_principal=due_principal,
            interest_days=interest_days,
            total_paid_principal=total_paid_principal,
            total_paid_interest=total_paid_interest,
            balance=balance,
        )
        out.append(entry)

    due_date = add_month(repayments_begin, term_months - 1).date()
    interest_days = (due_date - current_date).days
    due_interest = dec2(calc_simple_interest(balance, interest_days, interest_rate_daily))
    due_principal = balance
    last_payment = due_principal + due_interest
    balance -= due_principal
    total_paid_principal += due_principal
    total_paid_interest += due_interest

    entry = PaymentScheduleData(
        due_date=due_date,
        due_amount=last_payment,
        due_interest=due_interest,
        due_principal=due_principal,
        interest_days=interest_days,
        total_paid_principal=total_paid_principal,
        total_paid_interest=total_paid_interest,
        balance=balance,
    )
    out.append(entry)
    return out
