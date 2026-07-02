"""
Provider-agnostic LLM client.

The problem this solves: the chatbot only ran behind a self-hosted Llama-3.1-8B
deployment on RunPod -- real GPU cost, deployment fiddliness, and a genuine barrier
to anyone (a recruiter, an interviewer, or a fresh contributor) actually trying it.
OpenAI, Google Gemini, and DeepSeek are all reachable through the *exact same*
`OpenAI(api_key=..., base_url=...)` SDK client shape this codebase already uses --
switching providers is a config change, not a rewrite.

Backward compatibility: the original deployment used RUNPOD_TOKEN/RUNPOD_CHATBOT_URL/
MODEL_NAME/RUNPOD_EMBEDDING_URL env vars directly in each agent's __init__. The
default provider ("runpod") reads those exact names so an existing .env keeps
working unchanged. Set LLM_PROVIDER=openai|gemini|deepseek to opt into a cheap
managed API instead.

The `openai` package import is deferred into get_client()/get_embedding_client()
(not done at module import time) so the rest of this module -- and anything that
depends on it via dependency injection (pass a `client` in, rather than constructing
one internally) -- can be unit-tested without the `openai` package installed.
"""

import os


# Model name is intentionally not hardcoded beyond a documented fallback --
# DeepSeek's "deepseek-chat" alias is flagged in their own docs for deprecation
# around 2026-07-24, so the active model should come from config, not be baked in.
PROVIDER_CONFIG = {
    "runpod": {
        # Legacy env var names -- keeps the original .env working unchanged.
        "api_key_env": "RUNPOD_TOKEN",
        "base_url_env": "RUNPOD_CHATBOT_URL",
        "model_env": "MODEL_NAME",
        "embedding_base_url_env": "RUNPOD_EMBEDDING_URL",
        "default_model": None,  # no sane universal default; must come from env
        # Whether the deployed vLLM instance supports guaranteed structured output
        # depends on how it was launched (--enable-auto-tool-choice etc.) -- don't
        # assume a guarantee for an arbitrary self-hosted deployment.
        "supports_strict_json_schema": False,
    },
    "openai": {
        "base_url": None,  # None => SDK default (https://api.openai.com/v1)
        "default_model": "gpt-4o-mini",
        "supports_strict_json_schema": True,
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-flash-latest",
        # Real per Google's docs, but whether it works unchanged through the OpenAI
        # *compatibility* endpoint (vs. Gemini's native responseSchema field) wasn't
        # confirmed empirically -- treat as unverified until tested against a live key.
        "supports_strict_json_schema": True,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        # DeepSeek's compat layer is JSON-mode-only per their docs at research time --
        # no confirmed json_schema/strict guarantee.
        "supports_strict_json_schema": False,
    },
}


class UnknownProviderError(ValueError):
    pass


class MissingCredentialError(ValueError):
    pass


def resolve_provider_config(provider=None, api_key=None, model=None, base_url=None):
    """
    Resolve (api_key, base_url, model, supports_strict_json_schema) for a provider.
    Pure function -- no network access, no SDK import -- fully unit-testable alone.

    Args:
        provider (str, optional): one of PROVIDER_CONFIG's keys. Defaults to the
            LLM_PROVIDER env var, then "runpod" (preserves original behavior).
        api_key, model, base_url (str, optional): explicit overrides.

    Returns:
        dict: {"provider", "api_key", "base_url", "model", "supports_strict_json_schema"}

    Raises:
        UnknownProviderError: unrecognized provider name.
        MissingCredentialError: no api_key (or, for "runpod", no base_url) available.
    """
    provider = provider or os.environ.get("LLM_PROVIDER", "runpod")
    if provider not in PROVIDER_CONFIG:
        raise UnknownProviderError(
            f"Unknown LLM provider '{provider}'. Valid options: {sorted(PROVIDER_CONFIG)}"
        )
    config = PROVIDER_CONFIG[provider]

    if provider == "runpod":
        resolved_key = api_key or os.environ.get(config["api_key_env"])
        resolved_base_url = base_url or os.environ.get(config["base_url_env"])
        resolved_model = model or os.environ.get(config["model_env"])
        if resolved_key and not resolved_base_url:
            raise MissingCredentialError(
                f"Provider 'runpod' needs {config['base_url_env']} set (or pass base_url=)."
            )
    else:
        resolved_key = api_key or os.environ.get("LLM_API_KEY")
        resolved_base_url = base_url or os.environ.get("LLM_BASE_URL") or config["base_url"]
        resolved_model = model or os.environ.get("LLM_MODEL") or config["default_model"]

    if not resolved_key:
        raise MissingCredentialError(
            f"No API key available for provider '{provider}'. "
            f"Set {config.get('api_key_env', 'LLM_API_KEY')} (or pass api_key=)."
        )

    return {
        "provider": provider,
        "api_key": resolved_key,
        "base_url": resolved_base_url,
        "model": resolved_model,
        "supports_strict_json_schema": config["supports_strict_json_schema"],
    }


