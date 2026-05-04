from typing import Any

from utils import call_openai_json, clamp_score, get_output_path, get_persona_config, write_json_file


QUESTION_SYSTEM_PROMPT = """
You generate practical market validation interview questions.
Return only valid JSON. Questions must reveal how target users feel after using
the service, whether they trust it, where they feel friction, and whether they
would keep using or pay for it.
""".strip()


INTERVIEW_SYSTEM_PROMPT = """
You are a realistic user interview simulator.
Answer as the given persona, like a real market participant who has tried the service.
Return only valid JSON. Each answer must include sentiment and feasibility score.
Treat example_options as sample inputs the service may analyze, not as the final
product being evaluated.
""".strip()


VALID_SENTIMENTS = {"긍정", "부정", "중립"}


def generate_interview_questions(
    target_condition: str,
    service_description: str,
    seed_rules: dict[str, Any],
    question_count: int,
) -> list[str]:
    persona_config = get_persona_config()
    user_prompt = f"""
Generate {question_count} interview questions for validating this AI service.

Target condition:
{target_condition}

Service condition:
{service_description}

Seed rules:
{seed_rules}

Decision context:
{persona_config.get("decision_context", {})}

Important interpretation:
- decision_context.example_options are only sample user inputs/actions that the service can analyze.
- Do not make the interview about choosing those examples.
- Ask about the user's feeling after using the service, trust in its recommendation, usefulness, friction, purchase intent, and repeat usage.

Required JSON shape:
{{
  "questions": [
    "question text"
  ]
}}

Rules:
- Create exactly {question_count} questions.
- Questions must be written in Korean.
- Avoid generic satisfaction survey questions.
""".strip()

    data = call_openai_json(QUESTION_SYSTEM_PROMPT, user_prompt, temperature=0.55)
    questions = data.get("questions", [])
    normalized = [str(question).strip() for question in questions if str(question).strip()]
    return normalized[:question_count]


def run_interviews(
    personas: list[dict[str, Any]],
    service_description: str,
    questions: list[str],
) -> dict[str, Any]:
    persona_config = get_persona_config()
    results = {
        "service_description": service_description,
        "questions": questions,
        "decision_context": persona_config.get("decision_context", {}),
        "personas": [],
    }

    total = len(personas)
    for index, persona in enumerate(personas, start=1):
        name = persona.get("name", f"Persona {index}")
        print(f"  - 인터뷰 진행 중: {index}/{total} {name}")
        result = interview_persona(persona, service_description, questions, persona_config)
        results["personas"].append(result)
        print(f"  - 인터뷰 완료: {index}/{total} {name}")

    write_json_file(get_output_path("interview_results.json"), results)
    return results


def interview_persona(
    persona: dict[str, Any],
    service_description: str,
    questions: list[str],
    persona_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    persona_config = persona_config or get_persona_config()
    user_prompt = f"""
Interview this persona after they tried the AI service.

Persona:
{persona}

Service condition:
{service_description}

Decision context:
{persona_config.get("decision_context", {})}

Important interpretation:
- example_options are sample actions the service analyzes during usage.
- The persona is evaluating the service experience itself, not the example options as products.
- Answers should describe what the persona felt, trusted, doubted, found useful, or found uncomfortable.

Questions:
{questions}

Required JSON shape:
{{
  "persona_id": {persona.get("id")},
  "persona_name": "{persona.get("name", "")}",
  "answers": [
    {{
      "question": "question text",
      "answer": "first-person realistic answer",
      "sentiment": "긍정|부정|중립",
      "feasibility_score": 1,
      "felt_value": "what felt valuable or empty string",
      "concern": "main concern or empty string"
    }}
  ]
}}

Rules:
- Answer every question exactly once.
- Use the persona's job, age, personality, situation, and problem.
- Sentiment must be exactly one of: 긍정, 부정, 중립.
- feasibility_score means likelihood that this persona would use the service in their real workflow, from 1 to 10.
- Be candid. Include objections when the persona would object.
""".strip()

    data = call_openai_json(INTERVIEW_SYSTEM_PROMPT, user_prompt, temperature=0.75)
    answers = data.get("answers", [])

    normalized_answers = []
    for index, question in enumerate(questions):
        raw = answers[index] if index < len(answers) else {}
        sentiment = str(raw.get("sentiment", "중립")).strip()
        if sentiment not in VALID_SENTIMENTS:
            sentiment = "중립"
        normalized_answers.append(
            {
                "question": str(raw.get("question") or question),
                "answer": str(raw.get("answer", "")),
                "sentiment": sentiment,
                "feasibility_score": int(round(clamp_score(raw.get("feasibility_score", 1), 1, 10))),
                "felt_value": str(raw.get("felt_value", "")),
                "concern": str(raw.get("concern", "")),
            }
        )

    return {
        "persona": persona,
        "answers": normalized_answers,
    }
