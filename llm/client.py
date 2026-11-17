"""LLM client wrapper supporting Google Gemini, OpenAI, and Ollama."""
import json
from typing import Optional
import httpx

from config.settings import settings
from utils.logger import logger


class BaseLLMClient:
    def generate(self, prompt: str, system_instruction: str = "") -> str:
        raise NotImplementedError


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY chưa được cấu hình! "
                "Vui lòng tạo API key miễn phí tại https://aistudio.google.com/ và điền vào file .env "
                "hoặc truyền tham số --api-key khi chạy lệnh."
            )

        from google import genai
        from google.genai import types

        logger.info(f"[LLM] Đang gửi yêu cầu phân tích tới Google Gemini ({self.model})...")

        client = genai.Client(api_key=self.api_key)

        config = types.GenerateContentConfig(
            temperature=0.3,
            system_instruction=system_instruction if system_instruction else None,
        )

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        return response.text or ""


class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY chưa được cấu hình trong .env!")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
        }

        with httpx.Client(timeout=60) as client:
            resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]


class OllamaClient(BaseLLMClient):
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
        }
        with httpx.Client(timeout=120) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "")


def get_llm_client(provider: Optional[str] = None, api_key: Optional[str] = None) -> BaseLLMClient:
    """Factory to get configured LLM provider."""
    p = (provider or settings.DEFAULT_LLM_PROVIDER).lower()
    if p == "gemini":
        return GeminiClient(api_key=api_key)
    elif p == "openai":
        return OpenAIClient(api_key=api_key)
    elif p == "ollama":
        return OllamaClient()
    else:
        raise ValueError(f"Unknown LLM provider '{provider}'. Supported: gemini, openai, ollama")