def get_client(provider=None, api_key=None, model=None, base_url=None):
    """
    Construct a real OpenAI-SDK chat client for the given/active provider. The one
    function here that needs the `openai` package installed -- see module docstring.

    Returns:
        tuple: (client, resolved_config_dict)
    """
    from openai import OpenAI  # deferred import -- see module docstring

    resolved = resolve_provider_config(provider, api_key=api_key, model=model, base_url=base_url)
    client = OpenAI(api_key=resolved["api_key"], base_url=resolved["base_url"])
    return client, resolved


def get_embedding_client(provider=None, api_key=None, base_url=None):
    """
    Construct an embedding-specific client. For "runpod" this points at
    RUNPOD_EMBEDDING_URL (the original deployment used a separate embedding
    endpoint from the chat endpoint); for other providers it defaults to the same
    base_url as the chat client, since OpenAI/Gemini/DeepSeek all serve embeddings
    from the same host in the common case.
    """
    from openai import OpenAI  # deferred import -- see module docstring

    provider = provider or os.environ.get("LLM_PROVIDER", "runpod")
    if provider not in PROVIDER_CONFIG:
        raise UnknownProviderError(
            f"Unknown LLM provider '{provider}'. Valid options: {sorted(PROVIDER_CONFIG)}"
        )
    config = PROVIDER_CONFIG[provider]

    if provider == "runpod":
        resolved_key = api_key or os.environ.get(config["api_key_env"])
        resolved_base_url = base_url or os.environ.get(config["embedding_base_url_env"])
        if not resolved_key or not resolved_base_url:
            raise MissingCredentialError(
                f"Provider 'runpod' embeddings need {config['api_key_env']} and "
                f"{config['embedding_base_url_env']} set."
            )
    else:
        resolved = resolve_provider_config(provider, api_key=api_key, base_url=base_url)
        resolved_key = resolved["api_key"]
        resolved_base_url = resolved["base_url"]

    return OpenAI(api_key=resolved_key, base_url=resolved_base_url)


def validate_startup_config(provider=None):
    """
    Validate that every env var the active provider (and, for "runpod", the
    embedding/Pinecone dependencies DetailsAgent needs) requires is actually set --
    all at once, with one clear message listing everything missing, rather than
    crashing deep inside the OpenAI/Pinecone SDK on whichever call happens first.

    Call this once at process startup (see main.py). Pure function -- no network
    calls, just os.environ reads -- so it's cheap to call eagerly.

    Raises:
        MissingCredentialError: listing every missing variable, if any.
    """
    provider = provider or os.environ.get("LLM_PROVIDER", "runpod")
    missing = []

    try:
        resolve_provider_config(provider)
    except MissingCredentialError as e:
        missing.append(str(e))

    if provider == "runpod":
        config = PROVIDER_CONFIG["runpod"]
        if not os.environ.get(config["embedding_base_url_env"]):
            missing.append(f"{config['embedding_base_url_env']} is required (DetailsAgent's embedding client).")

    if not os.environ.get("PINECONE_API_KEY"):
        missing.append("PINECONE_API_KEY is required (DetailsAgent's RAG lookup).")
    if not os.environ.get("PINECONE_INDEX_NAME"):
        missing.append("PINECONE_INDEX_NAME is required (DetailsAgent's RAG lookup).")

    if missing:
        raise MissingCredentialError(
            "Missing required configuration:\n  - " + "\n  - ".join(missing)
        )


def call_chat(client, model, messages, temperature=0, max_tokens=2000, **kwargs):
    """
    Thin wrapper around client.chat.completions.create(...) returning just the text
    content. Accepts any object duck-typed like the OpenAI SDK's client, so tests can
    pass a fake without needing the real `openai` package installed.
    """
    response = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
    )
    return response.choices[0].message.content
