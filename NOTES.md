# Project notes

Working notes: decisions, sources, assumptions and how each part works.
The README is for visitors; this file is for me.

## What this project is

South Africa's two-pot system lets retirement fund members withdraw from their
savings pot once a tax year. This tool prices a withdrawal as **a loan from your
future self**: you receive the after-tax cash today and "repay" the retirement
money you give up. It then compares that with the loan you would otherwise take.

Why this angle: Alexforbes' *Member Insights 2026* (14 October 2026) already
published the headline cost of habitual withdrawal. Its replacement ratio falls
from 76.5% to 51%, which is exactly two-thirds, because the savings pot is always
one-third of contributions. That result needs no model. The open question is what
the member gets in exchange, and compared with what.

## How to resume

- Python 3.10.11, git 2.54 (checked 2026-11-16). Python 3.10 is past end of life;
  it works locally, and the deployed app should use a newer version.
- The virtual environment is **outside OneDrive** so it is not synced:
  `%USERPROFILE%\.venvs\two-pot-simulator`
- Activate it (PowerShell): `& "$env:USERPROFILE\.venvs\two-pot-simulator\Scripts\Activate.ps1"`
- Install after cloning or after changing dependencies: `pip install -e ".[dev]"`
- Run the tests: `pytest`
- Launch the app: `streamlit run app.py`
- The repo lives in OneDrive. OneDrive syncing `.git` can occasionally lock files;
  pushing to GitHub early is the safeguard.

## Decisions

| Date | Decision | Reason |
|---|---|---|
| 2026-11-16 | Build concept 1, "the loan from your future self" | Most defensible core, smallest build, a finding that is not a replication |
| 2026-11-16 | Version 1 is steps 1 to 4 plus a simple app | Habit model, stochastic layer and deployment come later |
| 2026-11-16 | All comparisons are real-vs-real or nominal-vs-nominal | Enforced in code: rates carry a basis tag and mixing them raises an error |
| 2026-11-16 | The headline comes from the model | My first back-of-envelope compared a 30-year rate with a 3-year loan, which is not like for like |
| 2026-11-16 | Any statistic without a verifiable source is dropped | A test fails if a constant in `params.py` has no source or stated assumption |

## Verified facts used by the model

All read on 2026-11-16. Rand amounts are for the 2026/27 tax year
(1 March 2026 to 28 February 2027), which SARS calls the 2027 tax year.

