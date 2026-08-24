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

## Installation & Setup Step-by-Step

Follow these steps to set up and run the system:

### 1. Clone Repository & Navigate to Directory
```bash
git clone https://github.com/Amanraj-S/The-Grounded-Answer.git
cd The-Grounded-Answer
```

### 2. Create & Activate Virtual Environment
```bash
# On Windows (PowerShell):
python -m venv .venv
.venv\Scripts\activate

# On Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Build FAISS Vector Index (Optional / Verification)
The pre-built vector index is included in `index/`. To rebuild it from scratch at any time:
```bash
python -m src.retrieval.index
```
*(Parses `data/policy-manual.md` and generates FAISS index files in `index/policy.index` and `index/metadata.json`)*.

---

## How Evaluators Can Run & Ask Custom Questions

Evaluators can test the system using automated evaluation benchmarks, demonstration scenarios, the interactive CLI prompt, or the programmatic Python API.

---

### Option A: Automated Evaluation Benchmark & Demo Suites 

1. **Run 10-Question Evaluation Benchmark (10/10 Pass Rate)**:
   ```bash
   python evaluation/run_evaluation.py
   ```
   *(Executes all 10 evaluation benchmark questions, prints detailed status and clause citations in the terminal, and automatically generates [`evaluation/results.md`](evaluation/results.md))*.

2. **Run Automated Demonstration Suite (8 Core Scenarios)**:
   ```bash
   python demo.py
   ```
   *(Executes 8 core demonstration scenarios covering answer grounding, missing dates, policy contradictions, apparent gaps, pre/post amendment date routing, and explicit refusals)*.

3. **Run Automated Unit Test Suite (24 Pytest Cases)**:
   ```bash
   pytest
   ```

---

### Option B: Interactive Terminal CLI (Ask Custom Policy Questions)

Evaluators can ask custom input questions directly in an interactive terminal prompt:

#### 1. Launch the interactive CLI pipeline:
```bash
python -m src.pipeline.date_aware_pipeline
```

#### 2. How to ask a question in CLI:
- When the terminal displays:
  ```text
  ======================================================================
  GROUNDED ANSWER — DATE-AWARE POLICY PIPELINE
  ======================================================================

  Ask a policy question (or press Enter to exit):
  ```
- Type **ANY custom policy question**, for example:
  - `"My income changed on 10 March 2026. How long do I have to report it?"`
  - `"The Department made my determination on 5 March 2026. What is the monthly income threshold for a household of 3?"`
  - `"How long do I have to report a change in income?"`
  - `"Can I apply for a housing loan through the Department?"`
- Press `Enter`.

#### 3. Output displayed in terminal:
- **Question Information**: Detected topic, change date, determination date.
- **Decision Status & Grounded Answer / Refusal**: Verbatim policy text or clear refusal explanation with next steps.
- **Citations**: Exact clause citations (§X.Y.Z), source document, version, and evidence score.

---

### Option C: Programmatic Python API

Evaluators can test arbitrary questions programmatically in Python code:

```python
from src.pipeline.date_aware_pipeline import build_pipeline, process_question

# 1. Initialize engine components
components = build_pipeline()

# 2. Pass ANY custom policy question
result = process_question(
    question="The Department made my determination on 5 March 2026. What is the monthly income threshold for a household of 3?",
    components=components
)

# 3. Output results
print("Status:", result["status"])
print("Topic:", result["topic"])
print("Change Date:", result["change_date"])
print("Determination Date:", result["determination_date"])
print("Answer:\n", result["answer"])
print("Citations:", result["citations"])
```

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

## Repository Structure & Deliverables

* `src/`: Core production engine:
  * `src/ingestion/parser.py`: Policy manual text parser.
  * `src/policy/amendment_parser.py`: Amendment No. 2026-01 parser.
  * `src/policy/date_extractor.py`: Contextual date extraction module.
  * `src/policy/date_requirement.py`: Date requirement safety gate.
  * `src/policy/versioning.py`: Effective policy version routing.
  * `src/policy/effective_policy.py`: Provision text overlay resolver.
  * `src/retrieval/index.py`: Vector index builder.
  * `src/retrieval/retriever.py`: Dense vector retriever & FAISS search.
  * `src/retrieval/date_aware_retriever.py`: Date-aware candidate retrieval & version overlay.
  * `src/evidence/evaluator.py`: Multi-stage evidence relevance & concept verification.
  * `src/evidence/contradiction.py`: Contradiction & conflict detector.
  * `src/answer/generator.py`: Grounded answer generator & citation builder.
  * `src/pipeline/date_aware_pipeline.py`: Main entry point (pipeline runner & interactive CLI).
* `data/`: Policy Manual and Amendment No. 2026-01 markdown text.
* `evaluation/`: 10-question evaluation benchmark suite and generated results report.
* `tests/`: 24 unit tests covering date extraction, amendment parsing, contradiction detection, and effective policy resolution.
* `demo.py`: Automated demonstration script for core scenarios.
* `DECISIONS.md`: Architectural decisions & technical rationale document.
* `AI-USAGE.md`: Full AI disclosure and development methodology record.
