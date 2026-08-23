from src.answer.generator import AnswerGenerator


def test_answer_uses_validated_evidence():

    generator = AnswerGenerator()

    evidence = [
        {
            "citation": "§4.3.2",
            "text": (
                "A recipient must report any change "
                "in income within 14 calendar days."
            ),
            "score": 0.5823,
            "source": "Amendment No. 2026-01.md",
            "version": "amended",
        }
    ]

    result = generator.generate(
        question=(
            "My income changed on 10 March 2026. "
            "How long do I have to report it?"
        ),
        evidence=evidence,
    )

    assert "14 calendar days" in result.answer
    assert result.citations[0]["citation"] == "§4.3.2"
    assert (
        result.citations[0]["source"]
        == "Amendment No. 2026-01.md"
    )