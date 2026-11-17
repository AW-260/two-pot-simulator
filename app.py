"""Streamlit front end. All calculation lives in the ``twopot`` package.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Streamlit Community Cloud installs requirements.txt but not this package, so
# fall back to importing it straight from the source folder.
try:
    import twopot  # noqa: F401
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from twopot import params
from twopot.compare import PutBack, Scenario, compare
from twopot.headline import comparison_headline, percent, price_headline, rands
from twopot.loan import CreditType, max_initiation_fee, max_quoted_rate
from twopot.params import Source
from twopot.rates import Rate
from twopot.withdrawal import Withdrawal, price_withdrawal

st.set_page_config(page_title="Two-pot: the loan from your future self")

CREDIT_LABELS = {
    CreditType.UNSECURED: "Personal loan (unsecured)",
    CreditType.CREDIT_FACILITY: "Credit card or overdraft",
    CreditType.SHORT_TERM: "Short-term loan",
}
PLAN_LABELS = {
    PutBack.SPEND: "Spend them",
    PutBack.SAVE_AFTER_TAX: "Save them (after-tax savings)",
    PutBack.FUND_CONTRIBUTIONS: "Pay them into my retirement fund",
}

UPPER_BOUND_NOTE = (
    "Paying into your fund is an upper bound: two-thirds of new contributions "
    "are locked in until retirement and must buy a pension, so this money is "
    "less flexible than the savings-pot money it replaces."
)

_PLAIN_WORDS = {
    "nca": "credit law",
    "tfsa": "tax-free savings",
    "pct": "percentage",
    "min": "minimum",
    "max": "maximum",
}


def _plain_name(constant: str) -> str:
    """'NCA_INITIATION_FEE_CAP' -> 'credit law initiation fee cap'."""
    return " ".join(_PLAIN_WORDS.get(word, word) for word in constant.lower().split("_"))


# --- Inputs ------------------------------------------------------------------
with st.sidebar:
    st.header("You")
    age = st.number_input("Age", 18, 69, 35)
    retirement_age = st.number_input("Retirement age", 55, 70, 65)
    taxable_income = st.number_input(
        "Taxable income this year (R)",
        min_value=0,
        value=300_000,
        step=10_000,
        help="Roughly your annual salary minus your own retirement contributions.",
    )

    st.header("The withdrawal")
    gross = st.number_input(
        "Amount withdrawn from the savings pot (R)",
        min_value=params.MIN_SAVINGS_WITHDRAWAL,
        value=10_000,
        step=1_000,
        help="Before tax. The legal minimum is R2,000, once per tax year.",
    )
    admin_fee = st.number_input(
        "Fund's withdrawal fee (R)",
        min_value=0,
        value=int(params.DEFAULT_ADMIN_FEE),
        step=50,
        help="Funds charge different fees. Check your fund's fee and enter it here.",
    )

    st.header("The alternative")
    borrowing = st.checkbox("Otherwise I would borrow this money", value=True)
    if borrowing:
        credit_type = st.selectbox(
            "Type of credit", list(CREDIT_LABELS), format_func=CREDIT_LABELS.get
        )
        legal_max = max_quoted_rate(credit_type)
        short_term = credit_type is CreditType.SHORT_TERM
        quoted_rate_pct = st.number_input(
            "Interest rate (% a year)",
            min_value=0.0,
            max_value=200.0,
            value=round(legal_max * 100, 2),
            step=0.25,
            key=f"rate_{credit_type.value}",
            help=f"Defaults to the legal maximum for this type, {legal_max:.2%}. "
            "Enter the rate you were actually quoted.",
        )
        term_months = st.number_input(
            "Repaid over (months)",
            min_value=1,
            max_value=84,
            value=6 if short_term else 36,
            key=f"term_{credit_type.value}",
        )
        fee_choice = st.radio(
            "Loan fees",
            ["None", "Legal maximum", "Enter my own"],
            help="The legal maximum is an initiation fee of R165 plus 10% of the "
            "loan above R1,000 (capped at R1,050) and R60 a month.",
        )
        st.caption(
            "The legal maximum is a worst case and makes the loan look as "
            "expensive as the law allows. If you have a quote, enter its fees."
        )
        own_initiation_fee = own_service_fee = 0
        if fee_choice == "Enter my own":
            own_initiation_fee = st.number_input("Initiation fee (R)", 0, 10_000, 0)
            own_service_fee = st.number_input("Monthly service fee (R)", 0, 1_000, 0)

        st.header("The instalments you avoid")
        plan = st.radio(
            "If you withdraw instead of borrowing, what happens to the money "
            "you would have paid in instalments?",
            list(PLAN_LABELS),
            index=1,
            format_func=PLAN_LABELS.get,
        )
        share_saved = 0.0
        if plan is not PutBack.SPEND:
            share_saved = st.slider("Share of each instalment you save (%)", 0, 100, 100) / 100

    with st.expander("Assumptions"):
        real_return_pct = st.number_input(
            "Investment return above inflation, after fees (% a year)",
            min_value=0.0,
            max_value=10.0,
            value=params.DEFAULT_REAL_RETURN * 100,
            step=0.5,
        )
        inflation_pct = st.number_input(
            "Inflation (% a year)",
            min_value=0.0,
            max_value=15.0,
            value=params.DEFAULT_INFLATION * 100,
            step=0.5,
        )
        other_lump_sums = st.number_input(
            "Other cash you expect to take from retirement funds at retirement "
            "(R, today's money)",
            min_value=0,
            value=0,
            step=50_000,
            help="The first R550,000 of retirement cash is tax-free. Other lump "
            "sums use that allowance first.",
        )
        current_contributions = st.number_input(
            "Current retirement contributions (R a year, yours and your employer's)",
            min_value=0,
            value=0,
            step=5_000,
            help="Only used to check the tax-deduction limit on extra contributions.",
        )

# --- Calculation -------------------------------------------------------------
real_return = Rate.real(real_return_pct / 100)
inflation = inflation_pct / 100

try:
    withdrawal = Withdrawal(
        gross=gross,
        taxable_income=taxable_income,
        age=age,
        retirement_age=retirement_age,
        admin_fee=admin_fee,
        other_lump_sums_at_retirement=other_lump_sums,
    )
    price = price_withdrawal(withdrawal, real_return)
    result = None
    if borrowing:
        if fee_choice == "Legal maximum":
            initiation_fee = max_initiation_fee(price.net_cash)
            service_fee = params.NCA_MAX_MONTHLY_SERVICE_FEE
        else:
            initiation_fee, service_fee = own_initiation_fee, own_service_fee
        scenario = Scenario(
            withdrawal=withdrawal,
            quoted_loan_rate=quoted_rate_pct / 100,
            term_months=term_months,
            real_return=real_return,
            inflation=inflation,
            initiation_fee=initiation_fee,
            monthly_service_fee=service_fee,
            current_contributions=current_contributions,
        )
        result = compare(scenario, plan, share_saved)
        all_plans = {
            PutBack.SPEND: compare(scenario, PutBack.SPEND, 0.0),
            PutBack.SAVE_AFTER_TAX: compare(scenario, PutBack.SAVE_AFTER_TAX, 1.0),
            PutBack.FUND_CONTRIBUTIONS: compare(scenario, PutBack.FUND_CONTRIBUTIONS, 1.0),
        }
except ValueError as problem:
    st.error(f"These inputs do not work together: {problem}.")
    st.stop()

# --- Headline ----------------------------------------------------------------
st.caption("South Africa's two-pot system · a withdrawal priced as a loan from your future self")
headline = comparison_headline(result) if result else price_headline(price)
st.title(headline.title)
st.write(headline.detail)
if result:
    if plan is PutBack.FUND_CONTRIBUTIONS:
        st.info(UPPER_BOUND_NOTE)
    for warning in result.warnings:
        st.warning(warning)

# --- The withdrawal ----------------------------------------------------------
st.subheader("What the withdrawal gives and takes")
left, middle, right = st.columns(3)
left.metric("Cash in your hand", rands(price.net_cash))
middle.metric(
    "Lost to tax and fees today",
    rands(price.tax_now + price.admin_fee),
    help=f"Tax of {rands(price.tax_now)} ({price.tax_rate_now:.0%} of the withdrawal) "
    f"plus a fee of {rands(price.admin_fee)}.",
)
right.metric(
    "Retirement money given up",
    rands(price.forgone_after_tax),
    help="What the withdrawal would have been worth at retirement, after tax, "
    "in today's money.",
)
st.write(
    f"Seen as a loan from your future self, repaid at retirement in "
    f"{price.years_to_retirement} years, this costs **{percent(price.implied_rate)} "
    f"a year above inflation**, or "
    f"{percent(price.implied_rate.to_nominal(inflation))} a year in money terms."
)

# --- The comparison ----------------------------------------------------------
if result:
    st.subheader("Against the loan")
    left, middle, right = st.columns(3)
    left.metric("Instalment you avoid", f"{rands(result.loan.instalment)} a month")
    middle.metric(
        "This loan's all-in cost",
        f"{percent(result.loan_cost)} a year",
        help="Interest and fees together, as an effective annual rate in money "
        f"terms. That is {percent(result.loan_cost.to_real(inflation))} above inflation.",
    )
    selected = all_plans[plan] if plan is not PutBack.SPEND else None
    if selected and selected.break_even_loan_cost is not None:
        right.metric(
            "Withdrawing wins above",
            f"{percent(selected.break_even_loan_cost)} a year",
            help="If you save every instalment you avoid, withdrawing beats any "
            "loan with an all-in cost above this. Same basis and same term as "
            "the loan's cost, so the two can be compared directly.",
        )
    else:
        right.metric("Withdrawing wins above", "Never")

    st.write("**How the answer depends on what you do with the avoided instalments**")
    table = [
        "| If you | Withdrawing wins if the loan costs more than | "
        "At retirement, versus taking this loan |",
        "|---|---|---|",
    ]
    for put_back, outcome in all_plans.items():
        break_even = outcome.break_even_loan_cost
        threshold = f"{percent(break_even)} a year" if break_even is not None else "Never"
        verdict = "better off" if outcome.advantage >= 0 else "poorer"
        label = PLAN_LABELS[put_back]
        if put_back is PutBack.FUND_CONTRIBUTIONS:
            label += " (upper bound)"
        table.append(
            f"| {label} | {threshold} | {rands(abs(outcome.advantage))} {verdict} |"
        )
    st.markdown("\n".join(table))
    st.caption(
        "Rows two and three assume you save every rand of every instalment. "
        f"{UPPER_BOUND_NOTE} Retirement amounts are in today's money. Loan costs "
        "are effective annual rates in money terms, over the loan's own term."
    )

# --- Method and sources ------------------------------------------------------
with st.expander("How this is calculated"):
    st.markdown(
        f"""
