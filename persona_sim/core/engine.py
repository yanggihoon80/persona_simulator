from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from persona_generator import save_personas
from persona_sim.core.agents import agents_for_prompt, merge_agent_roles
from persona_sim.core.cache import JsonCache
from persona_sim.core.config import (
    get_persona_count,
    get_preset_names,
    get_question_count,
    get_questions,
    get_service_condition,
    get_target_condition,
)
from persona_sim.core.llm import LLMClient
from persona_sim.presets.registry import get_preset
from utils import clamp_score, write_text_file


KOREAN_ONLY_RULES = """
Language rules:
- All user-facing string values must be written in Korean only.
- Technical JSON keys may remain English.
- Do not write English sentences, English headings, or English explanations in answers, summaries, persona fields, feedback, or plans.
- If an English product name or fixed brand name appears in the input, keep the name as-is, but explain everything around it in Korean.
""".strip()

ALLOWED_ENGLISH_TERMS = {
    "AI",
    "B2B",
    "FlowX",
    "Input",
    "JSON",
    "KPI",
    "Output",
    "PickSense",
    "Process",
    "Step",
    "Task",
    "To-do",
}


class CompositePreset:
    def __init__(self, presets: list[Any]) -> None:
        if not presets:
            raise ValueError("At least one preset is required.")
        self.presets = presets
        self.names = [preset.name for preset in presets]
        self.name = "+".join(self.names)
        self.description = "\n".join(f"- {preset.name}: {preset.description}" for preset in presets)
        self.required_config_paths = self._merge_required_paths()
        self.scoring_focus = self._merge_list("scoring_focus")
        self.output_schema = self._merge_output_schema()

    def build_question_prompt(self, config: dict[str, Any], question_count: int) -> str:
        contexts = "\n\n".join(preset.build_question_prompt(config, question_count) for preset in self.presets)
        return f"""
Generate one unified set of {question_count} Korean interview questions for multiple presets.

Active presets:
{self.description}

Preset-specific guidance:
{contexts}

Rules:
- Return exactly {question_count} questions total, not {question_count} questions per preset.
- Cover the combined intent of all active presets.
- Avoid duplicate questions.
- Every question must be written in Korean only.
{KOREAN_ONLY_RULES}
""".strip()

    def build_persona_prompt_context(self, config: dict[str, Any]) -> str:
        return "\n\n".join(preset.build_persona_prompt_context(config) for preset in self.presets)

    def build_interview_prompt_context(self, config: dict[str, Any]) -> str:
        return "\n\n".join(preset.build_interview_prompt_context(config) for preset in self.presets)

    def build_summary_prompt_context(self, config: dict[str, Any]) -> str:
        return f"""
Active presets:
{self.description}

Combined scoring focus:
{self.scoring_focus}

Combined expected output schema:
{self.output_schema}

Preset-specific summary guidance:
{chr(10).join(preset.build_summary_prompt_context(config) for preset in self.presets)}

{KOREAN_ONLY_RULES}
""".strip()

    def _merge_required_paths(self) -> list[str]:
        paths: list[str] = []
        for preset in self.presets:
            for path in preset.required_config_paths:
                if path not in paths:
                    paths.append(path)
        return paths

    def _merge_list(self, attribute: str) -> list[str]:
        values: list[str] = []
        for preset in self.presets:
            for value in getattr(preset, attribute, []):
                if value not in values:
                    values.append(value)
        return values

    def _merge_output_schema(self) -> dict[str, Any]:
        schema: dict[str, Any] = {}
        for preset in self.presets:
            schema.update(preset.output_schema)
        return schema

    def has_preset(self, name: str) -> bool:
        return name in self.names


