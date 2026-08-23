import re
from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass
class ContradictionResult:
    """
    Result of comparing retrieved policy provisions.
    """

    conflict: bool
    clauses: List[Dict]
    reason: str


class ContradictionDetector:
    """
    Detects explicit contradictions between policy provisions.

    A contradiction is reported only when two provisions appear
    to state different values for the SAME policy requirement.

    Different numbers in different policy contexts are not treated
    as contradictions.
    """

    # =========================================================
    # Time-period pattern
    # =========================================================

    TIME_PATTERN = re.compile(
        r"\b\d+\s+(?:calendar\s+)?days?\b",
        re.IGNORECASE,
    )

    # =========================================================
    # Monetary amount pattern
    # =========================================================

    MONEY_PATTERN = re.compile(
        r"\$\s?\d+(?:,\d{3})*(?:\.\d+)?",
        re.IGNORECASE,
    )

    # =========================================================
    # Monetary concepts
    # =========================================================

    MONEY_CONCEPTS = {
        "income_threshold": [
            "income threshold",
            "income thresholds",
            "monthly threshold",
            "monthly income threshold",
            "threshold",
        ],

        "earnings_disregard": [
            "earnings disregard",
            "earnings are disregarded",
            "disregarded per month",
            "earnings disregarded",
            "earnings are ignored",
            "disregarded",
        ],

        "sanction": [
            "sanction",
            "sanction percentage",
            "sanction rate",
            "sanction amount",
        ],

        "award": [
            "award amount",
            "amount of the award",
            "award",
        ],

        "resource_limit": [
            "resource limit",
            "resource threshold",
            "resource",
            "resources",
        ],
    }

    # =========================================================
    # Main contradiction detection
    # =========================================================

    def detect(
        self,
        provisions: List[Dict],
    ) -> ContradictionResult:

        if len(provisions) < 2:

            return ContradictionResult(
                conflict=False,
                clauses=[],
                reason=(
                    "Fewer than two provisions were available."
                ),
            )

        # -----------------------------------------------------
        # Compare every pair of retrieved provisions.
        # -----------------------------------------------------

        for i in range(len(provisions)):

            for j in range(
                i + 1,
                len(provisions),
            ):

                first = provisions[i]
                second = provisions[j]

                conflict_reason = self._compare_pair(
                    first,
                    second,
                )

                if conflict_reason:

                    return ContradictionResult(
                        conflict=True,
                        clauses=[
                            first,
                            second,
                        ],
                        reason=conflict_reason,
                    )

        return ContradictionResult(
            conflict=False,
            clauses=[],
            reason=(
                "No explicit contradiction was detected."
            ),
        )

    # =========================================================
    # Compare two provisions
    # =========================================================

    def _compare_pair(
        self,
        first: Dict,
        second: Dict,
    ) -> str:

        first_text = first.get("text", "")
        second_text = second.get("text", "")

        first_citation = first.get(
            "citation",
            "unknown provision",
        )

        second_citation = second.get(
            "citation",
            "unknown provision",
        )

        # =====================================================
        # CHECK TIME PERIODS
        # =====================================================

        first_times = self.TIME_PATTERN.findall(
            first_text
        )

        second_times = self.TIME_PATTERN.findall(
            second_text
        )

        if first_times and second_times:

            first_days = self._extract_days(
                first_times
            )

            second_days = self._extract_days(
                second_times
            )

            first_unique_days = set(
                first_days
            )

            second_unique_days = set(
                second_days
            )

            # -------------------------------------------------
            # Same numeric requirement.
            #
            # Example:
            # §4.3.2 -> 14 days, 14 days
            # §9.1.4 -> 14 days
            #
            # This is NOT a contradiction.
            # -------------------------------------------------

            if first_unique_days == second_unique_days:

                return ""

            # -------------------------------------------------
            # Different numbers.
            #
            # Only compare them when BOTH provisions clearly
            # concern the same reporting requirement.
            # -------------------------------------------------

            if self._same_reporting_topic(
                first_text,
                second_text,
            ):

                return (
                    "Different reporting periods were found: "
                    f"{first_citation} states "
                    f"{first_times[0]}, while "
                    f"{second_citation} states "
                    f"{second_times[0]}."
                )

        # =====================================================
        # CHECK MONETARY AMOUNTS
        # =====================================================

        first_money = self.MONEY_PATTERN.findall(
            first_text
        )

        second_money = self.MONEY_PATTERN.findall(
            second_text
        )

        if first_money and second_money:

            first_unique_money = set(
                first_money
            )

            second_unique_money = set(
                second_money
            )

            # -------------------------------------------------
            # Same monetary value.
            # -------------------------------------------------

            if first_unique_money == second_unique_money:

                return ""

            # -------------------------------------------------
            # Different monetary values do NOT automatically
            # mean contradiction.
            #
            # Both provisions must describe the same monetary
            # concept.
            # -------------------------------------------------

            first_concepts = self._money_concepts(
                first_text
            )

            second_concepts = self._money_concepts(
                second_text
            )

            common_concepts = (
                first_concepts
                & second_concepts
            )

            if common_concepts:

                concept = sorted(
                    common_concepts
                )[0]

                return (
                    "Different monetary amounts were found "
                    "for the same policy concept "
                    f"'{concept}': "
                    f"{first_citation} contains "
                    f"{first_money[0]}, while "
                    f"{second_citation} contains "
                    f"{second_money[0]}."
                )

        return ""

    # =========================================================
    # Determine whether two provisions concern the same
    # reporting/deadline requirement.
    # =========================================================

    @staticmethod
    def _same_reporting_topic(
        first_text: str,
        second_text: str,
    ) -> bool:

        first_lower = first_text.lower()
        second_lower = second_text.lower()

        reporting_concepts = [
            "reporting period",
            "report within",
            "report within the",
            "failure to report",
            "must report",
            "required to report",
            "reported the change",
            "report the change",
            "report any change",
            "change of circumstances",
            "change in income",
            "required under §4.3",
            "required under 4.3",
        ]

        # -----------------------------------------------------
        # Reporting language must appear in BOTH provisions.
        # -----------------------------------------------------

        first_matches = any(
            term in first_lower
            for term in reporting_concepts
        )

        second_matches = any(
            term in second_lower
            for term in reporting_concepts
        )

        return (
            first_matches
            and second_matches
        )

    # =========================================================
    # Identify monetary concepts
    # =========================================================

    @classmethod
    def _money_concepts(
        cls,
        text: str,
    ) -> Set[str]:

        text_lower = text.lower()

        concepts: Set[str] = set()

        for concept, phrases in (
            cls.MONEY_CONCEPTS.items()
        ):

            if any(
                phrase in text_lower
                for phrase in phrases
            ):

                concepts.add(
                    concept
                )

        return concepts

    # =========================================================
    # Extract numeric day values
    # =========================================================

    @staticmethod
    def _extract_days(
        values: List[str],
    ) -> List[int]:

        days: List[int] = []

        for value in values:

            match = re.search(
                r"\d+",
                value,
            )

            if match:

                days.append(
                    int(match.group())
                )

        return days


