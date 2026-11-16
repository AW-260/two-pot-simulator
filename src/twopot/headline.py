"""Turn a result into one plain-English sentence and a short explanation.

Kept apart from the app so the wording is tested like any other logic. Every
rand figure about retirement is in today's money.
"""

from __future__ import annotations

from dataclasses import dataclass

from twopot.compare import Comparison, PutBack
from twopot.rates import Rate
from twopot.withdrawal import WithdrawalPrice


@dataclass(frozen=True)
class Headline:
    title: str
    detail: str


def rands(amount: float) -> str:
    return f"R{amount:,.0f}"


def percent(rate: Rate) -> str:
    return f"{rate.value:.1%}"


def _months(count: int) -> str:
    return "1 month" if count == 1 else f"{count} months"


def _years(count: int) -> str:
    return "1 year" if count == 1 else f"{count} years"


def price_headline(price: WithdrawalPrice) -> Headline:
    """For a withdrawal with no loan alternative: what each rand costs."""
    deductions = f"{rands(price.tax_now)} tax"
    if price.admin_fee:
        deductions += f" and a {rands(price.admin_fee)} fee"
    return Headline(
        title=(
            f"Every R1 you take out today costs you R{price.cost_per_rand:.2f} "
            "of retirement money."
        ),
        detail=(
            f"You withdraw {rands(price.gross)} and, after {deductions}, receive "
            f"{rands(price.net_cash)}. Left alone for {_years(price.years_to_retirement)}, "
            f"that money would have been worth {rands(price.forgone_after_tax)} at "
            "retirement, in today's money."
        ),
    )


def comparison_headline(result: Comparison) -> Headline:
    """For a withdrawal that replaces a loan: which is cheaper, and on what condition."""
    hole = result.price.forgone_after_tax
    instalment = result.loan.instalment
    term = _months(result.loan.term_months)

    if result.put_back is PutBack.SPEND or result.share_saved == 0:
        return Headline(
            title=(
                "Withdraw instead of borrowing, spend what you save on instalments, "
                f"and you retire {rands(hole)} poorer."
            ),
            detail=(
                f"The loan would cost {rands(instalment)} a month for {term}. "
                f"Skipping it feels free, but the {rands(result.price.gross)} you take "
                f"out would have grown to {rands(hole)} by retirement, in today's money."
            ),
        )

    if result.advantage_if_all_saved < 0:
        if result.break_even_loan_cost is None:
            threshold = "No loan is expensive enough for withdrawing to win."
        else:
            threshold = (
                "Withdrawing only wins against loans costing more than "
                f"{percent(result.break_even_loan_cost)} a year."
            )
        return Headline(
            title=(
                "Take the loan. Even if you saved every instalment you avoid, "
                f"withdrawing leaves you {rands(-result.advantage_if_all_saved)} "
                "poorer at retirement."
            ),
            detail=(
                f"This loan costs {percent(result.loan_cost)} a year all-in. "
                f"{threshold}"
            ),
        )

    needed = result.break_even_share * instalment
    if result.advantage >= 0:
        return Headline(
            title=(
                "Withdrawing beats this loan, as long as you really save "
                f"{rands(result.monthly_saving)} a month for {term}."
            ),
            detail=(
                f"You would retire {rands(result.advantage)} better off, in today's "
                f"money. You need to save at least {result.break_even_share:.0%} of "
                f"each instalment you avoid ({rands(needed)} a month) to come out "
                f"ahead. Spend it instead and you retire {rands(hole)} poorer."
            ),
        )

    return Headline(
        title=(
            "Withdrawing only beats this loan if you save at least "
            f"{result.break_even_share:.0%} of the instalments you avoid."
        ),
        detail=(
            f"That is {rands(needed)} a month for {term}. At the "
            f"{result.share_saved:.0%} you plan to save, you retire "
            f"{rands(-result.advantage)} poorer, in today's money."
        ),
    )
