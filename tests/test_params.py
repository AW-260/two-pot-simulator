"""Every constant must say where it came from."""

from datetime import date

from twopot import params
from twopot.params import Assumption, Source

_HELPERS = {name for name, value in vars(params).items() if isinstance(value, Source)}


def _constants() -> set[str]:
    return {
        name
        for name in vars(params)
        if name.isupper() and not name.startswith("_") and name not in _HELPERS
    } - {"PROVENANCE"}


def test_every_constant_has_provenance():
    missing = _constants() - set(params.PROVENANCE)
    assert not missing, f"constants with no source or stated assumption: {missing}"


def test_provenance_has_no_stale_entries():
    stale = set(params.PROVENANCE) - _constants()
    assert not stale, f"provenance entries for constants that no longer exist: {stale}"


def test_sources_are_complete():
    for name, origin in params.PROVENANCE.items():
        if isinstance(origin, Source):
            assert origin.name, name
            assert origin.url.startswith("https://"), name
            date.fromisoformat(origin.accessed)
        else:
            assert isinstance(origin, Assumption), name
            assert origin.rationale, name
