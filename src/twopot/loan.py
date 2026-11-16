"""A level-instalment consumer loan and the legal caps on its cost.

South African loan rates are quoted per year and charged monthly, in money terms.
Fees matter as much as the rate on a small loan, so the cost reported here is the
all-in effective annual rate: the rate that equates the cash received with every
payment made, fees included.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from twopot import params
from twopot.rates import Rate
from twopot.solver import internal_rate_of_return


class CreditType(str, Enum):
    UNSECURED = "unsecured"
    CREDIT_FACILITY = "credit_facility"
    SHORT_TERM = "short_term"


def max_quoted_rate(credit_type: CreditType) -> float:
    """Highest annual rate a lender may quote under the National Credit Act."""
    if credit_type is CreditType.UNSECURED:
        return params.REPO_RATE + params.NCA_UNSECURED_SPREAD
    if credit_type is CreditType.CREDIT_FACILITY:
        return params.REPO_RATE + params.NCA_CREDIT_FACILITY_SPREAD
    return params.NCA_SHORT_TERM_MONTHLY_RATE * 12


def max_initiation_fee(principal: float) -> float:
    """Highest once-off fee a lender may charge on an unsecured loan."""
    above = max(0.0, principal - params.NCA_INITIATION_FEE_THRESHOLD)
    fee = params.NCA_INITIATION_FEE_BASE + params.NCA_INITIATION_FEE_PCT_ABOVE * above
    return min(fee, params.NCA_INITIATION_FEE_CAP)


@dataclass(frozen=True)
class Loan:
    principal: float  # cash the borrower receives
    quoted_rate: float  # per year, charged monthly, money terms
    term_months: int
    initiation_fee: float = 0.0  # added to the balance and repaid with interest
    monthly_service_fee: float = 0.0

    def __post_init__(self) -> None:
        if self.principal <= 0 or self.term_months < 1:
            raise ValueError("a loan needs a positive amount and term")
        if self.quoted_rate < 0 or self.initiation_fee < 0 or self.monthly_service_fee < 0:
            raise ValueError("rate and fees cannot be negative")

    @property
    def instalment(self) -> float:
        """Level monthly payment, in the rands of the month it is paid."""
        financed = self.principal + self.initiation_fee
        j = self.quoted_rate / 12
        if j == 0:
            repayment = financed / self.term_months
        else:
            repayment = financed * j / (1 - (1 + j) ** -self.term_months)
        return repayment + self.monthly_service_fee

    @property
    def total_repaid(self) -> float:
        return self.instalment * self.term_months

    def effective_cost(self) -> Rate:
        """All-in cost as an effective annual rate in money terms."""
        return all_in_cost(self.principal, self.instalment, self.term_months)


def all_in_cost(cash_received: float, instalment: float, term_months: int) -> Rate:
    """Effective annual cost of receiving cash and repaying level instalments.

    It depends only on the cash flows, not on how the lender splits them between
    interest and fees. That makes it the right yardstick for comparing loans.
    """
    cash_flows = [cash_received] + [-instalment] * term_months
    monthly = internal_rate_of_return(cash_flows)
    return Rate.nominal((1 + monthly) ** 12 - 1)
