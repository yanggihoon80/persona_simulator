from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentSpec:
    name: str
    role: str
    responsibility: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)


DEFAULT_AGENTS: dict[str, AgentSpec] = {
    "persona_agent": AgentSpec(
        name="persona_agent",
        role="Virtual target user",
        responsibility="Respond as a realistic persona and surface feelings, objections, adoption likelihood, and practical constraints.",
        input_schema={
            "persona": "object",
            "service_condition": "string",
            "questions": "array[string]",
            "context": "object",
        },
        output_schema={
            "answers": [
                {
                    "question": "string",
                    "answer": "string",
                    "sentiment": "긍정|부정|중립",
                    "feasibility_score": "integer 1-10",
                    "felt_value": "string",
                    "concern": "string",
                }
            ]
        },
    ),
    "strategy_agent": AgentSpec(
        name="strategy_agent",
        role="Strategy analyst",
        responsibility="Analyze fit between the service, target context, options, and strategic priority.",
        input_schema={
            "service_condition": "string",
            "decision_context": "object",
            "interview_results": "object",
        },
        output_schema={
            "strategy_agent_review": "string",
            "alignment_analysis": "string",
            "counter_insight": "string",
        },
    ),
    "evaluation_agent": AgentSpec(
        name="evaluation_agent",
        role="Evaluation analyst",
        responsibility="Aggregate persona response, market risk, feasibility, scoring, and decision guidance.",
        input_schema={
            "interview_results": "object",
            "scoring_schema": "object",
            "output_requirements": "object",
        },
        output_schema={
            "scores": "object",
            "market_fit_score": "integer 1-100",
            "decision_guidance": "string",
        },
    ),
    "execution_planner_agent": AgentSpec(
        name="execution_planner_agent",
        role="Execution planner",
        responsibility="Convert the validated direction into weekly tasks and Input-Process-Output steps.",
        input_schema={
            "summary": "object",
            "decision_context": "object",
        },
        output_schema={
            "execution_plan": [
                {
                    "task": "string",
                    "objective": "string",
                    "steps": [
                        {
                            "step": "string",
                            "input": "string",
                            "process": "string",
                            "output": "string",
                        }
                    ],
                }
            ]
        },
    ),
    "learning_agent": AgentSpec(
        name="learning_agent",
        role="Learning loop analyst",
        responsibility="Compare expected and actual outcomes, diagnose the gap, correct hypotheses, and suggest next iteration actions.",
        input_schema={
            "expected_result": "object",
            "actual_result": "object",
            "analysis_object": "object",
            "interview_results": "object",
        },
        output_schema={
            "learning_feedback": [
                {
                    "expected": "string",
                    "actual": "string",
                    "delta": "string",
                    "gap_analysis": "string",
                    "assumption_correction": "string",
                    "next_iteration_suggestion": "string",
                }
            ]
        },
    ),
}


LEGACY_AGENT_ALIASES = {
    "persona_agents": "persona_agent",
}


def merge_agent_roles(config_roles: dict[str, Any] | None) -> dict[str, AgentSpec]:
    agents = dict(DEFAULT_AGENTS)
    if not isinstance(config_roles, dict):
        return agents

    for raw_name, raw_spec in config_roles.items():
        name = LEGACY_AGENT_ALIASES.get(raw_name, raw_name)
        if not isinstance(raw_spec, dict):
            continue
        base = agents.get(name)
        agents[name] = AgentSpec(
            name=name,
            role=str(raw_spec.get("role") or (base.role if base else "")),
            responsibility=str(raw_spec.get("responsibility") or raw_spec.get("task") or (base.responsibility if base else "")),
            input_schema=raw_spec.get("input_schema") if isinstance(raw_spec.get("input_schema"), dict) else (base.input_schema if base else {}),
            output_schema=raw_spec.get("output_schema") if isinstance(raw_spec.get("output_schema"), dict) else (base.output_schema if base else {}),
        )
    return agents


def agents_for_prompt(agents: dict[str, AgentSpec]) -> dict[str, Any]:
    return {
        name: {
            "role": agent.role,
            "responsibility": agent.responsibility,
            "input_schema": agent.input_schema,
            "output_schema": agent.output_schema,
        }
        for name, agent in agents.items()
    }
