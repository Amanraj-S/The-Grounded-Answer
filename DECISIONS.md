# Architectural Decisions & Technical Rationale

## Grounded Answer — Calder County Household Support Program

### Brite Spark 2026 — Problem 1: The Grounded Answer

This document records the major architectural decisions, retrieval strategy,
evidence thresholds, refusal boundaries, contradiction handling, date-aware
policy resolution, and implementation choices used in the Grounded Answer
system.

The system is designed around one core principle:

> When the policy manual does not provide sufficient evidence, the system
> must refuse rather than invent an answer.

---

# 1. Core Design Philosophy

Grounded Answer is a policy-question answering engine built around the
provided Calder County Household Support Program policy corpus.

The system does not use a generative LLM to invent policy answers.

Instead, answers are constructed from retrieved policy provisions and include
the corresponding clause-level citations.

The architecture separates:

1. Question understanding
2. Date extraction
3. Date requirement validation
4. Semantic retrieval
5. Effective policy version resolution
6. Evidence evaluation
7. Contradiction detection
8. Grounded answer formatting

This separation makes the system easier to test, audit, and maintain.

---

# 2. Answer-vs-Refuse Boundary

In policy assistance, an incorrect answer can be more harmful than an
explicit refusal.

Therefore, the engine follows a strict:

**"Never Guess — Answer Only From Evidence"**

principle.

The system produces one of the following outcomes:

### `ANSWER`

Returned when:

- relevant policy evidence is found,
- the required date information is available when necessary,
- the evidence is sufficiently strong,
- no unresolved policy contradiction is detected.

The response contains policy text and clause-level citations.

---

### `NOT_COVERED`

Returned when:

- the policy manual does not sufficiently support the question,
- retrieved passages are only superficially related,
- or the question falls outside the policy manual's authority.

The system explicitly tells the user that the question cannot be answered
from the policy manual.

It also provides an appropriate next-step recommendation rather than
inventing a policy answer.

---

### `MISSING_DATE`

Returned when a date-sensitive policy question does not contain the date
needed to determine the applicable policy version.

Examples include:

- reporting-change questions without a change date,
- determination-based questions without a determination date.

The system refuses to guess which policy version applies.

---

### `CONFLICT`

Returned when relevant policy provisions contain unresolved contradictory
requirements.

The system does not arbitrarily select one provision.

Instead, it reports the conflicting clauses and recommends escalation.

---

### `REFUSE`

Used for evidence situations where the retrieved material is not strong
enough to safely support an answer.

---

# 3. Processing Pipeline

The production pipeline follows this structure:

```text
User Question
      |
      v
Date Extraction
      |
      v
Topic Detection
      |
      v
Date Requirement Evaluation
      |
      +---- Missing required date ----> MISSING_DATE
      |
      v
FAISS Semantic Retrieval
      |
      v
Date-Aware Policy Resolution
      |
      v
Evidence Evaluation
      |
      +---- Insufficient evidence ----> NOT_COVERED / REFUSE
      |
      v
Contradiction Detection
      |
      +---- Conflict detected ----> CONFLICT
      |
      v
Grounded Answer Generation
      |
      v
Clause-Level Citations
```

---

# 4. Evidence Thresholds

The system uses a two-stage evidence validation strategy.

Semantic similarity alone is not considered sufficient evidence because a question can be semantically similar to policy text without being directly supported by it.

The evidence evaluator therefore applies:

- `minimum_score = 0.45`
- `strong_score = 0.50`

Evidence below the minimum threshold is rejected as insufficient.

Evidence above the strong threshold can be considered for an `ANSWER`, provided that the required concept is directly supported and no contradiction is detected.

The evaluator also checks conceptual relevance to prevent false positives. For example, a question about a housing loan must not be answered merely because general recipient or assistance provisions are semantically similar.

This creates a clear separation between:

`Retrieval` → finding potentially relevant text

`Evidence Evaluation` → determining whether that text actually supports the question

`Answer Generation` → presenting only validated policy evidence

---

# 5. Contradiction Handling

The system is intentionally conservative when policy provisions disagree.

The `ContradictionDetector` checks retrieved provisions for conflicting requirements, including numerical differences such as:

- reporting periods,
- monetary amounts,
- percentages,
- and other policy values.

For the pre-amendment reporting rule, the policy corpus contains:

- `§4.3.2` — 10 calendar days
- `§9.1.4` — 30 calendar days

When these provisions apply to the same historical claim, the system returns `CONFLICT`.

