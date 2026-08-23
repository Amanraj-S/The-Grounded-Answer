from datetime import date

from src.policy.effective_policy import EffectivePolicyResolver
from src.policy.amendment_parser import AmendmentParser


AMENDMENT_PATH = "data/Amendment No. 2026-01.md"


def create_resolver():

    provisions = [
        {
            "id": "4.3.2",
            "citation": "§4.3.2",
            "text": (
                "A recipient must report any change in "
                "household composition, income, address, "
                "or circumstances within 10 calendar days."
            ),
        }
    ]

    parser = AmendmentParser()

    amendments = parser.parse(
        AMENDMENT_PATH
    )

    return EffectivePolicyResolver(
        provisions=provisions,
        amendments=amendments,
    )


def test_old_reporting_rule():

    resolver = create_resolver()

    result = resolver.get_provision(
        section="4.3.2",
        topic="reporting_change",
        change_date=date(2026, 2, 20),
    )

    assert result.version == "original"
    assert result.source == "policy-manual.md"
    assert "10 calendar days" in result.text


def test_new_reporting_rule():

    resolver = create_resolver()

    result = resolver.get_provision(
        section="4.3.2",
        topic="reporting_change",
        change_date=date(2026, 3, 10),
    )

    assert result.version == "amended"
    assert result.source == "Amendment No. 2026-01.md"
    assert "14 calendar days" in result.text
    assert "10 calendar days" not in result.text