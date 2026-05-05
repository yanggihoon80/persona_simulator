from typing import Any

from utils import call_openai_json, clamp_score, get_output_path, get_persona_config, write_json_file


SUMMARY_SYSTEM_PROMPT = """
You are a senior market research analyst.
Analyze how personas reacted after using an AI service.
Return only valid JSON. Focus on user feelings, trust, usefulness, friction,
repeat usage intent, purchase possibility, market risk, and product-market fit.
""".strip()


def summarize_results(
    target_condition: str,
    service_description: str,
    interview_results: dict[str, Any],
) -> dict[str, Any]:
    persona_config = get_persona_config()
    average_feasibility = calculate_average_feasibility(interview_results)

    user_prompt = f"""
Analyze these user interview results.

Target condition:
{target_condition}

Service description:
{service_description}

Decision context:
{persona_config.get("decision_context", {})}

Agent roles:
{persona_config.get("agent_roles", {})}

Output requirements:
{persona_config.get("output_requirements", {})}

Important interpretation:
- decision_context.example_options are sample inputs/actions used to demonstrate the service.
- Do not evaluate those examples as the product.
- Analyze how personas felt about the service itself after using it.

Interview results:
{interview_results}

Average feasibility score calculated from all answers:
{average_feasibility}

Required JSON shape:
{{
  "positive_points_top3": ["point1", "point2", "point3"],
  "negative_points_top3": ["point1", "point2", "point3"],
  "biggest_failure_factor": "single biggest reason this service may fail",
  "improvement_points": ["improvement1", "improvement2", "improvement3"],
  "average_feasibility_score": {average_feasibility},
  "market_fit_score": 1,
  "service_reaction_summary": "how personas felt about the service",
  "trust_barriers": ["barrier1", "barrier2", "barrier3"],
  "purchase_triggers": ["trigger1", "trigger2", "trigger3"],
  "analysis_object": {{
    "target_customer": "who is expected to pay",
    "value_proposition": "why they would pay",
    "pricing": "possible pricing expectation",
    "time_to_revenue": "expected time to revenue"
  }},
  "assumption_validation": {{
    "validated_points": ["validated point1", "validated point2", "validated point3"],
    "invalidated_points": ["invalidated point1", "invalidated point2", "invalidated point3"],
    "unknowns": ["unknown1", "unknown2", "unknown3"]
  }},
  "learning_feedback": ["learning1", "learning2", "learning3"],
  "alignment_analysis": "whether the service aligns with the target user's real situation and direction",
  "counter_insight": "important opposing insight or uncomfortable truth",
  "decision_guidance": "practical guidance for what the user should decide next",
  "strategy_agent_review": "strategic review based on agent_roles.strategy_agent or empty string",
  "execution_plan": [
    {{
      "task": "weekly task name",
      "objective": "objective of this task",
      "steps": [
        {{
          "step": "step name",
          "input": "required input",
          "process": "what to do",
          "output": "expected output"
        }}
      ]
    }}
  ],
  "one_line_conclusion": "one sentence conclusion"
}}

Rules:
- Write every value in Korean.
- Focus on repeated patterns across personas.
- Include emotional reactions and practical objections.
- If output_requirements include alignment/counter/decision guidance, fill those fields with concrete Korean analysis.
- If output_requirements.include_analysis_object is true, fill analysis_object using decision_context.analysis_object_fields when provided.
- If output_requirements.include_assumption_validation is true, compare interview evidence against the analysis object assumptions.
- If output_requirements.include_learning_feedback is true, summarize what should be learned for the next simulation cycle.
- If output_requirements.include_strategy_agent_review is true, write strategy_agent_review using agent_roles.strategy_agent.
- If agent_roles.execution_planner_agent exists or output_requirements.include_execution_plan is true, create execution_plan as practical weekly tasks with Input-Process-Output steps.
- Do not recommend or rank decision_context.example_options.
- market_fit_score must be 1 to 100.
- Keep each bullet concise but specific.
""".strip()

    data = call_openai_json(SUMMARY_SYSTEM_PROMPT, user_prompt, temperature=0.45)
    summary = normalize_summary(data, average_feasibility)
    write_json_file(get_output_path("summary.json"), summary)
    return summary


def calculate_average_feasibility(interview_results: dict[str, Any]) -> float:
    scores = []
    for persona_result in interview_results.get("personas", []):
        for answer in persona_result.get("answers", []):
            scores.append(clamp_score(answer.get("feasibility_score"), 1, 10))
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


def normalize_summary(data: dict[str, Any], average_feasibility: float) -> dict[str, Any]:
    return {
        "positive_points_top3": normalize_list(data.get("positive_points_top3"), 3),
        "negative_points_top3": normalize_list(data.get("negative_points_top3"), 3),
        "biggest_failure_factor": str(data.get("biggest_failure_factor", "")),
        "improvement_points": normalize_list(data.get("improvement_points"), 3),
        "average_feasibility_score": average_feasibility,
        "market_fit_score": int(round(clamp_score(data.get("market_fit_score"), 1, 100))),
        "service_reaction_summary": str(data.get("service_reaction_summary", "")),
        "trust_barriers": normalize_list(data.get("trust_barriers"), 3),
        "purchase_triggers": normalize_list(data.get("purchase_triggers"), 3),
        "analysis_object": normalize_analysis_object(data.get("analysis_object")),
        "assumption_validation": normalize_assumption_validation(data.get("assumption_validation")),
        "learning_feedback": normalize_list(data.get("learning_feedback"), 3),
        "alignment_analysis": str(data.get("alignment_analysis", "")),
        "counter_insight": str(data.get("counter_insight", "")),
        "decision_guidance": str(data.get("decision_guidance", "")),
        "strategy_agent_review": str(data.get("strategy_agent_review", "")),
        "execution_plan": normalize_execution_plan(data.get("execution_plan")),
        "one_line_conclusion": str(data.get("one_line_conclusion", "")),
    }


def normalize_list(value: Any, size: int) -> list[str]:
    if not isinstance(value, list):
        value = []
    items = [str(item) for item in value[:size]]
    while len(items) < size:
        items.append("")
    return items


def normalize_analysis_object(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        value = {}
    return {
        "target_customer": str(value.get("target_customer", "")),
        "value_proposition": str(value.get("value_proposition", "")),
        "pricing": str(value.get("pricing", "")),
        "time_to_revenue": str(value.get("time_to_revenue", "")),
    }


def normalize_assumption_validation(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        value = {}
    return {
        "validated_points": normalize_list(value.get("validated_points"), 3),
        "invalidated_points": normalize_list(value.get("invalidated_points"), 3),
        "unknowns": normalize_list(value.get("unknowns"), 3),
    }


def normalize_execution_plan(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    normalized = []
    for task in value:
        if not isinstance(task, dict):
            continue
        steps = task.get("steps", [])
        if not isinstance(steps, list):
            steps = []
        normalized_steps = []
        for step in steps:
            if not isinstance(step, dict):
                continue
            normalized_steps.append(
                {
                    "step": str(step.get("step", "")),
                    "input": str(step.get("input", "")),
                    "process": str(step.get("process", "")),
                    "output": str(step.get("output", "")),
                }
            )
        normalized.append(
            {
                "task": str(task.get("task", "")),
                "objective": str(task.get("objective", "")),
                "steps": normalized_steps,
            }
        )
    return normalized