The system does not select one provision arbitrarily.

Instead, it:

1. identifies the conflicting provisions,
2. reports both requirements,
3. provides the relevant clause citations,
4. recommends escalation to the appropriate Department authority.

This ensures that an unresolved policy conflict never becomes a fabricated answer.

---

# 6. Date-Aware Amendment Logic

The system does not assume that the newest policy rule applies to every question.

Amendment No. 2026-01 has an effective date of:

`1 March 2026`

The `PolicyDateExtractor` identifies dates contained in natural-language questions.

The `DateRequirementEvaluator` determines whether a date is mandatory before retrieval and policy resolution can proceed.

The `PolicyVersionResolver` then determines which policy version applies.

### Reporting Changes

For reporting-change questions:

- Changes before `1 March 2026` use the original policy.
- Changes on or after `1 March 2026` use the amended reporting rule.

Therefore:

`10 February 2026` → historical policy → unresolved conflict

`10 March 2026` → amended policy → `14 calendar days`

### Determination-Based Rules

For determination-based rules such as:

- earnings disregard,
- income thresholds,
- sanctions,

the determination date controls the applicable policy version.

Determinations made on or after `1 March 2026` use the amended values.

This preserves historical policy behavior while correctly applying the amendment to later determinations.

---

# 7. Modular Architecture

The system is divided into independent components so that individual responsibilities remain testable and maintainable.

```text
src/
├── ingestion/
│   └── parser.py
│
├── policy/
│   ├── amendment_parser.py
│   ├── date_extractor.py
│   ├── date_requirement.py
│   ├── versioning.py
│   └── effective_policy.py
│
├── retrieval/
│   ├── retriever.py
│   ├── date_aware_retriever.py
│   └── index.py
│
├── evidence/
│   ├── evaluator.py
│   └── contradiction.py
│
├── answer/
│   └── generator.py
│
└── pipeline/
    └── date_aware_pipeline.py
```

Each component has a focused responsibility:

* **Ingestion** parses the policy corpus.
* **Retrieval** finds relevant provisions using FAISS.
* **Date extraction** identifies claim and determination dates.
* **Version resolution** selects the applicable policy version.
* **Evidence evaluation** verifies that retrieved evidence is sufficient.
* **Contradiction detection** identifies unresolved policy conflicts.
* **Answer generation** formats grounded responses and citations.
* **Pipeline orchestration** connects the components into the production decision flow.

This modular design allows future amendments to be incorporated without rewriting the entire system.

---

# 8. Testing and Evaluation

The implementation is validated at multiple levels.

### Unit Testing

The `tests/` directory contains unit tests covering important components including:

* date extraction,
* amendment parsing,
* policy version resolution,
* evidence evaluation,
* contradiction detection,
* and related edge cases.

Run:

```bash
pytest
```

### Demonstration Suite

The `demo.py` script exercises the main system behaviors, including:

* grounded policy answers,
* unsupported questions,
* apparent policy gaps,
* contradiction detection,
* pre-amendment handling,
* post-amendment handling,
* missing-date refusal,
* and unrelated queries.

Run:

```bash
python demo.py
```

### Benchmark Evaluation

The automated benchmark contains 10 representative policy questions covering the major decision paths.

Run:

```bash
python evaluation/run_evaluation.py
```

The evaluation report is written to:

```text
evaluation/results.md
```

The current benchmark result is:

* **10 total cases**
* **10 passed**
* **0 failed**
* **100% benchmark accuracy**

The benchmark verifies that the system can distinguish between valid answers, historical conflicts, missing dates, unsupported questions, amended policy values, and grounded supporting evidence.

---

# 9. Design Outcome

The final architecture prioritizes correctness, traceability, and safe refusal over producing an answer for every question.

The system therefore follows this decision hierarchy:

```text
Can the question be understood?
        |
        v
Is the required date available?
        |
        +---- No ----> MISSING_DATE
        |
        v
Is relevant evidence retrieved?
        |
        +---- No ----> NOT_COVERED
        |
        v
Does the evidence directly support the claim?
        |
        +---- No ----> NOT_COVERED / REFUSE
        |
        v
Do relevant provisions conflict?
        |
        +---- Yes ---> CONFLICT
        |
        v
ANSWER
with exact policy evidence and clause-level citations
```

The resulting system is designed to be auditable: every answer can be traced back to the policy provision used to support it, while unsupported or contradictory situations remain explicitly visible to the user.