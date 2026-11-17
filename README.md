# Two-pot withdrawal: the loan from your future self

South Africa's two-pot retirement system lets fund members withdraw from their
savings pot once a tax year. This tool prices that withdrawal as a loan: you
receive the after-tax cash today and repay it with the retirement money you give
up. It then answers the question people actually face: **is withdrawing cheaper
than the loan I would otherwise take?**

**Try it: https://two-pot-simulator.streamlit.app/**

## What it finds

The answer depends less on the loan than on what you do with the instalments you
avoid by not borrowing.

For someone earning R300,000 who withdraws R10,000 instead of taking a 36-month
loan:

| If you | Withdrawing wins if the loan's all-in cost is above |
|---|---|
| Spend the avoided instalments | Never. You retire R32,434 poorer (age 35, today's money) |
| Save them after tax | 32.6% a year |
| Pay them back into your retirement fund (upper bound) | 7.1% a year, the fund's own return |

The 32.6% rises with your tax band (23.0% on R150,000, 48.4% on R600,000),
because the tax paid on the withdrawal is never recovered. A loan at the legal
maximum rate of 28.25% costs 32.2% a year all-in without fees and 63.2% with the
maximum legal fees, so the same withdrawal can be the better or the worse choice
depending on the loan's fees and on the member's discipline.

The last row is an upper bound: two-thirds of new contributions are locked in
until retirement and must buy a pension, so that money is less flexible than the
savings-pot money it replaces.

These figures assume a 4% real return and 3% inflation. Both can be changed in
the app.

## How it works

- **Tax today:** the withdrawal is added to taxable income and taxed at the
  marginal rate, using the 2026/27 SARS tables.
- **Tax at retirement:** the same money would have come out on the retirement
  lump-sum table, where the first R550,000 is tax-free.
- **Like for like:** the model works in today's rands. Every rate is tagged real
  or nominal, and the code refuses to compare one with the other. Loan costs are
  all-in effective rates, compared over the loan's own term.
- **Sourced inputs:** every constant sits in
  [src/twopot/params.py](src/twopot/params.py) with its source and the date it
  was read. A test fails if a constant has neither a source nor a stated
  assumption.

## Run it

Requires Python 3.10 or newer.

```
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
pytest
streamlit run app.py
```

## Limitations

- One fixed investment return; investment risk is not modelled yet.
- Tax tables are assumed to rise with inflation.
- The savings pot is assumed to be taken as cash at retirement.
- Paying instalments back into the fund is treated as fully deductible and
  accessible at retirement. In practice two-thirds of new contributions are
  locked in and must buy a pension.
- A fund's withdrawal fee is a user input; no reliable industry figure was found.

This is an educational model, not financial advice.

## Status

Version 1: tax engine, single-withdrawal pricing, loan comparison and a simple
app, deployed on Streamlit Community Cloud. Planned: repeated annual withdrawals
and uncertain investment returns.
