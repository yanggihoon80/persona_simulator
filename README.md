# AI 페르소나 기반 사용자 반응 시뮬레이션

서비스 아이디어 또는 의사결정 지원 서비스에 대해 AI 페르소나를 생성하고, 각 페르소나가 서비스를 사용해본 뒤 느낀 가치, 우려, 신뢰 장벽, 구매 가능성을 인터뷰 형태로 시뮬레이션하는 Python CLI 프로그램입니다.

최종 결과는 HTML, Markdown, TXT 리포트로 생성됩니다.

## 핵심 개념

이 프로젝트의 평가 대상은 `decision_context.example_options`에 들어간 예시 선택지가 아니라 `service_condition`에 정의된 서비스 자체입니다.

`example_options`는 서비스가 분석할 수 있는 입력 예시입니다. 예를 들어 사용자가 여러 행동 후보를 넣었을 때 서비스가 어떤 식으로 분석하는지 보여주기 위한 샘플이며, 리포트는 “A안과 B안 중 무엇이 좋은가”보다 “페르소나들이 이 서비스를 써보고 어떤 가치를 느꼈는가”를 중심으로 작성됩니다.

## 파일 구조

```text
main.py
persona_config.json
persona_config.example.json
persona_generator.py
interview_engine.py
summary_engine.py
report_generator.py
utils.py
.env
.env.example
.gitignore
README.md
```

## 실행 요구사항

- Python 3.10+
- OpenAI Python SDK
- OpenAI API Key

필요 패키지가 없다면 설치합니다.

```powershell
pip install openai
```

## 환경 변수

