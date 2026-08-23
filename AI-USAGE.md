# AI Usage Disclosure & Assistance Log

**Grounded Answer — Calder County Household Support Program**
**Brite Spark 2026 — Problem 1**

This document provides a transparent record of AI assistant usage during the architectural design, implementation, testing, and documentation of the Grounded Answer project.

---

## 1. Overview of AI Integration

An AI coding assistant (Gemini / Antigravity pair-programming agent) was utilized as an agentic pair-programmer during the development of this repository. AI assistance was used for rapid prototyping, RegEx pattern formulation, boilerplate creation, unit test generation, and audit compliance verification.

All AI-generated code and logic underwent strict human inspection, empirical testing via `pytest`, and validation against the 10-question evaluation benchmark suite.

---

## 2. Specific AI Usage by Component

| Component | AI Role | Human Verification & Engineering |
|---|---|---|
| **Policy Ingestion (`src/ingestion/parser.py`)** | Generated initial markdown RegEx parsing patterns for `**X.Y.Z**` provision identifiers. | Verified provision boundaries against all 12 Parts of `data/policy-manual.md` to ensure zero lost text. |
| **Amendment Parser (`src/policy/amendment_parser.py`)** | Drafted RegEx patterns for text substitutions, table replacements, and section insertions. | Tested parser on `data/Amendment No. 2026-01.md` and added markdown cleaning logic. |
| **Vector Retrieval (`src/retrieval/`)** | Assisted with FAISS `IndexFlatIP` setup and `all-MiniLM-L6-v2` embedding integration. | Tuned candidate pool sizes (`candidate_k=15`) and calibrated concept ranking boosts. |
| **Date Extraction (`src/policy/date_extractor.py`)** | Formulated contextual RegEx patterns for change dates and determination dates. | Added month parsing dictionaries and invalid date error handling (e.g. Feb 31 protection). |
| **Date-Aware Routing (`src/policy/versioning.py`)** | Implemented version routing logic matching Amendment No. 2026-01 Paragraph 5 transitional rules. | Verified effective date boundary (`2026-03-01`) for pre-amendment vs post-amendment claims. |
| **Contradiction Detection (`src/evidence/contradiction.py`)** | Drafted RegEx extraction for days (`\d+ calendar days`) and monetary amounts. | Designed non-hardcoded pair-comparison logic to detect §4.3.2 vs §9.1.4 conflict while avoiding false positives across different policy concepts. |
| **Evidence Evaluator (`src/evidence/evaluator.py`)** | Generated initial keyword stop-word sets and concept mapping dictionaries. | Calibrated `minimum_score` (0.45) and `strong_score` (0.50) thresholds; added direct concept validation to prevent Apparent Gap false positives. |
| **Unit Test Suite (`tests/`)** | Drafted initial pytest test cases for amendment parsing, date extraction, and contradiction handling. | Expanded test suite to 24 passing tests covering all edge cases. |
| **Evaluation Suite (`evaluation/`)** | Assisted in drafting `run_evaluation.py` and markdown report writer. | Verified evaluation correctness on all 10 policy benchmark questions. |

---

## 3. Prompting Strategies & Workflow

1. **Iterative Component-Driven Prompts**:
   * Pipeline components were requested individually (Ingestion $\to$ Indexing $\to$ Retrieval $\to$ Refusal Logic $\to$ Contradiction Handling $\to$ Date Awareness $\to$ Pipeline Orchestration).
2. **Empirical Grounding**:
   * Instructions strictly prohibited LLM hallucination or text generation without verbatim corpus backing.
   * Required that answers format exact policy text verbatim.
3. **Automated Verification Loops**:
   * Every component addition was immediately followed by running `pytest` and checking test outputs.

---

## 4. Verification & Quality Control

* **Code Review**: Every line of generated Python code was inspected for safety, clarity, type annotations, and compliance with guidelines.
* **Test Verification**: 24/24 unit tests pass cleanly under `pytest`.
* **Benchmark Evaluation**: 10/10 evaluation benchmark cases pass with 100% accuracy in `evaluation/results.md`.
* **Real-World Audit**: Executed all 8 required real-world scenarios via `demo.py` to confirm robust behavior across normal, refusal, gap, contradiction, date-aware, and out-of-domain queries.
