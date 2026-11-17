"""LLM package for JobSonar."""
from .client import get_llm_client, GeminiClient, OpenAIClient, OllamaClient
from .synthesizer import JobSynthesizer
from .prompts import HR_SYSTEM_PROMPT, build_synthesis_prompt

__all__ = [
    "get_llm_client",
    "GeminiClient",
    "OpenAIClient",
    "OllamaClient",
    "JobSynthesizer",
    "HR_SYSTEM_PROMPT",
    "build_synthesis_prompt"
]
