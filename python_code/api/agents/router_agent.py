from copy import deepcopy
# llm_client/structured_output live alongside agent_controller.py in api/, which
# (like this codebase's other cross-package references) is a plain sys.path entry,
# not a formal package -- hence a top-level import rather than a relative one.
import llm_client
from structured_output import get_structured_router_response, SchemaValidationError


class RouterAgent():
    """Single-call router combining the guard and classification steps.

    The original pipeline made two sequential LLM calls per turn: a GuardAgent
    call to decide whether the message is in scope, then a ClassificationAgent
    call to pick the downstream agent. This agent does both in one call,
    removing a full LLM round-trip from every turn.

    Also migrated to real structured outputs (see structured_output.py) -- the
    highest-frequency call in the whole system (runs on every turn), so it's the
    highest-leverage place to replace "prompt for JSON and hope" with a genuine
    schema guarantee where the active provider supports one.
    """
    def __init__(self, provider=None):
        # dotenv is only imported when an agent is actually constructed, not at
        # module import time -- keeps this module importable without the package.
        from dotenv import load_dotenv
        load_dotenv()
        self.client, self._config = llm_client.get_client(provider=provider)
        self.model_name = self._config["model"]
        self.supports_strict_json_schema = self._config["supports_strict_json_schema"]

    def get_response(self, messages):
        messages = deepcopy(messages)

        system_prompt = """
            You are the router for a coffee shop assistant that serves drinks and pastries.
            In a single step, do two things:
            (1) decide whether the user's latest message is something this assistant may handle, and
            (2) if it is, choose which downstream agent should handle it.

            ALLOWED:
            1. Questions about the coffee shop (location, working hours, menu items, item details/ingredients) or listing menu items.
            2. Making an order.
            3. Asking for a recommendation of what to buy.

            NOT ALLOWED:
            1. Anything unrelated to this coffee shop.
            2. Questions about the staff or how to make a menu item.

            Downstream agents (only when the message is allowed):
            - details_agent: answers questions about the shop and menu items, or lists menu items.
            - order_taking_agent: takes and manages an order until it is complete.
            - recommendation_agent: recommends what to buy.

            Output ONLY a JSON object. Each key is a string and each value is a string. Follow this format exactly:
            {
            "chain of thought": "briefly reason about allowed vs not allowed, then which agent fits",
            "decision": "allowed" or "not allowed",
            "category": one of "details_agent", "order_taking_agent", "recommendation_agent" when allowed, otherwise "",
            "message": "" when allowed, otherwise "Sorry, I can't help with that. Can I help you with your order?"
            }
            """

        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        # Routing needs only a short reply, so cap tokens to keep it fast. When the
        # active provider supports strict JSON schema, this call is guaranteed to
        # conform -- no json.loads()-and-hope, no chance of a schema-violating
        # response, no wasted repair round-trip.
        try:
            decision = get_structured_router_response(
                self.client, self.model_name, input_messages, self.supports_strict_json_schema, max_tokens=200
            )
        except SchemaValidationError:
            # Only realistically reachable on the non-strict fallback path (a
            # provider without a schema guarantee returning something unparseable).
            # Fail safe rather than crashing the whole request.
            return {
                "role": "assistant",
                "content": "Sorry, something went wrong on my end. Could you rephrase that?",
                "memory": {"agent": "router_agent", "guard_decision": "not allowed", "classification_decision": ""},
            }
        return self.postprocess(decision)

    def postprocess(self, decision):
        return {
            "role": "assistant",
            "content": decision.message,
            "memory": {
                "agent": "router_agent",
                "guard_decision": decision.decision,
                "classification_decision": decision.category,
            },
        }
