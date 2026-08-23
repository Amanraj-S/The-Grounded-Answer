from src.policy.amendment_parser import AmendmentParser
from src.policy.date_extractor import PolicyDateExtractor
from src.policy.date_requirement import DateRequirementEvaluator

from src.retrieval.retriever import PolicyRetriever
from src.retrieval.date_aware_retriever import DateAwareRetriever

from src.evidence.evaluator import EvidenceEvaluator
from src.evidence.contradiction import ContradictionDetector


POLICY_PATH = "data/policy-manual.md"
AMENDMENT_PATH = "data/Amendment No. 2026-01.md"


def load_policy_provisions():
    """
    Load the policy provisions used by the FAISS index.
    """

    from src.ingestion.parser import parse_policy

    return parse_policy(
        POLICY_PATH
    )


def detect_topic(question: str) -> str:
    """
    Deterministic topic classification.
    """

    question_lower = question.lower()

    # Reporting changes
    if any(
        phrase in question_lower
        for phrase in [
            "report",
            "reporting",
            "change",
            "income change",
            "salary change",
        ]
    ):
        return "reporting_change"

    # Income thresholds
    if any(
        phrase in question_lower
        for phrase in [
            "income threshold",
            "threshold",
            "income limit",
        ]
    ):
        return "income_threshold"

    # Sanctions
    if any(
        phrase in question_lower
        for phrase in [
            "sanction",
            "penalty",
        ]
    ):
        return "sanction"

    # Earnings disregard
    if any(
        phrase in question_lower
        for phrase in [
            "earnings disregard",
            "disregard",
        ]
    ):
        return "earnings_disregard"

    return "general"


def build_pipeline():
    """
    Build all components required for the
    date-aware policy pipeline.
    """

    # ---------------------------------------------
    # Load original policy
    # ---------------------------------------------

    provisions = load_policy_provisions()

    # ---------------------------------------------
    # Parse amendments
    # ---------------------------------------------

    amendment_parser = AmendmentParser()

    amendments = amendment_parser.parse(
        AMENDMENT_PATH
    )

    # ---------------------------------------------
    # Real FAISS retriever
    # ---------------------------------------------

    retriever = PolicyRetriever()

    # ---------------------------------------------
    # Date-aware retriever
    # ---------------------------------------------

    date_aware_retriever = DateAwareRetriever(
        retriever=retriever,
        provisions=provisions,
        amendments=amendments,
    )

    # ---------------------------------------------
    # Date extractor
    # ---------------------------------------------

    date_extractor = PolicyDateExtractor()

    # ---------------------------------------------
    # Date requirement evaluator
    # ---------------------------------------------

    date_requirement_evaluator = (
        DateRequirementEvaluator()
    )

    # ---------------------------------------------
    # Evidence evaluator
    # ---------------------------------------------

    evidence_evaluator = EvidenceEvaluator()

    # ---------------------------------------------
    # Contradiction detector
    # ---------------------------------------------

    contradiction_detector = ContradictionDetector()

    return (
        date_extractor,
        date_requirement_evaluator,
        date_aware_retriever,
        evidence_evaluator,
        contradiction_detector,
    )


def run():

    (
        date_extractor,
        date_requirement_evaluator,
        retriever,
        evidence_evaluator,
        contradiction_detector,
    ) = build_pipeline()

    print("=" * 70)
    print("DATE-AWARE POLICY RETRIEVAL")
    print("=" * 70)

    question = input(
        "\nAsk a policy question: "
    )

    # =================================================
    # STEP 1 — Extract dates
    # =================================================

    dates = date_extractor.extract(
        question
    )

    # =================================================
    # STEP 2 — Detect topic
    # =================================================

    topic = detect_topic(
        question
    )

    print("\n----------------------------------------")
    print("QUESTION INFORMATION")
    print("----------------------------------------")

    print(
        f"Topic: {topic}"
    )

    print(
        f"Change date: "
        f"{dates.change_date}"
    )

    print(
        f"Determination date: "
        f"{dates.determination_date}"
    )

    # =================================================
    # STEP 3 — Check required date information
    # =================================================

    date_decision = (
        date_requirement_evaluator.evaluate(
            topic=topic,
            change_date=dates.change_date,
            determination_date=dates.determination_date,
        )
    )

    # =================================================
    # STEP 4 — Refuse if required date is missing
    # =================================================

    if not date_decision.can_proceed:

        print("\n========================================")
        print("REFUSAL")
        print("========================================")

        print(
            "\nI cannot determine the applicable "
            "policy rule from the information provided."
        )

        print(
            f"\nReason: {date_decision.reason}"
        )

        if (
            date_decision.required_date
            == "change_date"
        ):

            print(
                "\nPlease provide the date on which "
                "the change of circumstances occurred."
            )

        elif (
            date_decision.required_date
            == "determination_date"
        ):

            print(
                "\nPlease provide the date on which "
                "the Department made the determination."
            )

        return

    # =================================================
    # STEP 5 — Retrieve effective policy evidence
    # =================================================

    results = retriever.search(
        question=question,
        topic=topic,
        change_date=dates.change_date,
        determination_date=dates.determination_date,
        top_k=5,
    )

    if not results:

        print("\n========================================")
        print("REFUSAL")
        print("========================================")

        print(
            "\nNo relevant policy evidence was found."
        )

        return

    # =================================================
    # STEP 6 — Evaluate evidence strength
    # =================================================

    evidence_decision = evidence_evaluator.evaluate(
        results
    )

    if evidence_decision.decision == "REFUSE":

        print("\n========================================")
        print("REFUSAL — INSUFFICIENT EVIDENCE")
        print("========================================")

        print(
            f"\nReason: {evidence_decision.reason}"
        )

        return

    # =================================================
    # STEP 7 — Detect contradictions
    # =================================================

    contradiction_result = (
        contradiction_detector.detect(
            evidence_decision.evidence
        )
    )

    if contradiction_result.conflict:

        print("\n========================================")
        print("REFUSAL — CONFLICTING POLICY EVIDENCE")
        print("========================================")

        print(
            "\nThe retrieved policy provisions contain "
            "a conflict that prevents a reliable answer."
        )

        print(
            "\nConflicting clauses:"
        )

        for clause in contradiction_result.clauses:

            print(
                f"\n{clause['citation']}"
            )

            print(
                clause["text"]
            )

        return

    # =================================================
    # STEP 8 — Safe evidence
    # =================================================

    print("\n========================================")
    print("SAFE POLICY EVIDENCE")
    print("========================================")

    for result in evidence_decision.evidence:

        print(
            f"\n{result['citation']} "
            f"(score={result['score']:.4f})"
        )

        print(
            f"Version: {result['version']}"
        )

        print(
            f"Source: {result['source']}"
        )

        print(
            f"Text:\n{result['text'][:1000]}"
        )

    # =================================================
    # STEP 9 — Answer layer comes next
    # =================================================

    print("\n========================================")
    print("DECISION")
    print("========================================")

    print(
        "\nEvidence is sufficient and no "
        "contradiction was detected."
    )

    print(
        "\nThe system is ready for the Answer layer."
    )


if __name__ == "__main__":
    run()