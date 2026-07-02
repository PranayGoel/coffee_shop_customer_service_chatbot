"""
~35 hand-labeled example conversations for the routing eval harness (see
eval_harness.py). Each entry is one user turn plus the routing outcome a correct
RouterAgent should produce.

expected_decision: "allowed" or "not allowed"
expected_category: one of "details_agent"/"order_taking_agent"/"recommendation_agent"
    when allowed, else None.

Menu items match order_taking_agent.py's system prompt, for realism.
"""

EXAMPLES = [
    # --- details_agent: shop info / menu questions ---
    {"message": "What are your opening hours?", "expected_decision": "allowed", "expected_category": "details_agent"},
    {"message": "Where are you located?", "expected_decision": "allowed", "expected_category": "details_agent"},
    {"message": "What's in a Jumbo Savory Scone?", "expected_decision": "allowed", "expected_category": "details_agent"},
    {"message": "Does the latte have nuts in it?", "expected_decision": "allowed", "expected_category": "details_agent"},
    {"message": "What pastries do you have?", "expected_decision": "allowed", "expected_category": "details_agent"},
    {"message": "Is the chocolate croissant vegan?", "expected_decision": "allowed", "expected_category": "details_agent"},
    {"message": "Can you list your full menu?", "expected_decision": "allowed", "expected_category": "details_agent"},
    {"message": "What ingredients are in the dark chocolate drink?", "expected_decision": "allowed", "expected_category": "details_agent"},
    {"message": "Do you have gluten-free options?", "expected_decision": "allowed", "expected_category": "details_agent"},
    {"message": "How much is a cappuccino?", "expected_decision": "allowed", "expected_category": "details_agent"},

    # --- order_taking_agent: making an order ---
    {"message": "I'd like to order a cappuccino and a croissant.", "expected_decision": "allowed", "expected_category": "order_taking_agent"},
    {"message": "Can I get two lattes please?", "expected_decision": "allowed", "expected_category": "order_taking_agent"},
    {"message": "I want to place an order.", "expected_decision": "allowed", "expected_category": "order_taking_agent"},
    {"message": "Give me a hazelnut biscotti.", "expected_decision": "allowed", "expected_category": "order_taking_agent"},
    {"message": "I'll take an espresso shot and a ginger scone.", "expected_decision": "allowed", "expected_category": "order_taking_agent"},
    {"message": "Add a chocolate syrup to my drink.", "expected_decision": "allowed", "expected_category": "order_taking_agent"},
    {"message": "One almond croissant please.", "expected_decision": "allowed", "expected_category": "order_taking_agent"},
    {"message": "Can I order 3 cranberry scones?", "expected_decision": "allowed", "expected_category": "order_taking_agent"},
    {"message": "I want to buy a latte.", "expected_decision": "allowed", "expected_category": "order_taking_agent"},
    {"message": "That's all, thanks -- that's my order.", "expected_decision": "allowed", "expected_category": "order_taking_agent"},

    # --- recommendation_agent ---
    {"message": "What do you recommend to go with a latte?", "expected_decision": "allowed", "expected_category": "recommendation_agent"},
    {"message": "What's popular here?", "expected_decision": "allowed", "expected_category": "recommendation_agent"},
    {"message": "What should I get if I like chocolate?", "expected_decision": "allowed", "expected_category": "recommendation_agent"},
    {"message": "Any suggestions for a first-time visitor?", "expected_decision": "allowed", "expected_category": "recommendation_agent"},
    {"message": "What goes well with a chocolate croissant?", "expected_decision": "allowed", "expected_category": "recommendation_agent"},
    {"message": "Recommend me something sweet.", "expected_decision": "allowed", "expected_category": "recommendation_agent"},
    {"message": "What's your best-selling pastry?", "expected_decision": "allowed", "expected_category": "recommendation_agent"},

    # --- not allowed: off-topic or explicitly excluded ---
    {"message": "What's the weather like today?", "expected_decision": "not allowed", "expected_category": None},
    {"message": "Can you help me with my homework?", "expected_decision": "not allowed", "expected_category": None},
    {"message": "How do I make a latte at home?", "expected_decision": "not allowed", "expected_category": None},
    {"message": "What's your barista's name?", "expected_decision": "not allowed", "expected_category": None},
    {"message": "Tell me a joke.", "expected_decision": "not allowed", "expected_category": None},
    {"message": "What's the capital of France?", "expected_decision": "not allowed", "expected_category": None},
    {"message": "Can you write me a poem?", "expected_decision": "not allowed", "expected_category": None},
    {"message": "How do you make your espresso shots?", "expected_decision": "not allowed", "expected_category": None},
]
