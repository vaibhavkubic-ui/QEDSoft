from __future__ import annotations

from qedsoft.models import FormalizationBundle, VerificationSubgoal

from .spec_parser import HardwareSpecParser


class QEDAIChipAutoformalizer:
    """Chip-verification adaptation of the original QEDAI autoformalizer.

    Original QEDAI formalizes a natural-language theorem into Lean4.
    QEDSoft formalizes a chip specification into paired SVA and Lean
    obligations that can be verified, repaired, and ranked.
    """

    def __init__(self, parser: HardwareSpecParser | None = None) -> None:
        self.parser = parser or HardwareSpecParser()

    def formalize(
        self,
        spec_text: str,
        rtl_text: str = "",
        design_name: str = "qedsoft_design",
        top_module: str | None = None,
        clock: str | None = None,
        reset: str | None = None,
        reset_active_low: bool | None = None,
    ) -> FormalizationBundle:
        parsed = self.parser.parse(
            spec_text=spec_text,
            rtl_text=rtl_text,
            design_name=design_name,
            top_module=top_module,
            clock=clock,
            reset=reset,
            reset_active_low=reset_active_low,
        )
        subgoals = [
            self._requirement_to_subgoal(index, requirement)
            for index, requirement in enumerate(parsed.model.requirements, start=1)
        ]
        strategy = {
            "qedai_mapping": {
                "autoformalizer": "spec_to_requirement_graph",
                "proof_planner": "requirement_to_sva_and_lean_subgoals",
                "pgtm": "template_and_tool_selection",
                "dpps_lf_hgt": "parallel_candidate_ranking_placeholder",
                "sera_vgp": "structured_verifier_guided_repair",
                "vph_ac": "feedback_memory_for_future_ranking",
            },
            "unmapped_mentions": parsed.unmapped_mentions,
            "subgoal_count": len(subgoals),
        }
        return FormalizationBundle(model=parsed.model, subgoals=subgoals, strategy=strategy)

    def _requirement_to_subgoal(self, index: int, requirement) -> VerificationSubgoal:
        priority_by_category = {
            "reset": 10,
            "safety": 9,
            "protocol": 8,
            "temporal": 7,
            "equivalence": 6,
            "functional": 5,
        }
        return VerificationSubgoal(
            id=f"SG-{index:03d}",
            requirement_id=requirement.id,
            statement=requirement.text,
            artifact_type="both",
            signals=requirement.signals,
            assumptions=[],
            priority=priority_by_category.get(requirement.category, 5),
            confidence=requirement.confidence,
        )
