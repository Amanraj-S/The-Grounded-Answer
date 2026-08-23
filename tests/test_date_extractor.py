from datetime import date

from src.policy.date_extractor import PolicyDateExtractor


def test_extract_change_date():

    extractor = PolicyDateExtractor()

    result = extractor.extract(
        "My salary changed on 20 February 2026."
    )

    assert result.change_date == date(
        2026, 2, 20
    )

    assert result.determination_date is None


def test_extract_determination_date():

    extractor = PolicyDateExtractor()

    result = extractor.extract(
        "The Department determined my claim "
        "on 5 March 2026."
    )

    assert result.change_date is None

    assert result.determination_date == date(
        2026, 3, 5
    )


def test_extract_both_dates():

    extractor = PolicyDateExtractor()

    result = extractor.extract(
        "My income changed on 20 February 2026 "
        "and the Department determined my claim "
        "on 5 March 2026."
    )

    assert result.change_date == date(
        2026, 2, 20
    )

    assert result.determination_date == date(
        2026, 3, 5
    )


def test_no_date():

    extractor = PolicyDateExtractor()

    result = extractor.extract(
        "How long do I have to report "
        "a change in income?"
    )

    assert result.change_date is None
    assert result.determination_date is None


def test_invalid_date_is_ignored():

    extractor = PolicyDateExtractor()

    result = extractor.extract(
        "My salary changed on 31 February 2026."
    )

    assert result.change_date is None