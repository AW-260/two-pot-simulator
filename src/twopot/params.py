"""Every number the model relies on, and where it came from.

Rule: each UPPER_CASE constant in this module must appear in PROVENANCE, either
with a Source (a published figure) or an Assumption (a modelling choice the user
can change). tests/test_params.py fails if one is missing, so an unsourced
statistic cannot slip into the model.

All rand amounts are for the 2026/27 tax year (1 March 2026 to 28 February 2027).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import inf


@dataclass(frozen=True)
class Source:
    """A published figure: who published it, where, and when we read it."""

    name: str
    url: str
    accessed: str  # ISO date


@dataclass(frozen=True)
class Assumption:
    """A modelling choice, not a fact. Always adjustable in the app."""

    rationale: str


_ACCESSED = "2026-11-16"

SARS_RATES = Source(
    "SARS, Rates of tax for individuals (2027 tax year)",
    "https://www.sars.gov.za/tax-rates/income-tax/rates-of-tax-for-individuals/",
    _ACCESSED,
)
SARS_LUMP_SUMS = Source(
    "SARS, Retirement lump sum benefits (2027 tax year)",
    "https://www.sars.gov.za/tax-rates/income-tax/retirement-lump-sum-benefits/",
    _ACCESSED,
)
SARS_TWO_POT = Source(
    "SARS, Tax directives enhancements and tax implications of the two-pot "
    "retirement system (2 September 2024)",
    "https://www.sars.gov.za/latest-news/tax-directives-enhancements-and-tax-"
    "implications-of-the-two-pot-retirement-system/",
    _ACCESSED,
)
NCA_REG_42 = Source(
    "National Credit Regulations, reg. 42, Tables A and B (as amended by "
    "GN 1080, GG 39379, 6 November 2015)",
    "https://www.acts.co.za/national-credit/"
    "r489_42__maximum_prescribed_interest_and_initiation_fees",
    _ACCESSED,
)
NCA_REG_44 = Source(
    "National Credit Regulations, reg. 44 (maximum service fee)",
    "https://www.acts.co.za/national-credit/r489_44__maximum_service_fee",
    _ACCESSED,
)
SANEWS_REPO = Source(
    "SAnews, MPC raises repo rate to 7.25% (September 2026)",
    "https://www.sanews.gov.za/south-africa/mpc-raises-repo-rate-725",
    _ACCESSED,
)
SANLAM_FUND_VALUES = Source(
    "Sanlam, Key retirement fund values and changes effective 1 March 2026",
    "https://seb-news.sanlam.co.za/consultant-toolkit/"
    "key-retirement-fund-values-and-changes-effective-1-march-2026/",
    _ACCESSED,
)
MOONSTONE_TFSA = Source(
    "Moonstone, Changes to CGT, tax-free savings, retirement contributions, "
    "and donations (Budget 2026)",
    "https://www.moonstone.co.za/"
    "changes-to-cgt-tax-free-savings-retirement-contributions-and-donations/",
    _ACCESSED,
)

# --- Income tax, 2026/27 -----------------------------------------------------
# (upper limit of band, rate charged on income inside the band)
INCOME_TAX_BRACKETS = (
    (245_100, 0.18),
    (383_100, 0.26),
    (530_200, 0.31),
    (695_800, 0.36),
    (887_000, 0.39),
    (1_878_600, 0.41),
    (inf, 0.45),
)
PRIMARY_REBATE = 17_820  # everyone
SECONDARY_REBATE = 9_765  # additional, age 65 and older
TERTIARY_REBATE = 3_249  # additional, age 75 and older

# Published thresholds below which no tax is payable. The model derives these
# from brackets and rebates; the published values are kept as a test check.
TAX_THRESHOLD_UNDER_65 = 99_000
TAX_THRESHOLD_65_TO_74 = 153_250
TAX_THRESHOLD_75_PLUS = 171_300

# --- Retirement fund lump sums taken at retirement ---------------------------
# Applied to the running total of lump sums over a lifetime.
RETIREMENT_LUMP_SUM_BRACKETS = (
    (550_000, 0.00),
    (770_000, 0.18),
    (1_155_000, 0.27),
    (inf, 0.36),
)

# --- Two-pot rules -----------------------------------------------------------
MIN_SAVINGS_WITHDRAWAL = 2_000  # per withdrawal; one withdrawal per tax year

# --- Retirement contribution deduction and tax-free savings ------------------
RETIREMENT_DEDUCTION_PCT = 0.275
RETIREMENT_DEDUCTION_CAP = 430_000  # per year, from 1 March 2026
TFSA_ANNUAL_LIMIT = 46_000  # per year, from 1 March 2026

# --- Consumer credit caps (National Credit Act) ------------------------------
REPO_RATE = 0.0725  # effective 25 September 2026; next MPC decision 19 Nov 2026
NCA_UNSECURED_SPREAD = 0.21  # unsecured credit: repo rate + 21% a year
NCA_CREDIT_FACILITY_SPREAD = 0.14  # credit cards, overdrafts: repo rate + 14%
NCA_SHORT_TERM_MONTHLY_RATE = 0.05  # short-term credit, first loan: 5% a month
NCA_INITIATION_FEE_BASE = 165  # unsecured credit
NCA_INITIATION_FEE_THRESHOLD = 1_000
NCA_INITIATION_FEE_PCT_ABOVE = 0.10
NCA_INITIATION_FEE_CAP = 1_050
NCA_MAX_MONTHLY_SERVICE_FEE = 60

# --- Assumptions (defaults the user can change) ------------------------------
DEFAULT_REAL_RETURN = 0.04
DEFAULT_INFLATION = 0.03
DEFAULT_ADMIN_FEE = 0.0

PROVENANCE: dict[str, Source | Assumption] = {
    "INCOME_TAX_BRACKETS": SARS_RATES,
    "PRIMARY_REBATE": SARS_RATES,
    "SECONDARY_REBATE": SARS_RATES,
    "TERTIARY_REBATE": SARS_RATES,
    "TAX_THRESHOLD_UNDER_65": SARS_RATES,
    "TAX_THRESHOLD_65_TO_74": SARS_RATES,
    "TAX_THRESHOLD_75_PLUS": SARS_RATES,
    "RETIREMENT_LUMP_SUM_BRACKETS": SARS_LUMP_SUMS,
    "MIN_SAVINGS_WITHDRAWAL": SARS_TWO_POT,
    "RETIREMENT_DEDUCTION_PCT": SANLAM_FUND_VALUES,
    "RETIREMENT_DEDUCTION_CAP": SANLAM_FUND_VALUES,
    "TFSA_ANNUAL_LIMIT": MOONSTONE_TFSA,
    "REPO_RATE": SANEWS_REPO,
    "NCA_UNSECURED_SPREAD": NCA_REG_42,
    "NCA_CREDIT_FACILITY_SPREAD": NCA_REG_42,
    "NCA_SHORT_TERM_MONTHLY_RATE": NCA_REG_42,
    "NCA_INITIATION_FEE_BASE": NCA_REG_42,
    "NCA_INITIATION_FEE_THRESHOLD": NCA_REG_42,
    "NCA_INITIATION_FEE_PCT_ABOVE": NCA_REG_42,
    "NCA_INITIATION_FEE_CAP": NCA_REG_42,
    "NCA_MAX_MONTHLY_SERVICE_FEE": NCA_REG_44,
    "DEFAULT_REAL_RETURN": Assumption(
        "Investment return above inflation, after fees, for a balanced fund. "
        "A round planning figure, not a forecast and not a published statistic."
    ),
    "DEFAULT_INFLATION": Assumption(
        "The Reserve Bank's 3% inflation target. Used only to convert between "
        "real and money-terms rates."
    ),
    "DEFAULT_ADMIN_FEE": Assumption(
        "Fund administrators charge different withdrawal fees and no current "
        "figure could be verified, so the user enters their own."
    ),
}
