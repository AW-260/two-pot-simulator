import pytest

from twopot.rates import Basis, BasisMismatchError, Rate
from twopot.solver import bisect, internal_rate_of_return
from twopot.withdrawal import Withdrawal, price_withdrawal

FOUR_PERCENT = Rate.real(0.04)


def base_case(**changes) -> Withdrawal:
    inputs = dict(gross=10_000, taxable_income=300_000, age=35, retirement_age=65)
    inputs.update(changes)
    return Withdrawal(**inputs)


def test_bisect_finds_a_root():
    assert bisect(lambda x: x * x - 2, 0, 2) == pytest.approx(2**0.5)


def test_irr_of_a_simple_loan():
    assert internal_rate_of_return([100, -110]) == pytest.approx(0.10)
    assert internal_rate_of_return([100, -100]) == 0.0


def test_hand_calculation():
    price = price_withdrawal(base_case(), FOUR_PERCENT)
    assert price.tax_now == pytest.approx(2_600)  # 26% band
    assert price.net_cash == pytest.approx(7_400)
    assert price.forgone_before_tax == pytest.approx(10_000 * 1.04**30)
    assert price.exit_tax == 0.0  # well inside the R550,000 tax-free band
    assert price.cost_per_rand == pytest.approx(10_000 * 1.04**30 / 7_400)
    # The tax paid up front is spread over 30 years on top of the 4% return.
    assert price.implied_rate.value == pytest.approx(1.04 * (1 / 0.74) ** (1 / 30) - 1)
    assert price.implied_rate.basis is Basis.REAL


def test_closed_form_matches_numeric_irr():
    price = price_withdrawal(base_case(), FOUR_PERCENT)
    cash_flows = [price.net_cash] + [0.0] * 29 + [-price.forgone_after_tax]
    assert price.implied_rate.value == pytest.approx(internal_rate_of_return(cash_flows))


def test_no_tax_either_side_means_the_rate_is_just_the_return():
    # Income below the threshold: nothing is lost to tax, so the only cost of the
    # withdrawal is the investment return given up.
    price = price_withdrawal(base_case(taxable_income=60_000), FOUR_PERCENT)
    assert price.tax_now == 0.0
    assert price.implied_rate.value == pytest.approx(0.04)


def test_exit_tax_lowers_the_cost():
    # With R600,000 of other lump sums the money given up would have been taxed
    # at 18% on the way out, so less is lost.
    taxed = price_withdrawal(
        base_case(other_lump_sums_at_retirement=600_000), FOUR_PERCENT
    )
    untaxed = price_withdrawal(base_case(), FOUR_PERCENT)
    assert taxed.exit_tax == pytest.approx(0.18 * 10_000 * 1.04**30)
    assert taxed.implied_rate.value == pytest.approx(
        1.04 * (0.82 / 0.74) ** (1 / 30) - 1
    )
    assert taxed.implied_rate < untaxed.implied_rate


def test_rand_cost_is_highest_young_but_rate_is_highest_near_retirement():
    young = price_withdrawal(base_case(age=30), FOUR_PERCENT)
    old = price_withdrawal(base_case(age=60), FOUR_PERCENT)
    assert young.forgone_after_tax > old.forgone_after_tax
    assert old.implied_rate > young.implied_rate


def test_admin_fee_reduces_cash_and_raises_the_rate():
    with_fee = price_withdrawal(base_case(admin_fee=300), FOUR_PERCENT)
    without = price_withdrawal(base_case(), FOUR_PERCENT)
    assert with_fee.net_cash == pytest.approx(7_100)
    assert with_fee.implied_rate > without.implied_rate


def test_nominal_return_is_rejected():
    with pytest.raises(BasisMismatchError):
        price_withdrawal(base_case(), Rate.nominal(0.07))


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        base_case(gross=1_999)
    with pytest.raises(ValueError):
        base_case(age=65)
    with pytest.raises(ValueError):
        price_withdrawal(base_case(gross=2_000, admin_fee=2_000), FOUR_PERCENT)
