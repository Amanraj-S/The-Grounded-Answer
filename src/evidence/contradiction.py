import re

from dataclasses import dataclass
from typing import Dict, List


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

    The detector only reports a conflict when two provisions
    appear to state different values for the same type of
    requirement.

    Repeated mentions of the same value inside a provision
    do not count as a contradiction.
    """

    TIME_PATTERN = re.compile(
        r"\b\d+\s+(?:calendar\s+)?days?\b",
        re.IGNORECASE,
    )

    MONEY_PATTERN = re.compile(
        r"\$\s?\d+(?:,\d{3})*(?:\.\d+)?",
        re.IGNORECASE,
    )

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

        # Compare every pair of retrieved provisions.
        for i in range(len(provisions)):

            for j in range(i + 1, len(provisions)):

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

    def _compare_pair(
        self,
        first: Dict,
        second: Dict,
    ) -> str:

        first_text = first["text"]
        second_text = second["text"]

        # ==================================================
        # CHECK TIME PERIODS
        # ==================================================

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

            # ----------------------------------------------
            # IMPORTANT:
            #
            # A provision may mention the same deadline
            # more than once.
            #
            # Example:
            # §4.3.2 -> 14 days, 14 days
            # §9.1.4 -> 14 days
            #
            # [14, 14] and [14] are not contradictory.
            # ----------------------------------------------

            first_unique_days = set(
                first_days
            )

            second_unique_days = set(
                second_days
            )

            # Same effective time requirement.
            if first_unique_days == second_unique_days:

                return ""

            # Different values are only considered a
            # contradiction when both provisions concern
            # the same reporting/deadline topic.
            if self._same_reporting_topic(
                first_text,
                second_text,
            ):

                return (
                    "Different reporting periods were found: "
                    f"{first['citation']} states "
                    f"{first_times[0]}, while "
                    f"{second['citation']} states "
                    f"{second_times[0]}."
                )

        # ==================================================
        # CHECK MONETARY AMOUNTS
        # ==================================================

        first_money = self.MONEY_PATTERN.findall(
            first_text
        )

        second_money = self.MONEY_PATTERN.findall(
            second_text
        )

        if first_money and second_money:

            # Compare unique monetary values so repeated
            # mentions of the same amount do not create
            # a false contradiction.

            first_unique_money = set(
                first_money
            )

            second_unique_money = set(
                second_money
            )

            # Same effective monetary requirement.
            if first_unique_money == second_unique_money:

                return ""

            if self._same_money_topic(
                first_text,
                second_text,
            ):

                return (
                    "Different monetary amounts were found: "
                    f"{first['citation']} contains "
                    f"{first_money[0]}, while "
                    f"{second['citation']} contains "
                    f"{second_money[0]}."
                )

        return ""

    @staticmethod
    def _same_reporting_topic(
        first_text: str,
        second_text: str,
    ) -> bool:

        combined = (
            first_text.lower()
            + " "
            + second_text.lower()
        )

        reporting_terms = [
            "report",
            "reporting",
            "failure to report",
            "change of circumstances",
            "change in income",
        ]

        return any(
            term in combined
            for term in reporting_terms
        )

    @staticmethod
    def _same_money_topic(
        first_text: str,
        second_text: str,
    ) -> bool:

        combined = (
            first_text.lower()
            + " "
            + second_text.lower()
        )

        money_terms = [
            "amount",
            "threshold",
            "income",
            "resource",
            "resources",
            "disregard",
            "sanction",
            "award",
        ]

        return any(
            term in combined
            for term in money_terms
        )

    @staticmethod
    def _extract_days(
        values: List[str],
    ) -> List[int]:

        days = []

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