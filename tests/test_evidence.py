from src.evidence.evaluator import EvidenceEvaluator
from src.evidence.contradiction import ContradictionDetector


def test_conflicting_evidence_is_detected_by_contradiction_layer():

    evaluator = EvidenceEvaluator()
    detector = ContradictionDetector()

    results = [
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

    # ---------------------------------------------
    # Evidence layer
    # ---------------------------------------------

    decision = evaluator.evaluate(
        results
    )

    # Evidence is strong enough.
    assert decision.decision == "ANSWER"

    # ---------------------------------------------
    # Contradiction layer
    # ---------------------------------------------

    contradiction = detector.detect(
        decision.evidence
    )

    assert contradiction.conflict is True
    assert len(contradiction.clauses) == 2