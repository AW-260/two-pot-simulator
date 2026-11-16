import pytest

from twopot.rates import Basis, BasisMismatchError, Rate


def test_comparing_real_with_nominal_raises():
    real, nominal = Rate.real(0.05), Rate.nominal(0.05)
    for compare in (
        lambda: real < nominal,
        lambda: real <= nominal,
        lambda: real > nominal,
        lambda: real >= nominal,
    ):
        with pytest.raises(BasisMismatchError):
            compare()


def test_same_basis_compares_normally():
    assert Rate.real(0.04) < Rate.real(0.05)
    assert Rate.nominal(0.28) > Rate.nominal(0.21)
    assert Rate.real(0.04) >= Rate.real(0.04)


def test_fisher_conversion():
    # 4% real with 3% inflation is 7.12% in money terms, not 7%.
    nominal = Rate.real(0.04).to_nominal(0.03)
    assert nominal.basis is Basis.NOMINAL
    assert nominal.value == pytest.approx(1.04 * 1.03 - 1)


def test_conversion_round_trip():
    back = Rate.nominal(0.2825).to_real(0.03).to_nominal(0.03)
    assert back.value == pytest.approx(0.2825)
    assert back.basis is Basis.NOMINAL


def test_converting_to_own_basis_changes_nothing():
    rate = Rate.real(0.04)
    assert rate.to_real(0.03) is rate


def test_quoted_monthly_rate_becomes_effective():
    # 12% a year charged monthly is 1% a month, which compounds to 12.68%.
    assert Rate.from_quoted_monthly(0.12).value == pytest.approx(1.01**12 - 1)


def test_require_rejects_wrong_basis():
    with pytest.raises(BasisMismatchError):
        Rate.nominal(0.07).require(Basis.REAL)
    assert Rate.real(0.04).require(Basis.REAL).value == 0.04


def test_growth():
    assert Rate.real(0.04).growth(30) == pytest.approx(1.04**30)
