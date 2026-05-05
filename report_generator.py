from html import escape
from typing import Any

from utils import get_agent_roles, get_output_path, get_output_requirements, write_text_file


SENTIMENT_CLASS = {
    "긍정": "positive",
    "부정": "negative",
    "중립": "neutral",
}

FIELD_LABELS = {
    "expected": "예상",
    "actual": "실제",
    "delta": "차이",
    "gap_analysis": "차이 분석",
    "hypothesis_correction": "가설 수정",
    "assumption_correction": "가정 수정",
    "next_iteration_suggestion": "다음 반복 제안",
    "target_customer": "대상 고객",
    "value_proposition": "제공 가치",
    "pricing": "가격",
    "time_to_revenue": "결과 발생 시점",
}

CARD_HELP = {
    "시장 반응과 구매 신호": "페르소나들이 느낀 핵심 가치와 실제 사용 또는 구매로 이어질 조건을 함께 보여줍니다.",
    "리스크와 실패 가능성": "반복적으로 나온 부정 반응, 신뢰 장벽, 가장 큰 실패 요인을 묶어 먼저 줄여야 할 위험을 보여줍니다.",
    "가정 검증과 학습": "입력한 분석 객체가 얼마나 지지되는지, 무엇을 모르는지, 다음 반복에서 어떤 가설을 고쳐야 하는지 알려줍니다.",
    "전략 판단": "타겟 맥락과 서비스 방향이 맞는지, 놓치기 쉬운 반대 관점은 무엇인지 정리합니다.",
    "다음 실행 방향": "지금 무엇을 결정하고 어떤 개선과 실행 계획으로 이어가야 하는지 보여줍니다.",
    "서비스 반응 요약": "페르소나들이 서비스를 전체적으로 어떻게 받아들였는지 요약합니다. 첫인상, 기대 가치, 거부감, 반복 사용 가능성을 빠르게 파악하는 카드입니다.",
    "공통 긍정 포인트 TOP 3": "여러 페르소나에게 반복해서 나타난 긍정 신호입니다. 어떤 가치 제안이나 기능이 시장에서 먹힐 가능성이 있는지 보여줍니다.",
    "공통 부정 포인트 TOP 3": "여러 페르소나에게 반복해서 나타난 불만과 반대 이유입니다. 출시 전 반드시 줄여야 할 마찰과 리스크를 알려줍니다.",
    "신뢰 장벽": "사용자가 이 서비스를 믿고 쓰기 전에 걸리는 심리적, 실무적 장애물입니다. 온보딩, 근거 제시, 가격 정책을 설계할 때 중요합니다.",
    "구매/사용 트리거": "사용자가 실제로 써보거나 돈을 낼 가능성이 커지는 조건입니다. 메시지, 랜딩페이지, 세일즈 포인트를 잡는 데 씁니다.",
    "분석 객체": "현재 preset이 중점적으로 해석하는 구조화된 분석 대상입니다. 예를 들어 수익 가설 검증 preset에서는 대상 고객, 제공 가치, 가격, 결과 발생 시점을 봅니다.",
    "가정 검증": "입력한 가정 중 페르소나 반응으로 지지되는 것, 반박되는 것, 아직 모르는 것을 나눕니다. 다음 시장 테스트에서 무엇을 확인해야 할지 알려줍니다.",
    "학습 피드백": "예상과 실제 결과를 비교해 무엇을 배웠는지 정리합니다. 점수가 맞았는지보다 다음 반복에서 가설을 어떻게 고칠지가 핵심입니다.",
    "정렬성 분석": "서비스가 타겟 사용자의 실제 상황, 문제 강도, 행동 방식과 얼마나 맞는지 봅니다. 좋은 아이디어라도 타겟 맥락과 어긋나면 여기서 드러납니다.",
    "반대 인사이트": "좋게 보이는 결과 뒤에 숨어 있는 불편한 반론이나 역설입니다. 과대 확신을 줄이고 더 날카로운 검증 질문을 만드는 데 씁니다.",
    "의사결정 가이드": "이 결과를 바탕으로 지금 무엇을 선택하거나 보류해야 하는지 알려줍니다. 다음 행동의 우선순위를 정하는 카드입니다.",
    "전략 에이전트 리뷰": "전략 관점에서 시장 포지션, 타겟 적합성, 성장 가능성, 리스크를 해석합니다. 제품 방향이 큰 그림과 맞는지 보는 카드입니다.",
    "실행 계획": "검증된 방향을 실제 행동으로 바꾸기 위한 Task와 Step입니다. 리포트가 분석에서 끝나지 않고 실행으로 이어지게 해줍니다.",
    "가장 큰 실패 요인": "이 서비스가 시장에서 실패할 가능성이 가장 큰 이유 하나를 압축합니다. 가장 먼저 제거하거나 검증해야 할 핵심 리스크입니다.",
    "개선 포인트": "페르소나 반응을 바탕으로 제품, 메시지, 가격, 실행 방식에서 보완할 점을 정리합니다. 다음 버전의 수정 방향입니다.",
}


