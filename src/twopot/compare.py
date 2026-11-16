"""Withdraw from the savings pot, or borrow the same cash? A like-for-like test.

Two ways to get the same cash in hand today:

* WITHDRAW: take it from the savings pot. No loan, so no instalments.
* BORROW: leave the pot alone and repay a loan in monthly instalments.

Borrowing leaves the retirement fund whole. Withdrawing leaves a hole in it, but
frees up the instalments. So the fair question is: what does the member do with
the instalments they avoided?

* SPEND: nothing is put back. The hole stays.
* SAVE_AFTER_TAX: they go into after-tax savings such as a tax-free account.
* FUND_CONTRIBUTIONS: they go back into the retirement fund as extra
  contributions, which are tax-deductible, so the tax paid on the withdrawal is
  recovered.

Both strategies then have identical take-home cash in every month, and can be
judged on one number: retirement money in today's rands. Everything here is in
real terms. The loan's instalments are fixed in money terms, so each one is
deflated by inflation before it is valued.

The break-even is expressed as a loan's all-in cost (interest and fees together,
as an effective annual rate in money terms), and it is compared with the actual
loan's all-in cost over the same term. Same basis, same term, same yardstick.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from twopot import params
from twopot.loan import Loan, all_in_cost
from twopot.rates import Basis, Rate
from twopot.solver import bisect
from twopot.tax import income_tax, retirement_lump_sum_tax
from twopot.withdrawal import Withdrawal, WithdrawalPrice, price_withdrawal

# Upper end of the break-even search: repaying twice the cash received every
# month, which is far beyond any legal loan.
_HIGHEST_INSTALMENT_MULTIPLE = 2.0


class PutBack(str, Enum):
    SPEND = "spend"
    SAVE_AFTER_TAX = "save_after_tax"
    FUND_CONTRIBUTIONS = "fund_contributions"


@dataclass(frozen=True)
class Scenario:
    withdrawal: Withdrawal
    quoted_loan_rate: float  # per year, charged monthly, money terms
    term_months: int
    real_return: Rate
    inflation: float
    initiation_fee: float = 0.0
    monthly_service_fee: float = 0.0
    # What the member and employer already contribute each year, used only to
    # check the tax-deduction limit on extra contributions.
    current_contributions: float = 0.0

    def __post_init__(self) -> None:
        self.real_return.require(Basis.REAL)
        if self.term_months > self.withdrawal.years_to_retirement * 12:
            raise ValueError("the loan must be repaid before retirement")


@dataclass(frozen=True)
class Comparison:
    """Amounts are in today's rands unless stated."""

    price: WithdrawalPrice
    loan: Loan
    loan_cost: Rate  # all-in, nominal
    put_back: PutBack
    share_saved: float
    monthly_saving: float  # share of the instalment saved, in money terms
    put_back_at_retirement: float
    # Retirement money under WITHDRAW minus under BORROW. Positive: withdrawing wins.
    advantage: float
    advantage_if_all_saved: float
    # Smallest share of the avoided instalments that must be saved for
    # withdrawing to match the loan. None if even saving all of it falls short.
    break_even_share: float | None
    # All-in loan cost above which withdrawing wins, if every avoided instalment
    # is saved. Zero means withdrawing beats even an interest-free loan. None
    # means no loan is expensive enough (always the case under SPEND).
    break_even_loan_cost: Rate | None
    warnings: tuple[str, ...]

    @property
    def withdrawing_wins(self) -> bool:
        return self.advantage >= 0


def gross_up_for_deduction(net_cost: float, taxable_income: float, age: int) -> float:
    """Contribution that costs ``net_cost`` of take-home pay after its tax saving.

    A deductible contribution C lowers taxable income by C, so it costs
    C minus the tax saved. Solve for the C whose cost equals ``net_cost``.
    """
    if net_cost <= 0:
        return 0.0
    tax_before = income_tax(taxable_income, age)

    def shortfall(contribution: float) -> float:
        # A deduction cannot take taxable income below zero.
        income_after = max(0.0, taxable_income - contribution)
        tax_saved = tax_before - income_tax(income_after, age)
        return contribution - tax_saved - net_cost

    if shortfall(net_cost) >= 0:
        return net_cost  # no tax is being paid, so there is nothing to recover
    # The saving can never exceed the top rate, which bounds the answer.
    top_rate = max(rate for _, rate in params.INCOME_TAX_BRACKETS)
    upper = net_cost / (1 - top_rate) * 1.000001
    return bisect(shortfall, net_cost, upper)


def _saved_instalments_at_retirement(
    scenario: Scenario, instalment: float, share: float
) -> float:
    """Take-home rands saved each month, deflated and grown to retirement."""
    years = scenario.withdrawal.years_to_retirement
    total = 0.0
    for month in range(1, scenario.term_months + 1):
        t = month / 12
        in_todays_rands = share * instalment / (1 + scenario.inflation) ** t
        total += in_todays_rands * scenario.real_return.growth(years - t)
    return total


