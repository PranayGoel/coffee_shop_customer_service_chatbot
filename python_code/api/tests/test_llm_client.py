import os
import unittest
from unittest import mock

import llm_client
from llm_client import (
    resolve_provider_config,
    validate_startup_config,
    UnknownProviderError,
    MissingCredentialError,
    call_chat,
)
from tests.fakes import FakeClient, FakeResponse


class TestResolveProviderConfig(unittest.TestCase):
    def test_defaults_to_runpod_for_backward_compatibility(self):
        with mock.patch.dict(os.environ, {"RUNPOD_TOKEN": "t", "RUNPOD_CHATBOT_URL": "u", "MODEL_NAME": "m"}, clear=True):
            resolved = resolve_provider_config()
        self.assertEqual(resolved["provider"], "runpod")
        self.assertEqual(resolved["api_key"], "t")
        self.assertEqual(resolved["base_url"], "u")
        self.assertEqual(resolved["model"], "m")

    def test_runpod_requires_base_url_when_key_present(self):
        with mock.patch.dict(os.environ, {"RUNPOD_TOKEN": "t"}, clear=True):
            with self.assertRaises(MissingCredentialError):
                resolve_provider_config("runpod")

    def test_unknown_provider_raises(self):
        with self.assertRaises(UnknownProviderError):
            resolve_provider_config("not-a-real-provider", api_key="k")

    def test_generic_provider_missing_key_raises(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(MissingCredentialError):
                resolve_provider_config("openai")

    def test_generic_provider_env_fallback(self):
        with mock.patch.dict(os.environ, {"LLM_API_KEY": "k", "LLM_MODEL": "custom-model"}, clear=True):
            resolved = resolve_provider_config("openai")
        self.assertEqual(resolved["api_key"], "k")
        self.assertEqual(resolved["model"], "custom-model")

    def test_gemini_uses_openai_compat_base_url(self):
        resolved = resolve_provider_config("gemini", api_key="k")
        self.assertEqual(resolved["base_url"], "https://generativelanguage.googleapis.com/v1beta/openai/")

    def test_deepseek_does_not_claim_strict_json_schema_support(self):
        resolved = resolve_provider_config("deepseek", api_key="k")
        self.assertFalse(resolved["supports_strict_json_schema"])

    def test_runpod_does_not_assume_strict_json_schema_support(self):
        with mock.patch.dict(os.environ, {"RUNPOD_TOKEN": "t", "RUNPOD_CHATBOT_URL": "u"}, clear=True):
            resolved = resolve_provider_config("runpod")
        self.assertFalse(resolved["supports_strict_json_schema"])

    def test_openrouter_uses_free_tier_default_model_and_base_url(self):
        resolved = resolve_provider_config("openrouter", api_key="k")
        self.assertEqual(resolved["base_url"], "https://openrouter.ai/api/v1")
        self.assertEqual(resolved["model"], "openai/gpt-oss-20b:free")
        self.assertTrue(resolved["supports_strict_json_schema"])


class TestValidateStartupConfig(unittest.TestCase):
    def test_reports_all_missing_vars_at_once(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(MissingCredentialError) as ctx:
                validate_startup_config("runpod")
        message = str(ctx.exception)
        # Should mention the chat credential AND the embedding/Pinecone ones in one error.
        self.assertIn("PINECONE_API_KEY", message)
        self.assertIn("PINECONE_INDEX_NAME", message)

    def test_passes_when_everything_present(self):
        env = {
            "RUNPOD_TOKEN": "t", "RUNPOD_CHATBOT_URL": "u", "MODEL_NAME": "m",
            "RUNPOD_EMBEDDING_URL": "e", "PINECONE_API_KEY": "p", "PINECONE_INDEX_NAME": "i",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            validate_startup_config("runpod")  # should not raise


class TestCallChat(unittest.TestCase):
    def test_returns_message_content_from_a_duck_typed_client(self):
        client = FakeClient([FakeResponse("hello")])
        result = call_chat(client, "any-model", [{"role": "user", "content": "hi"}])
        self.assertEqual(result, "hello")


if __name__ == "__main__":
    unittest.main()