def generate_report(
    target_condition: str,
    service_description: str,
    personas: list[dict[str, Any]],
    interview_results: dict[str, Any],
    summary: dict[str, Any],
    path: str | None = None,
) -> None:
    html_path = path or get_output_path("report.html")
    md_path = get_output_path("report.md")
    txt_path = get_output_path("report.txt")
    output_requirements = get_output_requirements()
    agent_roles = get_agent_roles()
    persona_results = collect_persona_results(personas, interview_results)

    html = render_html_report(
        target_condition,
        service_description,
        persona_results,
        summary,
        output_requirements,
        agent_roles,
    )
    markdown = render_markdown_report(
        target_condition,
        service_description,
        persona_results,
        summary,
        output_requirements,
        agent_roles,
    )
    write_text_file(html_path, html)
    write_text_file(md_path, markdown)
    write_text_file(txt_path, markdown)


def collect_persona_results(
    personas: list[dict[str, Any]],
    interview_results: dict[str, Any],
) -> list[dict[str, Any]]:
    persona_lookup = {persona.get("id"): persona for persona in personas}
    results = []
    for index, result in enumerate(interview_results.get("personas", []), start=1):
        persona = result.get("persona", {})
        persona = persona_lookup.get(persona.get("id"), persona)
        results.append({"index": index, "persona": persona, "answers": result.get("answers", [])})
    return results


