"""The price of one savings withdrawal, in today's rands.

Treat the withdrawal as a loan from your future self:

* Today you receive the gross amount less income tax and any admin fee.
* At retirement you "repay" what the gross amount would have grown to, less the
  tax it would have borne on the way out.

The implied interest rate is whatever turns the first number into the second
over the years in between.
"""

from __future__ import annotations

from dataclasses import dataclass

from twopot import params
from twopot.rates import Basis, Rate
from twopot.tax import retirement_lump_sum_tax, tax_on_extra_income


@dataclass(frozen=True)
class Withdrawal:
    gross: float  # amount leaving the savings pot
    taxable_income: float  # this year's taxable income before the withdrawal
    age: int
    retirement_age: int
    admin_fee: float = params.DEFAULT_ADMIN_FEE
    # Other cash the member expects to take from retirement funds at retirement,
    # in today's rands. It uses up the R550,000 tax-free band first.
    other_lump_sums_at_retirement: float = 0.0

    def __post_init__(self) -> None:
        if self.gross < params.MIN_SAVINGS_WITHDRAWAL:
            raise ValueError(
                f"the minimum savings withdrawal is R{params.MIN_SAVINGS_WITHDRAWAL:,}"
            )
        if self.retirement_age <= self.age:
            raise ValueError("retirement age must be after current age")
        if self.taxable_income < 0 or self.admin_fee < 0:
            raise ValueError("income and fee cannot be negative")
        if self.other_lump_sums_at_retirement < 0:
            raise ValueError("other lump sums cannot be negative")

    @property
    def years_to_retirement(self) -> int:
        return self.retirement_age - self.age


@dataclass(frozen=True)
class WithdrawalPrice:
    """All amounts are in today's rands."""

    gross: float
    tax_now: float
    admin_fee: float
    net_cash: float  # what reaches the bank account
    years_to_retirement: int
    forgone_before_tax: float  # what the gross amount would have grown to
    exit_tax: float  # tax that growth would have borne at retirement
    forgone_after_tax: float  # spendable retirement money given up
    implied_rate: Rate  # real, a year, from today to retirement

    @property
    def tax_rate_now(self) -> float:
        return self.tax_now / self.gross

    @property
    def cost_per_rand(self) -> float:
        """Retirement rands given up for each rand received today."""
        return self.forgone_after_tax / self.net_cash


def implied_rate(net_cash: float, forgone_after_tax: float, years: float) -> Rate:
    """Real annual rate at which ``net_cash`` grows into ``forgone_after_tax``.

    One amount in, one amount out, so there is a closed form:
    (1 + i) ** years = forgone_after_tax / net_cash.
    """
    return Rate.real((forgone_after_tax / net_cash) ** (1 / years) - 1)


def price_withdrawal(withdrawal: Withdrawal, real_return: Rate) -> WithdrawalPrice:
    """Work out what a withdrawal delivers today and what it costs at retirement."""
    real_return.require(Basis.REAL)
    w = withdrawal

    tax_now = tax_on_extra_income(w.gross, w.taxable_income, w.age)
    net_cash = w.gross - tax_now - w.admin_fee
    if net_cash <= 0:
        raise ValueError("tax and fees would consume the whole withdrawal")

    years = w.years_to_retirement
    forgone_before_tax = w.gross * real_return.growth(years)
    exit_tax = retirement_lump_sum_tax(
        forgone_before_tax, prior_lump_sums=w.other_lump_sums_at_retirement
    )
    forgone_after_tax = forgone_before_tax - exit_tax

    return WithdrawalPrice(
        gross=w.gross,
        tax_now=tax_now,
        admin_fee=w.admin_fee,
        net_cash=net_cash,
        years_to_retirement=years,
        forgone_before_tax=forgone_before_tax,
        exit_tax=exit_tax,
        forgone_after_tax=forgone_after_tax,
        implied_rate=implied_rate(net_cash, forgone_after_tax, years),
    )
