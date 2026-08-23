from dataclasses import dataclass
from typing import Optional


@dataclass
class DateRequirementDecision:
    """
    Determines whether enough date information is available
    to resolve the applicable policy version.
    """

    can_proceed: bool
    reason: str
    required_date: Optional[str] = None


class DateRequirementEvaluator:
    """
    Determines whether a policy question contains the date
    required to select the correct policy version.

    Different amendment paragraphs use different dates:

    - Reporting changes -> change date
    - Determination-based amendments -> determination date
    """

    def evaluate(
        self,
        topic: str,
        change_date=None,
        determination_date=None,
    ) -> DateRequirementDecision:

        # ---------------------------------------------
        # Reporting rules
        # ---------------------------------------------

        if topic == "reporting_change":

            if change_date is None:

                return DateRequirementDecision(
                    can_proceed=False,
                    reason=(
                        "The date on which the change "
                        "occurred is required to determine "
                        "which reporting rule applies."
                    ),
                    required_date="change_date",
                )

            return DateRequirementDecision(
                can_proceed=True,
                reason=(
                    "The change date required for the "
                    "reporting rule was provided."
                ),
            )

        # ---------------------------------------------
        # Determination-based rules
        # ---------------------------------------------

        if topic in {
            "income_threshold",
            "earnings_disregard",
            "sanction",
        }:

            if determination_date is None:

                return DateRequirementDecision(
                    can_proceed=False,
                    reason=(
                        "The Department's determination date "
                        "is required to determine which "
                        "policy figures apply."
                    ),
                    required_date="determination_date",
                )

            return DateRequirementDecision(
                can_proceed=True,
                reason=(
                    "The determination date required for "
                    "the policy version was provided."
                ),
            )

        # ---------------------------------------------
        # General questions
        # ---------------------------------------------

        return DateRequirementDecision(
            can_proceed=True,
            reason=(
                "No amendment-specific date is required "
                "for this topic."
            ),
        )