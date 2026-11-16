import pytest

from twopot import params
from twopot.loan import CreditType, Loan, max_initiation_fee, max_quoted_rate
from twopot.rates import Basis, Rate


def test_instalment_matches_the_annuity_formula():
    # R10,000 at 12% a year over 12 months: the textbook answer is R888.49.
    assert Loan(10_000, 0.12, 12).instalment == pytest.approx(888.49, abs=0.01)


def test_interest_free_loan():
    loan = Loan(12_000, 0.0, 12)
    assert loan.instalment == pytest.approx(1_000)
    assert loan.effective_cost().value == pytest.approx(0.0, abs=1e-9)


def test_cost_without_fees_is_the_quoted_rate_compounded():
    cost = Loan(10_000, 0.2825, 36).effective_cost()
    assert cost.basis is Basis.NOMINAL
    assert cost.value == pytest.approx(Rate.from_quoted_monthly(0.2825).value)


def test_fees_raise_the_all_in_cost():
    plain = Loan(7_400, 0.2825, 36)
    with_fees = Loan(7_400, 0.2825, 36, initiation_fee=805, monthly_service_fee=60)
    assert with_fees.instalment > plain.instalment
    assert with_fees.effective_cost() > plain.effective_cost()


def test_total_repaid():
    loan = Loan(10_000, 0.12, 12)
    assert loan.total_repaid == pytest.approx(loan.instalment * 12)


def test_legal_rate_caps_follow_the_repo_rate():
    assert max_quoted_rate(CreditType.UNSECURED) == pytest.approx(params.REPO_RATE + 0.21)
    assert max_quoted_rate(CreditType.CREDIT_FACILITY) == pytest.approx(
        params.REPO_RATE + 0.14
    )
    assert max_quoted_rate(CreditType.SHORT_TERM) == pytest.approx(0.60)


@pytest.mark.parametrize(
    "principal, fee",
    [(500, 165), (1_000, 165), (7_400, 805), (9_850, 1_050), (50_000, 1_050)],
)
def test_initiation_fee_cap(principal, fee):
    assert max_initiation_fee(principal) == pytest.approx(fee)


def test_invalid_loans_are_rejected():
    with pytest.raises(ValueError):
        Loan(0, 0.2, 12)
    with pytest.raises(ValueError):
        Loan(1_000, -0.1, 12)
    with pytest.raises(ValueError):
        Loan(1_000, 0.2, 0)
