from dotenv import load_dotenv
import os
import json
from copy import deepcopy
from .utils import get_chatbot_response
from openai import OpenAI
load_dotenv()


class RouterAgent():
    """Single-call router combining the guard and classification steps.

    The original pipeline made two sequential LLM calls per turn: a GuardAgent
    call to decide whether the message is in scope, then a ClassificationAgent
    call to pick the downstream agent. This agent does both in one call,
    removing a full LLM round-trip from every turn.
    """
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("RUNPOD_TOKEN"),
            base_url=os.getenv("RUNPOD_CHATBOT_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME")

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

        # Routing needs only a short JSON reply, so cap tokens to keep it fast.
        chatbot_output = get_chatbot_response(
            self.client, self.model_name, input_messages, max_tokens=200
        )
        return self.postprocess(chatbot_output)

    def postprocess(self, output):
        output = json.loads(output)

        return {
            "role": "assistant",
            "content": output.get("message", ""),
            "memory": {
                "agent": "router_agent",
                "guard_decision": output.get("decision"),
                "classification_decision": output.get("category"),
            },
        }
