"""The tax engine is checked against figures SARS publishes, not against itself."""

import pytest

from twopot import params
from twopot.tax import (
    income_tax,
    progressive_tax,
    rebate,
    retirement_lump_sum_tax,
    tax_on_extra_income,
)

# SARS prints the tax due at the bottom of each band ("44 118 + 26% of taxable
# income above 245 100"). Our code never stores these; it must reproduce them.
SARS_BASE_AMOUNTS = [
    (245_100, 44_118),
    (383_100, 79_998),
    (530_200, 125_599),
    (695_800, 185_215),
    (887_000, 259_783),
    (1_878_600, 666_339),
]


@pytest.mark.parametrize("income, published", SARS_BASE_AMOUNTS)
def test_reproduces_sars_base_amounts(income, published):
    assert progressive_tax(income, params.INCOME_TAX_BRACKETS) == pytest.approx(published)


@pytest.mark.parametrize(
    "age, threshold",
    [
        (40, params.TAX_THRESHOLD_UNDER_65),
        (65, params.TAX_THRESHOLD_65_TO_74),
        (75, params.TAX_THRESHOLD_75_PLUS),
    ],
)
def test_no_tax_at_published_threshold(age, threshold):
    assert income_tax(threshold, age) == pytest.approx(0.0, abs=0.01)
    assert income_tax(threshold + 1_000, age) == pytest.approx(180.0)


def test_rebate_by_age():
    assert rebate(30) == 17_820
    assert rebate(65) == 17_820 + 9_765
    assert rebate(80) == 17_820 + 9_765 + 3_249


def test_income_tax_hand_calculation():
    # R400,000 at age 40: 79,998 + 31% of (400,000 - 383,100) - 17,820
    assert income_tax(400_000, 40) == pytest.approx(79_998 + 0.31 * 16_900 - 17_820)


def test_income_tax_never_negative():
    assert income_tax(0, 30) == 0.0
    assert income_tax(50_000, 30) == 0.0


def test_withdrawal_inside_one_band_is_taxed_at_that_rate():
    assert tax_on_extra_income(10_000, 300_000, 40) == pytest.approx(2_600)


def test_withdrawal_straddling_two_bands():
    # R380,000 + R10,000: R3,100 falls in the 26% band and R6,900 in the 31% band.
    expected = 3_100 * 0.26 + 6_900 * 0.31
    assert tax_on_extra_income(10_000, 380_000, 40) == pytest.approx(expected)


def test_withdrawal_below_the_threshold_is_untaxed():
    assert tax_on_extra_income(10_000, 60_000, 40) == 0.0


def test_withdrawal_crossing_the_threshold_is_taxed_only_above_it():
    # R95,000 + R10,000 = R105,000, which is R6,000 above the R99,000 threshold.
    assert tax_on_extra_income(10_000, 95_000, 40) == pytest.approx(6_000 * 0.18)


@pytest.mark.parametrize(
    "lump_sum, published",
    [(550_000, 0), (770_000, 39_600), (1_155_000, 143_550)],
)
def test_reproduces_sars_lump_sum_base_amounts(lump_sum, published):
    assert retirement_lump_sum_tax(lump_sum) == pytest.approx(published)


def test_lump_sum_tax_counts_earlier_lump_sums():
    # R500,000 taken earlier, R100,000 now: only R50,000 of it is above R550,000.
    assert retirement_lump_sum_tax(100_000, prior_lump_sums=500_000) == pytest.approx(9_000)


def test_negative_amounts_are_rejected():
    with pytest.raises(ValueError):
        progressive_tax(-1, params.INCOME_TAX_BRACKETS)
    with pytest.raises(ValueError):
        tax_on_extra_income(-1, 100_000, 40)
    with pytest.raises(ValueError):
        retirement_lump_sum_tax(-1)
