import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Amendment:
    """
    Represents one amendment to a policy provision.

    amendment_type:
        SUBSTITUTE       -> replace specific text
        TABLE_REPLACEMENT -> replace a policy table
        INSERT            -> insert a new provision
    """

    section: str
    original_text: str
    replacement_text: str
    amendment_paragraph: str
    amendment_type: str


class AmendmentParser:
    """
    Parses Amendment No. 2026-01.md.

    Supports:
        1. Text substitutions
        2. Table replacements
        3. Inserted provisions
    """

    SUBSTITUTE_PATTERN = re.compile(
    r"In\s+§(?P<section>\d+\.\d+\.\d+)"
    r"[^.\n]*?"
    r"for\s+['\"](?P<old>[^'\"]+)['\"]"
    r"(?:\s*\([^)]*\))?"
    r"\s+substitute\s+"
    r"['\"](?P<new>[^'\"]+)['\"]",
    re.IGNORECASE,
)

    INSERT_PATTERN = re.compile(
        r"After\s+§(?P<after>\d+\.\d+\.\d+)"
        r",\s*insert\s*"
        r"(?:—|-)?\s*"
        r"\n*\s*>\s*\*\*(?P<section>\d+\.\d+\.\d+[A-Z]?)\*\*"
        r"\s+(?P<text>.*?)(?=\n\n|\n---|\Z)",
        re.IGNORECASE | re.DOTALL,
    )

    TABLE_PATTERN = re.compile(
        r"In\s+the\s+table\s+at\s+§(?P<section>\d+\.\d+\.\d+)"
        r",\s*substitute\s+the\s+following\s+—"
        r"(?P<table>.*?)(?=\n##|\n---|\Z)",
        re.IGNORECASE | re.DOTALL,
    )

    def parse(self, file_path: str) -> List[Amendment]:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Amendment file not found: {file_path}"
            )

        text = path.read_text(
            encoding="utf-8"
        )

        amendments: List[Amendment] = []

        # --------------------------------------------------
        # 1. TEXT SUBSTITUTIONS
        # --------------------------------------------------

        for match in self.SUBSTITUTE_PATTERN.finditer(text):

            amendments.append(
                Amendment(
                    section=match.group("section"),
                    original_text=match.group("old").strip(),
                    replacement_text=self._clean_markdown(
                        match.group("new")
                    ),
                    amendment_paragraph=self._find_paragraph(
                        text,
                        match.start()
                    ),
                    amendment_type="SUBSTITUTE",
                )
            )

        # --------------------------------------------------
        # 2. TABLE REPLACEMENTS
        # --------------------------------------------------

        for match in self.TABLE_PATTERN.finditer(text):

            table_text = match.group("table").strip()

            amendments.append(
                Amendment(
                    section=match.group("section"),
                    original_text="Existing table",
                    replacement_text=self._clean_markdown(
                        table_text
                    ),
                    amendment_paragraph=self._find_paragraph(
                        text,
                        match.start()
                    ),
                    amendment_type="TABLE_REPLACEMENT",
                )
            )

        # --------------------------------------------------
        # 3. INSERTED PROVISIONS
        # --------------------------------------------------

        for match in self.INSERT_PATTERN.finditer(text):

            amendments.append(
                Amendment(
                    section=match.group("section"),
                    original_text="No previous provision",
                    replacement_text=self._clean_markdown(
                        match.group("text")
                    ),
                    amendment_paragraph=self._find_paragraph(
                        text,
                        match.start()
                    ),
                    amendment_type="INSERT",
                )
            )

        return amendments

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """
        Remove simple Markdown formatting while preserving
        the actual policy content.
        """

        text = text.replace("**", "")
        text = text.replace("*", "")
        text = text.replace("`", "")
        text = text.strip()

        return text

    @staticmethod
    def _find_paragraph(
        text: str,
        position: int
    ) -> str:

        before = text[:position]

        matches = list(
            re.finditer(
                r"\*\*(\d+\.\d+)\*\*",
                before
            )
        )

        if not matches:
            return "unknown"

        return matches[-1].group(1)


if __name__ == "__main__":

    parser = AmendmentParser()

    amendment_path = (
        "data/Amendment No. 2026-01.md"
    )

    amendments = parser.parse(
        amendment_path
    )

    print("=" * 60)
    print("AMENDMENT PARSING COMPLETE")
    print("=" * 60)

    print(
        f"Total amendments found: {len(amendments)}"
    )

    for amendment in amendments:

        print("\n" + "-" * 60)

        print(
            f"Type: {amendment.amendment_type}"
        )

        print(
            f"Section: §{amendment.section}"
        )

        print(
            f"OLD: {amendment.original_text}"
        )

        print(
            f"NEW: {amendment.replacement_text}"
        )

        print(
            f"Amendment paragraph: "
            f"{amendment.amendment_paragraph}"
        )