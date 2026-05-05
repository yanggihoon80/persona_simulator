from persona_sim import PersonaSimulationEngine
from report_generator import generate_report
from utils import get_output_path, get_persona_config, load_env_file


def main() -> None:
    load_env_file()
    print("AI 페르소나 기반 사용자 반응 시뮬레이션")
    print("=" * 44)

    config = get_persona_config()
    engine = PersonaSimulationEngine()
    result = engine.run(config)

    print("\n[4/4] 리포트를 생성합니다...")
    generate_report(
        result["target_condition"],
        result["service_condition"],
        result["personas"],
        result["interview_results"],
        result["summary"],
    )
    print(f"report.html 생성 완료: {get_output_path('report.html').resolve()}")
    print(f"report.md 생성 완료: {get_output_path('report.md').resolve()}")
    print(f"report.txt 생성 완료: {get_output_path('report.txt').resolve()}")


if __name__ == "__main__":
    main()
