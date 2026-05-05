from __future__ import annotations

from persona_sim.presets.action_evaluation import ACTION_EVALUATION_PRESET
from persona_sim.presets.decision_comparison import DECISION_COMPARISON_PRESET
from persona_sim.presets.idea_validation import IDEA_VALIDATION_PRESET
from persona_sim.presets.revenue_hypothesis_validation import REVENUE_HYPOTHESIS_VALIDATION_PRESET


PRESETS = {
    "idea_validation": IDEA_VALIDATION_PRESET,
    "decision_comparison": DECISION_COMPARISON_PRESET,
    "action_evaluation": ACTION_EVALUATION_PRESET,
    "revenue_hypothesis_validation": REVENUE_HYPOTHESIS_VALIDATION_PRESET,
}


def get_preset(name: str):
    try:
        return PRESETS[name]
    except KeyError as exc:
        available = ", ".join(sorted(PRESETS))
        raise ValueError(f"Unknown preset '{name}'. Available presets: {available}") from exc


def list_presets() -> list[str]:
    return sorted(PRESETS)
