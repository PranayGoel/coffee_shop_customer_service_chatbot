from agents import (RouterAgent,
                    DetailsAgent,
                    OrderTakingAgent,
                    RecommendationAgent,
                    AgentProtocol
                    )

class AgentController():
    def __init__(self):
        # Single routing agent replaces the sequential guard + classification calls.
        self.router_agent = RouterAgent()
        self.recommendation_agent = RecommendationAgent('recommendation_objects/apriori_recommendations.json',
                                                        'recommendation_objects/popularity_recommendation.csv'
                                                        )

        self.agent_dict: dict[str, AgentProtocol] = {
            "details_agent": DetailsAgent(),
            "order_taking_agent": OrderTakingAgent(self.recommendation_agent),
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
        agent = self.agent_dict.get(chosen_agent, self.agent_dict["details_agent"])
        response = agent.get_response(messages)

        return response
