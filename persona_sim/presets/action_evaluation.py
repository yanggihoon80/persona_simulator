from persona_sim.presets.base import COMMON_SUMMARY_SCHEMA, PresetSpec


ACTION_EVALUATION_PRESET = PresetSpec(
    name="action_evaluation",
    description="Evaluate whether a proposed action is worth executing, what blocks execution, and how users perceive its practical value.",
    required_config_paths=["service_condition", "seed_rules.target_condition", "decision_context.goal"],
    scoring_focus=[
        "action value",
        "execution feasibility",
        "required inputs",
        "risk",
        "next-step clarity",
    ],
    output_schema=COMMON_SUMMARY_SCHEMA,
)
