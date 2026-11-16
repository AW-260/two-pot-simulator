"""South African tax for the 2026/27 tax year.

Two separate tables matter for a two-pot withdrawal:

* A savings withdrawal before retirement is ordinary income. SARS adds it to the
  year's taxable income and taxes it at the marginal rate, with no tax-free
  amount.
* Cash taken from a retirement fund at retirement is taxed on the retirement
  lump-sum table, where the first R550,000 over a lifetime is tax-free.

The gap between those two treatments is the tax cost of withdrawing early.
"""

from __future__ import annotations

from collections.abc import Sequence

from twopot import params

Brackets = Sequence[tuple[float, float]]


def progressive_tax(amount: float, brackets: Brackets) -> float:
    """Tax on ``amount`` where each band's rate applies only to income inside it."""
    if amount < 0:
        raise ValueError("amount cannot be negative")
    tax = 0.0
    lower = 0.0
    for upper, rate in brackets:
        if amount <= lower:
            break
        tax += (min(amount, upper) - lower) * rate
        lower = upper
    return tax


def rebate(age: int) -> float:
    """Annual rebate, which is deducted from tax and depends on age."""
    total = params.PRIMARY_REBATE
    if age >= 65:
        total += params.SECONDARY_REBATE
    if age >= 75:
        total += params.TERTIARY_REBATE
    return total


def income_tax(taxable_income: float, age: int) -> float:
    """Annual income tax after rebates. Never negative."""
    before_rebates = progressive_tax(taxable_income, params.INCOME_TAX_BRACKETS)
    return max(0.0, before_rebates - rebate(age))


def tax_on_extra_income(extra: float, base_income: float, age: int) -> float:
    """Extra tax caused by adding ``extra`` on top of ``base_income``.

    This is the method SARS uses for a savings withdrawal: tax on income including
    the withdrawal, minus tax on income without it. It handles a withdrawal that
    straddles two bands, or that lifts someone above the tax threshold.
    """
    if extra < 0:
        raise ValueError("extra income cannot be negative")
    return income_tax(base_income + extra, age) - income_tax(base_income, age)


def retirement_lump_sum_tax(lump_sum: float, prior_lump_sums: float = 0.0) -> float:
    """Tax on a retirement lump sum, given lump sums already counted.

    The table applies to the lifetime running total, so the tax on this lump sum
    is the tax on the new total minus the tax on the earlier total.
    """
    if lump_sum < 0 or prior_lump_sums < 0:
        raise ValueError("lump sums cannot be negative")
    table = params.RETIREMENT_LUMP_SUM_BRACKETS
    return progressive_tax(prior_lump_sums + lump_sum, table) - progressive_tax(
        prior_lump_sums, table
    )
