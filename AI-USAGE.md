# AI Usage Disclosure & Assistance Log

**Grounded Answer — Calder County Household Support Program**

**Brite Spark 2026 — Problem 1: The Grounded Answer**

This document provides a transparent record of **ChatGPT** assistance during the architectural design, implementation, testing, debugging, and documentation of the Grounded Answer project.

---

## 1. Overview of AI Assistance

**ChatGPT** was used exclusively as a development and pair-programming assistant during the implementation of this project.

ChatGPT assistance was utilized for:

- Rapid prototyping of Python modules and components
- Software design, code modularity, and structure
- Regular expression pattern formulation (date extraction, clause citation parsing)
- Boilerplate code generation
- Debugging and error traceback analysis
- Unit test suite generation (`pytest`)
- Evaluation benchmark suite development
- Technical documentation drafting (`README.md`, `DECISIONS.md`)
- Reviewing edge cases and boundary conditions

ChatGPT-generated code snippets were not treated as authoritative policy logic. All policy rules, effective date boundaries, evidence thresholds, and refusal mechanics were strictly grounded in and verified against `data/policy-manual.md` and `data/Amendment No. 2026-01.md`.

All generated code was thoroughly reviewed, modified, refactored, and validated by the developer.

---

## 2. AI Usage by Component

| Component | ChatGPT Assistance | Human Verification & Engineering |
|---|---|---|
| **Policy Ingestion (`src/ingestion/parser.py`)** | Assisted with Markdown parsing patterns and provision identification. | Verified provision boundaries against `data/policy-manual.md` and ensured policy text was preserved correctly. |
| **Amendment Parser (`src/policy/amendment_parser.py`)** | Assisted with regular expressions for amendment substitutions, table replacements, and insertions. | Tested parsing against `data/Amendment No. 2026-01.md` and verified the resulting amendment structures. |
| **Vector Retrieval (`src/retrieval/`)** | Assisted with FAISS integration and embedding implementation. | Verified retrieval behaviour, ranking, candidate selection, and relevance against actual policy provisions. |
| **Date Extraction (`src/policy/date_extractor.py`)** | Assisted with contextual date-extraction regular expressions. | Verified change-date and determination-date extraction and invalid-date handling. |
| **Date Requirement (`src/policy/date_requirement.py`)** | Assisted with the structure of date-sensitive safety checks. | Verified which policy topics require a change date or determination date. |
| **Policy Versioning (`src/policy/versioning.py`)** | Assisted with original-versus-amended policy routing. | Verified the 1 March 2026 effective boundary and transitional behaviour. |
| **Effective Policy Resolver (`src/policy/effective_policy.py`)** | Assisted with the structure for applying amendments to original provisions. | Verified historical and amended provision selection. |
| **Date-Aware Retrieval (`src/retrieval/date_aware_retriever.py`)** | Assisted with combining retrieval and effective-policy resolution. | Verified that retrieved provisions are resolved according to the relevant date. |
| **Evidence Evaluator (`src/evidence/evaluator.py`)** | Assisted with relevance thresholds, keyword checks, and concept validation. | Calibrated thresholds and verified refusal behaviour for unsupported questions. |
| **Contradiction Detector (`src/evidence/contradiction.py`)** | Assisted with numeric pattern extraction and contradiction-detection structure. | Verified detection of conflicting policy requirements without relying on a single hard-coded benchmark answer. |
| **Answer Generator (`src/answer/generator.py`)** | Assisted with response formatting and citation presentation. | Verified that responses remain grounded in retrieved policy text. |
| **Pipeline (`src/pipeline/date_aware_pipeline.py`)** | Assisted with orchestration and integration of components. | Tested the complete production pipeline using custom questions and benchmark scenarios. |
| **Unit Tests (`tests/`)** | Assisted with drafting pytest cases and edge-case scenarios. | Tested the complete suite against the implemented behaviour. |
| **Evaluation Suite (`evaluation/`)** | Assisted with evaluation runner structure and result reporting. | Verified the benchmark against the production engine and confirmed the final 10/10 result. |
| **Demo Suite (`demo.py`)** | Assisted with demonstration scenario structure and output formatting. | Verified all eight demonstration scenarios. |
| **Documentation** | Assisted with drafting and organizing technical documentation. | Reviewed documentation to ensure it accurately reflects the implemented repository. |

---

## 3. Policy Grounding and AI Limitations

A core design principle of this project is that ChatGPT was **never** used as a live policy generator or policy truth source:

1. **No Live Generative Policy Invention**: The production system executes offline using local FAISS embeddings and deterministic Python logic.
2. **Grounding Priority**: All policy answers are pulled directly from the authoritative corpus files:
   - `data/policy-manual.md`
   - `data/Amendment No. 2026-01.md`
3. **Refusal Mechanism**: When policy coverage is insufficient, missing required dates, or contradictory, the system explicitly refuses to answer rather than relying on LLM completion/hallucination.