def render_html_report(
    target_condition: str,
    service_description: str,
    persona_results: list[dict[str, Any]],
    summary: dict[str, Any],
    output_requirements: dict[str, Any],
    agent_roles: dict[str, Any],
) -> str:
    average_score = float(summary.get("average_feasibility_score", 0))
    market_fit_score = int(summary.get("market_fit_score", 0))

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Persona Simulation Report</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #fff;
      --text: #20242a;
      --muted: #68707c;
      --line: #dfe3e8;
      --brand: #2251a4;
      --positive: #16803c;
      --negative: #c93636;
      --neutral: #747b85;
      --score-low: #d64545;
      --score-mid: #7ac943;
      --score-high: #1f78d1;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, "Noto Sans KR", sans-serif;
      line-height: 1.55;
    }}
    header {{
      background: #172033;
      color: #fff;
      padding: 32px 24px;
      border-bottom: 4px solid var(--brand);
    }}
    main {{
      width: min(1120px, calc(100% - 32px));
      margin: 24px auto 48px;
    }}
    h1, h2, h3 {{ margin: 0; letter-spacing: 0; }}
    h1 {{ font-size: 28px; }}
    h2 {{ font-size: 22px; margin: 32px 0 14px; }}
    h3 {{ font-size: 18px; margin-bottom: 8px; }}
    h4 {{ font-size: 15px; margin: 16px 0 6px; color: var(--muted); }}
    h5 {{ font-size: 14px; margin: 12px 0 4px; }}
    .title-help {{
      display: flex;
      align-items: center;
      gap: 7px;
      position: relative;
      width: fit-content;
      max-width: 100%;
    }}
    .help-icon {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      border: 1px solid var(--line);
      background: #f3f6fa;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      cursor: help;
      user-select: none;
    }}
    .tooltip {{
      position: absolute;
      left: 100%;
      top: 50%;
      z-index: 10;
      width: min(320px, calc(100vw - 64px));
      margin-left: 10px;
      padding: 10px 12px;
      border-radius: 8px;
      background: #172033;
      color: #fff;
      box-shadow: 0 10px 24px rgba(23, 32, 51, 0.18);
      font-size: 13px;
      font-weight: 400;
      line-height: 1.45;
      opacity: 0;
      pointer-events: none;
      transform: translateY(-50%) translateX(-4px);
      transition: opacity 0.15s ease, transform 0.15s ease;
    }}
    .tooltip::before {{
      content: "";
      position: absolute;
      right: 100%;
      top: 50%;
      transform: translateY(-50%);
      border-width: 6px;
      border-style: solid;
      border-color: transparent #172033 transparent transparent;
    }}
    .help-icon:hover + .tooltip,
    .help-icon:focus + .tooltip {{
      opacity: 1;
      transform: translateY(-50%) translateX(0);
    }}
    .subtitle {{ color: #cfd6e2; margin-top: 8px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .panel, details {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    details {{ margin-bottom: 12px; }}
    summary {{
      cursor: pointer;
      font-weight: 700;
      color: var(--text);
      list-style-position: inside;
    }}
    details[open] summary {{ margin-bottom: 14px; }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 12px;
      color: var(--muted);
      font-size: 14px;
    }}
    .qa {{
      border-top: 1px solid var(--line);
      padding-top: 14px;
      margin-top: 14px;
    }}
    .question {{ font-weight: 700; margin-bottom: 6px; }}
    .answer {{ margin-bottom: 10px; }}
    .badge {{
      display: inline-block;
      min-width: 48px;
      text-align: center;
      color: #fff;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 13px;
      font-weight: 700;
    }}
    .positive {{ background: var(--positive); }}
    .negative {{ background: var(--negative); }}
    .neutral {{ background: var(--neutral); }}
    .score-row {{
      display: grid;
      grid-template-columns: 130px 1fr 56px;
      align-items: center;
      gap: 10px;
      margin-top: 8px;
      color: var(--muted);
      font-size: 14px;
    }}
    .bar {{
      height: 10px;
      background: #e7ebf0;
      border-radius: 999px;
      overflow: hidden;
    }}
    .fill {{
      height: 100%;
      border-radius: 999px;
    }}
    .fill.low {{ background: var(--score-low); }}
    .fill.mid {{ background: var(--score-mid); }}
    .fill.high {{ background: var(--score-high); }}
    .score-label {{
      display: inline-block;
      margin-left: 4px;
      font-weight: 700;
    }}
    .score-label.low {{ color: var(--score-low); }}
    .score-label.mid {{ color: #4d8d20; }}
    .score-label.high {{ color: var(--score-high); }}
    .kv {{
      display: grid;
      grid-template-columns: 120px 1fr;
      gap: 8px 12px;
      margin-top: 8px;
      font-size: 14px;
    }}
    .kv strong {{ color: var(--muted); }}
    .feedback-item {{
      border-top: 1px solid var(--line);
      padding-top: 12px;
      margin-top: 12px;
    }}
    .feedback-item:first-child {{
      border-top: 0;
      padding-top: 0;
      margin-top: 0;
    }}
    ul {{ margin: 8px 0 0; padding-left: 20px; }}
    li {{ margin: 6px 0; }}
    .final {{
      background: #fff;
      border-left: 5px solid var(--brand);
      padding: 20px;
      border-radius: 8px;
      border-top: 1px solid var(--line);
      border-right: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
    }}
    @media (max-width: 760px) {{
      .grid, .meta, .kv {{ grid-template-columns: 1fr; }}
      .score-row {{ grid-template-columns: 100px 1fr 48px; }}
      .tooltip {{
        left: 0;
        top: calc(100% + 8px);
        margin-left: 0;
        transform: translateY(0);
      }}
      .tooltip::before {{ display: none; }}
      .help-icon:hover + .tooltip,
      .help-icon:focus + .tooltip {{
        transform: translateY(0);
      }}
      h1 {{ font-size: 24px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>AI 페르소나 시뮬레이션 리포트</h1>
    <div class="subtitle">페르소나 반응, 신뢰 장벽, 실행 가능성, 시장 적합도 분석</div>
  </header>
  <main>
    <h2>1. 개요</h2>
    <section class="grid">
      <div class="panel">
        <h3>서비스 조건</h3>
        <p>{nl2br(service_description)}</p>
      </div>
      <div class="panel">
        <h3>타겟 조건</h3>
        <p>{nl2br(target_condition)}</p>
      </div>
    </section>

    <h2>2. 통합분석</h2>
    <section class="grid">
      {render_integrated_analysis_html(summary, output_requirements, agent_roles)}
    </section>

    <h2>3. 최종결과</h2>
    <section class="final">
      {render_score("평균 실행 가능성", average_score, 10)}
      {render_score("최종 시장 적합도", market_fit_score, 100)}
      <h3>한 줄 결론</h3>
      <p>{escape(str(summary.get("one_line_conclusion", "")))}</p>
    </section>

    <h2>4. 각 페르소나 결과</h2>
    {''.join(render_persona_accordion(result) for result in persona_results)}
  </main>
</body>
</html>
"""


def render_persona_accordion(result: dict[str, Any]) -> str:
    persona = result["persona"]
    answers = result["answers"]
    summary_text = f"{result['index']}. {persona.get('name', '')} ({persona.get('job', '')}, {persona.get('age', '')})"
    return f"""
    <details>
      <summary>{escape(summary_text)}</summary>
      <div class="meta">
        <div><strong>직업</strong><br>{escape(str(persona.get("job", "")))}</div>
        <div><strong>나이</strong><br>{escape(str(persona.get("age", "")))}</div>
        <div><strong>성격</strong><br>{escape(str(persona.get("personality", "")))}</div>
        <div><strong>현재 상황</strong><br>{escape(str(persona.get("current_situation", "")))}</div>
        <div><strong>주요 문제</strong><br>{escape(str(persona.get("main_problem", "")))}</div>
      </div>
      {''.join(render_answer(answer) for answer in answers)}
    </details>
"""


def render_answer(answer: dict[str, Any]) -> str:
    sentiment = str(answer.get("sentiment", "중립"))
    css_class = SENTIMENT_CLASS.get(sentiment, "neutral")
    score = int(answer.get("feasibility_score", 0))
    return f"""
      <div class="qa">
        <div class="question">Q. {escape(str(answer.get("question", "")))}</div>
        <div class="answer">{nl2br(str(answer.get("answer", "")))}</div>
        <span class="badge {css_class}">{escape(sentiment)}</span>
        {render_score("실행 가능성", score, 10)}
        {render_optional_answer_meta(answer)}
      </div>
"""


def render_score(label: str, score: float, maximum: int) -> str:
    percentage = 0 if maximum == 0 else max(0, min(100, (float(score) / maximum) * 100))
    level_class, level_label = score_level(score, maximum)
    return f"""
      <div class="score-row">
        <strong>{escape(label)}</strong>
        <div class="bar"><div class="fill {level_class}" style="width: {percentage:.1f}%"></div></div>
        <span>{score:g}/{maximum}<span class="score-label {level_class}">{level_label}</span></span>
      </div>
"""


def score_level(score: float, maximum: int) -> tuple[str, str]:
    if maximum <= 0:
        return "low", "낮음"
    normalized = (float(score) / maximum) * 100
    if normalized < 60:
        return "low", "낮음"
    if normalized < 80:
        return "mid", "중간"
    return "high", "높음"


def render_html_list(items: Any) -> str:
    safe_items = normalize_text_items(items)
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in safe_items) + "</ul>"


def render_card_title(title: str) -> str:
    help_text = CARD_HELP.get(title, "")
    if not help_text:
        return f"<h3>{escape(title)}</h3>"
    return f"""
        <h3 class="title-help">
          <span>{escape(title)}</span>
          <span class="help-icon" tabindex="0" aria-label="{escape(help_text)}">?</span>
          <span class="tooltip" role="tooltip">{escape(help_text)}</span>
        </h3>
"""


def render_integrated_analysis_html(
    summary: dict[str, Any],
    output_requirements: dict[str, Any],
    agent_roles: dict[str, Any],
) -> str:
    cards = [
        render_market_signal_card(summary),
        render_risk_card(summary),
        render_assumption_learning_card(summary, output_requirements),
        render_strategy_card(summary, output_requirements),
        render_next_action_card(summary, output_requirements, agent_roles),
    ]
    return "".join(card for card in cards if card)


def render_market_signal_card(summary: dict[str, Any]) -> str:
    return f"""
      <div class="panel">
        {render_card_title("시장 반응과 구매 신호")}
        <h4>서비스 반응 요약</h4>
        <p>{escape(str(summary.get("service_reaction_summary", "")))}</p>
        <h4>긍정 포인트</h4>
        {render_html_list(summary.get("positive_points_top3", []))}
        <h4>구매/사용 트리거</h4>
        {render_html_list(summary.get("purchase_triggers", []))}
      </div>
"""


def render_risk_card(summary: dict[str, Any]) -> str:
    return f"""
      <div class="panel">
        {render_card_title("리스크와 실패 가능성")}
        <h4>부정 포인트</h4>
        {render_html_list(summary.get("negative_points_top3", []))}
        <h4>신뢰 장벽</h4>
        {render_html_list(summary.get("trust_barriers", []))}
        <h4>가장 큰 실패 요인</h4>
        <p>{escape(str(summary.get("biggest_failure_factor", "")))}</p>
      </div>
"""


def render_assumption_learning_card(summary: dict[str, Any], output_requirements: dict[str, Any]) -> str:
    sections = []
    if output_requirements.get("include_analysis_object", False):
        sections.append(render_analysis_object_section(summary.get("analysis_object")))
    if output_requirements.get("include_assumption_validation", False):
        sections.append(render_assumption_validation_section(summary.get("assumption_validation")))
    if output_requirements.get("include_learning_feedback", False):
        sections.append(render_learning_feedback_section(summary.get("learning_feedback", [])))

    content = "".join(section for section in sections if section)
    if not content:
        return ""
    return f"""
      <div class="panel">
        {render_card_title("가정 검증과 학습")}
        {content}
      </div>
"""


def render_strategy_card(summary: dict[str, Any], output_requirements: dict[str, Any]) -> str:
    sections = []
    if output_requirements.get("include_alignment_analysis", False):
        sections.append(render_text_section("정렬성 분석", summary.get("alignment_analysis", "")))
    if output_requirements.get("include_counter_insight", False):
        sections.append(render_text_section("반대 인사이트", summary.get("counter_insight", "")))
    if output_requirements.get("include_strategy_agent_review", False):
        sections.append(render_text_section("전략 에이전트 리뷰", summary.get("strategy_agent_review", "")))

    content = "".join(section for section in sections if section)
    if not content:
        return ""
    return f"""
      <div class="panel">
        {render_card_title("전략 판단")}
        {content}
      </div>
"""


def render_next_action_card(
    summary: dict[str, Any],
    output_requirements: dict[str, Any],
    agent_roles: dict[str, Any],
) -> str:
    sections = []
    if output_requirements.get("include_decision_guidance", False):
        sections.append(render_text_section("의사결정 가이드", summary.get("decision_guidance", "")))
    sections.append(render_list_section("개선 포인트", summary.get("improvement_points", [])))
    if should_include_execution_plan(output_requirements, agent_roles):
        sections.append(render_execution_plan_section(summary.get("execution_plan", [])))

    content = "".join(section for section in sections if section)
    if not content:
        return ""
    return f"""
      <div class="panel">
        {render_card_title("다음 실행 방향")}
        {content}
      </div>
"""


def render_text_section(title: str, content: Any) -> str:
    text = str(content).strip()
    if not text:
        return ""
    return f"<h4>{escape(title)}</h4><p>{escape(text)}</p>"


def render_list_section(title: str, items: Any) -> str:
    if not normalize_text_items(items):
        return ""
    return f"<h4>{escape(title)}</h4>{render_html_list(items)}"


def render_analysis_object_section(analysis_object: Any) -> str:
    if not isinstance(analysis_object, dict) or not has_meaningful_value(analysis_object):
        return ""
    return f"<h4>분석 객체</h4>{render_key_value_html(analysis_object)}"


def render_assumption_validation_section(validation: Any) -> str:
    if not isinstance(validation, dict):
        return ""
    if not any(validation.get(key) for key in ("validated_points", "invalidated_points", "unknowns")):
        return ""
    return f"""
        <h4>가정 검증</h4>
        <strong>검증된 점</strong>
        {render_html_list(validation.get("validated_points", []))}
        <strong>반증된 점</strong>
        {render_html_list(validation.get("invalidated_points", []))}
        <strong>아직 모르는 점</strong>
        {render_html_list(validation.get("unknowns", []))}
"""


def render_learning_feedback_section(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return ""

    blocks = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            blocks.append(
                f"""
        <div class="feedback-item">
          <strong>학습 피드백 {index}</strong>
          {render_key_value_html(item)}
        </div>
"""
            )
        elif str(item).strip():
            blocks.append(f'<div class="feedback-item">{escape(str(item))}</div>')

    if not blocks:
        return ""
    return f"<h4>학습 피드백</h4>{''.join(blocks)}"


def render_execution_plan_section(execution_plan: Any) -> str:
    if not isinstance(execution_plan, list) or not execution_plan:
        return ""

    task_blocks = []
    for task in execution_plan:
        if not isinstance(task, dict):
            continue
        step_items = []
        steps = task.get("steps", [])
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict):
                    continue
                step_items.append(
                    f"""
          <li>
            <strong>{escape(str(step.get("step", "")))}</strong><br>
            입력: {escape(str(step.get("input", "")))}<br>
            처리: {escape(str(step.get("process", "")))}<br>
            산출물: {escape(str(step.get("output", "")))}
          </li>
"""
                )
        task_blocks.append(
            f"""
        <div>
          <h5>{escape(str(task.get("task", "")))}</h5>
          <p>{escape(str(task.get("objective", "")))}</p>
          <ul>{''.join(step_items)}</ul>
        </div>
"""
        )

    if not task_blocks:
        return ""
    return f"<h4>실행 계획</h4>{''.join(task_blocks)}"


def render_analysis_object_html(analysis_object: Any, enabled: bool) -> str:
    if not enabled or not isinstance(analysis_object, dict) or not has_meaningful_value(analysis_object):
        return ""
    return f"""
      <div class="panel">
        {render_card_title("분석 객체")}
        {render_key_value_html(analysis_object)}
      </div>
"""


def render_assumption_validation_html(validation: Any, enabled: bool) -> str:
    if not enabled or not isinstance(validation, dict):
        return ""
    if not any(validation.get(key) for key in ("validated_points", "invalidated_points", "unknowns")):
        return ""
    return f"""
      <div class="panel">
        {render_card_title("가정 검증")}
        <strong>검증된 점</strong>
        {render_html_list(validation.get("validated_points", []))}
        <strong>반증된 점</strong>
        {render_html_list(validation.get("invalidated_points", []))}
        <strong>아직 모르는 점</strong>
        {render_html_list(validation.get("unknowns", []))}
      </div>
"""


def render_learning_feedback_html(items: Any, enabled: bool) -> str:
    if not enabled or not isinstance(items, list) or not items:
        return ""

    blocks = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            blocks.append(
                f"""
        <div class="feedback-item">
          <strong>학습 피드백 {index}</strong>
          {render_key_value_html(item)}
        </div>
"""
            )
        elif str(item).strip():
            blocks.append(f'<div class="feedback-item">{escape(str(item))}</div>')

    if not blocks:
        return ""

    return f"""
      <div class="panel">
        {render_card_title("학습 피드백")}
        {''.join(blocks)}
      </div>
"""


def render_key_value_html(data: dict[str, Any]) -> str:
    rows = []
    for key, value in data.items():
        if not has_meaningful_value(value):
            continue
        rows.append(
            f"<strong>{escape(label_for(key))}</strong><span>{escape(format_value(value))}</span>"
        )
    if not rows:
        return ""
    return '<div class="kv">' + "".join(rows) + "</div>"


def should_include_execution_plan(output_requirements: dict[str, Any], agent_roles: dict[str, Any]) -> bool:
    return bool(output_requirements.get("include_execution_plan", False) or agent_roles.get("execution_planner_agent"))


def render_optional_panel(title: str, content: Any, enabled: bool) -> str:
    text = str(content).strip()
    if not enabled or not text:
        return ""
    return f"""
      <div class="panel">
        {render_card_title(title)}
        <p>{escape(text)}</p>
      </div>
"""


def render_execution_plan_html(execution_plan: Any, enabled: bool) -> str:
    if not enabled or not isinstance(execution_plan, list) or not execution_plan:
        return ""

    task_blocks = []
    for task in execution_plan:
        if not isinstance(task, dict):
            continue
        step_items = []
        steps = task.get("steps", [])
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict):
                    continue
                step_items.append(
                    f"""
          <li>
            <strong>{escape(str(step.get("step", "")))}</strong><br>
            입력: {escape(str(step.get("input", "")))}<br>
            처리: {escape(str(step.get("process", "")))}<br>
            산출물: {escape(str(step.get("output", "")))}
          </li>
"""
                )
        task_blocks.append(
            f"""
        <div>
          <h4>{escape(str(task.get("task", "")))}</h4>
          <p>{escape(str(task.get("objective", "")))}</p>
          <ul>{''.join(step_items)}</ul>
        </div>
"""
        )

    if not task_blocks:
        return ""

    return f"""
      <div class="panel">
        {render_card_title("실행 계획")}
        {''.join(task_blocks)}
      </div>
"""


def render_optional_answer_meta(answer: dict[str, Any]) -> str:
    felt_value = str(answer.get("felt_value", "")).strip()
    concern = str(answer.get("concern", "")).strip()
    parts = []
    if felt_value:
        parts.append(f"<div><strong>느낀 가치</strong>: {escape(felt_value)}</div>")
    if concern:
        parts.append(f"<div><strong>우려</strong>: {escape(concern)}</div>")
    if not parts:
        return ""
    return '<div class="meta">' + "".join(parts) + "</div>"


def render_markdown_report(
    target_condition: str,
    service_description: str,
    persona_results: list[dict[str, Any]],
    summary: dict[str, Any],
    output_requirements: dict[str, Any],
    agent_roles: dict[str, Any],
) -> str:
    lines = [
        "# AI 페르소나 시뮬레이션 리포트",
        "",
        "## 1. 개요",
        "",
        "### 서비스 조건",
        service_description,
        "",
        "### 타겟 조건",
        target_condition,
        "",
        "## 2. 통합분석",
        "",
        *markdown_integrated_analysis(summary, output_requirements, agent_roles),
        "## 3. 최종결과",
        "",
        f"- 평균 실행 가능성 점수: {summary.get('average_feasibility_score', 0)}/10",
        f"- 최종 시장 적합도 점수: {summary.get('market_fit_score', 0)}/100",
        f"- 한 줄 결론: {summary.get('one_line_conclusion', '')}",
        "",
        "## 4. 각 페르소나 결과",
        "",
    ]

    for result in persona_results:
        persona = result["persona"]
        lines.extend(
            [
                f"### {result['index']}. {persona.get('name', '')}",
                "",
                f"- 직업: {persona.get('job', '')}",
                f"- 나이: {persona.get('age', '')}",
                f"- 성격: {persona.get('personality', '')}",
                f"- 현재 상황: {persona.get('current_situation', '')}",
                f"- 주요 문제: {persona.get('main_problem', '')}",
                "",
            ]
        )
        for answer_index, answer in enumerate(result["answers"], start=1):
            lines.extend(
                [
                    f"#### Q{answer_index}. {answer.get('question', '')}",
                    "",
                    str(answer.get("answer", "")),
                    "",
                    f"- 감정 판단: {answer.get('sentiment', '')}",
                    f"- 실행 가능성 점수: {answer.get('feasibility_score', '')}/10",
                    f"- 느낀 가치: {answer.get('felt_value', '')}",
                    f"- 우려: {answer.get('concern', '')}",
                    "",
                ]
            )

    return "\n".join(lines).rstrip() + "\n"


def markdown_bullets(items: Any) -> list[str]:
    return [f"- {item}" for item in normalize_text_items(items)]


def markdown_integrated_analysis(
    summary: dict[str, Any],
    output_requirements: dict[str, Any],
    agent_roles: dict[str, Any],
) -> list[str]:
    lines = [
        "### 시장 반응과 구매 신호",
        "#### 서비스 반응 요약",
        str(summary.get("service_reaction_summary", "")),
        "",
        "#### 긍정 포인트",
        *markdown_bullets(summary.get("positive_points_top3", [])),
        "",
        "#### 구매/사용 트리거",
        *markdown_bullets(summary.get("purchase_triggers", [])),
        "",
        "### 리스크와 실패 가능성",
        "#### 부정 포인트",
        *markdown_bullets(summary.get("negative_points_top3", [])),
        "",
        "#### 신뢰 장벽",
        *markdown_bullets(summary.get("trust_barriers", [])),
        "",
        "#### 가장 큰 실패 요인",
        str(summary.get("biggest_failure_factor", "")),
        "",
    ]

    assumption_lines = []
    if output_requirements.get("include_analysis_object", False):
        assumption_lines.extend(markdown_analysis_object(summary.get("analysis_object"), True, heading_level="####"))
    if output_requirements.get("include_assumption_validation", False):
        assumption_lines.extend(markdown_assumption_validation(summary.get("assumption_validation"), True, heading_level="####"))
    if output_requirements.get("include_learning_feedback", False):
        assumption_lines.extend(markdown_learning_feedback(summary.get("learning_feedback", []), True, heading_level="####"))
    if assumption_lines:
        lines.extend(["### 가정 검증과 학습", *assumption_lines])

    strategy_lines = []
    if output_requirements.get("include_alignment_analysis", False):
        strategy_lines.extend(markdown_optional_section("#### 정렬성 분석", summary.get("alignment_analysis", ""), True))
    if output_requirements.get("include_counter_insight", False):
        strategy_lines.extend(markdown_optional_section("#### 반대 인사이트", summary.get("counter_insight", ""), True))
    if output_requirements.get("include_strategy_agent_review", False):
        strategy_lines.extend(markdown_optional_section("#### 전략 에이전트 리뷰", summary.get("strategy_agent_review", ""), True))
    if strategy_lines:
        lines.extend(["### 전략 판단", *strategy_lines])

    next_lines = []
    if output_requirements.get("include_decision_guidance", False):
        next_lines.extend(markdown_optional_section("#### 의사결정 가이드", summary.get("decision_guidance", ""), True))
    next_lines.extend(["#### 개선 포인트", *markdown_bullets(summary.get("improvement_points", [])), ""])
    if should_include_execution_plan(output_requirements, agent_roles):
        next_lines.extend(markdown_execution_plan(summary.get("execution_plan", []), True, heading_level="####"))
    if next_lines:
        lines.extend(["### 다음 실행 방향", *next_lines])

    return lines


def markdown_analysis_object(analysis_object: Any, enabled: bool, heading_level: str = "###") -> list[str]:
    if not enabled or not isinstance(analysis_object, dict) or not has_meaningful_value(analysis_object):
        return []
    lines = [f"{heading_level} 분석 객체"]
    lines.extend(f"- {label_for(key)}: {format_value(value)}" for key, value in analysis_object.items() if has_meaningful_value(value))
    lines.append("")
    return lines


def markdown_assumption_validation(validation: Any, enabled: bool, heading_level: str = "###") -> list[str]:
    if not enabled or not isinstance(validation, dict):
        return []
    if not any(validation.get(key) for key in ("validated_points", "invalidated_points", "unknowns")):
        return []
    return [
        f"{heading_level} 가정 검증",
        f"{heading_level}# 검증된 점",
        *markdown_bullets(validation.get("validated_points", [])),
        "",
        f"{heading_level}# 반증된 점",
        *markdown_bullets(validation.get("invalidated_points", [])),
        "",
        f"{heading_level}# 아직 모르는 점",
        *markdown_bullets(validation.get("unknowns", [])),
        "",
    ]


def markdown_learning_feedback(items: Any, enabled: bool, heading_level: str = "###") -> list[str]:
    if not enabled or not isinstance(items, list) or not items:
        return []

    lines = [f"{heading_level} 학습 피드백"]
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            lines.append(f"{heading_level}# 학습 피드백 {index}")
            for key, value in item.items():
                if has_meaningful_value(value):
                    lines.append(f"- {label_for(key)}: {format_value(value)}")
            lines.append("")
        elif str(item).strip():
            lines.append(f"- {item}")
    lines.append("")
    return lines


def markdown_optional_section(title: str, content: Any, enabled: bool) -> list[str]:
    text = str(content).strip()
    if not enabled or not text:
        return []
    return [title, text, ""]


def markdown_execution_plan(execution_plan: Any, enabled: bool, heading_level: str = "###") -> list[str]:
    if not enabled or not isinstance(execution_plan, list) or not execution_plan:
        return []

    lines = [f"{heading_level} 실행 계획", ""]
    for task in execution_plan:
        if not isinstance(task, dict):
            continue
        lines.extend([f"{heading_level}# " + str(task.get("task", "")), "", f"- 목표: {task.get('objective', '')}"])
        steps = task.get("steps", [])
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict):
                    continue
                lines.extend(
                    [
                        f"- Step: {step.get('step', '')}",
                        f"  - Input: {step.get('input', '')}",
                        f"  - Process: {step.get('process', '')}",
                        f"  - Output: {step.get('output', '')}",
                    ]
                )
        lines.append("")
    return lines


def normalize_text_items(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    normalized = []
    for item in items:
        if isinstance(item, dict):
            text = "; ".join(
                f"{label_for(key)}: {format_value(value)}"
                for key, value in item.items()
                if has_meaningful_value(value)
            )
        else:
            text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized


def has_meaningful_value(value: Any) -> bool:
    if isinstance(value, dict):
        return any(has_meaningful_value(item) for item in value.values())
    if isinstance(value, list):
        return any(has_meaningful_value(item) for item in value)
    return bool(str(value).strip())


def format_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(format_value(item) for item in value if has_meaningful_value(item))
    if isinstance(value, dict):
        return "; ".join(
            f"{label_for(key)}: {format_value(item)}"
            for key, item in value.items()
            if has_meaningful_value(item)
        )
    return str(value).strip()


def label_for(key: Any) -> str:
    key_text = str(key)
    return FIELD_LABELS.get(key_text, key_text.replace("_", " "))


def nl2br(text: str) -> str:
    return "<br>".join(escape(text).splitlines())
