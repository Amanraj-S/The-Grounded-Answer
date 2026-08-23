import re
from dataclasses import dataclass
from datetime import date
from typing import Optional

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


# ============================================================
# LOAD POLICY
# ============================================================

def load_policy_provisions():
    """
    Load the policy provisions used by the FAISS index.
    """

    from src.ingestion.parser import parse_policy

    return parse_policy(
        POLICY_PATH
    )


# ============================================================
# TOPIC DETECTION
# ============================================================

def detect_topic(
    question: str
) -> str:
    """
    Deterministic topic classification.

    The topic is used by the date requirement layer
    and evidence layer.
    """

    question_lower = question.lower()

    # --------------------------------------------------------
    # Explicit section references
    #
    # These are checked first so that a section-specific
    # question is classified correctly even if its wording
    # contains generic terms.
    # --------------------------------------------------------

    if "§6.4.1" in question_lower:
        return "earnings_disregard"

    if "§6.6.1" in question_lower:
        return "income_threshold"

    if "§10.5.2" in question_lower:
        return "sanction"

    if "§9.1.4" in question_lower:
        return "reporting_change"

    # --------------------------------------------------------
    # Reporting changes
    # --------------------------------------------------------

    if any(
        phrase in question_lower
        for phrase in [
            "report",
            "reporting",
            "change",
            "income change",
            "salary change",
            "change of circumstances",
            "changed",
            "notify the department",
            "notification",
        ]
    ):
        return "reporting_change"

    # --------------------------------------------------------
    # Income thresholds
    # --------------------------------------------------------

    if any(
        phrase in question_lower
        for phrase in [
            "income threshold",
            "threshold",
            "income limit",
            "monthly threshold",
        ]
    ):
        return "income_threshold"

    # --------------------------------------------------------
    # Earnings disregard
    # --------------------------------------------------------

    if any(
        phrase in question_lower
        for phrase in [
            "earnings disregard",
            "earnings are disregarded",
            "disregard",
            "disregarded",
            "earnings",
        ]
    ):
        return "earnings_disregard"

    # --------------------------------------------------------
    # Sanctions
    # --------------------------------------------------------

    if any(
        phrase in question_lower
        for phrase in [
            "sanction",
            "sanctions",
            "penalty",
            "penalties",
        ]
    ):
        return "sanction"

    # --------------------------------------------------------
    # General
    # --------------------------------------------------------

    return "general"


# ============================================================
# BUILD PIPELINE
# ============================================================

def build_pipeline():
    """
    Build the complete production engine.

    The same engine is used by:

        1. CLI
        2. Automated evaluation
        3. Any future API layer

    No evaluation-specific logic is included here.
    """

    # --------------------------------------------------------
    # 1. Load original policy
    # --------------------------------------------------------

    provisions = load_policy_provisions()

    # --------------------------------------------------------
    # 2. Parse amendments
    # --------------------------------------------------------

    amendment_parser = AmendmentParser()

    amendments = amendment_parser.parse(
        AMENDMENT_PATH
    )

    # --------------------------------------------------------
    # 3. Create FAISS retriever
    # --------------------------------------------------------

    retriever = PolicyRetriever()

    # --------------------------------------------------------
    # 4. Create date-aware retriever
    # --------------------------------------------------------

    date_aware_retriever = DateAwareRetriever(
        retriever=retriever,
        provisions=provisions,
        amendments=amendments,
    )

    # --------------------------------------------------------
    # 5. Date extractor
    # --------------------------------------------------------

    date_extractor = PolicyDateExtractor()

    # --------------------------------------------------------
    # 6. Date requirement evaluator
    # --------------------------------------------------------

    date_requirement_evaluator = (
        DateRequirementEvaluator()
    )

    # --------------------------------------------------------
    # 7. Evidence evaluator
    # --------------------------------------------------------

    evidence_evaluator = EvidenceEvaluator()

    # --------------------------------------------------------
    # 8. Contradiction detector
    # --------------------------------------------------------

    contradiction_detector = ContradictionDetector()

    # --------------------------------------------------------
    # 9. Answer generator
    # --------------------------------------------------------

    answer_generator = AnswerGenerator()

    return (
        date_extractor,
        date_requirement_evaluator,
        date_aware_retriever,
        evidence_evaluator,
        contradiction_detector,
        answer_generator,
    )


# ============================================================
# MAIN PRODUCTION ENGINE
# ============================================================