`.env` 파일에 OpenAI API 키를 설정합니다.

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o
```

`.env.example`은 공유용 템플릿입니다. 실제 키는 `.env`에만 넣고 Git에 올리지 않습니다.

## 실행 방법

```powershell
python .\main.py
```

현재 구조는 CLI에서 값을 입력받지 않습니다. 실행에 필요한 값은 `persona_config.json`에서 읽습니다.

필수 값이 없으면 실행 시 에러가 출력됩니다.

필수 값:

- `service_condition`
- `seed_rules.target_condition`
- `comparison_enabled`가 `true`일 때:
  - `decision_context.goal`
  - `decision_context.decision_type`
  - `decision_context.example_options`

## persona_config.json 구조

`persona_config.json`에는 실제 사업 아이디어와 타겟 조건이 들어갈 수 있으므로 Git에 올리지 않습니다. 공유용 더미 구조는 `persona_config.example.json`을 참고합니다.

처음 설정할 때는 예시 파일을 복사해 실제 설정 파일을 만들 수 있습니다.

```powershell
Copy-Item .\persona_config.example.json .\persona_config.json
```

주요 키는 다음과 같습니다.

```json
{
  "persona_count": 10,
  "mode": "decision_simulation",
  "comparison_enabled": true,
  "generated_question_count": 7,
  "service_condition": "서비스 설명",
  "decision_context": {
    "goal": "사용자가 달성하려는 목표",
    "decision_type": "의사결정 유형",
    "example_options": [
      {
        "id": "A",
        "name": "예시 행동 또는 선택지",
        "description": "서비스가 분석할 수 있는 입력 예시"
      }
    ]
  },
  "seed_rules": {
    "target_condition": "타겟 조건",
    "age_range": "25-60",
    "jobs": [],
    "personalities": [],
    "situations": [],
    "must_include_constraints": []
  },
  "questions": [],
  "output_requirements": {
    "include_persona_opinions": true,
    "include_sentiment": true,
    "sentiment_labels": ["긍정", "부정", "중립"],
    "include_scores": true,
    "include_alignment_analysis": true,
    "include_counter_insight": true,
    "include_decision_guidance": true,
    "include_final_summary": true,
    "report_format": "html"
  },
  "persona_blueprints": []
}
```

## 설정 항목 설명

`persona_count`
: 생성할 페르소나 수입니다. 없으면 기본값 5명을 사용합니다.

`service_condition`
: 페르소나들이 사용해보고 평가할 서비스 설명입니다.

`seed_rules.target_condition`
: 어떤 사용자를 타겟으로 볼지 정의합니다. 직업, 매출 수준, 현재 상태, 행동 특성, 핵심 문제 등을 넣습니다.

`decision_context`
: 서비스가 다루는 의사결정 상황입니다. `example_options`는 실제 평가 대상이 아니라 서비스 입력 예시입니다.

`questions`
: 5~10개의 질문을 직접 넣을 수 있습니다. 비어 있으면 AI가 자동 생성합니다.

`generated_question_count`
: 질문 자동 생성 시 만들 질문 수입니다. 5~10 범위로 제한됩니다.

`persona_blueprints`
: 사용자가 특정 페르소나 조건을 직접 줄 수 있습니다. 값이 비어 있으면 `seed_rules`에 따라 AI가 자동 생성합니다.

`output_requirements`
: 리포트에 포함할 분석 섹션을 제어합니다.

`agent_roles`
: AI가 각 단계에서 어떤 관점으로 판단할지 안내합니다. `persona_agents`는 페르소나 인터뷰의 평가 책임, `strategy_agent`는 전략 리뷰, `evaluation_agent`는 종합 평가 관점에 반영됩니다.

## 실행 흐름

1. `persona_config.json` 로드
2. 필수 설정 검증
3. 질문 생성 또는 캐시 사용
4. 페르소나 생성 또는 캐시 사용
5. 페르소나별 인터뷰 수행 또는 캐시 사용
6. 통합 요약 분석 또는 캐시 사용
7. HTML, Markdown, TXT 리포트 생성

## 출력 파일

모든 결과물과 캐시는 `output/` 폴더에 생성됩니다.

```text
output/condition.md
output/questions.json
output/personas.json
output/personas.txt
output/interview_results.json
output/summary.json
output/report.html
output/report.md
output/report.txt
```

## 캐시 동작

각 단계는 캐시 파일이 있으면 AI를 다시 호출하지 않습니다.

- `output/questions.json` 있으면 질문 생성 생략
- `output/personas.json` 있으면 페르소나 생성 생략
- `output/interview_results.json` 있으면 인터뷰 생략
- `output/summary.json` 있으면 요약 분석 생략

새로 생성하고 싶으면 해당 캐시 파일을 삭제합니다.

전체를 새로 만들려면:

```powershell
Remove-Item .\output -Recurse -Force
python .\main.py
```

인터뷰와 요약만 새로 만들려면:

```powershell
Remove-Item .\output\interview_results.json
Remove-Item .\output\summary.json
python .\main.py
```

## 리포트 구성

리포트는 다음 순서로 작성됩니다.

1. 개요
2. 통합분석
3. 최종결과
4. 각 페르소나 결과

각 페르소나 결과는 HTML에서 아코디언 UI로 표시됩니다.

통합분석에는 다음 항목이 포함됩니다.

- 서비스 반응 요약
- 공통 긍정 포인트 TOP 3
- 공통 부정 포인트 TOP 3
- 신뢰 장벽
- 구매/재사용 트리거
- 정렬성 분석
- 반대 인사이트
- 의사결정 가이드
- 가장 큰 실패 요인
- 개선 포인트

## 현재 구현상의 참고 사항

- `example_options`는 서비스 입력 예시입니다. 리포트에서 특정 옵션을 최종 추천하거나 순위화하는 용도로 사용하지 않습니다.
- 페르소나 인터뷰 결과에는 `felt_value`와 `concern`이 포함됩니다.
- 감정 판단은 `긍정`, `부정`, `중립` 중 하나입니다.
- 사용 가능성 점수는 1~10점입니다.
- 최종 시장 적합도 점수는 1~100점입니다.
- `output_requirements`의 새 키인 `include_alignment_analysis`, `include_counter_insight`, `include_decision_guidance`는 리포트 섹션 표시 여부를 제어합니다.

## 한글 깨짐 참고

PowerShell 콘솔에서 `Get-Content`로 한글 JSON을 볼 때 글자가 깨져 보일 수 있습니다. 파일 자체는 UTF-8로 저장되며, 편집기는 UTF-8 설정으로 여는 것을 권장합니다.

필요하면 PowerShell에서 다음을 먼저 실행한 뒤 확인합니다.

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

## 주의사항

- `.env`에는 실제 API 키가 들어가므로 공유하거나 커밋하지 않습니다.
- `output/`은 생성 결과와 캐시를 담는 폴더이며 `.gitignore`에 포함되어 있습니다.
- 프롬프트나 `persona_config.json` 구조를 바꾼 뒤에는 기존 캐시가 이전 구조 결과를 재사용할 수 있으므로 `output/`을 삭제하고 재실행하는 것이 좋습니다.
