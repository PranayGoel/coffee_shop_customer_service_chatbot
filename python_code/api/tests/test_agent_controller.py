import unittest

from agent_controller import AgentController


class FakeRouterAgent:
    def __init__(self, decision, category):
        self.decision = decision
        self.category = category

    def get_response(self, messages):
        return {
            "role": "assistant",
            "content": "" if self.decision == "allowed" else "Sorry, I can't help with that.",
            "memory": {"agent": "router_agent", "guard_decision": self.decision, "classification_decision": self.category},
        }


class FakeDownstreamAgent:
    def __init__(self, name):
        self.name = name
        self.received_messages = None

    def get_response(self, messages):
        self.received_messages = messages
        return {"role": "assistant", "content": f"handled by {self.name}", "memory": {"agent": self.name}}


class TestAgentControllerDispatch(unittest.TestCase):
    def test_blocked_message_returns_router_response_directly(self):
        router = FakeRouterAgent("not allowed", "")
        controller = AgentController(router_agent=router, agent_dict={})
        response = controller.get_response({"input": {"messages": [{"role": "user", "content": "off topic"}]}})
        self.assertEqual(response["memory"]["agent"], "router_agent")

    def test_allowed_message_dispatches_to_the_right_agent(self):
        router = FakeRouterAgent("allowed", "details_agent")
        details = FakeDownstreamAgent("details_agent")
        controller = AgentController(router_agent=router, agent_dict={"details_agent": details})
        response = controller.get_response({"input": {"messages": [{"role": "user", "content": "what are your hours"}]}})
        self.assertEqual(response["content"], "handled by details_agent")

    def test_unexpected_category_falls_back_to_details_agent(self):
        router = FakeRouterAgent("allowed", "some_future_agent_not_yet_wired_up")
        details = FakeDownstreamAgent("details_agent")
        controller = AgentController(router_agent=router, agent_dict={"details_agent": details})
        response = controller.get_response({"input": {"messages": [{"role": "user", "content": "hi"}]}})
        self.assertEqual(response["content"], "handled by details_agent")

    def test_downstream_agent_receives_the_original_messages(self):
        router = FakeRouterAgent("allowed", "order_taking_agent")
        order = FakeDownstreamAgent("order_taking_agent")
        controller = AgentController(router_agent=router, agent_dict={"order_taking_agent": order})
        messages = [{"role": "user", "content": "I'd like a latte"}]
        controller.get_response({"input": {"messages": messages}})
        self.assertEqual(order.received_messages, messages)


if __name__ == "__main__":
    unittest.main()
