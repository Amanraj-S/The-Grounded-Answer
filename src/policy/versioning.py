from dataclasses import dataclass
from datetime import date
from typing import Optional


AMENDMENT_EFFECTIVE_DATE = date(2026, 3, 1)


@dataclass
class PolicyVersion:
    """
    Represents which policy version applies to a question.
    """

    version: str
    source: str
    reason: str


class PolicyVersionResolver:
    """
    Determines whether the original policy manual or
    Amendment No. 2026-01 applies.

    Different policy changes can use different dates.
    """

    def resolve(
        self,
        topic: str,
        change_date: Optional[date] = None,
        determination_date: Optional[date] = None,
    ) -> PolicyVersion:

        topic = topic.lower().strip()

        # -----------------------------------------------
        # Reporting of changes
        # -----------------------------------------------
        #
        # Amendment paragraph 5.2 says that paragraph 2
        # applies according to the date of the change.
        #
        if topic == "reporting_change":

            if change_date is None:
                raise ValueError(
                    "A change date is required for "
                    "reporting-change questions."
                )

            if change_date < AMENDMENT_EFFECTIVE_DATE:

                return PolicyVersion(
                    version="original",
                    source="policy-manual.md",
                    reason=(
                        "The change occurred before "
                        "1 March 2026."
                    ),
                )

            return PolicyVersion(
                version="amended",
                source="Amendment No. 2026-01.md",
                reason=(
                    "The change occurred on or after "
                    "1 March 2026."
                ),
            )

        # -----------------------------------------------
        # Earnings, thresholds and sanctions
        # -----------------------------------------------
        #
        # Amendment paragraphs 1, 3 and 4 apply according
        # to the determination date.
        #
        if topic in {
            "earnings_disregard",
            "income_threshold",
            "sanction",
        }:

            if determination_date is None:
                raise ValueError(
                    "A determination date is required "
                    "for this policy topic."
                )

            if determination_date < AMENDMENT_EFFECTIVE_DATE:

                return PolicyVersion(
                    version="original",
                    source="policy-manual.md",
                    reason=(
                        "The determination was made "
                        "before 1 March 2026."
                    ),
                )

            return PolicyVersion(
                version="amended",
                source="Amendment No. 2026-01.md",
                reason=(
                    "The determination was made on or "
                    "after 1 March 2026."
                ),
            )

        # -----------------------------------------------
        # Unknown topic
        # -----------------------------------------------

        raise ValueError(
            f"Unknown date-sensitive policy topic: {topic}"
        )