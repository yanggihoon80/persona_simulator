from interview_engine import generate_interview_questions, run_interviews
from persona_generator import generate_personas, save_personas
from report_generator import generate_report
from summary_engine import summarize_results
from utils import (
    get_generated_question_count,
    get_output_path,
    get_persona_config,
    get_persona_count,
    get_questions_from_config,
    get_service_condition_from_config,
    get_target_condition_from_config,
    is_comparison_enabled,
    load_env_file,
    read_json_file,
    write_json_file,
    write_text_file,
)


def main() -> None:
    load_env_file()
    print("AI 페르소나 기반 사용자 반응 시뮬레이션")
    print("=" * 44)

    persona_config = get_persona_config()
    target_condition = get_target_condition_from_config(persona_config)
    service_description = get_service_condition_from_config(persona_config)
    validate_required_config(persona_config, target_condition, service_description)

    seed_rules = persona_config.get("seed_rules", {})
    persona_count = get_persona_count(persona_config)

    questions = get_or_create_questions(persona_config, target_condition, service_description, seed_rules)
    save_condition(persona_config, target_condition, service_description, questions, persona_count)

    personas = get_or_create_personas(target_condition, service_description, persona_count)
    print(f"{get_output_path('personas.txt')} 저장 완료 ({len(personas)}명)")

    interview_results = get_or_create_interview_results(personas, service_description, questions)
    print(f"{get_output_path('interview_results.json')} 저장 완료")

    summary = get_or_create_summary(target_condition, service_description, interview_results)

    print("\n[4/4] 리포트를 생성합니다...")
    generate_report(target_condition, service_description, personas, interview_results, summary)
    print(f"report.html 생성 완료: {get_output_path('report.html').resolve()}")
    print(f"report.md 생성 완료: {get_output_path('report.md').resolve()}")
    print(f"report.txt 생성 완료: {get_output_path('report.txt').resolve()}")


def get_or_create_questions(
    persona_config: dict,
    target_condition: str,
    service_description: str,
    seed_rules: dict,
) -> list[str]:
    cached = load_questions_from_cache()
    if cached:
        print(f"\n[0/4] 질문 캐시 사용: {get_output_path('questions.json')}")
        return cached

    configured = get_questions_from_config(persona_config)
    if configured:
        print("\n[0/4] persona_config.json의 질문 리스트를 사용합니다.")
        write_json_file(get_output_path("questions.json"), {"questions": configured})
        return configured

    print("\n[0/4] 질문 캐시가 없어 AI가 인터뷰 질문을 생성합니다...")
    questions = generate_interview_questions(
        target_condition=target_condition,
        service_description=service_description,
        seed_rules=seed_rules if isinstance(seed_rules, dict) else {},
        question_count=get_generated_question_count(persona_config),
    )
    write_json_file(get_output_path("questions.json"), {"questions": questions})
    return questions


def get_or_create_personas(
    target_condition: str,
    service_description: str,
    persona_count: int,
) -> list[dict]:
    cached = load_personas_from_cache()
    if cached:
        print(f"\n[1/4] 페르소나 캐시 사용: {get_output_path('personas.json')}")
        save_personas(cached)
        return cached

    print("\n[1/4] 페르소나 캐시가 없어 AI가 페르소나를 생성합니다...")
    return generate_personas(target_condition, service_description, persona_count)


def get_or_create_interview_results(
    personas: list[dict],
    service_description: str,
    questions: list[str],
) -> dict:
    cached = load_dict_cache("interview_results.json")
    if cached:
        print(f"\n[2/4] 인터뷰 결과 캐시 사용: {get_output_path('interview_results.json')}")
        return cached

    print("\n[2/4] 인터뷰 결과 캐시가 없어 페르소나 인터뷰를 수행합니다...")
    return run_interviews(personas, service_description, questions)


def get_or_create_summary(
    target_condition: str,
    service_description: str,
    interview_results: dict,
) -> dict:
    cached = load_dict_cache("summary.json")
    if cached:
        print(f"\n[3/4] 요약 분석 캐시 사용: {get_output_path('summary.json')}")
        return cached

    print("\n[3/4] 요약 분석 캐시가 없어 전체 결과를 분석합니다...")
    return summarize_results(target_condition, service_description, interview_results)


def load_questions_from_cache() -> list[str]:
    data = load_dict_cache("questions.json")
    if not data:
        return []

    questions = data.get("questions", [])
    if not isinstance(questions, list):
        return []
    return [str(question).strip() for question in questions if str(question).strip()]


def load_personas_from_cache() -> list[dict]:
    data = load_dict_cache("personas.json")
    if not data:
        return []

    personas = data.get("personas", [])
    if not isinstance(personas, list):
        return []
    return [persona for persona in personas if isinstance(persona, dict)]


def load_dict_cache(filename: str) -> dict:
    path = get_output_path(filename)
    if not path.exists():
        return {}

    try:
        data = read_json_file(path)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def validate_required_config(
    persona_config: dict,
    target_condition: str,
    service_description: str,
) -> None:
    missing = []
    if not target_condition:
        missing.append("seed_rules.target_condition")
    if not service_description:
        missing.append("service_condition")
    if is_comparison_enabled(persona_config):
        decision_context = persona_config.get("decision_context", {})
        if not isinstance(decision_context, dict):
            missing.append("decision_context")
        else:
            if not str(decision_context.get("goal", "")).strip():
                missing.append("decision_context.goal")
            if not str(decision_context.get("decision_type", "")).strip():
                missing.append("decision_context.decision_type")
            options = decision_context.get("example_options", [])
            if not isinstance(options, list) or not options:
                missing.append("decision_context.example_options")

    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"ERROR: persona_config.json에 필수 값이 없습니다: {joined}")


def save_condition(
    persona_config: dict,
    target_condition: str,
    service_description: str,
    questions: list[str],
    persona_count: int,
) -> None:
    question_text = "\n".join(f"{index}. {question}" for index, question in enumerate(questions, start=1))
    content = f"""# 사용자 반응 시뮬레이션 조건

## 타겟 조건
{target_condition}

## 서비스 설명
{service_description}

## 실행 모드
{persona_config.get("mode", "")}

## 비교 활성화
{persona_config.get("comparison_enabled", False)}

## 의사결정 컨텍스트
{persona_config.get("decision_context", {})}

## 에이전트 역할
{persona_config.get("agent_roles", {})}

## 점수 체계
{persona_config.get("scoring_schema", {})}

## 질문 리스트
{question_text}

## 페르소나 수
{persona_count}
"""
    write_text_file(get_output_path("condition.md"), content)
    print(f"\n{get_output_path('condition.md')} 저장 완료")


if __name__ == "__main__":
    main()
