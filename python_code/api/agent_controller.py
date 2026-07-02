from agents import (RouterAgent,
                    DetailsAgent,
                    OrderTakingAgent,
                    RecommendationAgent,
                    AgentProtocol
                    )

class AgentController():
    def __init__(self, provider=None, router_agent=None, agent_dict=None):
        """
        Args:
            provider (str, optional): which LLM provider to construct real agents
                against (see llm_client.py) -- "runpod" (default), "openai",
                "gemini", or "deepseek". Ignored if router_agent/agent_dict are
                supplied directly.
            router_agent, agent_dict (optional): inject fakes for testing instead of
                constructing real agents (which need live credentials/network).
                Passing both skips all real agent construction entirely.
        """
        if router_agent is not None and agent_dict is not None:
            self.router_agent = router_agent
            self.agent_dict: dict[str, AgentProtocol] = agent_dict
            return

        # Single routing agent replaces the sequential guard + classification calls.
        self.router_agent = router_agent or RouterAgent(provider=provider)
        self.recommendation_agent = RecommendationAgent('recommendation_objects/apriori_recommendations.json',
                                                        'recommendation_objects/popularity_recommendation.csv',
                                                        provider=provider,
                                                        )

        self.agent_dict: dict[str, AgentProtocol] = agent_dict or {
            "details_agent": DetailsAgent(provider=provider),
            "order_taking_agent": OrderTakingAgent(self.recommendation_agent, provider=provider),
            "recommendation_agent": self.recommendation_agent
        }

    def get_response(self,input):
        # Extract User Input
        job_input = input["input"]
        messages = job_input["messages"]

        # One LLM call handles both the guard decision and agent routing.
        router_response = self.router_agent.get_response(messages)
        if router_response["memory"]["guard_decision"] == "not allowed":
            return router_response

        chosen_agent = router_response["memory"]["classification_decision"]

        # Fall back to the details agent if routing returns an unexpected category.
        # (dict.get(key, default) evaluates `default` eagerly even when `key` is
        # present, so self.agent_dict["details_agent"] as the default would require
        # "details_agent" to always exist even for a valid, present chosen_agent --
        # using an explicit None-check avoids that.)
        agent = self.agent_dict.get(chosen_agent)
        if agent is None:
            agent = self.agent_dict["details_agent"]
        response = agent.get_response(messages)

        return response
