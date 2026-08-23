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

    Date requirements:

    - Reporting changes -> change date
    - Determination-based amendments -> determination date

    Exception:
    If the user explicitly refers to a policy section, the
    section itself may be sufficient to retrieve and explain
    that provision. A date is not unnecessarily demanded when
    the question is explicitly about the cited provision.
    """

    def evaluate(
        self,
        topic: str,
        change_date=None,
        determination_date=None,
        question: str = "",
    ) -> DateRequirementDecision:

        question_lower = question.lower()

        # =====================================================
        # 1. Explicit policy-section reference
        # =====================================================

        # Examples:
        #   "What does §6.4.1 say?"
        #   "Explain §10.5.2"
        #   "What is the rule under §4.3.2?"
        #
        # The retriever can use the explicitly requested
        # section. Do not unnecessarily reject these questions
        # just because no date was supplied.
        # =====================================================

        if "§" in question_lower:

            return DateRequirementDecision(
                can_proceed=True,
                reason=(
                    "An explicit policy section was provided, "
                    "so the requested provision can be retrieved "
                    "directly."
                ),
            )

        # =====================================================
        # 2. Reporting rules
        # =====================================================

        if topic == "reporting_change":

            if change_date is None:

                return DateRequirementDecision(
                    can_proceed=False,
                    reason=(
                        "The date on which the change occurred "
                        "is required to determine which "
                        "reporting rule applies."
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

        # =====================================================
        # 3. Determination-based rules
        # =====================================================

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

        # =====================================================
        # 4. General questions
        # =====================================================

        return DateRequirementDecision(
            can_proceed=True,
            reason=(
                "No amendment-specific date is required "
                "for this topic."
            ),
        )