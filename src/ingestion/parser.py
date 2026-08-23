import re
from pathlib import Path


# Matches provisions such as:
# **1.1.1** Some policy text...
# **4.3.2** Some policy text...
PROVISION_PATTERN = re.compile(
    r"^\*\*(\d+\.\d+\.\d+)\*\*\s*(.*)$",
    re.MULTILINE
)


def parse_policy(file_path: str):
    """
    Parse policy-manual.md into individual policy provisions.

    Each provision is identified by a stable number such as:
        1.1.1
        4.3.2
        12.3.3

    Returns a list of dictionaries containing:
        id
        citation
        text
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Policy file not found: {file_path}"
        )

    text = path.read_text(encoding="utf-8")

    matches = list(PROVISION_PATTERN.finditer(text))

    provisions = []

    for index, match in enumerate(matches):

        provision_number = match.group(1)

        # Start immediately after the provision number
        start = match.start(2)

        # End immediately before the next provision
        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(text)

        # Extract the complete provision text
        provision_text = text[start:end].strip()

        # Remove Markdown headings that belong to the
        # surrounding section, not to the provision.
        provision_text = re.sub(
            r"^#{1,6}\s+.*$",
            "",
            provision_text,
            flags=re.MULTILINE
        )

        provision_text = provision_text.strip()

        provisions.append(
            {
                "id": provision_number,
                "citation": f"§{provision_number}",
                "text": provision_text,
            }
        )

    return provisions


if __name__ == "__main__":

    policy_path = "data/policy-manual.md"

    provisions = parse_policy(policy_path)

    print(f"Total provisions found: {len(provisions)}")

    for provision in provisions[:5]:

        print("\n" + "=" * 60)
        print(provision["citation"])
        print("=" * 60)

        print(provision["text"][:500])