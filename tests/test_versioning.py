from datetime import date

from src.policy.versioning import PolicyVersionResolver


def test_reporting_before_amendment():

    resolver = PolicyVersionResolver()

    result = resolver.resolve(
        topic="reporting_change",
        change_date=date(2026, 2, 20),
    )

    assert result.version == "original"
    assert result.source == "policy-manual.md"


def test_reporting_after_amendment():

    resolver = PolicyVersionResolver()

    result = resolver.resolve(
        topic="reporting_change",
        change_date=date(2026, 3, 10),
    )

    assert result.version == "amended"
    assert result.source == "Amendment No. 2026-01.md"


def test_sanction_uses_determination_date():

    resolver = PolicyVersionResolver()

    result = resolver.resolve(
        topic="sanction",
        determination_date=date(2026, 3, 5),
    )

    assert result.version == "amended"


def test_date_is_required_for_reporting():

    resolver = PolicyVersionResolver()

    try:
        resolver.resolve(
            topic="reporting_change"
        )
        assert False
    except ValueError:
        assert True