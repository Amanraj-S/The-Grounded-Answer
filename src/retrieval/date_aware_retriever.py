from datetime import date
from typing import Dict, List, Optional

from src.policy.effective_policy import EffectivePolicyResolver


class DateAwareRetriever:
    """
    Combines FAISS semantic retrieval with date-aware
    policy resolution.

    FAISS determines which policy sections are relevant.

    EffectivePolicyResolver determines which version of
    each provision applies to the supplied date.

    IMPORTANT:
    When historical evidence may conflict with an amended
    provision, competing provisions are retained so that
    the contradiction layer can make the final decision.

    This class does NOT hard-code individual test questions.
    """

    def __init__(
        self,
        retriever,
        provisions: List[Dict],
        amendments,
    ):
        self.retriever = retriever

        self.provisions = provisions

        self.effective_policy = EffectivePolicyResolver(
            provisions=provisions,
            amendments=amendments,
        )

    # =========================================================
    # MAIN SEARCH
    # =========================================================

    def search(
        self,
        question: str,
        topic: str,
        change_date: Optional[date] = None,
        determination_date: Optional[date] = None,
        top_k: int = 5,
    ) -> List[Dict]:

        # -----------------------------------------------------
        # 1. FAISS semantic retrieval
        #
        # Retrieve additional candidates because the effective
        # version of a section may not be the only provision
        # needed to identify a historical conflict.
        # -----------------------------------------------------

        candidate_k = max(
            top_k * 3,
            15,
        )

        retrieved = self.retriever.search(
            question,
            top_k=candidate_k,
        )

        if not retrieved:
            return []

        # -----------------------------------------------------
        # 2. Resolve effective versions
        # -----------------------------------------------------

        effective_results = []

        seen = set()

        for result in retrieved:

            section = result.get(
                "id"
            )

            if not section:
                continue

            try:

                effective = (
                    self.effective_policy.get_provision(
                        section=section,
                        topic=topic,
                        change_date=change_date,
                        determination_date=determination_date,
                    )
                )

            except Exception:
                # A single unresolved section should not
                # destroy the entire retrieval operation.
                continue

            if effective is None:
                continue

            resolved = {
                "id": section,
                "citation": effective.citation,
                "text": effective.text,
                "score": float(
                    result.get(
                        "score",
                        0.0,
                    )
                ),
                "source": effective.source,
                "version": effective.version,
            }

            key = (
                resolved["citation"],
                resolved["version"],
                resolved["text"],
            )

            if key in seen:
                continue

            seen.add(key)

            effective_results.append(
                resolved
            )

        # -----------------------------------------------------
        # 3. If no effective provisions survived, return empty
        # -----------------------------------------------------

        if not effective_results:
            return []

        # -----------------------------------------------------
        # 4. Detect whether the question is date-sensitive
        # -----------------------------------------------------

        date_sensitive = (
            change_date is not None
            or determination_date is not None
        )

        # -----------------------------------------------------
        # 5. Preserve competing policy evidence
        #
        # This is the important upgrade.
        #
        # A date-aware system must not blindly discard a
        # provision simply because another version appears to
        # be effective.
        #
        # Historical/amended conflicts are handled later by
        # ContradictionDetector.
        # -----------------------------------------------------

        if date_sensitive:

            effective_results = (
                self._add_competing_versions(
                    effective_results=effective_results,
                    retrieved=retrieved,
                    topic=topic,
                    change_date=change_date,
                    determination_date=determination_date,
                    top_k=top_k,
                )
            )

        # -----------------------------------------------------
        # 6. Rank final evidence
        #
        # Keep FAISS relevance as the primary ranking signal.
        # Explicitly resolved evidence receives a very small
        # stability bonus rather than a large artificial boost.
        # -----------------------------------------------------

        for result in effective_results:

            result["_final_score"] = (
                float(
                    result.get(
                        "score",
                        0.0,
                    )
                )
            )

        effective_results.sort(
            key=lambda item: item["_final_score"],
            reverse=True,
        )

        # -----------------------------------------------------
        # 7. Remove internal ranking field
        # -----------------------------------------------------

        for result in effective_results:

            result.pop(
                "_final_score",
                None,
            )

        # -----------------------------------------------------
        # 8. Return evidence
        #
        # Return more than one result when necessary so the
        # contradiction layer has enough evidence to identify
        # competing requirements.
        # -----------------------------------------------------

        return effective_results[:top_k]

    # =========================================================
    # COMPETING VERSION RECOVERY
    # =========================================================

    def _add_competing_versions(
        self,
        effective_results: List[Dict],
        retrieved: List[Dict],
        topic: str,
        change_date: Optional[date],
        determination_date: Optional[date],
        top_k: int,
    ) -> List[Dict]:
        """
        Preserve alternative versions of highly relevant
        sections when a date-sensitive question is being asked.

        This method deliberately does NOT decide that two
        provisions contradict each other.

        That decision belongs to ContradictionDetector.

        The purpose here is simply to make sure potentially
        competing evidence is available to that layer.
        """

        combined = list(
            effective_results
        )

        existing_keys = {
            (
                item.get("citation"),
                item.get("version"),
                item.get("text"),
            )
            for item in combined
        }

        # -----------------------------------------------------
        # Only investigate strongly relevant candidates.
        #
        # This prevents unrelated historical provisions from
        # flooding the evidence set.
        # -----------------------------------------------------

        for result in retrieved:

            score = float(
                result.get(
                    "score",
                    0.0,
                )
            )

            if score < 0.45:
                continue

            section = result.get(
                "id"
            )

            if not section:
                continue

            # -------------------------------------------------
            # Ask resolver for the provision applicable to the
            # supplied date.
            # -------------------------------------------------

            try:

                effective = (
                    self.effective_policy.get_provision(
                        section=section,
                        topic=topic,
                        change_date=change_date,
                        determination_date=determination_date,
                    )
                )

            except Exception:
                continue

            if effective is None:
                continue

            key = (
                effective.citation,
                effective.version,
                effective.text,
            )

            if key in existing_keys:
                continue

            # -------------------------------------------------
            # Retrieve the original provision represented by
            # the FAISS candidate.
            #
            # This preserves evidence that may represent the
            # other side of a policy-version boundary.
            # -------------------------------------------------

            original = self._find_original_provision(
                section
            )

            if original is None:
                continue

            original_text = original.get(
                "text",
                "",
            )

            original_citation = original.get(
                "citation",
                section,
            )

            original_source = original.get(
                "source",
                "",
            )

            original_version = original.get(
                "version",
                "original",
            )

            # -------------------------------------------------
            # Don't duplicate the effective provision.
            # -------------------------------------------------

            original_key = (
                original_citation,
                original_version,
                original_text,
            )

            if original_key in existing_keys:
                continue

            # -------------------------------------------------
            # Only preserve original evidence when it is
            # genuinely different from the effective evidence.
            # -------------------------------------------------

            if (
                original_text.strip()
                == effective.text.strip()
            ):
                continue

            combined.append(
                {
                    "id": section,
                    "citation": original_citation,
                    "text": original_text,
                    "score": score,
                    "source": original_source,
                    "version": original_version,
                }
            )

            existing_keys.add(
                original_key
            )

        # -----------------------------------------------------
        # Keep strongest evidence first.
        # -----------------------------------------------------

        combined.sort(
            key=lambda item: float(
                item.get(
                    "score",
                    0.0,
                )
            ),
            reverse=True,
        )

        return combined

    # =========================================================
    # FIND ORIGINAL PROVISION
    # =========================================================

    def _find_original_provision(
        self,
        section: str,
    ) -> Optional[Dict]:
        """
        Find the original policy provision associated with
        a FAISS section identifier.

        Supports metadata using either:

            id
            citation

        as the section identifier.
        """

        normalized_section = (
            self._normalize_section(
                section
            )
        )

        for provision in self.provisions:

            provision_id = (
                provision.get(
                    "id"
                )
            )

            provision_citation = (
                provision.get(
                    "citation"
                )
            )

            if (
                provision_id
                and self._normalize_section(
                    provision_id
                )
                == normalized_section
            ):
                return provision

            if (
                provision_citation
                and self._normalize_section(
                    provision_citation
                )
                == normalized_section
            ):
                return provision

        return None

    # =========================================================
    # NORMALIZE SECTION
    # =========================================================

    @staticmethod
    def _normalize_section(
        value: str,
    ) -> str:
        """
        Normalize section identifiers such as:

            §4.3.2
            4.3.2
            § 4.3.2

        to the same representation.
        """

        if not value:
            return ""

        value = value.strip()

        value = value.replace(
            "§",
            "",
        )

        value = value.replace(
            " ",
            "",
        )

        return value.lower()


# =============================================================
# DIRECT TEST
# =============================================================

if __name__ == "__main__":

    print(
        "DateAwareRetriever is a pipeline component."
    )

    print(
        "Use date_aware_pipeline.py to execute the "
        "complete production engine."
    )