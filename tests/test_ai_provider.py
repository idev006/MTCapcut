import os
import unittest
from unittest.mock import patch

from mtcapcut.ai_provider import ChatMessage, ChatRequest, OpenAICompatibleProvider, create_provider
from mtcapcut.config import AIProviderSettings


class RecordingTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post_json(self, url, headers, payload, timeout_seconds):
        self.calls.append((url, headers, payload, timeout_seconds))
        return self.response


class AIProviderTests(unittest.TestCase):
    def test_openrouter_uses_bearer_secret_from_environment(self):
        settings = AIProviderSettings(
            name="openrouter", kind="openrouter", base_url="https://openrouter.ai/api/v1",
            model="vendor/model", api_key_env="OPENROUTER_API_KEY", timeout_seconds=45,
            enabled=True, app_url="https://example.invalid", app_name="MTCapcut",
        )
        transport = RecordingTransport({
            "id": "r1", "model": "vendor/model",
            "choices": [{"message": {"content": "คำตอบ"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
        })
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "secret-value"}):
            provider = create_provider(settings, transport=transport)
            response = provider.complete(ChatRequest((ChatMessage("user", "สวัสดี"),),
                                                      response_format={"type": "json_object"}))
        url, headers, payload, timeout = transport.calls[0]
        self.assertEqual(url, "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(headers["Authorization"], "Bearer secret-value")
        self.assertEqual(headers["HTTP-Referer"], "https://example.invalid")
        self.assertEqual(headers["X-Title"], "MTCapcut")
        self.assertEqual(payload["model"], "vendor/model")
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(timeout, 45)
        self.assertEqual(response.text, "คำตอบ")
        self.assertEqual(response.total_tokens, 5)
        self.assertEqual(response.finish_reason, "stop")

    def test_local_openai_provider_needs_no_cloud_key(self):
        settings = AIProviderSettings(
            name="ollama", kind="local_openai", base_url="http://127.0.0.1:11434/v1/",
            model="qwen3:8b", enabled=True,
        )
        transport = RecordingTransport({
            "id": "local-1", "model": "qwen3:8b",
            "choices": [{"message": {"content": "local"}}],
        })
        provider = OpenAICompatibleProvider(settings, transport=transport, api_key=None)
        self.assertEqual(provider.complete(ChatRequest((ChatMessage("user", "test"),))).text, "local")
        _, headers, _, _ = transport.calls[0]
        self.assertNotIn("Authorization", headers)

    def test_toml_key_is_used_and_environment_key_takes_precedence(self):
        settings = AIProviderSettings(
            name="openrouter", kind="openrouter", base_url="https://openrouter.ai/api/v1",
            model="vendor/model", api_key_env="OPENROUTER_API_KEY", api_key="toml-key",
            enabled=True,
        )
        response = {"choices": [{"message": {"content": "ok"}}]}
        toml_transport = RecordingTransport(response)
        create_provider(settings, transport=toml_transport, environ={}).complete(
            ChatRequest((ChatMessage("user", "test"),))
        )
        self.assertEqual(toml_transport.calls[0][1]["Authorization"], "Bearer toml-key")

        env_transport = RecordingTransport(response)
        create_provider(
            settings, transport=env_transport,
            environ={"OPENROUTER_API_KEY": "environment-key"},
        ).complete(ChatRequest((ChatMessage("user", "test"),)))
        self.assertEqual(env_transport.calls[0][1]["Authorization"], "Bearer environment-key")

    def test_missing_openrouter_secret_and_malformed_response_fail_closed(self):
        settings = AIProviderSettings(
            name="openrouter", kind="openrouter", base_url="https://openrouter.ai/api/v1",
            model="vendor/model", api_key_env="MISSING_TEST_KEY", enabled=True,
        )
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                create_provider(settings, transport=RecordingTransport({}))
        provider = OpenAICompatibleProvider(
            AIProviderSettings("local", "local_openai", "http://127.0.0.1:8000/v1", "model", enabled=True),
            transport=RecordingTransport({"choices": []}), api_key=None,
        )
        with self.assertRaises(ValueError):
            provider.complete(ChatRequest((ChatMessage("user", "test"),)))


if __name__ == "__main__":
    unittest.main()