def _saved_per_year(scenario: Scenario, instalment: float, share: float) -> float:
    return share * instalment * min(12, scenario.term_months)


def _contribution_gross_up(scenario: Scenario, instalment: float, share: float) -> float:
    """Fund rands bought by each take-home rand of extra contribution."""
    net_per_year = _saved_per_year(scenario, instalment, share)
    if net_per_year <= 0:
        return 1.0
    w = scenario.withdrawal
    return gross_up_for_deduction(net_per_year, w.taxable_income, w.age) / net_per_year


def put_back_at_retirement(
    scenario: Scenario, instalment: float, put_back: PutBack, share: float
) -> float:
    """Retirement value, after exit tax, of the instalments saved under WITHDRAW."""
    if put_back is PutBack.SPEND or share <= 0:
        return 0.0
    saved = _saved_instalments_at_retirement(scenario, instalment, share)
    if put_back is PutBack.SAVE_AFTER_TAX:
        return saved  # growth and proceeds assumed tax-free
    in_fund = saved * _contribution_gross_up(scenario, instalment, share)
    exit_tax = retirement_lump_sum_tax(
        in_fund, prior_lump_sums=scenario.withdrawal.other_lump_sums_at_retirement
    )
    return in_fund - exit_tax


def _warnings(
    scenario: Scenario, instalment: float, put_back: PutBack, share: float
) -> tuple[str, ...]:
    notes = []
    saved_per_year = _saved_per_year(scenario, instalment, share)
    if put_back is PutBack.SAVE_AFTER_TAX and saved_per_year > params.TFSA_ANNUAL_LIMIT:
        notes.append(
            f"Saving R{saved_per_year:,.0f} a year exceeds the "
            f"R{params.TFSA_ANNUAL_LIMIT:,} tax-free savings limit. Growth on the "
            "excess would be taxed, which this model ignores."
        )
    if put_back is PutBack.FUND_CONTRIBUTIONS and saved_per_year > 0:
        w = scenario.withdrawal
        extra = saved_per_year * _contribution_gross_up(scenario, instalment, share)
        income_before_deduction = w.taxable_income + scenario.current_contributions
        limit = min(
            params.RETIREMENT_DEDUCTION_PCT * income_before_deduction,
            params.RETIREMENT_DEDUCTION_CAP,
        )
        if scenario.current_contributions + extra > limit:
            notes.append(
                f"Total contributions would exceed the deductible limit of "
                f"R{limit:,.0f} a year, so part of the extra contribution would "
                "not reduce tax now. The result is too favourable to withdrawing."
            )
    return tuple(notes)


def compare(scenario: Scenario, put_back: PutBack, share_saved: float) -> Comparison:
    """Compare withdrawing with borrowing the same cash on the scenario's loan."""
    if not 0 <= share_saved <= 1:
        raise ValueError("share saved must be between 0 and 1")
    price = price_withdrawal(scenario.withdrawal, scenario.real_return)
    cash = price.net_cash
    term = scenario.term_months
    loan = Loan(
        principal=cash,
        quoted_rate=scenario.quoted_loan_rate,
        term_months=term,
        initiation_fee=scenario.initiation_fee,
        monthly_service_fee=scenario.monthly_service_fee,
    )
    hole = price.forgone_after_tax

    def advantage(share: float, instalment: float = loan.instalment) -> float:
        return put_back_at_retirement(scenario, instalment, put_back, share) - hole

    advantage_if_all_saved = advantage(1.0)

    break_even_share = None
    if advantage_if_all_saved >= 0:
        break_even_share = bisect(advantage, 0.0, 1.0)

    # Find the level instalment at which saving all of it exactly refills the
    # hole, then express that instalment as a loan's all-in cost.
    break_even_loan_cost = None
    if put_back is not PutBack.SPEND:
        interest_free = cash / term
        highest = cash * _HIGHEST_INSTALMENT_MULTIPLE

        def advantage_at(instalment: float) -> float:
            return advantage(1.0, instalment)

        if advantage_at(interest_free) >= 0:
            break_even_loan_cost = Rate.nominal(0.0)
        elif advantage_at(highest) > 0:
            break_even_instalment = bisect(advantage_at, interest_free, highest)
            break_even_loan_cost = all_in_cost(cash, break_even_instalment, term)

    return Comparison(
        price=price,
        loan=loan,
        loan_cost=loan.effective_cost(),
        put_back=put_back,
        share_saved=share_saved,
        monthly_saving=share_saved * loan.instalment,
        put_back_at_retirement=put_back_at_retirement(
            scenario, loan.instalment, put_back, share_saved
        ),
        advantage=advantage(share_saved),
        advantage_if_all_saved=advantage_if_all_saved,
        break_even_share=break_even_share,
        break_even_loan_cost=break_even_loan_cost,
        warnings=_warnings(scenario, loan.instalment, put_back, share_saved),
    )
