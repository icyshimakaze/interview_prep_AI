"""OpenAI Responses and local Ollama adapters. No SDK or model download is required."""

from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

from interview_prep.ai.errors import InvalidProviderOutput, ProviderRefusal, ProviderUnavailable
from interview_prep.ai.prompts import instructions, user_data
from interview_prep.ai.provider import BaseProvider
from interview_prep.ai.schemas import Contract, Input, Operation
from interview_prep.ai.transport import request_json


class Wire(BaseModel):
    # Transport metadata evolves independently; domain payloads forbid extra fields.
    model_config = ConfigDict(extra="ignore", strict=True, hide_input_in_errors=True)


class Part(Wire):
    type: str
    text: str | None = Field(default=None, max_length=131072)


class Item(Wire):
    type: str
    role: str | None = None
    status: str | None = None
    content: list[Part] = Field(default_factory=list, max_length=20)


class Response(Wire):
    status: str
    output: list[Item] = Field(max_length=20)


class Message(Wire):
    role: Literal["assistant"]
    content: str = Field(max_length=131072)
    tool_calls: list[object] = Field(default_factory=list, max_length=0)


class OllamaResponse(Wire):
    done: Literal[True]
    done_reason: Literal["stop"]
    message: Message


class RemoteProvider(BaseProvider):
    kind: Literal["simulation", "model_assisted"] = "model_assisted"

    def __init__(
        self,
        client: httpx.AsyncClient,
        model: str,
        timeout_seconds: float = 30,
        max_retries: int = 1,
    ) -> None:
        self.client = client
        self.model = model.strip() or None
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries


class OpenAIProvider(RemoteProvider):
    name = "OpenAIProvider"
    version = "openai-responses-v1"

    def __init__(
        self,
        client: httpx.AsyncClient,
        api_key: SecretStr,
        model: str,
        timeout_seconds: float = 30,
        max_retries: int = 1,
    ) -> None:
        super().__init__(client, model, timeout_seconds, max_retries)
        self._api_key = api_key

    async def _generate(self, operation: Operation, content: Input, schema: type[Contract]) -> str:
        if not self._api_key.get_secret_value().strip() or not self.model:
            raise ProviderUnavailable()
        raw = await request_json(
            self.client,
            "https://api.openai.com/v1/responses",
            {
                "model": self.model,
                "store": False,
                "max_output_tokens": 4096,
                "instructions": instructions(operation),
                "input": [{"role": "user", "content": user_data(content)}],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": operation,
                        "strict": True,
                        "schema": schema.model_json_schema(),
                    }
                },
            },
            {"Authorization": "Bearer " + self._api_key.get_secret_value()},
            self.timeout_seconds,
            self.max_retries,
        )
        try:
            response = Response.model_validate_json(raw)
        except ValidationError:
            raise InvalidProviderOutput() from None
        if any(p.type == "refusal" for item in response.output for p in item.content):
            raise ProviderRefusal()
        if response.status != "completed":
            raise InvalidProviderOutput()
        messages = [item for item in response.output if item.type == "message"]
        if (
            len(messages) != 1
            or messages[0].role != "assistant"
            or messages[0].status != "completed"
            or len(messages[0].content) != 1
            or any(item.type not in {"reasoning", "message"} for item in response.output)
        ):
            raise InvalidProviderOutput()
        part = messages[0].content[0]
        if part.type != "output_text" or part.text is None:
            raise InvalidProviderOutput()
        return part.text


class OllamaProvider(RemoteProvider):
    name = "OllamaProvider"
    version = "ollama-chat-v1"

    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: str,
        model: str,
        timeout_seconds: float = 30,
        max_retries: int = 1,
    ) -> None:
        super().__init__(client, model, timeout_seconds, max_retries)
        self.base_url = base_url.rstrip("/") or "http://127.0.0.1:11434"

    async def _generate(self, operation: Operation, content: Input, schema: type[Contract]) -> str:
        if not self.model:
            raise ProviderUnavailable()
        raw = await request_json(
            self.client,
            self.base_url + "/api/chat",
            {
                "model": self.model,
                "stream": False,
                "format": schema.model_json_schema(),
                "messages": [
                    {"role": "system", "content": instructions(operation)},
                    {"role": "user", "content": user_data(content)},
                ],
                "options": {"temperature": 0, "seed": 0, "num_predict": 4096},
            },
            {},
            self.timeout_seconds,
            self.max_retries,
        )
        try:
            return OllamaResponse.model_validate_json(raw).message.content
        except ValidationError:
            raise InvalidProviderOutput() from None
