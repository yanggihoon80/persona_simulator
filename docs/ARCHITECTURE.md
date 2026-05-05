# persona_sim Architecture

## 1. System Architecture Diagram

```text
persona_config.json
        |
        v
+--------------------------+
| Preset Resolver          |
| - idea_validation        |
| - decision_comparison    |
| - action_evaluation      |
| - revenue_hypothesis     |
+------------+-------------+
             |
             v
+--------------------------+        +------------------+
| persona_sim Core Engine  | <----> | JSON Cache       |
|                          |        | output/*.json    |
| 1. validate config       |        +------------------+
| 2. generate questions    |
| 3. generate personas     |
| 4. run persona agents    |
| 5. aggregate evaluation  |
| 6. execution planning    |
| 7. learning feedback     |
+------------+-------------+
             |
             v
+--------------------------+
| Structured Result        |
| - scores                 |
| - explanation            |
| - counter insight        |
| - decision guidance      |
| - analysis object        |
| - learning feedback      |
+------------+-------------+
             |
             v
+--------------------------+
| Report Generator         |
| report.html/md/txt       |
+--------------------------+
```

## 2. Module Breakdown

```text
persona_sim/
  core/
    agents.py      Agent role definitions and input/output contracts
    cache.py       JSON cache layer
    config.py      Config access and preset resolution helpers
    engine.py      Reusable simulation pipeline
    llm.py         OpenAI JSON adapter
  presets/
    base.py
    idea_validation.py
    decision_comparison.py
    action_evaluation.py
    revenue_hypothesis_validation.py
    registry.py

main.py             Thin entrypoint
report_generator.py HTML/MD/TXT renderer
persona_config.json Private local config, ignored by Git
persona_config.example.json Public dummy config
```

## 3. Layering

Layer 1 is the core engine. It owns loading config, validating required paths, generating questions and personas, running interviews, creating summaries, caching results, and passing the result to the report generator.

Layer 2 is the preset layer. A preset owns domain-specific prompt context, scoring focus, required config paths, and expected output shape. The core engine should not contain service-specific business logic. Config may select one preset as a string or multiple presets as an array.

## 4. Presets

Implemented presets:

1. `idea_validation`
2. `decision_comparison`
3. `action_evaluation`
4. `revenue_hypothesis_validation`

`revenue_hypothesis_validation` is the only preset that interprets `decision_context.example_options[].analysis_object` as a revenue hypothesis. The generic config key remains `analysis_object`, so the engine can be reused for other analysis objects later.

Multiple presets are combined by `CompositePreset`. It merges required config paths, scoring focus, and output schema, then creates one unified set of questions and one unified report summary.

## 5. Agent Design

| Agent | Responsibility | Output |
| --- | --- | --- |
| `persona_agent` | Simulates realistic target-user reactions | answers, sentiment, feasibility, felt value, concerns |
| `strategy_agent` | Reviews strategic fit and priority | strategy review, alignment, counter insight |
| `evaluation_agent` | Aggregates scores and market fit | scores, guidance, market fit |
| `execution_planner_agent` | Converts direction into weekly tasks and IPO steps | execution plan |
| `learning_agent` | Compares expected vs actual results | gap analysis, assumption correction, next iteration |

## 6. Generic Analysis Object

Options may include a generic `analysis_object`.

```json
{
  "id": "A",
  "name": "Option A",
  "description": "Option description",
  "analysis_object": {
    "target_customer": "who the option targets",
    "value_proposition": "why it matters",
    "pricing": "price or cost assumption",
    "time_to_revenue": "expected time to outcome"
  }
}
```

The meaning of these fields is preset-specific. For example, the revenue hypothesis preset treats them as revenue assumptions. A future preset could reuse `analysis_object` for risk, usability, operational load, or another structured object.

## 7. Learning Loop

The config may include expected and actual results under `decision_context`.

```json
{
  "decision_context": {
    "expected_result": {
      "outcome": "120만원"
    },
    "actual_result": {
      "outcome": "20만원"
    }
  }
}
```

The learning output includes:

- expected
- actual
- delta
- gap analysis
- assumption correction
- next iteration suggestion

## 8. Design Decisions

- The core engine knows only generic pipeline steps.
- Presets own domain-specific interpretation and prompt context.
- Service-specific naming is kept out of shared config keys.
- `persona_config.example.json` is the public reference structure and must stay structurally aligned with private `persona_config.json`.
- Agent roles are config-driven and merged with safe defaults.
- Caching is at pipeline boundaries, so expensive LLM steps can be reused.
- Report rendering remains separate from simulation logic.
