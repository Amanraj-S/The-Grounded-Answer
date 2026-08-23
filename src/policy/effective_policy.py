from dataclasses import dataclass
from typing import Dict, List, Optional

from src.policy.amendment_parser import Amendment
from src.policy.versioning import PolicyVersionResolver


@dataclass
class EffectiveProvision:
    """
    Represents a policy provision selected for a case.

    version:
        original -> provision from the original policy manual
        amended  -> provision after applying the amendment
    """

    citation: str
    text: str
    source: str
    version: str


class EffectivePolicyResolver:
    """
    Resolves the effective version of policy provisions.

    IMPORTANT DESIGN RULE
    ---------------------
    This class determines which version is applicable to a case.

    It does NOT perform contradiction detection.

    For historical cases, the surrounding pipeline may need both
    the original and amended provisions so that the contradiction
    layer can determine whether conflicting rules exist.
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

    # =========================================================
    # PUBLIC API
    # =========================================================

    def get_provision(
        self,
        section: str,
        topic: str,
        change_date=None,
        determination_date=None,
    ) -> EffectiveProvision:

        original = self._find_original(section)

        if original is None:
            raise ValueError(
                f"Policy provision §{section} was not found."
            )

        amendment = self.amendments_by_section.get(section)

        # -----------------------------------------------------
        # No amendment exists for this section.
        # -----------------------------------------------------

        if amendment is None:
            return EffectiveProvision(
                citation=original["citation"],
                text=original["text"],
                source="policy-manual.md",
                version="original",
            )

        # -----------------------------------------------------
        # Resolve the applicable version.
        # -----------------------------------------------------

        version = self.version_resolver.resolve(
            topic=topic,
            change_date=change_date,
            determination_date=determination_date,
        )

        # -----------------------------------------------------
        # Original version applies.
        # -----------------------------------------------------

        if version.version == "original":
            return EffectiveProvision(
                citation=original["citation"],
                text=original["text"],
                source="policy-manual.md",
                version="original",
            )

        # -----------------------------------------------------
        # Amended version applies.
        # -----------------------------------------------------

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

    # =========================================================
    # HISTORICAL / CONFLICT SUPPORT
    # =========================================================

    def get_versions(
        self,
        section: str,
        topic: str,
        change_date=None,
        determination_date=None,
    ) -> List[EffectiveProvision]:
        """
        Return the policy versions relevant to the case.

        This is intentionally different from get_provision().

        get_provision()
            Returns the single effective version.

        get_versions()
            Returns the effective version plus the competing
            historical version when an amendment exists.

        This allows the contradiction layer to compare:

            original: 10 calendar days
            amended:  14 calendar days

        without embedding contradiction logic inside the
        version resolver.
        """

        original = self._find_original(section)

        if original is None:
            raise ValueError(
                f"Policy provision §{section} was not found."
            )

        amendment = self.amendments_by_section.get(section)

        # -----------------------------------------------------
        # No amendment => only one version exists.
        # -----------------------------------------------------

        if amendment is None:
            return [
                EffectiveProvision(
                    citation=original["citation"],
                    text=original["text"],
                    source="policy-manual.md",
                    version="original",
                )
            ]

        # -----------------------------------------------------
        # Resolve which version applies.
        # -----------------------------------------------------

        version = self.version_resolver.resolve(
            topic=topic,
            change_date=change_date,
            determination_date=determination_date,
        )

        amended_text = self._apply_amendment(
            original["text"],
            amendment,
        )

        original_provision = EffectiveProvision(
            citation=original["citation"],
            text=original["text"],
            source="policy-manual.md",
            version="original",
        )

        amended_provision = EffectiveProvision(
            citation=original["citation"],
            text=amended_text,
            source="Amendment No. 2026-01.md",
            version="amended",
        )

        # -----------------------------------------------------
        # If the resolver selected the original version,
        # put the original first.
        # -----------------------------------------------------

        if version.version == "original":
            return [
                original_provision,
                amended_provision,
            ]

        # -----------------------------------------------------
        # If the resolver selected amended version,
        # put amended first.
        # -----------------------------------------------------

        return [
            amended_provision,
            original_provision,
        ]

    # =========================================================
    # FIND ORIGINAL PROVISION
    # =========================================================

    def _find_original(
        self,
        section: str,
    ) -> Optional[Dict]:

        normalized_section = self._normalize_section(
            section
        )

        for provision in self.provisions:

            provision_id = self._normalize_section(
                provision.get("id", "")
            )

            citation = self._normalize_section(
                provision.get("citation", "")
            )

            if (
                provision_id == normalized_section
                or citation == normalized_section
            ):
                return provision

        return None

    # =========================================================
    # APPLY AMENDMENT
    # =========================================================

    @staticmethod
    def _apply_amendment(
        original_text: str,
        amendment: Amendment,
    ) -> str:

        amendment_type = (
            amendment.amendment_type
        )

        # -----------------------------------------------------
        # SUBSTITUTE
        # -----------------------------------------------------

        if amendment_type == "SUBSTITUTE":

            original_fragment = (
                amendment.original_text
            )

            replacement = (
                amendment.replacement_text
            )

            # Normal replacement.
            if original_fragment in original_text:
                return original_text.replace(
                    original_fragment,
                    replacement,
                )

            # If the exact original text cannot be found,
            # return the replacement as the authoritative
            # amended wording rather than silently keeping
            # stale policy text.
            return replacement

        # -----------------------------------------------------
        # TABLE REPLACEMENT
        # -----------------------------------------------------

        if amendment_type == "TABLE_REPLACEMENT":

            return (
                "The amended provision contains the "
                "following table:\n\n"
                + amendment.replacement_text
            )

        # -----------------------------------------------------
        # INSERT
        # -----------------------------------------------------

        if amendment_type == "INSERT":

            return (
                original_text
                + "\n\n"
                + amendment.replacement_text
            )

        # -----------------------------------------------------
        # Unknown amendment type.
        # -----------------------------------------------------

        raise ValueError(
            "Unsupported amendment type: "
            f"{amendment_type}"
        )

    # =========================================================
    # NORMALIZATION
    # =========================================================

    @staticmethod
    def _normalize_section(
        section: str,
    ) -> str:

        if not section:
            return ""

        value = section.strip().lower()

        value = value.replace("§", "")
        value = value.replace(" ", "")

        return value