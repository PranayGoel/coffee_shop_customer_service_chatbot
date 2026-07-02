"""
Real structured outputs for RouterAgent (the highest-frequency call -- it runs on
every single turn), replacing "prompt the model to output JSON, then json.loads() it
and hope" with a genuine schema guarantee where the active provider supports one.

Scope note: this round migrates RouterAgent only. DetailsAgent/OrderTakingAgent/
RecommendationAgent's schemas use idiosyncratic keys (e.g. "step number", "chain of
thought" -- literal spaces, matching the original prompts) and OrderTakingAgent's
postprocess has non-trivial downstream logic (recommendation triggering). Migrating
those without a live endpoint to validate schema compatibility against risks a
regression I can't verify -- narrowing scope to the router is the honest, contained
choice for this round; the others are documented as a natural next step.

Deliberately stdlib-only (dataclasses, not Pydantic): this environment's network
blocks PyPI entirely, so pydantic can't be installed here either. A dataclass +
a hand-written JSON Schema dict gets the same real guarantee from OpenAI's
response_format API without adding a dependency I can't verify.
"""

import json
from dataclasses import dataclass


ALLOWED_DECISIONS = ("allowed", "not allowed")
ALLOWED_CATEGORIES = ("details_agent", "order_taking_agent", "recommendation_agent", "")

ROUTER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "decision": {"type": "string", "enum": list(ALLOWED_DECISIONS)},
        "category": {"type": "string", "enum": list(ALLOWED_CATEGORIES)},
        "message": {"type": "string"},
    },
    "required": ["decision", "category", "message"],
    "additionalProperties": False,
}


class SchemaValidationError(ValueError):
    pass


@dataclass
class RouterDecision:
    decision: str
    category: str = ""
    message: str = ""

    def validate(self):
        """Raises SchemaValidationError if fields are out of the allowed enum ranges."""
        if self.decision not in ALLOWED_DECISIONS:
            raise SchemaValidationError(f"decision must be one of {ALLOWED_DECISIONS}, got {self.decision!r}")
        if self.category not in ALLOWED_CATEGORIES:
            raise SchemaValidationError(f"category must be one of {ALLOWED_CATEGORIES}, got {self.category!r}")
        return self

    @classmethod
    def from_json(cls, raw_text):
        """Parse + validate a raw JSON string into a RouterDecision. Raises
        SchemaValidationError (wrapping json.JSONDecodeError or a validation failure)
        on any problem -- callers get one clear exception type to handle."""
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise SchemaValidationError(f"Router output was not valid JSON: {e}") from e
        try:
            return cls(
                decision=data["decision"],
                category=data.get("category", ""),
                message=data.get("message", ""),
            ).validate()
        except KeyError as e:
            raise SchemaValidationError(f"Router JSON missing required key: {e}") from e


def get_structured_router_response(client, model, messages, supports_strict_json_schema, max_tokens=200):
    """
    Get a validated RouterDecision from the model.

    When the active provider supports strict JSON schema (per llm_client's
    per-provider config), passes response_format={"type":"json_schema",...} so the
    provider itself guarantees conformance -- the model literally cannot return
    malformed JSON or an out-of-enum value. Otherwise falls back to the existing
    prompt-based JSON pattern, still validated on this end via RouterDecision.from_json
    (catches malformed output here instead of upstream, same as before this change).

    Args:
        client: an OpenAI-SDK-shaped client (real or a test fake).
        model (str): model name.
        messages (list[dict]): chat messages, already including the router's system prompt.
        supports_strict_json_schema (bool): from llm_client.resolve_provider_config(...).
        max_tokens (int): kept small -- routing only needs a short reply.

    Returns:
        RouterDecision

    Raises:
        SchemaValidationError: if the response still can't be parsed/validated (only
        realistically possible on the non-strict fallback path).
    """
    kwargs = {}
    if supports_strict_json_schema:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "RouterDecision", "schema": ROUTER_JSON_SCHEMA, "strict": True},
        }

    response = client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, **kwargs)
    raw = response.choices[0].message.content
    return RouterDecision.from_json(raw)
