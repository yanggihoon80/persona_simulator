from html import escape
from typing import Any

from utils import get_output_path, get_output_requirements, write_text_file


SENTIMENT_CLASS = {
    "긍정": "positive",
    "부정": "negative",
    "중립": "neutral",
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

    persona_results = collect_persona_results(personas, interview_results)

    write_text_file(
        html_path,
        render_html_report(target_condition, service_description, persona_results, summary, output_requirements),
    )
    markdown = render_markdown_report(
        target_condition,
        service_description,
        persona_results,
        summary,
        output_requirements,
    )
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
        results.append(
            {
                "index": index,
                "persona": persona,
                "answers": result.get("answers", []),
            }
        )
    return results


def render_html_report(
    target_condition: str,
    service_description: str,
    persona_results: list[dict[str, Any]],
    summary: dict[str, Any],
    output_requirements: dict[str, Any],
) -> str:
    average_score = float(summary.get("average_feasibility_score", 0))
    market_fit_score = int(summary.get("market_fit_score", 0))

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Persona Market Simulation Report</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #20242a;
      --muted: #68707c;
      --line: #dfe3e8;
      --brand: #2251a4;
      --positive: #16803c;
      --negative: #c93636;
      --neutral: #747b85;
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
      background: var(--brand);
      border-radius: 999px;
    }}
    ul {{ margin: 8px 0 0; padding-left: 20px; }}
    li {{ margin: 6px 0; }}
    .final {{
      background: #ffffff;
      border-left: 5px solid var(--brand);
      padding: 20px;
      border-radius: 8px;
      border-top: 1px solid var(--line);
      border-right: 1px solid var(--line);
      border-bottom: 1px solid var(--line);
    }}
    @media (max-width: 760px) {{
      .grid, .meta {{ grid-template-columns: 1fr; }}
      .score-row {{ grid-template-columns: 100px 1fr 48px; }}
      h1 {{ font-size: 24px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>AI 페르소나 서비스 반응 시뮬레이션 리포트</h1>
    <div class="subtitle">페르소나들이 서비스를 이용한 뒤 느낀 가치, 우려, 구매 가능성을 분석한 결과</div>
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
      <div class="panel">
        <h3>서비스 반응 요약</h3>
        <p>{escape(str(summary.get("service_reaction_summary", "")))}</p>
      </div>
      <div class="panel">
        <h3>공통 긍정 포인트 TOP 3</h3>
        {render_html_list(summary.get("positive_points_top3", []))}
      </div>
      <div class="panel">
        <h3>공통 부정 포인트 TOP 3</h3>
        {render_html_list(summary.get("negative_points_top3", []))}
      </div>
      <div class="panel">
        <h3>신뢰 장벽</h3>
        {render_html_list(summary.get("trust_barriers", []))}
      </div>
      <div class="panel">
        <h3>구매/재사용 트리거</h3>
        {render_html_list(summary.get("purchase_triggers", []))}
      </div>
      {render_optional_panel("정렬성 분석", summary.get("alignment_analysis", ""), output_requirements.get("include_alignment_analysis", False))}
      {render_optional_panel("반대 인사이트", summary.get("counter_insight", ""), output_requirements.get("include_counter_insight", False))}
      {render_optional_panel("의사결정 가이드", summary.get("decision_guidance", ""), output_requirements.get("include_decision_guidance", False))}
      {render_optional_panel("전략 에이전트 리뷰", summary.get("strategy_agent_review", ""), output_requirements.get("include_strategy_agent_review", False))}
      <div class="panel">
        <h3>가장 큰 실패 요인</h3>
        <p>{escape(str(summary.get("biggest_failure_factor", "")))}</p>
      </div>
      <div class="panel">
        <h3>개선 포인트</h3>
        {render_html_list(summary.get("improvement_points", []))}
      </div>
    </section>

    <h2>3. 최종결과</h2>
    <section class="final">
      {render_score("평균 사용 가능성", average_score, 10)}
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
    summary_text = (
        f"{result['index']}. {persona.get('name', '')} "
        f"({persona.get('job', '')}, {persona.get('age', '')})"
    )
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
        {render_score("사용 가능성", score, 10)}
        {render_optional_answer_meta(answer)}
      </div>
"""


def render_score(label: str, score: float, maximum: int) -> str:
    percentage = 0 if maximum == 0 else max(0, min(100, (float(score) / maximum) * 100))
    return f"""
      <div class="score-row">
        <strong>{escape(label)}</strong>
        <div class="bar"><div class="fill" style="width: {percentage:.1f}%"></div></div>
        <span>{score:g}/{maximum}</span>
      </div>
"""


def render_html_list(items: list[str]) -> str:
    safe_items = [item for item in items if str(item).strip()]
    return "<ul>" + "".join(f"<li>{escape(str(item))}</li>" for item in safe_items) + "</ul>"


def render_optional_panel(title: str, content: Any, enabled: bool) -> str:
    text = str(content).strip()
    if not enabled or not text:
        return ""
    return f"""
      <div class="panel">
        <h3>{escape(title)}</h3>
        <p>{escape(text)}</p>
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
) -> str:
    lines = [
        "# AI 페르소나 서비스 반응 시뮬레이션 리포트",
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
        "### 서비스 반응 요약",
        str(summary.get("service_reaction_summary", "")),
        "",
        "### 공통 긍정 포인트 TOP 3",
        *markdown_bullets(summary.get("positive_points_top3", [])),
        "",
        "### 공통 부정 포인트 TOP 3",
        *markdown_bullets(summary.get("negative_points_top3", [])),
        "",
        "### 신뢰 장벽",
        *markdown_bullets(summary.get("trust_barriers", [])),
        "",
        "### 구매/재사용 트리거",
        *markdown_bullets(summary.get("purchase_triggers", [])),
        "",
        *markdown_optional_section("### 정렬성 분석", summary.get("alignment_analysis", ""), output_requirements.get("include_alignment_analysis", False)),
        *markdown_optional_section("### 반대 인사이트", summary.get("counter_insight", ""), output_requirements.get("include_counter_insight", False)),
        *markdown_optional_section("### 의사결정 가이드", summary.get("decision_guidance", ""), output_requirements.get("include_decision_guidance", False)),
        *markdown_optional_section("### 전략 에이전트 리뷰", summary.get("strategy_agent_review", ""), output_requirements.get("include_strategy_agent_review", False)),
        "### 가장 큰 실패 요인",
        str(summary.get("biggest_failure_factor", "")),
        "",
        "### 개선 포인트",
        *markdown_bullets(summary.get("improvement_points", [])),
        "",
        "## 3. 최종결과",
        "",
        f"- 평균 사용 가능성 점수: {summary.get('average_feasibility_score', 0)}/10",
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
                    f"- 사용 가능성 점수: {answer.get('feasibility_score', '')}/10",
                    f"- 느낀 가치: {answer.get('felt_value', '')}",
                    f"- 우려: {answer.get('concern', '')}",
                    "",
                ]
            )

    return "\n".join(lines).rstrip() + "\n"


def markdown_bullets(items: list[str]) -> list[str]:
    safe_items = [str(item).strip() for item in items if str(item).strip()]
    return [f"- {item}" for item in safe_items]


def markdown_optional_section(title: str, content: Any, enabled: bool) -> list[str]:
    text = str(content).strip()
    if not enabled or not text:
        return []
    return [title, text, ""]


def nl2br(text: str) -> str:
    return "<br>".join(escape(text).splitlines())
