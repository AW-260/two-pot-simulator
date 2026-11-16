"""The comparison is checked against cases where the answer is known exactly."""

import pytest

from twopot.compare import PutBack, Scenario, compare, gross_up_for_deduction
from twopot.rates import Basis, Rate
from twopot.withdrawal import Withdrawal

REAL_RETURN = Rate.real(0.04)
INFLATION = 0.03
FUND_RETURN_IN_MONEY_TERMS = REAL_RETURN.to_nominal(INFLATION)  # 7.12%


def scenario(**changes) -> Scenario:
    withdrawal = dict(gross=10_000, taxable_income=300_000, age=35, retirement_age=65)
    loan = dict(quoted_loan_rate=0.2825, term_months=36)
    for key in list(changes):
        if key in ("gross", "taxable_income", "age", "retirement_age",
                   "admin_fee", "other_lump_sums_at_retirement"):
            withdrawal[key] = changes.pop(key)
    loan.update(changes)
    return Scenario(
        withdrawal=Withdrawal(**withdrawal),
        real_return=REAL_RETURN,
        inflation=INFLATION,
        **loan,
    )


def test_no_tax_and_no_fees_break_even_is_the_fund_return():
    # Below the tax threshold nothing is lost to tax, so withdrawing and saving
    # the instalments beats a loan exactly when the loan costs more than the
    # fund earns. Both sides of the comparison are in money terms.
    result = compare(scenario(taxable_income=60_000), PutBack.SAVE_AFTER_TAX, 1.0)
    assert result.price.tax_now == 0.0
    assert result.break_even_loan_cost.basis is Basis.NOMINAL
    assert result.break_even_loan_cost.value == pytest.approx(
        FUND_RETURN_IN_MONEY_TERMS.value, abs=1e-6
    )


def test_deductible_contributions_recover_the_tax_paid():
    # In the 26% band, each R0.74 of take-home buys R1 in the fund, which is
    # exactly what the withdrawal cost. So the break-even is again the fund return.
    result = compare(scenario(), PutBack.FUND_CONTRIBUTIONS, 1.0)
    assert result.break_even_loan_cost.value == pytest.approx(
        FUND_RETURN_IN_MONEY_TERMS.value, abs=1e-6
    )


def test_after_tax_saving_needs_a_far_more_expensive_loan():
    # The 26% tax paid on the withdrawal is never recovered, and it has only the
    # three-year loan term to be made up. The break-even all-in cost is 32.6%.
    result = compare(scenario(), PutBack.SAVE_AFTER_TAX, 1.0)
    assert result.break_even_loan_cost.value == pytest.approx(0.326, abs=0.001)
    assert result.break_even_loan_cost > FUND_RETURN_IN_MONEY_TERMS


def test_break_even_does_not_depend_on_age():
    # Growth to retirement multiplies both the hole and the savings that refill
    # it, so it cancels. Only exit tax could break this.
    costs = [
        compare(scenario(age=age), PutBack.SAVE_AFTER_TAX, 1.0).break_even_loan_cost.value
        for age in (25, 45, 60)
    ]
    assert costs[0] == pytest.approx(costs[1]) == pytest.approx(costs[2])


def test_spending_the_instalments_leaves_the_whole_hole():
    result = compare(scenario(), PutBack.SPEND, 0.0)
    assert result.advantage == pytest.approx(-result.price.forgone_after_tax)
    assert result.break_even_share is None
    assert result.break_even_loan_cost is None
    assert not result.withdrawing_wins


def test_break_even_share_gives_zero_advantage():
    s = scenario(quoted_loan_rate=0.60)
    result = compare(s, PutBack.SAVE_AFTER_TAX, 1.0)
    assert 0 < result.break_even_share < 1
    at_break_even = compare(s, PutBack.SAVE_AFTER_TAX, result.break_even_share)
    assert at_break_even.advantage == pytest.approx(0.0, abs=0.01)


