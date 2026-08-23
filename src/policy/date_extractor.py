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

    The extractor uses the language immediately associated
    with each date to determine whether it is a change date
    or a determination date.
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

    DATE_PATTERN = re.compile(
        r"\b"
        r"(?P<day>\d{1,2})"
        r"(?:st|nd|rd|th)?"
        r"\s+"
        r"(?P<month>January|February|March|April|May|June|"
        r"July|August|September|October|November|December)"
        r"\s+"
        r"(?P<year>\d{4})"
        r"\b",
        re.IGNORECASE,
    )

    # Phrases that specifically indicate a change date.
    CHANGE_PATTERN = re.compile(
        r"(?:"
        r"change(?:d)?"
        r"|income changed"
        r"|salary changed"
        r"|circumstance changed"
        r"|job changed"
        r"|address changed"
        r")"
        r".{0,40}?"
        r"(?P<date>\d{1,2}"
        r"(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|"
        r"July|August|September|October|November|December)"
        r"\s+\d{4})",
        re.IGNORECASE,
    )

    # Phrases that specifically indicate a determination date.
    DETERMINATION_PATTERN = re.compile(
        r"(?:"
        r"Department determined"
        r"|Department made the determination"
        r"|determination was made"
        r"|claim was determined"
        r"|official determination"
        r"|official decision"
        r"|Department decided"
        r")"
        r".{0,60}?"
        r"(?P<date>\d{1,2}"
        r"(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|"
        r"July|August|September|October|November|December)"
        r"\s+\d{4})",
        re.IGNORECASE,
    )

    def extract(
        self,
        question: str
    ) -> ExtractedDates:

        result = ExtractedDates()

        # -----------------------------------------
        # 1. Look specifically for change dates.
        # -----------------------------------------

        change_match = self.CHANGE_PATTERN.search(
            question
        )

        if change_match:

            result.change_date = self._parse_text_date(
                change_match.group("date")
            )

        # -----------------------------------------
        # 2. Look specifically for determination
        #    dates.
        # -----------------------------------------

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
        text: str
    ) -> Optional[date]:

        match = self.DATE_PATTERN.search(text)

        if not match:
            return None

        day = int(match.group("day"))

        month = self.MONTHS[
            match.group("month").lower()
        ]

        year = int(match.group("year"))

        try:

            return date(
                year,
                month,
                day,
            )

        except ValueError:

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