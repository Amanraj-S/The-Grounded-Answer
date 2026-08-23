# Grounded Answer — Calder County Household Support Program

**Brite Spark 2026 — Problem 1: The Grounded Answer**

A deterministic, date-aware Retrieval-Augmented Generation (RAG) policy engine that provides plain-language policy answers backed by exact clause-level citations from the Calder County Household Support Program Policy Manual and Amendment No. 2026-01.

---

## Key Features

1. **Exact Clause-Level Grounding**: Every substantive answer quotes verbatim text from the authoritative policy corpus with clause citations (e.g. `§4.3.2`, `§6.6.1`).
2. **Explicit Visible Refusal**: Refuses to guess or generate ungrounded answers when policy text does not cover a topic (`NOT_COVERED`), evidence is weak (`REFUSE`), required dates are missing (`MISSING_DATE`), or policy provisions conflict (`CONFLICT`). Every refusal provides clear escalation next steps.
3. **Contradiction Detection**: Detects pre-amendment internal policy contradictions (e.g., §4.3.2 10 calendar days vs §9.1.4 30 calendar days), presents both conflicting provisions, and escalates to a supervisor without picking a side.
4. **Apparent Gap Safety**: Rejects queries where related text exists (e.g. general recipient obligations) but specific authority is not granted in the manual (e.g., housing loans, free legal representation).
5. **Day 2 Date-Aware Architecture**: Evaluates claims based on the **date of the claim** (`change_date` or `determination_date`), routing historical claims to original manual provisions and modern claims to Amendment No. 2026-01 provisions.
6. **Amendment No. 2026-01 Effective Date Logic**: Implements the 1 March 2026 effective boundary for Amendment No. 2026-01, respecting paragraph 5.1/5.2/5.3 transitional rules without destroying historical manual accessibility.

---

## Corpus Structure

The application operates exclusively over the local markdown policy corpus located in `data/`:
* `data/policy-manual.md`: Consolidated Policy Manual (as at 31 December 2025).
* `data/Amendment No. 2026-01.md`: Amendment No. 2026-01 (Issued 12 Feb 2026, Effective 1 Mar 2026).

No web search or secondary external policy documents are used.

---

## Requirements & Prerequisites

* **Python**: Python 3.10+
* **Dependencies**: Listed in `requirements.txt`:
  * `sentence-transformers` (all-MiniLM-L6-v2 vector embeddings)
  * `faiss-cpu` (FAISS dense vector index)
  * `numpy`
  * `python-dotenv`
  * `pytest`
* **Environment Variables**: None required. Execution runs locally and offline.

---

## Installation & Setup

1. **Clone the Repository** and navigate to the project directory:
   ```bash
   git clone https://github.com/Amanraj-S/The-Grounded-Answer.git
   cd The-Grounded-Answer
   ```

2. **Create & Activate Virtual Environment**:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Build the FAISS Vector Index**:
   ```bash
   python -m src.retrieval.index
   ```
   *(This parses `data/policy-manual.md` and generates vector index files in `index/policy.index` and `index/metadata.json`)*.

---

## Usage

### 1. Interactive CLI Application

Run the date-aware policy CLI pipeline:

```bash
python -m src.pipeline.date_aware_pipeline
```

**Sample Interaction**:
```text
Ask a policy question: My income changed on 10 March 2026. How long do I have to report it?

----------------------------------------
QUESTION INFORMATION
----------------------------------------
Topic: reporting_change
Change date: 2026-03-10
Determination date: None

========================================
FINAL ANSWER
========================================
According to the applicable policy provision:

A recipient must report any change in household composition, income, address, or the circumstances of any household member within 14 calendar days of the change occurring...

========================================
CITATIONS
========================================
§4.3.2
Source: Amendment No. 2026-01.md
Version: amended
Evidence score: 0.7245
```

### 2. Comprehensive Demo Suite

Run all 8 core test scenarios (Covered, Not Covered, Apparent Gap, Contradiction, Pre-March Date, Post-March Date, Missing Date, Unrelated Query) in one command:

```bash
python demo.py
```

### 3. Running Unit Tests

Execute the unit test suite:

```bash
pytest
```

### 4. Running the 10-Question Evaluation Suite

Run the automated evaluation benchmark suite:

```bash
python evaluation/run_evaluation.py
```

Results are printed to the console and automatically written to [`evaluation/results.md`](evaluation/results.md).

---

## Refusal & Decision Mechanics

The engine returns one of five distinct statuses for every question:

| Status | Meaning | Action / Output |
|---|---|---|
| `ANSWER` | Validated policy evidence retrieved. | Outputs verbatim grounded policy provision and exact clause citations. |
| `NOT_COVERED` | Manual does not cover the topic or lacks direct concept support. | Explicitly refuses to answer and directs user to Household Support Services team. |
| `MISSING_DATE` | Question requires a claim date to determine applicable policy rule. | Refuses to guess today's policy and prompts user for claim/determination date. |
| `CONFLICT` | Policy provisions state contradictory requirements. | Outlines conflict (§4.3.2 vs §9.1.4), quotes both clauses, and escalates to Supervisor under §1.1.3. |
| `REFUSE` | Evidence is weak or ambiguous. | Explains evidence gap and advises consulting a senior policy officer. |

---

## Date-Aware Policy Resolution & Amendment Rules

Amendment No. 2026-01 introduced date-sensitive policy rules taking effect on **1 March 2026**:

1. **Reporting Changes (§4.3.2 / §9.1.4)**:
   * **Change date before 1 March 2026**: Subject to original pre-amendment policy. Pre-amendment manual contains a genuine contradiction between §4.3.2 (10 calendar days) and §9.1.4 (30 calendar days). Engine returns `CONFLICT` status.
   * **Change date on/after 1 March 2026**: Subject to Amendment No. 2026-01 paragraph 2 (aligned to 14 calendar days). Engine returns `ANSWER` citing amended §4.3.2.
2. **Determination-Based Rules (§6.4.1 Disregard, §6.6.1 Thresholds, §10.5.2 Sanctions)**:
   * Determined by the **determination date**.
   * Determinations made on or after 1 March 2026 apply amended values ($175 disregard, updated income scale, 15% sanction).

---

## Repository Deliverables

* `src/`: Modular codebase (ingestion, retrieval, policy versioning, evidence evaluation, answer generation, pipeline).
* `data/`: Authoritative policy manual and Amendment No. 2026-01 markdown text.
* `evaluation/`: 10-question evaluation benchmark runner and generated results report.
* `tests/`: 24 pytest unit tests covering date extraction, amendment parsing, contradiction detection, and effective policy resolution.
* `demo.py`: Automated demonstration script for all core scenarios.
* `DECISIONS.md`: Architectural decisions and refusal boundary documentation.
* `AI-USAGE.md`: Full AI disclosure and development methodology record.