def test_saving_more_always_helps():
    s = scenario()
    advantages = [
        compare(s, PutBack.FUND_CONTRIBUTIONS, share).advantage
        for share in (0.0, 0.25, 0.5, 0.75, 1.0)
    ]
    assert advantages == sorted(advantages)


@pytest.mark.parametrize("put_back", [PutBack.SAVE_AFTER_TAX, PutBack.FUND_CONTRIBUTIONS])
def test_verdict_agrees_with_the_break_even_rate(put_back):
    for quoted_rate in (0.05, 0.15, 0.2825, 0.60):
        result = compare(scenario(quoted_loan_rate=quoted_rate), put_back, 1.0)
        loan_is_dearer = result.loan_cost > result.break_even_loan_cost
        assert loan_is_dearer == (result.advantage_if_all_saved > 0)


def test_when_saving_everything_is_not_enough():
    result = compare(scenario(quoted_loan_rate=0.15), PutBack.SAVE_AFTER_TAX, 1.0)
    assert result.advantage_if_all_saved < 0
    assert result.break_even_share is None


def test_fees_raise_the_loan_cost_but_not_the_break_even():
    # The break-even is an all-in cost, so it does not care how a lender splits
    # the instalment between interest and fees. The loan's own cost does.
    plain = compare(scenario(), PutBack.SAVE_AFTER_TAX, 1.0)
    with_fees = compare(
        scenario(initiation_fee=805, monthly_service_fee=60), PutBack.SAVE_AFTER_TAX, 1.0
    )
    assert with_fees.break_even_loan_cost.value == pytest.approx(
        plain.break_even_loan_cost.value, abs=1e-6
    )
    assert with_fees.loan_cost > plain.loan_cost
    assert plain.advantage_if_all_saved < 0 < with_fees.advantage_if_all_saved


def test_exit_tax_can_make_withdrawing_beat_an_interest_free_loan():
    # No tax now (income under the threshold) but 18% tax at retirement, because
    # other lump sums have used up the tax-free band. Money left in the fund is
    # then worth less than money taken out.
    result = compare(
        scenario(taxable_income=60_000, other_lump_sums_at_retirement=600_000),
        PutBack.SAVE_AFTER_TAX,
        1.0,
    )
    assert result.break_even_loan_cost.value == 0.0
    assert result.withdrawing_wins


def test_gross_up_inside_one_band():
    assert gross_up_for_deduction(740, 300_000, 40) == pytest.approx(1_000)


def test_gross_up_below_the_threshold_is_nothing():
    assert gross_up_for_deduction(740, 60_000, 40) == pytest.approx(740)


def test_gross_up_at_the_top_rate():
    assert gross_up_for_deduction(5_500, 3_000_000, 40) == pytest.approx(10_000)


def test_tax_free_savings_limit_warning():
    big = scenario(gross=200_000, quoted_loan_rate=0.2825, term_months=24)
    result = compare(big, PutBack.SAVE_AFTER_TAX, 1.0)
    assert any("tax-free savings limit" in note for note in result.warnings)
    assert not compare(scenario(), PutBack.SAVE_AFTER_TAX, 1.0).warnings


def test_deduction_limit_warning():
    # Limit is 27.5% of (300,000 + 110,000) = R112,750; the extra ~R5,000 tips it over.
    near_limit = scenario(current_contributions=110_000)
    result = compare(near_limit, PutBack.FUND_CONTRIBUTIONS, 1.0)
    assert any("deductible limit" in note for note in result.warnings)
    assert not compare(scenario(), PutBack.FUND_CONTRIBUTIONS, 1.0).warnings


def test_invalid_scenarios_are_rejected():
    with pytest.raises(ValueError):
        scenario(age=64, term_months=36)
    with pytest.raises(ValueError):
        compare(scenario(), PutBack.SAVE_AFTER_TAX, 1.5)
