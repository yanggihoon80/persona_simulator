from __future__ import annotations

from typing import Any


def get_preset_name(config: dict[str, Any]) -> str:
    return get_preset_names(config)[0]


def get_preset_names(config: dict[str, Any]) -> list[str]:
    explicit = config.get("preset")
    if isinstance(explicit, list):
        names = [str(name).strip() for name in explicit if str(name).strip()]
        if names:
            return list(dict.fromkeys(names))
    elif isinstance(explicit, str) and explicit.strip():
        return [explicit.strip()]

    decision_context = config.get("decision_context", {})
    if isinstance(decision_context, dict) and decision_context.get("analysis_object_required") is True:
        return ["revenue_hypothesis_validation"]

    mode = str(config.get("mode", "")).strip()
    if mode in {"revenue_hypothesis_validation"}:
        return ["revenue_hypothesis_validation"]
    if mode in {"decision_simulation", "decision_comparison"}:
        return ["decision_comparison"]
    if mode in {"action_evaluation"}:
        return ["action_evaluation"]
    return ["idea_validation"]


def get_target_condition(config: dict[str, Any]) -> str:
    seed_rules = config.get("seed_rules", {})
    if not isinstance(seed_rules, dict):
        return ""
    return str(seed_rules.get("target_condition", "")).strip()


def get_service_condition(config: dict[str, Any]) -> str:
    return str(config.get("service_condition", "")).strip()


def get_persona_count(config: dict[str, Any], default: int = 5) -> int:
    try:
        count = int(config.get("persona_count", default))
    except (TypeError, ValueError):
        return default
    return count if count > 0 else default


def get_questions(config: dict[str, Any]) -> list[str]:
    questions = config.get("questions", [])
    if not isinstance(questions, list):
        return []
    normalized = [str(question).strip() for question in questions if str(question).strip()]
    return normalized if len(normalized) >= 5 else []


def get_question_count(config: dict[str, Any], default: int = 7) -> int:
    try:
        count = int(config.get("generated_question_count", default))
    except (TypeError, ValueError):
        return default
    return max(5, count)
