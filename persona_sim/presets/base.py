from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PresetSpec:
    name: str
    description: str
    required_config_paths: list[str] = field(default_factory=list)
    scoring_focus: list[str] = field(default_factory=list)
    output_schema: dict[str, Any] = field(default_factory=dict)

    def build_question_prompt(self, config: dict[str, Any], question_count: int) -> str:
        return f"""
Generate {question_count} Korean interview questions for preset '{self.name}'.

Preset description:
{self.description}

Config:
{config}

Rules:
- Questions must validate the service or decision context defined in the config.
- Questions must expose trust, value, objections, willingness to use, and willingness to pay where relevant.
- Return exactly {question_count} questions.
""".strip()

    def build_persona_prompt_context(self, config: dict[str, Any]) -> str:
        return f"""
Preset:
{self.name}

Preset description:
{self.description}

Scoring focus:
{self.scoring_focus}
""".strip()

    def build_interview_prompt_context(self, config: dict[str, Any]) -> str:
        return f"""
Preset:
{self.name}

Interview focus:
{self.scoring_focus}
""".strip()

    def build_summary_prompt_context(self, config: dict[str, Any]) -> str:
        return f"""
Preset:
{self.name}

Expected output schema:
{self.output_schema}
""".strip()


COMMON_SUMMARY_SCHEMA: dict[str, Any] = {
    "positive_points_top3": ["string", "string", "string"],
    "negative_points_top3": ["string", "string", "string"],
    "biggest_failure_factor": "string",
    "improvement_points": ["string", "string", "string"],
    "average_feasibility_score": "number 1-10",
    "market_fit_score": "integer 1-100",
    "service_reaction_summary": "string",
    "trust_barriers": ["string", "string", "string"],
    "purchase_triggers": ["string", "string", "string"],
    "alignment_analysis": "string",
    "counter_insight": "string",
    "decision_guidance": "string",
    "strategy_agent_review": "string",
    "execution_plan": [
        {
            "task": "string",
            "objective": "string",
            "steps": [
                {
                    "step": "string",
                    "input": "string",
                    "process": "string",
                    "output": "string",
                }
            ],
        }
    ],
    "one_line_conclusion": "string",
}