def process_question(
    question: str,
    components=None,
):
    """
    SINGLE PRODUCTION ENGINE ENTRY POINT.

    Both the CLI and automated evaluation use this
    exact function.

    The evaluation layer does NOT reimplement:

        - date extraction
        - topic detection
        - policy retrieval
        - amendment resolution
        - evidence evaluation
        - contradiction detection
        - answer generation
    """

    # --------------------------------------------------------
    # Build components if not supplied
    # --------------------------------------------------------

    if components is None:
        components = build_pipeline()

    (
        date_extractor,
        date_requirement_evaluator,
        retriever,
        evidence_evaluator,
        contradiction_detector,
        answer_generator,
    ) = components

    # ========================================================
    # STEP 1 — Extract dates
    # ========================================================

    dates = date_extractor.extract(
        question
    )

    # ========================================================
    # STEP 2 — Detect topic
    # ========================================================

    topic = detect_topic(
        question
    )

    # ========================================================
    # STEP 3 — Check required date information
    # ========================================================

    date_decision = (
        date_requirement_evaluator.evaluate(
            topic=topic,
            change_date=dates.change_date,
            determination_date=dates.determination_date,
            question=question,
        )
    )

    # --------------------------------------------------------
    # Required date missing
    # --------------------------------------------------------

    if not date_decision.can_proceed:

        missing_date_answer = (
            f"{date_decision.reason}\n\n"
            "Who to ask / Next steps:\n"
            "Please specify the applicable claim date or determination date, "
            "or contact a Department caseworker for assistance."
        )

        return {
            "status": "MISSING_DATE",
            "question": question,
            "topic": topic,
            "change_date": dates.change_date,
            "determination_date": dates.determination_date,
            "answer": missing_date_answer,
            "citations": [],
            "evidence": [],
        }

    # ========================================================
    # STEP 4 — Retrieve effective policy evidence
    # ========================================================

    results = retriever.search(
        question=question,
        topic=topic,
        change_date=dates.change_date,
        determination_date=dates.determination_date,
        top_k=5,
    )

    # ========================================================
    # STEP 5 — Evaluate evidence
    # ========================================================

    # IMPORTANT:
    #
    # The upgraded EvidenceEvaluator needs the ORIGINAL
    # question and detected topic.
    #
    # This prevents semantically related evidence from being
    # treated as sufficient evidence for an unsupported
    # question.
    #
    # Example:
    #
    # "Can I receive a personal loan?"
    #
    # may retrieve general recipient obligations.
    #
    # But those obligations do not directly support a
    # personal-loan answer.
    #
    # Therefore the evidence layer should return
    # NOT_COVERED.

    evidence_decision = (
        evidence_evaluator.evaluate(
            results,
            question=question,
            topic=topic,
        )
    )

    # ========================================================
    # STEP 5A — POLICY NOT COVERED
    # ========================================================

    if evidence_decision.decision == "NOT_COVERED":

        not_covered_answer = (
            "I cannot answer this question from the "
            "Household Support Program policy manual.\n\n"
            f"Reason: {evidence_decision.reason}\n\n"
            "Who to ask:\n"
            "Please contact the Department's relevant "
            "Household Support Services team for assistance."
        )

        return {
            "status": "NOT_COVERED",
            "question": question,
            "topic": topic,
            "change_date": dates.change_date,
            "determination_date": dates.determination_date,
            "answer": not_covered_answer,
            "citations": [],
            "evidence": evidence_decision.evidence,
        }

    # ========================================================
    # STEP 5B — OTHER EVIDENCE REFUSAL
    # ========================================================

    if evidence_decision.decision == "REFUSE":

        refuse_answer = (
            f"Reason: {evidence_decision.reason}\n\n"
            "Who to ask / Next steps:\n"
            "Please consult a senior policy officer or supervisor for clarification."
        )

        return {
            "status": "REFUSE",
            "question": question,
            "topic": topic,
            "change_date": dates.change_date,
            "determination_date": dates.determination_date,
            "answer": refuse_answer,
            "citations": [],
            "evidence": evidence_decision.evidence,
        }

    # ========================================================
    # STEP 6 — DETECT CONTRADICTIONS
    # ========================================================

    contradiction_result = (
        contradiction_detector.detect(
            evidence_decision.evidence
        )
    )

    if contradiction_result.conflict:

        conflict_answer = (
            f"{contradiction_result.reason}\n\n"
            "Who to ask / Next steps:\n"
            "Please escalate this case to a Calder County Department Supervisor "
            "under §1.1.3 for discretionary determination."
        )

        return {
            "status": "CONFLICT",
            "question": question,
            "topic": topic,
            "change_date": dates.change_date,
            "determination_date": dates.determination_date,
            "answer": conflict_answer,
            "citations": [
                clause["citation"]
                for clause
                in contradiction_result.clauses
            ],
            "evidence": contradiction_result.clauses,
        }

    # ========================================================
    # STEP 7 — GENERATE FINAL GROUNDED ANSWER
    # ========================================================

    answer_result = answer_generator.generate(
        question=question,
        evidence=evidence_decision.evidence,
    )

    return {
        "status": "ANSWER",
        "question": question,
        "topic": topic,
        "change_date": dates.change_date,
        "determination_date": dates.determination_date,
        "answer": answer_result.answer,
        "citations": [
            citation["citation"]
            for citation in answer_result.citations
        ],
        "evidence": evidence_decision.evidence,
    }


