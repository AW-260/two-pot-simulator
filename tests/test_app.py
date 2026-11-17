"""Smoke tests: the app runs end to end and leads with a headline."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from twopot.compare import PutBack

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def run_app() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception, app.exception
    return app


def loan_fees(app: AppTest):
    return next(radio for radio in app.radio if radio.label == "Loan fees")


def all_text(app: AppTest) -> str:
    return "\n".join(block.value for block in [*app.markdown, *app.caption, *app.info])


def test_default_view_assumes_no_loan_fees():
    # Without fees the legal-maximum loan costs 32.2% against a 32.6% break-even,
    # so the default headline must not favour withdrawing.
    app = run_app()
    assert loan_fees(app).value == "None"
    assert app.title[0].value.startswith("Take the loan.")
    assert "legal maximum is a worst case" in all_text(app)
    assert not app.error


def test_legal_maximum_fees_flip_the_headline():
    app = run_app()
    loan_fees(app).set_value("Legal maximum").run()
    assert not app.exception
    assert app.title[0].value.startswith("Withdrawing beats this loan")


def test_fund_row_is_labelled_as_an_upper_bound():
    app = run_app()
    text = all_text(app)
    assert "Pay them into my retirement fund (upper bound)" in text
    assert "two-thirds of new contributions are locked in" in text
    assert not app.info  # the note is only promoted when that plan is selected


def test_choosing_the_fund_plan_shows_the_upper_bound_note():
    app = run_app()
    plan = next(radio for radio in app.radio if "instalments" in radio.label)
    plan.set_value(PutBack.FUND_CONTRIBUTIONS).run()
    assert not app.exception
    assert "upper bound" in app.info[0].value


def test_without_a_loan_the_headline_is_the_cost_per_rand():
    app = run_app()
    app.checkbox[0].uncheck().run()
    assert not app.exception
    assert app.title[0].value.startswith("Every R1 you take out today")


def test_spending_the_instalments_changes_the_headline():
    app = run_app()
    plan = next(radio for radio in app.radio if "instalments" in radio.label)
    plan.set_value(PutBack.SPEND).run()
    assert not app.exception
    assert "poorer" in app.title[0].value


def test_impossible_inputs_show_an_error_instead_of_crashing():
    app = run_app()
    app.number_input[0].set_value(64).run()  # one year to retirement, 36-month loan
    assert not app.exception
    assert "repaid before retirement" in app.error[0].value
