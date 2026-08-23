from src.policy.amendment_parser import AmendmentParser


AMENDMENT_PATH = "data/Amendment No. 2026-01.md"


def test_all_amendments_are_detected():

    parser = AmendmentParser()

    amendments = parser.parse(AMENDMENT_PATH)

    assert len(amendments) == 6


def test_reporting_change_is_detected():

    parser = AmendmentParser()

    amendments = parser.parse(AMENDMENT_PATH)

    amendment = next(
        item
        for item in amendments
        if item.section == "4.3.2"
    )

    assert amendment.amendment_type == "SUBSTITUTE"
    assert amendment.original_text == "10 calendar days"
    assert amendment.replacement_text == "14 calendar days"


def test_income_threshold_table_is_detected():

    parser = AmendmentParser()

    amendments = parser.parse(AMENDMENT_PATH)

    amendment = next(
        item
        for item in amendments
        if item.section == "6.6.1"
    )

    assert amendment.amendment_type == "TABLE_REPLACEMENT"
    assert "$1,225" in amendment.replacement_text
    assert "$2,925" in amendment.replacement_text


def test_new_sanction_clause_is_detected():

    parser = AmendmentParser()

    amendments = parser.parse(AMENDMENT_PATH)

    amendment = next(
        item
        for item in amendments
        if item.section == "10.5.3A"
    )

    assert amendment.amendment_type == "INSERT"
    assert "must not be imposed" in amendment.replacement_text


def test_sanction_percentage_is_detected():

    parser = AmendmentParser()

    amendments = parser.parse(AMENDMENT_PATH)

    amendment = next(
        item
        for item in amendments
        if item.section == "10.5.2"
    )

    assert amendment.original_text == "20 per cent"
    assert amendment.replacement_text == "15 per cent"