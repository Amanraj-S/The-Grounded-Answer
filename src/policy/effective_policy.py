from dataclasses import dataclass
from typing import Dict, List, Optional

from src.policy.amendment_parser import Amendment
from src.policy.versioning import PolicyVersionResolver


@dataclass
class EffectiveProvision:
    """
    Represents the version of a policy provision that
    applies to a particular case.
    """

    citation: str
    text: str
    source: str
    version: str


class EffectivePolicyResolver:
    """
    Combines the original policy manual with amendments
    and determines which version of a provision applies.
    """

    def __init__(
        self,
        provisions: List[Dict],
        amendments: List[Amendment],
    ):

        self.provisions = provisions
        self.amendments = amendments

        self.version_resolver = PolicyVersionResolver()

        self.amendments_by_section = {
            amendment.section: amendment
            for amendment in amendments
        }

    def get_provision(
        self,
        section: str,
        topic: str,
        change_date=None,
        determination_date=None,
    ) -> EffectiveProvision:

        # ---------------------------------------------
        # 1. Find the original provision
        # ---------------------------------------------

        original = self._find_original(section)

        if original is None:
            raise ValueError(
                f"Policy provision §{section} was not found."
            )

        # ---------------------------------------------
        # 2. Check whether this provision was actually
        #    modified by Amendment No. 2026-01.
        # ---------------------------------------------

        amendment = self.amendments_by_section.get(
            section
        )

        # If the provision was never amended,
        # the original wording remains valid.
        if amendment is None:

            return EffectiveProvision(
                citation=original["citation"],
                text=original["text"],
                source="policy-manual.md",
                version="original",
            )

        # ---------------------------------------------
        # 3. This provision WAS amended.
        #
        # Now determine whether the original or
        # amended version applies.
        # ---------------------------------------------

        version = self.version_resolver.resolve(
            topic=topic,
            change_date=change_date,
            determination_date=determination_date,
        )

        # ---------------------------------------------
        # 4. Original version applies
        # ---------------------------------------------

        if version.version == "original":

            return EffectiveProvision(
                citation=original["citation"],
                text=original["text"],
                source="policy-manual.md",
                version="original",
            )

        # ---------------------------------------------
        # 5. Amended version applies
        # ---------------------------------------------

        amended_text = self._apply_amendment(
            original["text"],
            amendment,
        )

        return EffectiveProvision(
            citation=original["citation"],
            text=amended_text,
            source="Amendment No. 2026-01.md",
            version="amended",
        )

    def _find_original(
        self,
        section: str,
    ) -> Optional[Dict]:

        for provision in self.provisions:

            if provision["id"] == section:
                return provision

        return None

    @staticmethod
    def _apply_amendment(
        original_text: str,
        amendment: Amendment,
    ) -> str:

        # ---------------------------------------------
        # SUBSTITUTE
        # ---------------------------------------------

        if amendment.amendment_type == "SUBSTITUTE":

            return original_text.replace(
                amendment.original_text,
                amendment.replacement_text,
            )

        # ---------------------------------------------
        # TABLE REPLACEMENT
        # ---------------------------------------------

        if amendment.amendment_type == "TABLE_REPLACEMENT":

            return (
                "The amended provision contains the "
                "following table:\n\n"
                + amendment.replacement_text
            )

        # ---------------------------------------------
        # INSERT
        # ---------------------------------------------

        if amendment.amendment_type == "INSERT":

            return (
                original_text
                + "\n\n"
                + amendment.replacement_text
            )

        # ---------------------------------------------
        # Unknown amendment type
        # ---------------------------------------------

        raise ValueError(
            f"Unsupported amendment type: "
            f"{amendment.amendment_type}"
        )