# =============================================================
# Standalone test
# =============================================================

if __name__ == "__main__":

    detector = ContradictionDetector()

    print("=" * 70)
    print("CONTRADICTION DETECTOR")
    print("=" * 70)

    # ---------------------------------------------------------
    # Example 1: Genuine reporting conflict
    # ---------------------------------------------------------

    provisions = [
        {
            "citation": "§4.3.2",
            "text": (
                "A recipient must report any change in "
                "income within 10 calendar days."
            ),
            "score": 0.6983,
        },
        {
            "citation": "§9.1.4",
            "text": (
                "The recipient reported the change within "
                "the 30 calendar days required under §4.3."
            ),
            "score": 0.5208,
        },
    ]

    result = detector.detect(
        provisions
    )

    print("\nTest 1 — Reporting conflict")

    print(
        f"Conflict: {result.conflict}"
    )

    print(
        f"Reason: {result.reason}"
    )

    # ---------------------------------------------------------
    # Example 2: Different monetary concepts
    # ---------------------------------------------------------

    provisions = [
        {
            "citation": "§6.6.1",
            "text": (
                "The monthly income threshold is $1,225."
            ),
            "score": 0.60,
        },
        {
            "citation": "§7.3.2",
            "text": (
                "The household resource amount is $140."
            ),
            "score": 0.55,
        },
    ]

    result = detector.detect(
        provisions
    )

    print("\nTest 2 — Different monetary concepts")

    print(
        f"Conflict: {result.conflict}"
    )

    print(
        f"Reason: {result.reason}"
    )

    # ---------------------------------------------------------
    # Example 3: Same monetary concept, different values
    # ---------------------------------------------------------

    provisions = [
        {
            "citation": "§6.6.1",
            "text": (
                "The monthly income threshold is $1,225."
            ),
            "score": 0.60,
        },
        {
            "citation": "§7.3.2",
            "text": (
                "The monthly income threshold is $1,500."
            ),
            "score": 0.55,
        },
    ]

    result = detector.detect(
        provisions
    )

    print("\nTest 3 — Same monetary concept")

    print(
        f"Conflict: {result.conflict}"
    )

    print(
        f"Reason: {result.reason}"
    )