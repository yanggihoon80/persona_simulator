import json
import os
import re
from pathlib import Path
from typing import Any

from openai import OpenAI


DEFAULT_MODEL = "gpt-4o"
DEFAULT_PERSONA_COUNT = 5
DEFAULT_QUESTION_COUNT = 7
OUTPUT_DIR = Path("output")
DEFAULT_PERSONA_CONFIG = {
    "persona_count": None,
    "mode": "decision_simulation",
    "comparison_enabled": True,
    "service_condition": "",
    "questions": [],
    "generated_question_count": DEFAULT_QUESTION_COUNT,
    "decision_context": {
        "goal": "",
        "decision_type": "",
        "example_options": [],
    },
    "seed_rules": {
        "target_condition": "",
        "age_range": "25-60",
        "jobs": ["small business owner", "team lead", "freelancer", "operations manager", "marketing manager"],
        "personalities": ["practical", "skeptical", "conservative", "curious", "price-sensitive"],
        "situations": [
            "has an active problem but limited time",
            "is comparing several alternatives",
            "has budget authority but needs clear ROI",
            "worries about switching cost",
        ],
        "must_include_constraints": ["budget", "trust", "workflow friction", "urgency", "switching cost"],
    },
    "persona_blueprints": [
        {
            "job": "",
            "age": "",
            "personality": "",
            "current_situation": "",
            "main_problem": "",
            "extra_notes": "",
        }
    ],
    "agent_roles": {
        "persona_agents": {
            "role": "virtual users",
            "task": "Evaluate realistic reactions, adoption possibility, rejection reasons, and execution likelihood.",
        },
        "strategy_agent": {
            "role": "strategy analyst",
            "task": "Review options through strategic and revenue contribution criteria.",
        },
        "evaluation_agent": {
            "role": "action value evaluator",
            "task": "Combine persona reaction and strategic evaluation into action value scores.",
        },
    },
    "scoring_schema": {
        "persona_reaction_score": "1-100",
        "strategic_fit_score": "1-100",
        "execution_feasibility_score": "1-100",
        "revenue_contribution_score": "1-100",
        "final_action_value_score_formula": "0.3 * persona_reaction_score + 0.3 * strategic_fit_score + 0.2 * execution_feasibility_score + 0.2 * revenue_contribution_score",
    },
    "output_requirements": {
        "include_persona_opinions": True,
        "include_sentiment": True,
        "sentiment_labels": ["긍정", "부정", "중립"],
        "include_option_comparison": True,
        "include_strategy_agent_review": True,
        "include_scores": True,
        "include_alignment_analysis": True,
        "include_counter_insight": True,
        "include_decision_guidance": True,
        "include_final_summary": True,
        "report_format": "html",
    },
}


def load_env_file(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.is_absolute():
        env_path = Path(__file__).resolve().parent / env_path
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip().lstrip("\ufeff")
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_openai_client() -> OpenAI:
    load_env_file()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing. Set it in .env or as an environment variable.")
    return OpenAI()


def get_model() -> str:
    load_env_file()
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


def get_persona_config(path: str | Path = "persona_config.json") -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        write_json_file(config_path, DEFAULT_PERSONA_CONFIG)
        return DEFAULT_PERSONA_CONFIG

    try:
        config = read_json_file(config_path)
    except (json.JSONDecodeError, OSError):
        return DEFAULT_PERSONA_CONFIG

    if not isinstance(config, dict):
        return DEFAULT_PERSONA_CONFIG
    return config


def get_persona_count_from_config(config: dict[str, Any] | None = None) -> int | None:
    config = config or get_persona_config()
    try:
        count = int(config.get("persona_count"))
    except (TypeError, ValueError):
        count = 0
    if count > 0:
        return count

    blueprints = config.get("persona_blueprints")
    if not isinstance(blueprints, list):
        return None

    filled_blueprints = [
        blueprint
        for blueprint in blueprints
        if isinstance(blueprint, dict) and any(str(value).strip() for value in blueprint.values())
    ]
    return len(filled_blueprints) or None


def get_persona_count(config: dict[str, Any] | None = None) -> int:
    return get_persona_count_from_config(config) or DEFAULT_PERSONA_COUNT


def get_target_condition_from_config(config: dict[str, Any] | None = None) -> str:
    config = config or get_persona_config()
    seed_rules = config.get("seed_rules")
    if not isinstance(seed_rules, dict):
        return ""
    return str(seed_rules.get("target_condition", "")).strip()


def get_service_condition_from_config(config: dict[str, Any] | None = None) -> str:
    config = config or get_persona_config()
    return str(config.get("service_condition", "")).strip()


def get_decision_context_from_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or get_persona_config()
    decision_context = config.get("decision_context", {})
    return decision_context if isinstance(decision_context, dict) else {}


def is_comparison_enabled(config: dict[str, Any] | None = None) -> bool:
    config = config or get_persona_config()
    return bool(config.get("comparison_enabled", False))


def get_output_requirements(config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or get_persona_config()
    output_requirements = config.get("output_requirements", {})
    return output_requirements if isinstance(output_requirements, dict) else {}


def get_questions_from_config(config: dict[str, Any] | None = None) -> list[str]:
    config = config or get_persona_config()
    questions = config.get("questions", [])
    if not isinstance(questions, list):
        return []
    normalized = [str(question).strip() for question in questions if str(question).strip()]
    return normalized if 5 <= len(normalized) <= 10 else []


def get_generated_question_count(config: dict[str, Any] | None = None) -> int:
    config = config or get_persona_config()
    try:
        count = int(config.get("generated_question_count", DEFAULT_QUESTION_COUNT))
    except (TypeError, ValueError):
        return DEFAULT_QUESTION_COUNT
    return max(5, min(10, count))


def ensure_positive_int(value: str, minimum: int = 1, maximum: int | None = None) -> int:
    try:
        number = int(value.strip())
    except ValueError as exc:
        raise ValueError("숫자를 입력해야 합니다.") from exc

    if number < minimum:
        raise ValueError(f"{minimum} 이상의 숫자를 입력해야 합니다.")
    if maximum is not None and number > maximum:
        raise ValueError(f"{maximum} 이하의 숫자를 입력해야 합니다.")
    return number


def write_text_file(path: str | Path, content: str) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def write_json_file(path: str | Path, data: Any) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_json_file(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_output_path(filename: str) -> Path:
    return OUTPUT_DIR / filename


def extract_json(text: str) -> Any:
    cleaned = text.strip()

    fence_match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start_candidates = [idx for idx in (cleaned.find("{"), cleaned.find("[")) if idx != -1]
    if not start_candidates:
        raise ValueError("JSON response not found.")

    start = min(start_candidates)
    end = max(cleaned.rfind("}"), cleaned.rfind("]"))
    if end <= start:
        raise ValueError("JSON response is incomplete.")

    return json.loads(cleaned[start : end + 1])


def call_openai_json(system_prompt: str, user_prompt: str, temperature: float = 0.7) -> Any:
    client = get_openai_client()
    response = client.chat.completions.create(
        model=get_model(),
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content or ""
    return extract_json(content)


def clamp_score(value: Any, minimum: float, maximum: float) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return minimum
    return max(minimum, min(maximum, score))
