from typing import Any

from utils import call_openai_json, get_output_path, get_persona_config, write_json_file, write_text_file


PERSONA_SYSTEM_PROMPT = """
You generate realistic market user personas for product validation.
Return only valid JSON. Create diverse people with different attitudes, buying power,
constraints, skepticism levels, and urgency. The personas must be plausible members
of the requested target market, not generic stereotypes.
""".strip()


def generate_personas(target_condition: str, service_description: str, persona_count: int) -> list[dict[str, Any]]:
    persona_config = get_persona_config()
    user_prompt = f"""
Create {persona_count} distinct personas for interviewing a service idea.

Target condition:
{target_condition}

Service description:
{service_description}

Decision context:
{persona_config.get("decision_context", {})}

Mode:
{persona_config.get("mode", "")}

Required JSON shape:
{{
  "personas": [
    {{
      "id": 1,
      "name": "fictional Korean or globally plausible name",
      "job": "job or role",
      "age": 35,
      "personality": "one of conservative/aggressive/skeptical/practical/curious/price-sensitive/etc.",
      "current_situation": "specific current context",
      "main_problem": "specific pain point related to the service market"
    }}
  ]
}}

Rules:
- Create exactly {persona_count} personas.
- Make each persona meaningfully different.
- Use concrete market details and realistic constraints.
- Do not mention that the persona is AI-generated.

Persona configuration JSON:
{persona_config}

Configuration rules:
- If persona_blueprints contains filled values, follow them as closely as possible.
- If persona_blueprints is empty or mostly blank, generate personas from seed_rules.
- If persona_count exists in the JSON, it describes the intended number of personas.
- Always include age, job, personality, current_situation, and main_problem.
- If decision_context.example_options exists, treat them only as sample inputs the service can analyze.
- Create personas who can realistically judge the service experience, not personas who only compare those examples.
""".strip()

    data = call_openai_json(PERSONA_SYSTEM_PROMPT, user_prompt, temperature=0.85)
    personas = data.get("personas", [])

    normalized = []
    for index, persona in enumerate(personas[:persona_count], start=1):
        normalized.append(
            {
                "id": int(persona.get("id") or index),
                "name": str(persona.get("name", f"Persona {index}")),
                "job": str(persona.get("job", "")),
                "age": str(persona.get("age", "")),
                "personality": str(persona.get("personality", "")),
                "current_situation": str(persona.get("current_situation", "")),
                "main_problem": str(persona.get("main_problem", "")),
            }
        )

    save_personas(normalized)
    write_json_file(get_output_path("personas.json"), {"personas": normalized})
    return normalized


def save_personas(personas: list[dict[str, Any]], path: str | None = None) -> None:
    path = path or get_output_path("personas.txt")
    blocks = []
    for persona in personas:
        blocks.append(
            "\n".join(
                [
                    f"[{persona['id']}] {persona['name']}",
                    f"- 직업: {persona['job']}",
                    f"- 나이: {persona['age']}",
                    f"- 성격: {persona['personality']}",
                    f"- 현재 상황: {persona['current_situation']}",
                    f"- 주요 문제: {persona['main_problem']}",
                ]
            )
        )
    write_text_file(path, "\n\n".join(blocks) + "\n")