| Fact | Value | Source |
|---|---|---|
| Income tax bands | 18% to R245,100; 26% to R383,100; 31% to R530,200; 36% to R695,800; 39% to R887,000; 41% to R1,878,600; 45% above | [SARS rates of tax for individuals](https://www.sars.gov.za/tax-rates/income-tax/rates-of-tax-for-individuals/) |
| Rebates | Primary R17,820; secondary (65+) R9,765; tertiary (75+) R3,249 | Same |
| Tax thresholds | R99,000 under 65; R153,250 at 65 to 74; R171,300 at 75+ | Same |
| Retirement lump-sum table | 0% to R550,000; 18% to R770,000; 27% to R1,155,000; 36% above; applied to the lifetime running total | [SARS retirement lump sum benefits](https://www.sars.gov.za/tax-rates/income-tax/retirement-lump-sum-benefits/) |
| Savings withdrawal | Minimum R2,000, once per tax year, up to the full savings balance | [SARS, 2 September 2024](https://www.sars.gov.za/latest-news/tax-directives-enhancements-and-tax-implications-of-the-two-pot-retirement-system/) |
| Tax on a savings withdrawal | Marginal rate, "annual payment/bonus" calculation; no retirement rates, exemptions or tax-free amounts | Same |
| Savings pot at retirement | Can be added to the retirement lump sum and taken in cash | Same |
| Withdrawals and the R550,000 | Savings withdrawals do not reduce the R550,000 tax-free amount at retirement | [Allan Gray, 31 October 2024](https://allangray.co.za/latest-insights/retirement/what-you-need-to-know-about-two-pot-withdrawals-and-tax) (secondary; consistent with the SARS wording) |
| Contribution deduction | 27.5% of income, capped at R430,000 a year from 1 March 2026 | [Sanlam](https://seb-news.sanlam.co.za/consultant-toolkit/key-retirement-fund-values-and-changes-effective-1-march-2026/) |
| Tax-free savings account limit | R46,000 a year from 1 March 2026 | [Moonstone](https://www.moonstone.co.za/changes-to-cgt-tax-free-savings-retirement-contributions-and-donations/) |
| Repo rate | 7.25%, effective 25 September 2026 | [SAnews](https://www.sanews.gov.za/south-africa/mpc-raises-repo-rate-725) |
| Maximum interest, unsecured credit | Repo rate + 21% a year (28.25% today) | [National Credit Regulations, reg. 42](https://www.acts.co.za/national-credit/r489_42__maximum_prescribed_interest_and_initiation_fees) |
| Maximum interest, credit facilities | Repo rate + 14% a year (21.25% today) | Same |
| Maximum interest, short-term credit | 5% a month on the first loan | Same |
| Maximum initiation fee, unsecured credit | R165 plus 10% of the amount above R1,000, capped at R1,050 | Same |
| Maximum monthly service fee | R60 | [National Credit Regulations, reg. 44](https://www.acts.co.za/national-credit/r489_44__maximum_service_fee) |

Things to recheck before publishing:

- **Repo rate:** the next MPC decision is on 19 November 2026. Update `REPO_RATE`.
- **Credit fee caps and VAT:** the regulation text I read does not say whether
  R1,050 and R60 exclude VAT. Some websites quote R1,207.50 and R69, which is
  exactly 15% more, so the caps are probably before VAT. Unconfirmed; the model
  uses the regulation's figures as written.
- **The R550,000 point** rests on a secondary source. Find the section of the
  Income Tax Act before relying on it.

## Context figures (not used in calculations)

| Figure | Value | Source |
|---|---|---|
| Replacement ratio, no withdrawals | 76.5% | Alexforbes *Member Insights 2026*, as reported by [Moonstone, 15 October 2026](https://www.moonstone.co.za/two-pot-system-softens-the-damage-of-annual-withdrawals/) |
| Replacement ratio, savings pot emptied every year | 51% | Same |
| Members who claimed in the 2025 tax year and claimed again in 2026 | 67% | Same |
| Average tax rate on withdrawals since the system began | 25% | Same |

## Dropped because I could not verify them

- SARS cumulative withdrawal totals for 2026 (one unverified blog).
- "About 50% cash out on changing jobs" (third-hand).
- Older persons grant means-test thresholds (sources conflict; out of scope for version 1).
- An average admin fee per withdrawal (a 2024 survey, only found second-hand). The fee is a user input defaulting to R0.
- Any "typical" personal loan rate. Only the legal caps and the user's own rate are used.
- Return volatility (no source yet; only matters for the later stochastic step).

## Assumptions (choices, not facts)

| Assumption | Default | Why, and which way it pushes the answer |
|---|---|---|
| Real return after fees | 4% a year | A round planning figure. Higher makes withdrawing look worse. |
| Inflation | 3% a year | The Reserve Bank's target. Used only to convert between real and money-terms rates. |
| Tax tables keep pace with inflation | Yes | Lets the model work in today's rands. Optimistic: income tax bands were frozen in the 2025 and 2026 tax years, and the lump-sum table has not moved since 2023. |
| Salary keeps pace with inflation | Yes | Keeps the member in the same tax band in real terms. |
| Savings pot taken as cash at retirement | Yes | So the lump-sum table applies to the money given up. Buying an annuity instead would be taxed as income. |
| Other cash lump sums at retirement | R0 | Makes the exit tax-free, the case most favourable to not withdrawing. Adjustable. |
| Admin fee | R0 | See dropped statistics. Adjustable. |

## Build log

### Step 1: scaffold (done)

- **What:** git repository, `.gitignore`, virtual environment outside OneDrive,
  the package skeleton, and `params.py`.
- **Why `params.py` matters:** every constant sits in one file next to its source,
  and `tests/test_params.py` fails if a constant has neither a source nor a stated
  assumption. That turns "source every statistic" into something the test suite
  enforces.

### Step 2: tax engine (done) — `src/twopot/tax.py`

- **What:** income tax with age rebates, the extra tax caused by a withdrawal,
  and the retirement lump-sum table.
- **The two tables are the heart of the project.** A withdrawal before retirement
  is taxed as income at the marginal rate with no tax-free amount. The same money
  left until retirement comes out on the lump-sum table, where the first R550,000
  is tax-free. The gap between the two is the tax cost of withdrawing early.
- **Tax on a withdrawal** = tax on (income + withdrawal) − tax on income. This is
  SARS's "annual payment/bonus" method. It is more accurate than multiplying by
  one marginal rate, because a withdrawal can straddle two bands or lift someone
  above the tax threshold.
- **Lump sums are cumulative.** The table applies to the lifetime running total,
  so tax on a lump sum = tax on (earlier + this) − tax on earlier.
- **How it is tested:** SARS prints the tax due at the bottom of each band (for
  example "R44,118 + 26% above R245,100"). The code stores only limits and rates,
  and the tests check that it reproduces every printed base amount and all three
  published tax thresholds. So the tests compare against SARS, not against my own
  arithmetic.
- **Simplification:** "taxable income" is one input. In practice it is salary
  minus your own retirement contributions and other deductions.

### Step 3: tagged rates and the price of one withdrawal (done)

Files: `rates.py`, `solver.py`, `withdrawal.py`.

**Rates carry a basis (`rates.py`).**

- Every rate is a `Rate` tagged REAL (above inflation) or NOMINAL (money terms).
  Comparing a real rate with a nominal one raises `BasisMismatchError`. This is
  how "real-vs-real or nominal-vs-nominal" is enforced, not just promised.
- Conversion uses the exact relation (1 + nominal) = (1 + real) × (1 + inflation).
  So 4% real with 3% inflation is 7.12% nominal, not 7%.
- "Nominal" also has a compounding meaning. A loan quoted at 12% a year, charged
  monthly, is 1% a month, which is 12.68% effective. Every `Rate` holds an
  effective annual rate; quoted loan rates are converted on the way in.

**The price of one withdrawal (`withdrawal.py`).** Everything is in today's rands.

1. Cash in hand = gross − extra income tax − admin fee.
2. Retirement money given up = gross × (1 + real return)^years, less the
   lump-sum tax it would have borne at retirement.
3. Implied rate: (1 + i)^years = money given up ÷ cash in hand.

With one amount in and one out, step 3 has a closed form, and the tests confirm
it against a numerical solver. It can be rewritten as

    1 + i = (1 + real return) × [(1 − exit tax rate) ÷ (1 − tax rate now)]^(1/years)

which is the formula to remember. The implied rate is the fund's return plus the
tax gap spread over the years to retirement.

**What the model shows** (R10,000 gross, R300,000 income, 4% real return, no fee):

| Age | Cash in hand | Retirement money given up | Cost per R1 received | Implied real rate |
|---|---|---|---|---|
| 30 | R7,400 | R39,461 | R5.33 | 4.9% |
| 45 | R7,400 | R21,911 | R2.96 | 5.6% |
| 60 | R7,400 | R12,167 | R1.64 | 10.5% |
| 64 | R7,400 | R10,400 | R1.41 | 40.5% |

- **In rands, withdrawing young costs most** (compounding).
- **As a rate, withdrawing near retirement costs most**, because 26% tax paid up
  front is spread over fewer years. At 64 you pay 26% tax to get money one year
  before you could have had it tax-free.
- If no tax is lost either side (income under R99,000), the implied rate is
  exactly the fund's return. A test checks this.

**Limits of this number.** The implied rate runs to retirement, so it cannot be
compared directly with a 3-year loan. Step 4 makes the like-for-like comparison.

**Simplifications:**

- The admin fee is taken off the cash received; tax is charged on the full gross.
- The whole amount given up is treated as cash on the lump-sum table.
- Money given up is valued at one fixed return. Uncertainty is the later
  stochastic step.
