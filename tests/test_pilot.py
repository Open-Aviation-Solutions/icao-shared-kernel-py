"""Pilot and Licence construction and validation — adapted from
icao-shared-kernel-rs tests/pilot.rs."""

import pytest

import icao_shared_kernel as k


def test_pilot_creation() -> None:
    licence = k.Licence("AU", "CASA", "12345")
    pilot = k.Pilot("John Smith", licences=[licence])
    assert pilot.display_name == "John Smith"
    assert [lic.number for lic in pilot.licences] == ["12345"]
    assert pilot.legal_name is None


def test_defaults_to_no_licences() -> None:
    pilot = k.Pilot("John Smith")
    assert pilot.licences == []


def test_holds_multiple_state_licences() -> None:
    pilot = k.Pilot(
        "Amelia",
        licences=[
            k.Licence("AU", "CASA", "CASA-1"),
            k.Licence("US", "FAA", "FAA-2"),
        ],
    )
    authorities = [(lic.issuing_state, lic.issuing_authority) for lic in pilot.licences]
    assert authorities == [("AU", "CASA"), ("US", "FAA")]


def test_with_legal_name() -> None:
    pilot = k.Pilot("Johnny", legal_name="Johnathan Michael Smith")
    assert pilot.display_name == "Johnny"
    assert pilot.legal_name == "Johnathan Michael Smith"


def test_licence_number_is_an_alphanumeric_string() -> None:
    # EASA-style identifiers embed a country prefix and letters.
    licence = k.Licence("GB", "UK CAA", "UK.FCL.0A1B2")
    assert licence.number == "UK.FCL.0A1B2"


def test_licence_number_has_no_upper_length_bound() -> None:
    # ICAO Annex 1 sets no maximum; only non-emptiness is enforced.
    long_number = "1" * 200
    k.Licence("AU", "CASA", long_number)


@pytest.mark.parametrize(
    "state, authority, number",
    [
        ("AU", "", "12345"),  # empty authority
        ("AU", "CASA", ""),  # empty number
    ],
)
def test_licence_validation_rejects_empty_fields(state: str, authority: str, number: str) -> None:
    with pytest.raises(k.EmptyFieldError):
        k.Licence(state, authority, number)


@pytest.mark.parametrize(
    "state",
    ["australia", "aus", "A", "au", ""],
)
def test_licence_validation_rejects_bad_issuing_state(state: str) -> None:
    with pytest.raises(k.IssuingStateError):
        k.Licence(state, "CASA", "12345")


@pytest.mark.parametrize(
    "display_name",
    ["", "A" * 101],
)
def test_pilot_validation_enforces_display_name_bounds(display_name: str) -> None:
    with pytest.raises(k.FieldLengthError):
        k.Pilot(display_name)


def test_pilot_equality_is_by_value() -> None:
    # Aggregates compare by value, so a reconstructed instance equals the
    # original — a repository round trip can be asserted with a plain ==.
    licences = [k.Licence("AU", "CASA", "12345")]
    pilot = k.Pilot("Michael Nelson", licences=licences)
    same = k.Pilot("Michael Nelson", licences=licences, id=pilot.id)

    assert pilot == same


def test_pilot_equality_covers_every_field() -> None:
    licences = [k.Licence("AU", "CASA", "12345")]
    pilot = k.Pilot("Michael Nelson", legal_name="M Nelson", licences=licences)

    assert pilot != k.Pilot("Someone Else", legal_name="M Nelson", licences=licences, id=pilot.id)
    assert pilot != k.Pilot("Michael Nelson", licences=licences, id=pilot.id)
    assert pilot != k.Pilot("Michael Nelson", legal_name="M Nelson", id=pilot.id)
    assert pilot != k.Pilot("Michael Nelson", legal_name="M Nelson", licences=licences)
