from persona_sim.presets.base import COMMON_SUMMARY_SCHEMA, PresetSpec


IDEA_VALIDATION_PRESET = PresetSpec(
    name="idea_validation",
    description="Validate whether a service or product idea solves a meaningful user problem and has adoption potential.",
    required_config_paths=["service_condition", "seed_rules.target_condition"],
    scoring_focus=[
        "problem severity",
        "perceived value",
        "trust",
        "adoption friction",
        "willingness to pay",
    ],
    output_schema=COMMON_SUMMARY_SCHEMA,
)
