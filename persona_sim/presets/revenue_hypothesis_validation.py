from __future__ import annotations

from typing import Any

from persona_sim.presets.base import COMMON_SUMMARY_SCHEMA, PresetSpec


REVENUE_VALIDATION_OUTPUT_SCHEMA: dict[str, Any] = {
    **COMMON_SUMMARY_SCHEMA,
    "analysis_object": {
        "target_customer": "string",
        "value_proposition": "string",
        "pricing": "string",
        "time_to_revenue": "string",
    },
    "assumption_validation": {
        "validated_points": ["string", "string", "string"],
        "invalidated_points": ["string", "string", "string"],
        "unknowns": ["string", "string", "string"],
    },
    "learning_feedback": [
        {
            "expected": "string",
            "actual": "string",
            "delta": "string",
            "gap_analysis": "string",
            "hypothesis_correction": "string",
            "next_iteration_suggestion": "string",
        }
    ],
}


class RevenueHypothesisValidationPreset(PresetSpec):
    def build_question_prompt(self, config: dict[str, Any], question_count: int) -> str:
        return f"""
Generate {question_count} Korean interview questions for revenue hypothesis validation.

Config:
{config}

Important:
- Each option must be evaluated through target customer, value proposition, pricing, and time to revenue.
- These fields live under the generic option.analysis_object key.
- Ask how the persona feels about the service's ability to validate revenue hypotheses.
- Ask about expected revenue, time to revenue, feasibility, and what evidence would change their mind.
- example_options are sample inputs to the service, not the product being sold.

Return exactly {question_count} questions.
""".strip()

    def build_summary_prompt_context(self, config: dict[str, Any]) -> str:
        return f"""
Preset:
{self.name}

Critical requirements:
- Require preset-specific analysis_object analysis for each option when options exist.
- In this preset, analysis_object means revenue hypothesis.
- Evaluate revenue impact, time to revenue, and feasibility.
- Include expected vs actual learning loop when actual_result or learning_history is provided.
- If actual_result is missing, provide the learning structure and next measurement plan.

Expected output schema:
{self.output_schema}
""".strip()


REVENUE_HYPOTHESIS_VALIDATION_PRESET = RevenueHypothesisValidationPreset(
    name="revenue_hypothesis_validation",
    description="Validate revenue hypotheses and support a learning loop from expected versus actual results.",
    required_config_paths=[
        "service_condition",
        "seed_rules.target_condition",
        "decision_context.goal",
        "decision_context.example_options",
    ],
    scoring_focus=[
        "revenue impact",
        "time to revenue",
        "feasibility",
        "hypothesis validity",
        "expected vs actual learning",
    ],
    output_schema=REVENUE_VALIDATION_OUTPUT_SCHEMA,
)
