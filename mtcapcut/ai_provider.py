"""Provider-neutral chat contract for OpenRouter and local OpenAI-compatible servers."""

from dataclasses import dataclass
import json
import os
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import AIProviderSettings


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: Any


@dataclass(frozen=True)
class ChatRequest:
    messages: tuple[ChatMessage, ...]
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    response_format: dict[str, Any] | None = None


@dataclass(frozen=True)
class ChatResponse:
    request_id: str | None
    model: str
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    raw: dict[str, Any] | None = None
    finish_reason: str | None = None


class JsonTransport(Protocol):
    def post_json(self, url: str, headers: dict[str, str], payload: dict[str, Any],
                  timeout_seconds: int) -> dict[str, Any]: ...


class UrllibJsonTransport:
    def post_json(self, url: str, headers: dict[str, str], payload: dict[str, Any],
                  timeout_seconds: int) -> dict[str, Any]:
        request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                document = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"AI provider HTTP {error.code}: {body[:500]}") from error
        except URLError as error:
            raise RuntimeError(f"AI provider connection failed: {error.reason}") from error
        if not isinstance(document, dict):
            raise ValueError("AI provider returned a non-object response")
        return document


class OpenAICompatibleProvider:
    def __init__(self, settings: AIProviderSettings, *, transport: JsonTransport | None = None,
                 api_key: str | None = None):
        if not settings.enabled:
            raise ValueError(f"AI provider is disabled: {settings.name}")
        self.settings = settings
        self.transport = transport or UrllibJsonTransport()
        self.api_key = api_key

    def complete(self, request: ChatRequest) -> ChatResponse:
        if not request.messages:
            raise ValueError("at least one chat message is required")
        payload: dict[str, Any] = {
            "model": request.model or self.settings.model,
            "messages": [{"role": item.role, "content": item.content} for item in request.messages],
            "stream": False,
        }
        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        if request.response_format is not None:
            payload["response_format"] = request.response_format
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.settings.kind == "openrouter":
            if self.settings.app_url:
                headers["HTTP-Referer"] = self.settings.app_url
            if self.settings.app_name:
                headers["X-Title"] = self.settings.app_name
        document = self.transport.post_json(
            f"{self.settings.base_url}/chat/completions", headers, payload,
            self.settings.timeout_seconds,
        )
        try:
            text = document["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise ValueError("AI provider response has no assistant message") from error
        if not isinstance(text, str):
            raise ValueError("AI provider assistant content is not text")
        usage = document.get("usage") or {}
        return ChatResponse(
            document.get("id"), str(document.get("model") or payload["model"]), text,
            usage.get("prompt_tokens"), usage.get("completion_tokens"),
            usage.get("total_tokens"), document, document["choices"][0].get("finish_reason"),
        )


def create_provider(settings: AIProviderSettings, *, transport: JsonTransport | None = None,
                    environ: dict[str, str] | None = None) -> OpenAICompatibleProvider:
    environment = os.environ if environ is None else environ
    environment_key = environment.get(settings.api_key_env) if settings.api_key_env else None
    api_key = environment_key or settings.api_key
    if settings.kind == "openrouter" and not api_key:
        raise ValueError("missing AI API key configuration")
    return OpenAICompatibleProvider(settings, transport=transport, api_key=api_key)
