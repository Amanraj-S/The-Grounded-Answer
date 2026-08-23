from src.policy.amendment_parser import AmendmentParser
from src.policy.date_extractor import PolicyDateExtractor
from src.policy.date_requirement import DateRequirementEvaluator

from src.retrieval.retriever import PolicyRetriever
from src.retrieval.date_aware_retriever import DateAwareRetriever

from src.evidence.evaluator import EvidenceEvaluator
from src.evidence.contradiction import ContradictionDetector

from src.answer.generator import AnswerGenerator


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

    # ---------------------------------------------
    # Reporting changes
    # ---------------------------------------------

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

    # ---------------------------------------------
    # Income thresholds
    # ---------------------------------------------

    if any(
        phrase in question_lower
        for phrase in [
            "income threshold",
            "threshold",
            "income limit",
        ]
    ):
        return "income_threshold"

    # ---------------------------------------------
    # Sanctions
    # ---------------------------------------------

    if any(
        phrase in question_lower
        for phrase in [
            "sanction",
            "penalty",
        ]
    ):
        return "sanction"

    # ---------------------------------------------
    # Earnings disregard
    # ---------------------------------------------

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
    date-aware grounded-answer pipeline.
    """

    # =============================================
    # 1. Load original policy
    # =============================================

    provisions = load_policy_provisions()

    # =============================================
    # 2. Parse amendments
    # =============================================

    amendment_parser = AmendmentParser()

    amendments = amendment_parser.parse(
        AMENDMENT_PATH
    )

    # =============================================
    # 3. Create FAISS retriever
    # =============================================

    retriever = PolicyRetriever()

    # =============================================
    # 4. Create date-aware retriever
    # =============================================

    date_aware_retriever = DateAwareRetriever(
        retriever=retriever,
        provisions=provisions,
        amendments=amendments,
    )

    # =============================================
    # 5. Date extractor
    # =============================================

    date_extractor = PolicyDateExtractor()

    # =============================================
    # 6. Date requirement evaluator
    # =============================================

    date_requirement_evaluator = (
        DateRequirementEvaluator()
    )

    # =============================================
    # 7. Evidence evaluator
    # =============================================

    evidence_evaluator = EvidenceEvaluator()

    # =============================================
    # 8. Contradiction detector
    # =============================================

    contradiction_detector = ContradictionDetector()

    # =============================================
    # 9. Answer generator
    # =============================================

    answer_generator = AnswerGenerator()

    return (
        date_extractor,
        date_requirement_evaluator,
        date_aware_retriever,
        evidence_evaluator,
        contradiction_detector,
        answer_generator,
    )


def run():

    (
        date_extractor,
        date_requirement_evaluator,
        retriever,
        evidence_evaluator,
        contradiction_detector,
        answer_generator,
    ) = build_pipeline()

    print("=" * 70)
    print("GROUNDED ANSWER — DATE-AWARE POLICY PIPELINE")
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
    # STEP 6 — Evaluate evidence
    # =================================================

    evidence_decision = (
        evidence_evaluator.evaluate(
            results
        )
    )

    if (
        evidence_decision.decision
        == "REFUSE"
    ):

        print("\n========================================")
        print("REFUSAL — INSUFFICIENT EVIDENCE")
        print("========================================")

        print(
            f"\nReason: "
            f"{evidence_decision.reason}"
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
            "\nThe retrieved policy provisions "
            "contain a conflict that prevents "
            "a reliable answer."
        )

        print(
            "\nConflicting clauses:"
        )

        for clause in (
            contradiction_result.clauses
        ):

            print(
                f"\n{clause['citation']}"
            )

            print(
                clause["text"]
            )

        return

    # =================================================
    # STEP 8 — Generate final answer
    # =================================================

    answer_result = answer_generator.generate(
        question=question,
        evidence=evidence_decision.evidence,
    )

    # =================================================
    # STEP 9 — Display final answer
    # =================================================

    print("\n========================================")
    print("FINAL ANSWER")
    print("========================================")

    print(
        f"\n{answer_result.answer}"
    )

    # =================================================
    # STEP 10 — Display citations
    # =================================================

    print("\n========================================")
    print("CITATIONS")
    print("========================================")

    for citation in answer_result.citations:

        print(
            f"\n{citation['citation']}"
        )

        print(
            f"Source: "
            f"{citation['source']}"
        )

        print(
            f"Version: "
            f"{citation['version']}"
        )

        print(
            f"Evidence score: "
            f"{citation['score']:.4f}"
        )


if __name__ == "__main__":
    run()