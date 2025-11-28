"""Lightweight wrapper around OpenAI GPT-4o-mini for AICMO backend."""

import asyncio
import logging
from fastapi import HTTPException
from openai import OpenAI, AuthenticationError, APIStatusError, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)


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
        Generate text from prompt with retry logic, timeout protection, and robust error handling.

        Args:
            prompt: Input prompt for LLM
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum output tokens

        Returns:
            Generated text

        Raises:
            HTTPException: If LLM call fails (auth, rate limit, API, connection)
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
            except AuthenticationError as e:
                logger.error("LLM authentication error: %s", e)
                raise HTTPException(
                    status_code=502, detail="LLM authentication error – check OPENAI_API_KEY"
                )
            except RateLimitError as e:
                logger.warning("LLM rate limit exceeded: %s", e)
                raise HTTPException(
                    status_code=429, detail="LLM rate limit exceeded – please retry later"
                )
            except APIStatusError as e:
                logger.error("LLM API status error: %s", e)
                raise HTTPException(status_code=502, detail="LLM API error – please retry")
            except APIConnectionError as e:
                logger.error("LLM connection error: %s", e)
                raise HTTPException(status_code=502, detail="LLM connection error – please retry")
            except asyncio.TimeoutError:
                if attempt == 2:
                    logger.error("LLM generation timed out after %d attempts", attempt + 1)
                    raise HTTPException(
                        status_code=504, detail="LLM generation timed out – please retry"
                    )
                logger.warning("LLM timeout on attempt %d, retrying...", attempt + 1)
                await asyncio.sleep(1)
            except HTTPException:
                # Already handled, re-raise
                raise
            except Exception as e:
                if attempt == 2:
                    logger.exception("Unexpected LLM error after retries: %s", type(e).__name__)
                    raise HTTPException(
                        status_code=500, detail=f"Unexpected LLM error: {type(e).__name__}"
                    )
                logger.warning("Unexpected error on attempt %d: %s, retrying...", attempt + 1, e)
                await asyncio.sleep(1)

        raise HTTPException(status_code=500, detail="LLM generation failed after all retries")
