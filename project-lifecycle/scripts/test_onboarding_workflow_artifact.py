#!/usr/bin/env python3
"""Verifier for onboarding workflow artifact (PLC-E3-S5 / CAF-126)."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parents[2]
WORKFLOW_PATH = PROJECT_ROOT / "workflow-artifacts" / "workflow-examples" / "onboarding-workflow.v1.json"
INTENT_PATH = PROJECT_ROOT / "workflow-artifacts" / "examples" / "onboarding-intent-capture.json"
WORKFLOW_VALIDATOR_PATH = SCRIPTS_DIR / "validate_workflow_artifacts.py"
INTENT_VALIDATOR_PATH = SCRIPTS_DIR / "validate_intent_capture.py"

workflow_spec = importlib.util.spec_from_file_location(
    "validate_workflow_artifacts",
    WORKFLOW_VALIDATOR_PATH,
)
workflow_validator = importlib.util.module_from_spec(workflow_spec)
sys.modules[workflow_spec.name] = workflow_validator
workflow_spec.loader.exec_module(workflow_validator)

intent_spec = importlib.util.spec_from_file_location(
    "validate_intent_capture",
    INTENT_VALIDATOR_PATH,
)
intent_validator = importlib.util.module_from_spec(intent_spec)
sys.modules[intent_spec.name] = intent_validator
intent_spec.loader.exec_module(intent_validator)


def _workflow() -> dict:
    return json.loads(WORKFLOW_PATH.read_text())


def _intent() -> dict:
    return json.loads(INTENT_PATH.read_text())


def _step(workflow: dict, step_id: str) -> dict:
    for step in workflow["steps"]:
        if step["step_id"] == step_id:
            return step
    raise AssertionError(f"step not found: {step_id}")


class OnboardingWorkflowArtifactTests(unittest.TestCase):
    def test_onboarding_intent_and_workflow_are_valid(self) -> None:
        intent_result = intent_validator.validate_capture(_intent(), label=str(INTENT_PATH))
        workflow_result = workflow_validator.validate_workflow(
            _workflow(),
            label=str(WORKFLOW_PATH),
        )

        self.assertEqual(intent_result.errors, [])
        self.assertEqual(workflow_result.errors, [])

    def test_current_onboarding_question_surface_is_represented(self) -> None:
        workflow = _workflow()
        prompts = {step["prompt"]["text"] for step in workflow["steps"]}

        expected_prompts = {
            "How often are migraines showing up for you right now?",
            "On average, what is your migraine intensity from 0 to 10?",
            "How long do they usually last?",
            (
                "What is the quality or feel of the migraine? For example: pressure, "
                "throbbing, stabbing, foggy, pulsing."
            ),
            "What symptoms are currently part of your migraine journey? Send one symptom at a time.",
            "What tends to trigger them? Send one trigger or a short list.",
            "When did migraines first start in your life?",
            "What impact have migraines had on your life?",
            "What is one thing migraines create that you no longer want?",
            "Anything else you no longer want?",
            (
                "What is one thing you do want instead? For example joy, energy, stamina, "
                "or being able to make and keep plans."
            ),
            "Anything else you want to have instead?",
            "Write a little about how your life will be once you have those things.",
            "What is your baseline well-being level from 0 to 10?"
        }
        self.assertTrue(expected_prompts.issubset(prompts))

    def test_clarification_never_advances_state(self) -> None:
        workflow = _workflow()

        for step in workflow["steps"]:
            clarification = step["clarification_behavior"]
            self.assertTrue(clarification["allow_clarification"], step["step_id"])
            self.assertFalse(clarification["advance_on_clarification"], step["step_id"])
            needs_clarification = [
                transition
                for transition in step["transitions"]
                if transition["on"] == "needs_clarification"
            ]
            self.assertEqual(needs_clarification[0]["target"], step["step_id"])

    def test_symptoms_queue_per_symptom_rating(self) -> None:
        workflow = _workflow()
        symptom_item = _step(workflow, "migraine_symptom_item")
        symptom_rating = _step(workflow, "migraine_symptom_rating")

        self.assertEqual(symptom_item["repeat_policy"], "until_no_or_done")
        self.assertEqual(symptom_item["duplicate_policy"], "ask_if_anything_else")
        self.assertEqual(symptom_item["transitions"][0], {
            "on": "valid_answer",
            "target": "migraine_symptom_rating",
        })
        self.assertEqual(symptom_rating["answer"]["type"], "rating_0_10")
        self.assertTrue(symptom_rating["completion_gate"]["rating_required"])
        self.assertEqual(symptom_rating["transitions"][0], {
            "on": "valid_answer",
            "target": "migraine_symptoms_more",
        })

    def test_impact_wants_and_no_longer_wants_loop_until_done(self) -> None:
        workflow = _workflow()
        loop_steps = {
            "migraine_life_impact_item": "migraine_life_impact_more",
            "negative_item": "negative_rating",
            "negative_more": "positive_item",
            "positive_item": "positive_rating",
            "positive_more": "life_after_migraine_vision",
        }

        self.assertEqual(_step(workflow, "migraine_life_impact_item")["repeat_policy"], "until_no_or_done")
        self.assertEqual(_step(workflow, "negative_item")["duplicate_policy"], "reject_duplicate")
        self.assertEqual(_step(workflow, "positive_item")["duplicate_policy"], "reject_duplicate")
        for step_id, target in loop_steps.items():
            step = _step(workflow, step_id)
            transition_targets = {transition["target"] for transition in step["transitions"]}
            self.assertIn(target, transition_targets)

    def test_objective_mappings_do_not_force_create_duplicates(self) -> None:
        workflow = _workflow()
        fields = {field["field_id"]: field for field in workflow["fields"]}

        negative_storage = fields["baseline_no_longer_want"]["storage"]
        positive_storage = fields["baseline_want"]["storage"]
        self.assertEqual(negative_storage["kind"], "objective")
        self.assertEqual(positive_storage["kind"], "objective")
        self.assertNotIn("force_create", negative_storage)
        self.assertNotIn("force_create", positive_storage)


if __name__ == "__main__":
    unittest.main(verbosity=2)
