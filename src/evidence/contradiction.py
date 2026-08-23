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
    Detects potential contradictions between policy provisions.

    This first version focuses on explicit numeric conflicts,
    such as two different deadlines or limits concerning
    the same policy topic.

    It does not silently choose one provision over another.
    """

    NUMBER_PATTERN = re.compile(
        r"\b\d+(?:\.\d+)?\b"
    )

    TIME_PATTERN = re.compile(
        r"\b\d+\s+(?:calendar\s+)?days?\b",
        re.IGNORECASE
    )

    MONEY_PATTERN = re.compile(
        r"\$\s?\d+(?:,\d{3})*(?:\.\d+)?",
        re.IGNORECASE
    )

    def detect(
        self,
        provisions: List[Dict]
    ) -> ContradictionResult:

        if len(provisions) < 2:
            return ContradictionResult(
                conflict=False,
                clauses=[],
                reason="Fewer than two provisions were available."
            )

        # Compare every pair of retrieved provisions.
        for i in range(len(provisions)):

            for j in range(i + 1, len(provisions)):

                first = provisions[i]
                second = provisions[j]

                conflict_reason = self._compare_pair(
                    first,
                    second
                )

                if conflict_reason:

                    return ContradictionResult(
                        conflict=True,
                        clauses=[first, second],
                        reason=conflict_reason
                    )

        return ContradictionResult(
            conflict=False,
            clauses=[],
            reason="No explicit contradiction was detected."
        )

    def _compare_pair(
        self,
        first: Dict,
        second: Dict
    ) -> str:

        first_text = first["text"]
        second_text = second["text"]

        # --------------------------------------------------
        # Check for conflicting time periods.
        # --------------------------------------------------

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

            if first_days and second_days:

                if first_days != second_days:

                    return (
                        f"Different time periods were found: "
                        f"{first['citation']} states "
                        f"{first_times[0]}, while "
                        f"{second['citation']} states "
                        f"{second_times[0]}."
                    )

        # --------------------------------------------------
        # Check for conflicting monetary amounts.
        # --------------------------------------------------

        first_money = self.MONEY_PATTERN.findall(
            first_text
        )

        second_money = self.MONEY_PATTERN.findall(
            second_text
        )

        if first_money and second_money:

            if first_money != second_money:

                return (
                    f"Different monetary amounts were found: "
                    f"{first['citation']} contains "
                    f"{first_money[0]}, while "
                    f"{second['citation']} contains "
                    f"{second_money[0]}."
                )

        return ""

    @staticmethod
    def _extract_days(
        values: List[str]
    ) -> List[int]:

        days = []

        for value in values:

            match = re.search(
                r"\d+",
                value
            )

            if match:
                days.append(
                    int(match.group())
                )

        return days