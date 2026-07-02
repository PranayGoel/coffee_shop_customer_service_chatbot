# Router fine-tuning pipeline (authored, not executed)

**Status: built, not run.** No GPU/API access in the environment this was written in.

- `generate_training_data.py` — **actually runnable and verified** (pure Python, no external deps): expands `../api/eval_dataset.py`'s 35 hand-labeled examples with template-based paraphrase variation into 242 labeled routing examples. Run it yourself: `python3 generate_training_data.py router_training_data.jsonl`.
- `finetune_router_llama.ipynb` — a Colab-ready QLoRA fine-tuning notebook (Unsloth, Llama-3.1-8B, LoRA rank 32) adapted from Unsloth's official recipe. Every training/inference cell is marked `# NOT RUN`. Ready to run on a free Colab T4 or a GCP T4/L4 — per Unsloth's published benchmarks, a run this size should take well under an hour and cost roughly $0–5 (likely $0 on Colab's free tier).

## Why this task is a reasonable fine-tuning candidate
`RouterAgent`'s job is a narrow, fixed-schema classification task — exactly the profile where a small LoRA adapter can be pushed toward near-deterministic structured output and lower latency, rather than a case that calls for prompting alone. See the main README for the research this is based on.

## Before treating any result as a real improvement
Run `../api/eval_harness.py`'s `run_eval()` against **both** the base model and the fine-tuned adapter, and report accuracy, JSON-schema-validity rate, and latency side by side. A fine-tune without that before/after comparison isn't evidence of anything.
