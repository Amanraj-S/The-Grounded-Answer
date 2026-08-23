from datetime import date

from src.policy.date_requirement import (
    DateRequirementEvaluator,
)


def test_reporting_requires_change_date():

    evaluator = DateRequirementEvaluator()

    result = evaluator.evaluate(
        topic="reporting_change",
        change_date=None,
    )

    assert result.can_proceed is False
    assert result.required_date == "change_date"


def test_reporting_with_change_date_can_proceed():

    evaluator = DateRequirementEvaluator()

    result = evaluator.evaluate(
        topic="reporting_change",
        change_date=date(2026, 3, 10),
    )

    assert result.can_proceed is True


def test_income_threshold_requires_determination_date():

    evaluator = DateRequirementEvaluator()

    result = evaluator.evaluate(
        topic="income_threshold",
        determination_date=None,
    )

    assert result.can_proceed is False
    assert result.required_date == "determination_date"


def test_income_threshold_with_determination_date():

    evaluator = DateRequirementEvaluator()

    result = evaluator.evaluate(
        topic="income_threshold",
        determination_date=date(2026, 3, 5),
    )

    assert result.can_proceed is True


def test_general_question_does_not_require_date():

    evaluator = DateRequirementEvaluator()

    result = evaluator.evaluate(
        topic="general",
    )

    assert result.can_proceed is True