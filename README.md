# AI 페르소나 시뮬레이션 엔진

`persona_sim`은 서비스 아이디어, 의사결정, 실행안, 수익 가설 등을 AI 페르소나로 검증하는 범용 시뮬레이션 엔진입니다. 특정 서비스에 고정하지 않고 preset을 바꿔 여러 검증 목적에 재사용하도록 구성했습니다.

최종 결과는 `output/` 폴더에 HTML, Markdown, TXT 리포트로 생성됩니다.

## 구조

```text
persona_sim/
  core/
    agents.py
    cache.py
    config.py
    engine.py
    llm.py
  presets/
    idea_validation.py
    decision_comparison.py
    action_evaluation.py
    revenue_hypothesis_validation.py
main.py
persona_config.json
persona_config.example.json
persona_generator.py
interview_engine.py
summary_engine.py
report_generator.py
utils.py
docs/ARCHITECTURE.md
.env
.env.example
.gitignore
README.md
```

## 설치

Python 3.10 이상이 필요합니다.

```powershell
pip install openai
```

`.env` 파일에 OpenAI API 키를 넣습니다.

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o
```

## 실행

```powershell
python .\main.py
```

이 프로젝트는 실행 중 CLI 입력을 받지 않습니다. 모든 입력은 `persona_config.json`에서 읽습니다.

처음 시작할 때는 예제 파일을 복사해서 실제 설정을 만듭니다.

```powershell
Copy-Item .\persona_config.example.json .\persona_config.json
```

`persona_config.json`에는 실제 사업 아이디어가 들어갈 수 있으므로 `.gitignore`에 포함되어 있습니다. Git에는 더미 데이터인 `persona_config.example.json`만 올립니다.

## persona_config.json 사용법

`persona_config.json`과 `persona_config.example.json`은 항상 같은 구조를 유지해야 합니다. 실제 파일에는 내 아이디어를 넣고, 예제 파일에는 공개 가능한 더미 값만 넣습니다.

필수 값:

- `service_condition`: 페르소나가 경험하고 평가할 대상 설명
- `seed_rules.target_condition`: 어떤 사용자를 타겟으로 볼지에 대한 조건

주요 키:

- `preset`: 실행할 검증 preset입니다. 문자열 하나 또는 배열을 사용할 수 있습니다. 지원 값은 `idea_validation`, `decision_comparison`, `action_evaluation`, `revenue_hypothesis_validation`입니다.
- `persona_count`: 생성할 페르소나 수입니다.
- `generated_question_count`: 질문을 자동 생성할 때 만들 질문 수입니다. 최소 5개 이상을 권장합니다.
- `decision_context`: 검증 목표, 의사결정 유형, 예시 입력, 분석 객체 요구사항을 정의합니다.
- `decision_context.example_options`: 서비스가 처리하거나 비교할 수 있는 예시 입력입니다. 서비스 자체가 아니라 페르소나가 반응할 샘플입니다.
- `decision_context.analysis_object_required`: 옵션별 분석 객체가 필수인지 지정합니다.
- `decision_context.analysis_object_fields`: 옵션별 `analysis_object`가 가져야 할 필드 목록입니다.
- `seed_rules`: 페르소나 자동 생성을 위한 초기 규칙입니다.
- `agent_roles`: 각 에이전트의 역할과 책임을 조정합니다.
- `questions`: 직접 질문을 넣을 수 있습니다. 비워두면 AI가 자동 생성합니다.
- `output_requirements`: 리포트에 포함할 섹션을 제어합니다.
- `persona_blueprints`: 사용자가 직접 페르소나 조건을 추가할 수 있습니다. 값이 비어 있으면 `persona_count`, `service_condition`, `seed_rules`를 기준으로 AI가 채웁니다.

예시 구조:

```json
{
  "persona_count": 5,
  "preset": [
    "idea_validation",
    "action_evaluation"
  ],
  "mode": "service_reaction_simulation",
  "comparison_enabled": false,
  "generated_question_count": 7,
  "service_condition": "검증할 서비스 설명",
  "decision_context": {
    "goal": "검증 목표",
    "decision_type": "의사결정 유형",
    "example_options": [],
    "analysis_object_required": false,
    "analysis_object_fields": []
  },
  "seed_rules": {
    "target_condition": "타겟 조건",
    "age_range": "25-55",
    "jobs": [],
    "personalities": [],
    "situations": [],
    "must_include_constraints": []
  },
  "agent_roles": {
    "persona_agent": {
      "role": "가상 타겟 사용자",
      "task": "현실적인 사용자 반응을 평가합니다."
    },
    "strategy_agent": {
      "role": "전략 분석가",
      "task": "타겟 상황과 서비스의 정렬성을 해석합니다."
    },
    "evaluation_agent": {
      "role": "시장 반응 평가자",
      "task": "반응, 위험, 점수, 의사결정 가이드를 종합합니다."
    },
    "execution_planner_agent": {
      "role": "실행 계획 설계자",
      "task": "검증된 방향을 Task와 Step으로 분해합니다."
    },
    "learning_agent": {
      "role": "학습 루프 분석가",
      "task": "기대 결과와 실제 결과의 차이를 분석합니다."
    }
  },
  "scoring_schema": {
    "persona_reaction_score": "1-100",
    "strategic_fit_score": "1-100",
    "execution_feasibility_score": "1-100",
    "outcome_contribution_score": "1-100",
    "final_action_value_score_formula": "0.3 * persona_reaction_score + 0.3 * strategic_fit_score + 0.2 * execution_feasibility_score + 0.2 * outcome_contribution_score"
  },
  "questions": [],
  "output_requirements": {
    "include_persona_opinions": true,
    "include_sentiment": true,
    "sentiment_labels": ["긍정", "부정", "중립"],
    "include_analysis_object": true,
    "include_assumption_validation": true,
    "include_learning_feedback": true,
    "include_option_comparison": false,
    "include_strategy_agent_review": true,
    "include_scores": true,
    "include_alignment_analysis": true,
    "include_counter_insight": true,
    "include_decision_guidance": true,
    "include_execution_plan": true,
    "include_final_summary": true,
    "report_format": "html"
  },
  "persona_blueprints": [
    {
      "job": "",
      "age": "",
      "personality": "",
      "current_situation": "",
      "main_problem": "",
      "extra_notes": ""
    }
  ]
}
```

## Preset

- `idea_validation`: 아이디어 또는 서비스의 초기 반응을 검증합니다.
- `decision_comparison`: 여러 선택지의 장단점과 의사결정 기준을 비교합니다.
- `action_evaluation`: 실행할 행동의 가치, 난이도, 우선순위를 평가합니다.
- `revenue_hypothesis_validation`: 수익 가설을 검증하는 preset입니다. 이 preset에서만 `analysis_object`를 수익 가설 객체로 해석합니다.

여러 preset을 동시에 적용하려면 배열로 작성합니다.

```json
{
  "preset": ["idea_validation", "action_evaluation"]
}
```

이 경우 질문 생성, 페르소나 인터뷰, 요약 분석 프롬프트에 두 preset의 관점이 함께 반영됩니다. 질문 수는 preset별로 각각 생성하지 않고 `generated_question_count`에 맞춰 통합 질문으로 생성합니다.

`revenue_hypothesis_validation`을 사용할 때 `decision_context.analysis_object_required`가 `true`라면 각 `example_options[]`에 다음과 같은 `analysis_object`가 필요합니다.

```json
{
  "id": "A",
  "name": "옵션 A",
  "description": "검증할 옵션 설명",
  "analysis_object": {
    "target_customer": "대상 고객",
    "value_proposition": "가치 제안",
    "pricing": "가격 또는 과금 방식",
    "time_to_revenue": "수익 발생까지 예상 시간"
  }
}
```

## Agent Roles

기본 에이전트:

- `persona_agent`: 실제 타겟 사용자처럼 답변합니다.
- `strategy_agent`: 전략적 정렬성과 시장 맥락을 분석합니다.
- `evaluation_agent`: 반응, 위험, 점수, 의사결정 가이드를 종합합니다.
- `execution_planner_agent`: 검증된 방향을 실행 계획으로 나눕니다.
- `learning_agent`: 기대 결과와 실제 결과를 비교하고 다음 반복을 제안합니다.

`persona_config.json`의 `agent_roles`에서 역할 설명을 바꾸면 프롬프트에 반영됩니다.

## 출력 파일

모든 결과와 캐시는 `output/` 폴더에 생성됩니다.

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

캐시 파일이 있으면 같은 단계에서 AI를 다시 호출하지 않습니다.

- `output/questions.json`: 질문 생성 캐시
- `output/personas.json`: 페르소나 생성 캐시
- `output/interview_results.json`: 인터뷰 결과 캐시
- `output/summary.json`: 요약 분석 캐시

새로 생성하려면 `output/` 폴더나 해당 캐시 파일을 삭제한 뒤 다시 실행합니다.

```powershell
Remove-Item .\output -Recurse -Force
python .\main.py
```

## 리포트 구성

리포트는 다음 순서로 생성됩니다.

1. 개요
2. 통합분석
3. 최종결과
4. 각 페르소나 결과

HTML 리포트의 각 페르소나 결과는 아코디언 UI로 표시됩니다. 감정 상태는 긍정은 녹색, 부정은 빨간색, 중립은 회색으로 표시하고 점수는 progress bar 형태로 보여줍니다.

## 설계 메모

- core engine은 preset을 동적으로 선택하고 실행합니다.
- 특정 서비스 전용 키는 core config에서 제거하고 `analysis_object` 같은 범용 키로 처리합니다.
- 수익 가설 검증은 core에 하드코딩하지 않고 `revenue_hypothesis_validation` preset에서만 해석합니다.
- `persona_config.example.json`은 공개 가능한 더미 데이터만 담아야 합니다.
