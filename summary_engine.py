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
  "alignment_analysis": "whether the service aligns with the target user's real situation and direction",
  "counter_insight": "important opposing insight or uncomfortable truth",
  "decision_guidance": "practical guidance for what the user should decide next",
  "strategy_agent_review": "strategic review based on agent_roles.strategy_agent or empty string",
  "one_line_conclusion": "one sentence conclusion"
}}

Rules:
- Write every value in Korean.
- Focus on repeated patterns across personas.
- Include emotional reactions and practical objections.
- If output_requirements include alignment/counter/decision guidance, fill those fields with concrete Korean analysis.
- If output_requirements.include_strategy_agent_review is true, write strategy_agent_review using agent_roles.strategy_agent.
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
        "alignment_analysis": str(data.get("alignment_analysis", "")),
        "counter_insight": str(data.get("counter_insight", "")),
        "decision_guidance": str(data.get("decision_guidance", "")),
        "strategy_agent_review": str(data.get("strategy_agent_review", "")),
        "one_line_conclusion": str(data.get("one_line_conclusion", "")),
    }


def normalize_list(value: Any, size: int) -> list[str]:
    if not isinstance(value, list):
        value = []
    items = [str(item) for item in value[:size]]
    while len(items) < size:
        items.append("")
    return items
