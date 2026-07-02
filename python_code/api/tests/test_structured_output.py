import json
import unittest

from structured_output import (
    RouterDecision,
    SchemaValidationError,
    get_structured_router_response,
    ROUTER_JSON_SCHEMA,
)
from tests.fakes import FakeClient, FakeResponse


class TestRouterDecisionFromJson(unittest.TestCase):
    def test_valid_json_parses(self):
        decision = RouterDecision.from_json(json.dumps({
            "decision": "allowed", "category": "details_agent", "message": "",
        }))
        self.assertEqual(decision.decision, "allowed")
        self.assertEqual(decision.category, "details_agent")

    def test_invalid_json_raises_schema_validation_error(self):
        with self.assertRaises(SchemaValidationError):
            RouterDecision.from_json("not json at all {")

    def test_out_of_enum_decision_raises(self):
        with self.assertRaises(SchemaValidationError):
            RouterDecision.from_json(json.dumps({"decision": "maybe", "category": "", "message": ""}))

    def test_out_of_enum_category_raises(self):
        with self.assertRaises(SchemaValidationError):
            RouterDecision.from_json(json.dumps({"decision": "allowed", "category": "not_a_real_agent", "message": ""}))

    def test_missing_required_key_raises(self):
        with self.assertRaises(SchemaValidationError):
            RouterDecision.from_json(json.dumps({"category": "details_agent"}))

    def test_missing_optional_keys_default_sensibly(self):
        decision = RouterDecision.from_json(json.dumps({"decision": "not allowed"}))
        self.assertEqual(decision.category, "")
        self.assertEqual(decision.message, "")


class TestGetStructuredRouterResponse(unittest.TestCase):
    def test_strict_mode_passes_response_format(self):
        client = FakeClient([FakeResponse(json.dumps({"decision": "allowed", "category": "details_agent", "message": ""}))])
        decision = get_structured_router_response(client, "any-model", [], supports_strict_json_schema=True)
        self.assertEqual(decision.category, "details_agent")
        sent_kwargs = client.calls[0]
        self.assertIn("response_format", sent_kwargs)
        self.assertEqual(sent_kwargs["response_format"]["json_schema"]["schema"], ROUTER_JSON_SCHEMA)

    def test_non_strict_mode_omits_response_format(self):
        client = FakeClient([FakeResponse(json.dumps({"decision": "not allowed", "category": "", "message": "sorry"}))])
        decision = get_structured_router_response(client, "any-model", [], supports_strict_json_schema=False)
        self.assertEqual(decision.decision, "not allowed")
        self.assertNotIn("response_format", client.calls[0])

    def test_non_strict_mode_raises_clean_error_on_malformed_output(self):
        client = FakeClient([FakeResponse("this is not json")])
        with self.assertRaises(SchemaValidationError):
            get_structured_router_response(client, "any-model", [], supports_strict_json_schema=False)


if __name__ == "__main__":
    unittest.main()
