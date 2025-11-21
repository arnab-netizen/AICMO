"""Lightweight wrapper around OpenAI GPT-4o-mini for AICMO backend."""

import asyncio

from openai import OpenAI


class LLMClient:
    """
    Lightweight wrapper around OpenAI GPT-4o-mini.
    Includes:
      - model selection
      - retry logic
      - timeout protection
      - unified call interface
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize LLM client with API key and model."""
        self.client = OpenAI(api_key=api_key)
        self.model = model

    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        Generate text from prompt with retry logic and timeout protection.

        Args:
            prompt: Input prompt for LLM
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum output tokens

        Returns:
            Generated text

        Raises:
            RuntimeError: If generation fails after retries
        """
        for attempt in range(3):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.messages.create,
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ),
                    timeout=25,
                )
                return response.content[0].text
            except asyncio.TimeoutError:
                if attempt == 2:
                    raise RuntimeError("LLM generation timed out after retries")
                await asyncio.sleep(1)
            except Exception as e:
                if attempt == 2:
                    raise RuntimeError(f"LLM generation failed after retries: {e}")
                await asyncio.sleep(1)

        raise RuntimeError("LLM generation failed after retries")
