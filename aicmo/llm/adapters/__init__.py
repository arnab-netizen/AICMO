"""
LLM adapters: Multi-provider language model implementations.

Each adapter supports:
- dry_run mode (stub responses for testing)
- check_health() method (for ProviderChain integration)
- generate() method (for text completion)
- generate_structured() method (for JSON output)
"""

from .mistral_llm import MistralLLMAdapter
from .cohere_llm import CohereLLMAdapter
from .deepseek_llm import DeepSeekLLMAdapter
from .llama_llm import LlamaLLMAdapter
from .perplexity_llm import PerplexityLLMAdapter
from .grok_llm import GrokLLMAdapter

__all__ = [
    "MistralLLMAdapter",
    "CohereLLMAdapter",
    "DeepSeekLLMAdapter",
    "LlamaLLMAdapter",
    "PerplexityLLMAdapter",
    "GrokLLMAdapter",
]
