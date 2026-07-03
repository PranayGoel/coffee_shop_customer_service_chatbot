import unittest

from eval_harness import run_eval, estimate_cost


class FakeRouter:
    """Scripted router: cycles through canned (decision, category) answers in order."""

    def __init__(self, answers):
        self._answers = list(answers)

    def get_response(self, messages):
        decision, category = self._answers.pop(0)
        return {"memory": {"guard_decision": decision, "classification_decision": category}}


class TestRunEval(unittest.TestCase):
    def test_perfect_score(self):
        examples = [
            {"message": "hi", "expected_decision": "allowed", "expected_category": "details_agent"},
            {"message": "bye", "expected_decision": "not allowed", "expected_category": None},
        ]
        router = FakeRouter([("allowed", "details_agent"), ("not allowed", "")])
        result = run_eval(router, examples)
        self.assertEqual(result["accuracy"], 1.0)
        self.assertEqual(result["correct"], 2)

    def test_partial_score_reports_misses(self):
        examples = [
            {"message": "hi", "expected_decision": "allowed", "expected_category": "details_agent"},
            {"message": "order it", "expected_decision": "allowed", "expected_category": "order_taking_agent"},
        ]
        router = FakeRouter([("allowed", "details_agent"), ("allowed", "recommendation_agent")])  # 2nd is wrong
        result = run_eval(router, examples)
        self.assertEqual(result["correct"], 1)
        self.assertEqual(result["accuracy"], 0.5)
        self.assertEqual(len(result["results"]), 2)
        self.assertFalse(result["results"][1]["correct"])

    def test_empty_category_normalized_to_none(self):
        # RouterDecision defaults category to "" when not allowed; run_eval should
        # treat that the same as the dataset's expected_category=None.
        examples = [{"message": "off topic", "expected_decision": "not allowed", "expected_category": None}]
        router = FakeRouter([("not allowed", "")])
        result = run_eval(router, examples)
        self.assertEqual(result["accuracy"], 1.0)

    def test_includes_latency_and_cost_estimate(self):
        examples = [{"message": "hi", "expected_decision": "allowed", "expected_category": "details_agent"}]
        router = FakeRouter([("allowed", "details_agent")])
        result = run_eval(router, examples, provider="openai")
        self.assertIn("avg_latency_s", result)
        self.assertGreater(result["estimated_cost_usd"], 0)


class TestEstimateCost(unittest.TestCase):
    def test_runpod_is_free_per_call_by_design(self):
        # Self-hosted is billed as GPU-hours, not per-token -- estimate_cost
        # correctly reports $0 marginal per-call cost for it, not a made-up number.
        self.assertEqual(estimate_cost(1000, "runpod"), 0.0)

    def test_cheaper_provider_estimates_lower_cost_for_same_volume(self):
        gemini_cost = estimate_cost(1000, "gemini")
        openai_cost = estimate_cost(1000, "openai")
        self.assertLess(gemini_cost, openai_cost)

    def test_unknown_provider_defaults_to_zero_rather_than_crashing(self):
        self.assertEqual(estimate_cost(100, "not-a-real-provider"), 0.0)

    def test_openrouter_free_tier_is_zero_cost(self):
        self.assertEqual(estimate_cost(1000, "openrouter"), 0.0)


if __name__ == "__main__":
    unittest.main()
