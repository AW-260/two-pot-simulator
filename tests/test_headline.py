"""Each branch of the headline, on a case whose verdict is known."""

from twopot.compare import PutBack, Scenario, compare
from twopot.headline import comparison_headline, price_headline, rands
from twopot.rates import Rate
from twopot.withdrawal import Withdrawal, price_withdrawal

WITHDRAWAL = Withdrawal(gross=10_000, taxable_income=300_000, age=35, retirement_age=65)


def scenario(quoted_loan_rate: float, **fees) -> Scenario:
    return Scenario(
        withdrawal=WITHDRAWAL,
        quoted_loan_rate=quoted_loan_rate,
        term_months=36,
        real_return=Rate.real(0.04),
        inflation=0.03,
        **fees,
    )


def test_rands_format():
    assert rands(12_345.6) == "R12,346"


def test_price_headline_states_cost_per_rand():
    headline = price_headline(price_withdrawal(WITHDRAWAL, Rate.real(0.04)))
    assert "Every R1" in headline.title and "R4.38" in headline.title
    assert "R2,600 tax" in headline.detail and "R7,400" in headline.detail
    assert "30 years" in headline.detail and "R32,434" in headline.detail


def test_price_headline_mentions_a_fee_only_when_there_is_one():
    with_fee = Withdrawal(10_000, 300_000, 35, 65, admin_fee=300)
    assert "R300 fee" in price_headline(price_withdrawal(with_fee, Rate.real(0.04))).detail
    assert "fee" not in price_headline(price_withdrawal(WITHDRAWAL, Rate.real(0.04))).detail


def test_spending_the_instalments():
    headline = comparison_headline(compare(scenario(0.2825), PutBack.SPEND, 0.0))
    assert "R32,434 poorer" in headline.title


def test_saving_nothing_reads_the_same_as_spending():
    spend = comparison_headline(compare(scenario(0.2825), PutBack.SPEND, 0.0))
    save_zero = comparison_headline(compare(scenario(0.2825), PutBack.SAVE_AFTER_TAX, 0.0))
    assert spend == save_zero


def test_cheap_loan_says_take_the_loan():
    headline = comparison_headline(compare(scenario(0.15), PutBack.SAVE_AFTER_TAX, 1.0))
    assert headline.title.startswith("Take the loan.")
    assert "32.6%" in headline.detail  # the break-even all-in cost


def test_expensive_loan_and_full_saving_says_withdrawing_wins():
    result = compare(
        scenario(0.2825, initiation_fee=805, monthly_service_fee=60),
        PutBack.SAVE_AFTER_TAX,
        1.0,
    )
    headline = comparison_headline(result)
    assert headline.title.startswith("Withdrawing beats this loan")
    assert "R400 a month for 36 months" in headline.title
    assert "77%" in headline.detail


def test_expensive_loan_but_too_little_saved():
    result = compare(
        scenario(0.2825, initiation_fee=805, monthly_service_fee=60),
        PutBack.SAVE_AFTER_TAX,
        0.5,
    )
    headline = comparison_headline(result)
    assert headline.title.startswith("Withdrawing only beats this loan if you save at least 77%")
    assert "50% you plan to save" in headline.detail
    assert "poorer" in headline.detail
