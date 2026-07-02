import json
import unittest

from agents.router_agent import RouterAgent
from tests.fakes import FakeClient, FakeResponse


def make_router(raw_response, supports_strict_json_schema=False):
    """Build a RouterAgent with its real __init__ bypassed -- avoids needing real
    credentials/network just to test get_response/postprocess's logic."""
    router = RouterAgent.__new__(RouterAgent)
    router.client = FakeClient([FakeResponse(raw_response)])
    router.model_name = "any-model"
    router.supports_strict_json_schema = supports_strict_json_schema
    return router


class TestRouterAgentGetResponse(unittest.TestCase):
    def test_allowed_message_routes_to_details_agent(self):
        router = make_router(json.dumps({"decision": "allowed", "category": "details_agent", "message": ""}))
        response = router.get_response([{"role": "user", "content": "what are your hours"}])
        self.assertEqual(response["memory"]["guard_decision"], "allowed")
        self.assertEqual(response["memory"]["classification_decision"], "details_agent")
        self.assertEqual(response["content"], "")

    def test_not_allowed_message_carries_the_apology_message(self):
        router = make_router(json.dumps({
            "decision": "not allowed", "category": "", "message": "Sorry, I can't help with that. Can I help you with your order?",
        }))
        response = router.get_response([{"role": "user", "content": "what's the weather"}])
        self.assertEqual(response["memory"]["guard_decision"], "not allowed")
        self.assertIn("Sorry", response["content"])

    def test_malformed_output_on_fallback_path_fails_safe_instead_of_crashing(self):
        router = make_router("not valid json at all", supports_strict_json_schema=False)
        response = router.get_response([{"role": "user", "content": "hi"}])
        # Must not raise -- should return a safe "not allowed" fallback per
        # RouterAgent.get_response's SchemaValidationError handling.
        self.assertEqual(response["memory"]["guard_decision"], "not allowed")


if __name__ == "__main__":
    unittest.main()
