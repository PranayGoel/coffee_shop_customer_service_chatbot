"""
Generates a labeled routing dataset for fine-tuning (see finetune_router_llama.ipynb),
by expanding api/eval_dataset.py's ~35 hand-labeled examples with simple template-based
paraphrase variation -- no LLM calls needed to build this (this environment has no
funded API key), so variation comes from substitution templates, not generation.

Output format matches what the Unsloth Llama-3.1 Alpaca-style notebook expects:
one JSON object per line, {"instruction": <router system prompt>, "input": <user
message>, "output": <expected structured JSON response>}.

Honest scope: this produces a plausible-sized (~200-400 example) dataset for the
notebook to consume, not a professionally curated one -- real fine-tuning would
benefit from human review of these before training, and ideally some genuine
(non-templated) example diversity. Documented as a starting point.
"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
from eval_dataset import EXAMPLES  # noqa: E402


ROUTER_INSTRUCTION = (
    "You are the router for a coffee shop assistant that serves drinks and pastries. "
    "In a single step, decide whether the user's message is something this assistant "
    "may handle, and if so, choose which downstream agent should handle it: "
    "details_agent, order_taking_agent, or recommendation_agent. Output a JSON object "
    'with keys "decision", "category", "message".'
)

# Simple substitution templates per category -- deliberately mechanical (not LLM-
# generated) so this script needs no API key and no network access to run.
DETAILS_TEMPLATES = [
    "Do you have {item}?",
    "What's in the {item}?",
    "Tell me about your {item}.",
    "Can you describe the {item}?",
    "How much does the {item} cost?",
    "Is the {item} available today?",
]
ORDER_TEMPLATES = [
    "I'd like a {item}.",
    "Can I get a {item}?",
    "One {item} please.",
    "I want to order a {item}.",
    "Give me two {item}s.",
    "I'll take a {item} to go.",
]
RECOMMENDATION_TEMPLATES = [
    "What goes well with {item}?",
    "What do you recommend besides {item}?",
    "Anything similar to {item}?",
    "What pairs nicely with a {item}?",
]
MENU_ITEMS = [
    "cappuccino", "latte", "croissant", "espresso shot", "chocolate croissant",
    "ginger scone", "hazelnut biscotti", "cranberry scone", "almond croissant",
    "jumbo savory scone", "chocolate chip biscotti", "dark chocolate", "oatmeal scone",
]


def _expected_output(decision, category, message=""):
    return json.dumps({"decision": decision, "category": category, "message": message})


def generate_examples():
    """
    Returns a list of {"instruction", "input", "output"} dicts: the base 35
    hand-labeled examples plus template-generated variations, deduplicated.
    """
    examples = []
    seen_inputs = set()

    def add(user_message, decision, category, message=""):
        if user_message in seen_inputs:
            return
        seen_inputs.add(user_message)
        examples.append({
            "instruction": ROUTER_INSTRUCTION,
            "input": user_message,
            "output": _expected_output(decision, category, message),
        })

    # Base hand-labeled examples.
    for ex in EXAMPLES:
        message = "" if ex["expected_decision"] == "allowed" else "Sorry, I can't help with that. Can I help you with your order?"
        add(ex["message"], ex["expected_decision"], ex["expected_category"] or "", message)

    # Template-expanded variations.
    for item in MENU_ITEMS:
        for template in DETAILS_TEMPLATES:
            add(template.format(item=item), "allowed", "details_agent")
        for template in ORDER_TEMPLATES:
            add(template.format(item=item), "allowed", "order_taking_agent")
        for template in RECOMMENDATION_TEMPLATES:
            add(template.format(item=item), "allowed", "recommendation_agent")

    return examples


def main(output_path):
    examples = generate_examples()
    with open(output_path, "w") as f:
        for example in examples:
            f.write(json.dumps(example) + "\n")
    print(f"Wrote {len(examples)} training examples to {output_path}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "router_training_data.jsonl"
    main(output)