# ============================================================
# CLI
# ============================================================

def run():
    """
    CLI interface.

    The CLI does NOT contain separate pipeline logic.
    It simply calls process_question().
    """

    print("=" * 70)
    print(
        "GROUNDED ANSWER — "
        "DATE-AWARE POLICY PIPELINE"
    )
    print("=" * 70)

    try:
        question = input(
            "\nAsk a policy question (or press Enter to exit): "
        )
    except (KeyboardInterrupt, EOFError):
        print("\nExiting Policy Pipeline.")
        return

    if not question or not question.strip():
        print("\nNo policy question was entered. Exiting.")
        return

    result = process_question(
        question
    )

    # ========================================================
    # QUESTION INFORMATION
    # ========================================================

    print(
        "\n----------------------------------------"
    )
    print(
        "QUESTION INFORMATION"
    )
    print(
        "----------------------------------------"
    )

    print(
        f"Topic: {result['topic']}"
    )

    print(
        f"Change date: "
        f"{result['change_date']}"
    )

    print(
        f"Determination date: "
        f"{result['determination_date']}"
    )

    # ========================================================
    # MISSING DATE
    # ========================================================

    if result["status"] == "MISSING_DATE":

        print(
            "\n========================================"
        )
        print(
            "REFUSAL — MISSING REQUIRED INFORMATION"
        )
        print(
            "========================================"
        )

        print(
            "\nI cannot determine the applicable "
            "policy rule from the information provided."
        )

        print(
            f"\nReason: {result['answer']}"
        )

        print(
            "\nPlease provide the required date "
            "needed to determine the applicable rule."
        )

        return

    # ========================================================
    # POLICY NOT COVERED
    # ========================================================

    if result["status"] == "NOT_COVERED":

        print(
            "\n========================================"
        )
        print(
            "I DON'T KNOW — POLICY NOT COVERED"
        )
        print(
            "========================================"
        )

        print(
            f"\n{result['answer']}"
        )

        return

    # ========================================================
    # GENERAL REFUSAL
    # ========================================================

    if result["status"] == "REFUSE":

        print(
            "\n========================================"
        )
        print(
            "REFUSAL — INSUFFICIENT EVIDENCE"
        )
        print(
            "========================================"
        )

        print(
            f"\nReason: {result['answer']}"
        )

        return

    # ========================================================
    # CONTRADICTION
    # ========================================================

    if result["status"] == "CONFLICT":

        print(
            "\n========================================"
        )
        print(
            "REFUSAL — CONFLICTING POLICY EVIDENCE"
        )
        print(
            "========================================"
        )

        print(
            "\nThe retrieved policy provisions "
            "contain a conflict that prevents "
            "a reliable answer."
        )

        print(
            "\nReason:"
        )

        print(
            result["answer"]
        )

        print(
            "\nConflicting clauses:"
        )

        for clause in result["evidence"]:

            print(
                f"\n{clause['citation']}"
            )

            print(
                clause["text"]
            )

        return

    # ========================================================
    # FINAL ANSWER
    # ========================================================

    print(
        "\n========================================"
    )
    print(
        "FINAL ANSWER"
    )
    print(
        "========================================"
    )

    print(
        f"\n{result['answer']}"
    )

    # ========================================================
    # CITATIONS
    # ========================================================

    print(
        "\n========================================"
    )
    print(
        "CITATIONS"
    )
    print(
        "========================================"
    )

    for evidence in result["evidence"]:

        print(
            f"\n{evidence['citation']}"
        )

        print(
            f"Source: "
            f"{evidence['source']}"
        )

        print(
            f"Version: "
            f"{evidence['version']}"
        )

        print(
            f"Evidence score: "
            f"{evidence['score']:.4f}"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run()