- **Today:** the withdrawal is added to your taxable income and taxed at your
  marginal rate. There is no tax-free amount.
- **At retirement:** the same money, left invested, would have come out on the
  retirement lump-sum table, where the first R550,000 is tax-free.
- **Growth:** {real_return_pct:.1f}% a year above inflation, so every retirement
  figure is in today's money.
- **The loan:** its all-in cost is the single rate that accounts for interest and
  fees together.
- **The comparison:** withdrawing and borrowing are judged on retirement money,
  after allowing for what you do with the instalments you avoid. Instalments are
  fixed in rands, so they are adjusted for {inflation_pct:.1f}% inflation before
  being compared with real growth.
- **Paying into your fund** assumes the extra contributions are tax-deductible
  and can be taken as cash at retirement. In practice two-thirds of new
  contributions are locked in until retirement and must buy a pension.
- **Tax tables** are assumed to rise with inflation in future. They have been
  frozen in some recent years, which would make withdrawing dearer than shown.
"""
    )

with st.expander("Figures and sources"):
    st.write("Tax year 2026/27. Published figures, grouped by where they were read:")
    by_source: dict[Source, list[str]] = {}
    assumptions = []
    for name, origin in params.PROVENANCE.items():
        if isinstance(origin, Source):
            by_source.setdefault(origin, []).append(_plain_name(name))
        else:
            assumptions.append(f"- **{_plain_name(name).capitalize()}:** {origin.rationale}")
    st.markdown(
        "\n".join(
            f"- [{source.name}]({source.url}), read {source.accessed}: "
            f"{', '.join(names)}."
            for source, names in by_source.items()
        )
    )
    st.write("Assumptions you can change in the sidebar:")
    st.markdown("\n".join(assumptions))

st.caption(
    "An educational model, not financial advice. It uses one fixed investment "
    "return and ignores investment risk."
)
