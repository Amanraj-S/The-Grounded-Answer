import re
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ExtractedDates:
    """
    Dates extracted from a user's policy question.
    """

    change_date: Optional[date] = None
    determination_date: Optional[date] = None


class PolicyDateExtractor:
    """
    Extracts dates from policy questions.

    The extractor uses the language associated with each date
    to determine whether it is a change date or a determination
    date.

    Supported examples:

        My income changed on 10 March 2026.
        The Department made my determination on 5 March 2026.
        The Department determined my claim on 5 March 2026.
        The determination was made on 5 March 2026.
    """

    MONTHS = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    # =========================================================
    # Generic date pattern
    # =========================================================

    DATE_TEXT = (
        r"\d{1,2}"
        r"(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|"
        r"July|August|September|October|November|December)"
        r"\s+\d{4}"
    )

    DATE_PATTERN = re.compile(
        rf"\b(?P<date>{DATE_TEXT})\b",
        re.IGNORECASE,
    )

    # =========================================================
    # Change-date patterns
    # =========================================================

    CHANGE_PATTERN = re.compile(
        rf"(?:"
        r"\bchange(?:d)?\b"
        r"|\bincome\s+changed\b"
        r"|\bsalary\s+changed\b"
        r"|\bcircumstance(?:s)?\s+changed\b"
        r"|\bjob\s+changed\b"
        r"|\baddress\s+changed\b"
        r"|\bchange\s+of\s+circumstances\b"
        r")"
        rf".{{0,60}}?"
        rf"(?P<date>{DATE_TEXT})",
        re.IGNORECASE,
    )

    # =========================================================
    # Determination-date patterns
    # =========================================================

    DETERMINATION_PATTERN = re.compile(
        rf"(?:"
        r"\bDepartment\s+determined\b"
        r"|\bDepartment\s+made\s+(?:the\s+)?(?:my\s+)?determination\b"
        r"|\bDepartment\s+made\s+(?:the\s+)?determination\s+of\b"
        r"|\bdetermination\s+was\s+made\b"
        r"|\bclaim\s+was\s+determined\b"
        r"|\bofficial\s+determination\b"
        r"|\bofficial\s+decision\b"
        r"|\bDepartment\s+decided\b"
        r"|\bdetermination\s+date\b"
        r")"
        rf".{{0,60}}?"
        rf"(?P<date>{DATE_TEXT})",
        re.IGNORECASE,
    )

    def extract(
        self,
        question: str,
    ) -> ExtractedDates:
        """
        Extract change and determination dates.

        The extractor does not guess the meaning of an
        unrelated date. It only assigns a date when the
        surrounding language identifies its purpose.
        """

        result = ExtractedDates()

        # =====================================================
        # 1. Extract change date
        # =====================================================

        change_match = self.CHANGE_PATTERN.search(
            question
        )

        if change_match:

            result.change_date = (
                self._parse_text_date(
                    change_match.group("date")
                )
            )

        # =====================================================
        # 2. Extract determination date
        # =====================================================

        determination_match = (
            self.DETERMINATION_PATTERN.search(
                question
            )
        )

        if determination_match:

            result.determination_date = (
                self._parse_text_date(
                    determination_match.group("date")
                )
            )

        return result

    def _parse_text_date(
        self,
        text: str,
    ) -> Optional[date]:
        """
        Convert a textual date such as
        '5 March 2026' into a datetime.date.
        """

        match = self.DATE_PATTERN.search(
            text
        )

        if not match:
            return None

        day = int(
            re.search(
                r"\d{1,2}",
                match.group("date"),
            ).group()
        )

        month_match = re.search(
            r"(January|February|March|April|May|June|"
            r"July|August|September|October|November|December)",
            match.group("date"),
            re.IGNORECASE,
        )

        year_match = re.search(
            r"\d{4}",
            match.group("date"),
        )

        if not month_match or not year_match:
            return None

        month = self.MONTHS[
            month_match.group().lower()
        ]

        year = int(
            year_match.group()
        )

        try:

            return date(
                year,
                month,
                day,
            )

        except ValueError:

            # Invalid dates such as:
            # 31 February 2026
            return None


if __name__ == "__main__":

    extractor = PolicyDateExtractor()

    print("=" * 60)
    print("POLICY DATE EXTRACTOR")
    print("=" * 60)

    while True:

        question = input(
            "\nEnter a policy question "
            "(or type 'exit'): "
        )

        if question.lower() == "exit":
            break

        dates = extractor.extract(
            question
        )

        print(
            f"\nChange date: "
            f"{dates.change_date}"
        )

        print(
            f"Determination date: "
            f"{dates.determination_date}"
        )