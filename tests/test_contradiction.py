from src.evidence.contradiction import ContradictionDetector


def test_income_reporting_conflict():

    detector = ContradictionDetector()

    provisions = [
        {
            "citation": "§4.3.2",
            "text": (
                "A recipient must report any change in "
                "income within 10 calendar days."
            ),
            "score": 0.6983,
        },
        {
            "citation": "§9.1.4",
            "text": (
                "The recipient reported the change within "
                "the 30 calendar days required under §4.3."
            ),
            "score": 0.5208,
        },
    ]

    result = detector.detect(provisions)

    assert result.conflict is True
    assert len(result.clauses) == 2


def test_related_resource_clauses_are_not_conflicting():

    detector = ContradictionDetector()

    provisions = [
        {
            "citation": "§2.4.1",
            "text": (
                "A household is not eligible where total "
                "countable resources exceed $4,000."
            ),
            "score": 0.54,
        },
        {
            "citation": "§2.4.2",
            "text": (
                "The following are not countable resources — "
                "the home, one motor vehicle, household goods."
            ),
            "score": 0.50,
        },
    ]

    result = detector.detect(provisions)

    assert result.conflict is False