class PersonaSimulationEngine:
    def __init__(
        self,
        llm: LLMClient | None = None,
        cache: JsonCache | None = None,
        use_cache: bool = True,
    ) -> None:
        self.llm = llm or LLMClient()
        self.cache = cache or JsonCache()
        self.use_cache = use_cache

    def run(self, config: dict[str, Any]) -> dict[str, Any]:
        self.cache.set_cache_key(self.build_cache_key(config))
        presets = [get_preset(name) for name in get_preset_names(config)]
        preset = CompositePreset(presets)
        agents = merge_agent_roles(config.get("agent_roles"))
        self.validate(config, preset)

        target_condition = get_target_condition(config)
        service_condition = get_service_condition(config)
        persona_count = get_persona_count(config)

        questions = self.get_or_create_questions(config, preset)
        self.save_condition(config, target_condition, service_condition, questions, persona_count, preset.name)

        personas = self.get_or_create_personas(config, preset, agents, target_condition, service_condition, persona_count)
        save_personas(personas, self.cache.path("personas.txt"))

        interviews = self.get_or_create_interviews(config, preset, agents, service_condition, questions, personas)
        summary = self.get_or_create_summary(config, preset, agents, target_condition, service_condition, interviews)

        return {
            "preset": preset.names,
            "target_condition": target_condition,
            "service_condition": service_condition,
            "questions": questions,
            "personas": personas,
            "interview_results": interviews,
            "summary": summary,
        }

    def build_cache_key(self, config: dict[str, Any]) -> str:
        payload = json.dumps(
            {"prompt_version": "ko-only-v3", "config": config},
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def validate(self, config: dict[str, Any], preset: Any) -> None:
        missing = []
        for path in preset.required_config_paths:
            if not self._has_path(config, path):
                missing.append(path)

        if preset.has_preset("revenue_hypothesis_validation"):
            decision_context = config.get("decision_context", {})
            options = decision_context.get("example_options", []) if isinstance(decision_context, dict) else []
            required_fields = decision_context.get("analysis_object_fields", []) if isinstance(decision_context, dict) else []
            if not required_fields:
                required_fields = ["target_customer", "value_proposition", "pricing", "time_to_revenue"]

            for index, option in enumerate(options):
                if not isinstance(option, dict):
                    continue
                analysis_object = option.get("analysis_object", {})
                if not isinstance(analysis_object, dict):
                    missing.append(f"decision_context.example_options[{index}].analysis_object")
                    continue
                for field in required_fields:
                    if not str(analysis_object.get(field, "")).strip():
                        missing.append(f"decision_context.example_options[{index}].analysis_object.{field}")

        if missing:
            joined = ", ".join(missing)
            raise SystemExit(f"ERROR: persona_config.json missing required values for preset '{preset.name}': {joined}")

    def get_or_create_questions(self, config: dict[str, Any], preset: Any) -> list[str]:
        cached = self.cache.load_list("questions.json", "questions") if self.use_cache else []
        if cached:
            print(f"\n[0/4] 질문 캐시 사용: {self.cache.path('questions.json')}")
            return [str(question) for question in cached if str(question).strip()]

        configured = get_questions(config)
        if configured:
            print("\n[0/4] persona_config.json의 질문 리스트를 사용합니다.")
            self.cache.save("questions.json", {"questions": configured})
            return configured

        question_count = get_question_count(config)
        print("\n[0/4] 질문 캐시가 없어 AI가 인터뷰 질문을 생성합니다...")
        data = self.llm.json(
            "You generate precise Korean interview questions. Return only valid JSON. Every user-facing value must be Korean only.",
            preset.build_question_prompt(config, question_count),
            temperature=0.55,
        )
        data = self.ensure_korean_json(data, "interview questions")
        questions = [str(question).strip() for question in data.get("questions", []) if str(question).strip()]
        questions = questions[:question_count]
        self.cache.save("questions.json", {"questions": questions})
        return questions

    def get_or_create_personas(
        self,
        config: dict[str, Any],
        preset: Any,
        agents: dict[str, Any],
        target_condition: str,
        service_condition: str,
        persona_count: int,
    ) -> list[dict[str, Any]]:
        cached = self.cache.load_list("personas.json", "personas") if self.use_cache else []
        if cached:
            print(f"\n[1/4] 페르소나 캐시 사용: {self.cache.path('personas.json')}")
            return [persona for persona in cached if isinstance(persona, dict)]

        print("\n[1/4] 페르소나 캐시가 없어 AI가 페르소나를 생성합니다...")
        prompt = f"""
Create {persona_count} realistic personas for this simulation.

Target condition:
{target_condition}

Service condition:
{service_condition}

Preset context:
{preset.build_persona_prompt_context(config)}

Agent roles:
{agents_for_prompt(agents)}

Full config:
{config}

Required JSON:
{{
  "personas": [
    {{
      "id": 1,
      "name": "가상 이름",
      "job": "직업",
      "age": "나이",
      "personality": "성격",
      "current_situation": "구체적인 현재 상황",
      "main_problem": "주요 문제"
    }}
  ]
}}

Rules:
- Create exactly {persona_count} personas.
- Make personas meaningfully different.
- Keep them realistic for the target condition.
{KOREAN_ONLY_RULES}
""".strip()
        data = self.llm.json(
            "You generate realistic Korean market personas. Return only valid JSON. Every user-facing value must be Korean only.",
            prompt,
            temperature=0.85,
        )
        data = self.ensure_korean_json(data, "personas")
        personas = self.normalize_personas(data.get("personas", []), persona_count)
        self.cache.save("personas.json", {"personas": personas})
        return personas

    def get_or_create_interviews(
        self,
        config: dict[str, Any],
        preset: Any,
        agents: dict[str, Any],
        service_condition: str,
        questions: list[str],
        personas: list[dict[str, Any]],
    ) -> dict[str, Any]:
        cached = self.cache.load_dict("interview_results.json") if self.use_cache else {}
        if cached:
            print(f"\n[2/4] 인터뷰 결과 캐시 사용: {self.cache.path('interview_results.json')}")
            return cached

        print("\n[2/4] 인터뷰 결과 캐시가 없어 페르소나 인터뷰를 수행합니다...")
        results: dict[str, Any] = {
            "service_description": service_condition,
            "questions": questions,
            "preset": preset.name,
            "decision_context": config.get("decision_context", {}),
            "personas": [],
        }
        total = len(personas)
        for index, persona in enumerate(personas, start=1):
            name = persona.get("name", f"Persona {index}")
            print(f"  - 인터뷰 진행 중: {index}/{total} {name}")
            results["personas"].append(
                self.interview_persona(config, preset, agents, persona, service_condition, questions)
            )
            print(f"  - 인터뷰 완료: {index}/{total} {name}")

        self.cache.save("interview_results.json", results)
        return results

    def interview_persona(
        self,
        config: dict[str, Any],
        preset: Any,
        agents: dict[str, Any],
        persona: dict[str, Any],
        service_condition: str,
        questions: list[str],
    ) -> dict[str, Any]:
        prompt = f"""
Interview this persona after they experience the service or simulation described by the preset.

Persona:
{persona}

Service condition:
{service_condition}

Preset interview context:
{preset.build_interview_prompt_context(config)}

Agent roles:
{agents_for_prompt(agents)}

Config:
{config}

Questions:
{questions}

Required JSON:
{{
  "answers": [
    {{
      "question": "질문 원문",
      "answer": "1인칭의 현실적인 답변",
      "sentiment": "긍정|부정|중립",
      "feasibility_score": 1,
      "felt_value": "느낀 가치",
      "concern": "주요 우려"
    }}
  ]
}}

Rules:
- Answer every question once.
- Treat example_options as sample inputs unless the preset explicitly says otherwise.
- feasibility_score is 1-10.
- The sentiment value must be exactly one of: 긍정, 부정, 중립.
{KOREAN_ONLY_RULES}
""".strip()
        data = self.llm.json(
            "You simulate realistic Korean persona interviews. Return only valid JSON. Every user-facing value must be Korean only.",
            prompt,
            temperature=0.75,
        )
        data = self.ensure_korean_json(data, "persona interview answers")
        answers = self.normalize_answers(data.get("answers", []), questions)
        return {"persona": persona, "answers": answers}

    def get_or_create_summary(
        self,
        config: dict[str, Any],
        preset: Any,
        agents: dict[str, Any],
        target_condition: str,
        service_condition: str,
        interviews: dict[str, Any],
    ) -> dict[str, Any]:
        cached = self.cache.load_dict("summary.json") if self.use_cache else {}
        if cached:
            print(f"\n[3/4] 요약 분석 캐시 사용: {self.cache.path('summary.json')}")
            return cached

        print("\n[3/4] 요약 분석 캐시가 없어 전체 결과를 분석합니다...")
        average_feasibility = self.calculate_average_feasibility(interviews)
        prompt = f"""
Analyze this persona simulation result.

Target condition:
{target_condition}

Service condition:
{service_condition}

Preset summary context:
{preset.build_summary_prompt_context(config)}

Agent roles:
{agents_for_prompt(agents)}

Config:
{config}

Interview results:
{interviews}

Average feasibility score:
{average_feasibility}

Return valid JSON following the preset schema.
{KOREAN_ONLY_RULES}

For revenue_hypothesis_validation, interpret analysis_object as the preset-specific revenue hypothesis and include expected vs actual learning feedback:
- expected
- actual
- delta
- gap_analysis
- hypothesis_correction
- next_iteration_suggestion
If actual data is not present, define the next measurement plan and mark unknown actuals clearly.
""".strip()
        data = self.llm.json(
            "You are a senior Korean market research, strategy, execution, and learning-loop analyst. Return only valid JSON. Every user-facing value must be Korean only.",
            prompt,
            temperature=0.45,
        )
        data = self.ensure_korean_json(data, "summary analysis")
        summary = self.normalize_summary(data, average_feasibility)
        self.cache.save("summary.json", summary)
        return summary

    def save_condition(
        self,
        config: dict[str, Any],
        target_condition: str,
        service_condition: str,
        questions: list[str],
        persona_count: int,
        preset_name: str,
    ) -> None:
        question_text = "\n".join(f"{index}. {question}" for index, question in enumerate(questions, start=1))
        content = f"""# Persona Simulation Condition

## Preset
{preset_name}

## Target Condition
{target_condition}

## Service Condition
{service_condition}

## Config
{config}

## Questions
{question_text}

## Persona Count
{persona_count}
"""
        write_text_file(self.cache.path("condition.md"), content)
        print(f"\n{self.cache.path('condition.md')} 저장 완료")

    def normalize_personas(self, personas: Any, persona_count: int) -> list[dict[str, Any]]:
        if not isinstance(personas, list):
            personas = []
        normalized = []
        for index, persona in enumerate(personas[:persona_count], start=1):
            if not isinstance(persona, dict):
                persona = {}
            normalized.append(
                {
                    "id": int(persona.get("id") or index),
                    "name": str(persona.get("name", f"페르소나 {index}")),
                    "job": str(persona.get("job", "")),
                    "age": str(persona.get("age", "")),
                    "personality": str(persona.get("personality", "")),
                    "current_situation": str(persona.get("current_situation", "")),
                    "main_problem": str(persona.get("main_problem", "")),
                }
            )
        return normalized

    def normalize_answers(self, answers: Any, questions: list[str]) -> list[dict[str, Any]]:
        if not isinstance(answers, list):
            answers = []
        normalized = []
        for index, question in enumerate(questions):
            raw = answers[index] if index < len(answers) and isinstance(answers[index], dict) else {}
            sentiment = str(raw.get("sentiment", "중립")).strip()
            if sentiment not in {"긍정", "부정", "중립"}:
                sentiment = "중립"
            normalized.append(
                {
                    "question": str(raw.get("question") or question),
                    "answer": str(raw.get("answer", "")),
                    "sentiment": sentiment,
                    "feasibility_score": int(round(clamp_score(raw.get("feasibility_score", 1), 1, 10))),
                    "felt_value": str(raw.get("felt_value", "")),
                    "concern": str(raw.get("concern", "")),
                }
            )
        return normalized

    def normalize_summary(self, data: dict[str, Any], average_feasibility: float) -> dict[str, Any]:
        def list3(key: str) -> list[str]:
            value = data.get(key, [])
            if not isinstance(value, list):
                value = []
            items = [str(item) for item in value[:3]]
            while len(items) < 3:
                items.append("")
            return items

        analysis_object = data.get("analysis_object")
        assumption_validation = data.get("assumption_validation")

        return {
            "positive_points_top3": list3("positive_points_top3"),
            "negative_points_top3": list3("negative_points_top3"),
            "biggest_failure_factor": str(data.get("biggest_failure_factor", "")),
            "improvement_points": list3("improvement_points"),
            "average_feasibility_score": average_feasibility,
            "market_fit_score": int(round(clamp_score(data.get("market_fit_score"), 1, 100))),
            "service_reaction_summary": str(data.get("service_reaction_summary", "")),
            "trust_barriers": list3("trust_barriers"),
            "purchase_triggers": list3("purchase_triggers"),
            "analysis_object": analysis_object if isinstance(analysis_object, dict) else {},
            "assumption_validation": assumption_validation if isinstance(assumption_validation, dict) else {},
            "learning_feedback": data.get("learning_feedback", []) if isinstance(data.get("learning_feedback"), list) else [],
            "alignment_analysis": str(data.get("alignment_analysis", "")),
            "counter_insight": str(data.get("counter_insight", "")),
            "decision_guidance": str(data.get("decision_guidance", "")),
            "strategy_agent_review": str(data.get("strategy_agent_review", "")),
            "execution_plan": data.get("execution_plan", []) if isinstance(data.get("execution_plan"), list) else [],
            "one_line_conclusion": str(data.get("one_line_conclusion", "")),
            "raw_summary": data,
        }

    def calculate_average_feasibility(self, interview_results: dict[str, Any]) -> float:
        scores = []
        for persona_result in interview_results.get("personas", []):
            for answer in persona_result.get("answers", []):
                if isinstance(answer, dict):
                    scores.append(clamp_score(answer.get("feasibility_score"), 1, 10))
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 2)

    def ensure_korean_json(self, data: Any, label: str) -> Any:
        if not self.has_english_user_values(data):
            return data

        prompt = f"""
The following JSON for {label} contains English user-facing string values.

Rewrite the JSON so that every user-facing string value is Korean only.
Preserve the exact same JSON keys and overall structure.
Do not translate technical JSON keys.
Allowed fixed terms may remain as-is only when they are brand or technical terms: {sorted(ALLOWED_ENGLISH_TERMS)}

JSON:
{json.dumps(data, ensure_ascii=False, indent=2)}
""".strip()
        fixed = self.llm.json(
            "Return only valid JSON. Translate or rewrite every user-facing string value into Korean only while preserving keys.",
            prompt,
            temperature=0.1,
        )
        return fixed if isinstance(fixed, type(data)) else data

    def has_english_user_values(self, value: Any) -> bool:
        if isinstance(value, dict):
            return any(self.has_english_user_values(item) for item in value.values())
        if isinstance(value, list):
            return any(self.has_english_user_values(item) for item in value)
        if not isinstance(value, str):
            return False

        words = re.findall(r"[A-Za-z][A-Za-z'-]*", value)
        meaningful_words = [
            word
            for word in words
            if word not in ALLOWED_ENGLISH_TERMS and len(word) > 2
        ]
        return len(meaningful_words) >= 3

    def _has_path(self, config: dict[str, Any], dotted_path: str) -> bool:
        current: Any = config
        for part in dotted_path.split("."):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        if isinstance(current, str):
            return bool(current.strip())
        if isinstance(current, list):
            return bool(current)
        return current is not None
