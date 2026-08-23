"""
Grounded Answer — Comprehensive Policy Pipeline Demonstration

Demonstrates the 8 key scenarios required by the Brite Spark 2026 audit:
1. Normal policy question (Covered)
2. Policy question not in manual (Refusal)
3. Apparent gap topic (Refusal)
4. Pre-amendment reporting conflict (Contradiction)
5. Pre-March 2026 claim date
6. Post-March 2026 claim date (Amendment No. 2026-01)
7. Missing required date (Refusal)
8. Unrelated question (Refusal)
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.pipeline.date_aware_pipeline import build_pipeline, process_question


SCENARIOS = [
    (
        "Scenario 1: Grounded Policy Question (Covered)",
        "What is the monthly needs figure for a single adult?",
        "Demonstrates precise clause retrieval and grounded answer generation."
    ),
    (
        "Scenario 2: Policy Not Covered",
        "Can I apply for a housing loan through the Department?",
        "Demonstrates explicit refusal when topic is outside policy authority."
    ),
    (
        "Scenario 3: Apparent Gap Handling",
        "Does the Department offer free legal representation for every applicant?",
        "Demonstrates refusal when related text exists but topic is not authorized."
    ),
    (
        "Scenario 4: Genuine Policy Contradiction",
        "My income changed on 10 February 2026. How long do I have to report it?",
        "Demonstrates detection of internal policy conflict (§4.3.2 vs §9.1.4)."
    ),
    (
        "Scenario 5: Pre-Amendment Claim Date (Before 1 March 2026)",
        "My income changed on 10 February 2026. How long do I have to report it?",
        "Demonstrates historical policy resolution under pre-amendment rules."
    ),
    (
        "Scenario 6: Post-Amendment Claim Date (Amendment No. 2026-01)",
        "My income changed on 10 March 2026. How long do I have to report it?",
        "Demonstrates amended policy resolution (14 calendar days under Amendment §4.3.2)."
    ),
    (
        "Scenario 7: Date Required But Not Provided",
        "How long do I have to report a change in income?",
        "Demonstrates date-aware safety refusal when claim date is omitted."
    ),
    (
        "Scenario 8: Completely Unrelated Query",
        "What is the capital of France?",
        "Demonstrates robust refusal for out-of-domain queries."
    ),
]


def run_demo():
    print("=" * 80)
    print("GROUNDED ANSWER — DEMONSTRATION SUITE")
    print("Brite Spark 2026 — Problem 1: The Grounded Answer")
    print("=" * 80)
    print("\nInitializing production pipeline engine...")

    components = build_pipeline()
    print("Engine ready. Running 8 core test scenarios:\n")

    for index, (title, question, description) in enumerate(SCENARIOS, 1):
        print(f"\n{'=' * 80}")
        print(f"[{index}/8] {title}")
        print(f"{'=' * 80}")
        print(f"Description: {description}")
        print(f"Question:    \"{question}\"")
        print("-" * 80)

        result = process_question(question=question, components=components)

        status = result["status"]
        topic = result.get("topic", "N/A")
        citations = result.get("citations", [])
        answer = result.get("answer", "")

        print(f"Status:      {status}")
        print(f"Topic:       {topic}")
        print(f"Change Date: {result.get('change_date')}")
        print(f"Det. Date:   {result.get('determination_date')}")
        if citations:
            print(f"Citations:   {', '.join(citations)}")
        else:
            print("Citations:   None")

        print("\nResult Text:")
        print(answer.strip())
        print()

    print("=" * 80)
    print("DEMONSTRATION COMPLETE — ALL 8 SCENARIOS EXECUTED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
