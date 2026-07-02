"""
Multi-provider routing eval harness: runs eval_dataset.EXAMPLES through a RouterAgent
and reports accuracy, latency, and estimated $ cost -- the actual "which cheap
provider is worth using" answer, not just "does routing work at all".

Runnable two ways:
  - `python3 eval_harness.py` -- constructs a real RouterAgent against whichever
    provider is configured (LLM_PROVIDER env var) and runs against a live model.
    Needs real credentials; not run by me in this environment (see README).
  - via run_eval(router_agent, examples) directly, injecting any object with a
    get_response(messages) method (real or a test fake) -- this is what the test
    suite uses, so the harness's own accounting logic is verified without a live key.

Cost estimates use approximate spot pricing gathered during Round 2's research
(2026-07); provider pricing changes -- treat PRICE_PER_1M_TOKENS as a rough estimate
to reverify against each provider's current pricing page, not an exact bill.
"""

import time


PRICE_PER_1M_TOKENS = {
    # (input, output) USD per 1M tokens. Approximate, gathered mid-2026 -- reverify
    # before relying on this for a real budget decision.
    "openai": (0.15, 0.60),      # gpt-4o-mini-class
    "gemini": (0.10, 0.40),      # Flash-Lite-class
    "deepseek": (0.14, 0.28),    # deepseek-chat, cache-miss pricing
    "runpod": (0.0, 0.0),        # self-hosted -- billed as GPU-hours, not per-token
}

# Rough per-call token estimate for this workload (short system prompt + a few
# turns of history in, short JSON reply out) -- used only for the cost estimate,
# not for anything correctness-critical.
ASSUMED_INPUT_TOKENS_PER_CALL = 700
ASSUMED_OUTPUT_TOKENS_PER_CALL = 120


def estimate_cost(num_calls, provider):
    """Rough $ estimate for `num_calls` routing calls on `provider`. See module docstring caveat."""
    input_price, output_price = PRICE_PER_1M_TOKENS.get(provider, (0.0, 0.0))
    input_tokens = num_calls * ASSUMED_INPUT_TOKENS_PER_CALL
    output_tokens = num_calls * ASSUMED_OUTPUT_TOKENS_PER_CALL
    return (input_tokens / 1_000_000) * input_price + (output_tokens / 1_000_000) * output_price


def run_eval(router_agent, examples, provider="runpod"):
    """
    Run every example through router_agent.get_response and score routing accuracy.

    Args:
        router_agent: any object with get_response(messages) -> dict shaped like
            RouterAgent's output (real or a test fake).
        examples (list[dict]): eval_dataset.EXAMPLES-shaped entries.
        provider (str): which provider this run is against, for cost estimation.

    Returns:
        dict: {"accuracy": float, "correct": int, "total": int, "results": [...],
               "avg_latency_s": float, "estimated_cost_usd": float}
    """
    results = []
    latencies = []
    correct = 0

    for example in examples:
        messages = [{"role": "user", "content": example["message"]}]
        start = time.perf_counter()
        response = router_agent.get_response(messages)
        latencies.append(time.perf_counter() - start)

        actual_decision = response["memory"]["guard_decision"]
        actual_category = response["memory"]["classification_decision"] or None

        is_correct = (
            actual_decision == example["expected_decision"]
            and actual_category == example["expected_category"]
        )
        if is_correct:
            correct += 1

        results.append({
            "message": example["message"],
            "expected": (example["expected_decision"], example["expected_category"]),
            "actual": (actual_decision, actual_category),
            "correct": is_correct,
        })

    total = len(examples)
    return {
        "accuracy": correct / total if total else 0.0,
        "correct": correct,
        "total": total,
        "results": results,
        "avg_latency_s": sum(latencies) / len(latencies) if latencies else 0.0,
        "estimated_cost_usd": estimate_cost(total, provider),
    }


def print_report(eval_result, provider):
    print(f"\n[eval] provider={provider}")
    print(f"[eval] accuracy: {eval_result['correct']}/{eval_result['total']} ({eval_result['accuracy']*100:.1f}%)")
    print(f"[eval] avg latency: {eval_result['avg_latency_s']*1000:.1f}ms/call")
    print(f"[eval] estimated cost: ${eval_result['estimated_cost_usd']:.4f} for this run")
    misses = [r for r in eval_result["results"] if not r["correct"]]
    if misses:
        print(f"[eval] {len(misses)} misclassified:")
        for m in misses:
            print(f"    '{m['message']}' -> expected {m['expected']}, got {m['actual']}")


if __name__ == "__main__":
    import os
    from agents.router_agent import RouterAgent
    from eval_dataset import EXAMPLES

    provider = os.environ.get("LLM_PROVIDER", "runpod")
    router = RouterAgent(provider=provider)
    result = run_eval(router, EXAMPLES, provider=provider)
    print_report(result, provider)
