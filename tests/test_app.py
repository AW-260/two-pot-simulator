"""Smoke tests: the app runs end to end and leads with a headline."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from twopot.compare import PutBack

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def run_app() -> AppTest:
    app = AppTest.from_file(APP, default_timeout=30).run()
    assert not app.exception, app.exception
    return app


def test_default_view_leads_with_the_loan_headline():
    app = run_app()
    assert app.title[0].value.startswith("Withdrawing beats this loan")
    assert not app.error


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
