from persona_sim.presets.base import COMMON_SUMMARY_SCHEMA, PresetSpec


DECISION_COMPARISON_PRESET = PresetSpec(
    name="decision_comparison",
    description="Compare user reaction to a decision-support service that helps evaluate multiple options. Example options are sample inputs, not the product itself.",
    required_config_paths=[
        "service_condition",
        "seed_rules.target_condition",
        "decision_context.goal",
        "decision_context.decision_type",
        "decision_context.example_options",
    ],
    scoring_focus=[
        "clarity improvement",
        "decision confidence",
        "trust in reasoning",
        "strategic fit",
        "execution likelihood",
    ],
    output_schema=COMMON_SUMMARY_SCHEMA,
)
