from src.evidence.evaluator import EvidenceEvaluator


def test_strong_evidence_allows_answer():

    evaluator = EvidenceEvaluator()

    results = [
        {
            "citation": "§2.4.1",
            "text": (
                "A household is not eligible where "
                "total countable resources exceed $4,000."
            ),
            "score": 0.54,
        }
    ]

    decision = evaluator.evaluate(results)

    assert decision.decision == "ANSWER"


def test_weak_evidence_causes_refusal():

    evaluator = EvidenceEvaluator()

    results = [
        {
            "citation": "§7.2.1",
            "text": "Monthly needs figures...",
            "score": 0.30,
        }
    ]

    decision = evaluator.evaluate(results)

    assert decision.decision == "REFUSE"


def test_no_evidence_causes_refusal():

    evaluator = EvidenceEvaluator()

    decision = evaluator.evaluate([])

    assert decision.decision == "REFUSE"