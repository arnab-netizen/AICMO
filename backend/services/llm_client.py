"""Lightweight wrapper around OpenAI GPT-4o-mini for AICMO backend with Perplexity fallback."""

import asyncio
import logging
import os
from fastapi import HTTPException
from openai import OpenAI, AuthenticationError, APIStatusError, APIConnectionError, RateLimitError

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Lightweight wrapper around OpenAI GPT-4o-mini with Perplexity fallback.

    Fallback chain:
    1. Try OpenAI (if OPENAI_API_KEY configured)
    2. If OpenAI fails, try Perplexity (if PERPLEXITY_API_KEY configured)
    3. If both fail and AICMO_ALLOW_STUBS=false, raise structured error

    Includes:
      - model selection
      - retry logic
      - timeout protection
      - unified call interface
      - structured error tracking
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """Initialize LLM client with API key and model."""
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.openai_key = api_key
        self.perplexity_key = os.getenv("PERPLEXITY_API_KEY", "").strip()

    async def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """
        Generate text from prompt with fallback chain: OpenAI → Perplexity → error.

        Args:
            prompt: Input prompt for LLM
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum output tokens

        Returns:
            Generated text

        Raises:
            ValueError: If both OpenAI and Perplexity fail and AICMO_ALLOW_STUBS=false
            HTTPException: If specific LLM error needs surfacing to API layer
        """
        openai_status = "not_attempted"
        perplexity_status = "not_attempted"
        last_error = None

        # Try OpenAI first
        if self.openai_key:
            try:
                result = await self._generate_with_openai(prompt, temperature, max_tokens)
                return result
            except Exception as e:
                openai_status = f"failed: {type(e).__name__}"
                last_error = e
                logger.warning(f"OpenAI generation failed: {e}, attempting Perplexity fallback")

        # Fallback to Perplexity
        if self.perplexity_key:
            try:
                result = await self._generate_with_perplexity(prompt, temperature, max_tokens)
                logger.info("✅ Perplexity fallback successful after OpenAI failure")
                return result
            except Exception as e:
                perplexity_status = f"failed: {type(e).__name__}"
                last_error = e
                logger.error(f"Perplexity generation failed: {e}")

        # Both failed - check if stubs are allowed
        from backend.utils.config import allow_stubs_in_production

        if not allow_stubs_in_production():
            # Production mode - raise structured error
            error_msg = (
                f"LLM chain failed - all providers exhausted. "
                f"OpenAI: {openai_status}, Perplexity: {perplexity_status}"
            )
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

        # Re-raise the last error for fallback handling
        if last_error:
            raise last_error

        raise ValueError("No LLM providers configured")

    async def _generate_with_openai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate text using OpenAI with retry logic."""
        for attempt in range(3):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ),
                    timeout=25,
                )
                return response.choices[0].message.content
            except AuthenticationError as e:
                logger.error("OpenAI authentication error: %s", e)
                raise HTTPException(
                    status_code=502, detail="OpenAI authentication error – check OPENAI_API_KEY"
                )
            except RateLimitError as e:
                logger.warning("OpenAI rate limit exceeded: %s", e)
                raise HTTPException(
                    status_code=429, detail="OpenAI rate limit exceeded – please retry later"
                )
            except APIStatusError as e:
                logger.error("OpenAI API status error: %s", e)
                raise HTTPException(status_code=502, detail="OpenAI API error – please retry")
            except APIConnectionError as e:
                logger.error("OpenAI connection error: %s", e)
                raise HTTPException(
                    status_code=502, detail="OpenAI connection error – please retry"
                )
            except asyncio.TimeoutError:
                if attempt == 2:
                    logger.error("OpenAI generation timed out after %d attempts", attempt + 1)
                    raise HTTPException(
                        status_code=504, detail="OpenAI generation timed out – please retry"
                    )
                logger.warning("OpenAI timeout on attempt %d, retrying...", attempt + 1)
                await asyncio.sleep(1)
            except HTTPException:
                # Already handled, re-raise
                raise
            except Exception as e:
                if attempt == 2:
                    logger.exception("Unexpected OpenAI error after retries: %s", type(e).__name__)
                    raise HTTPException(
                        status_code=500, detail=f"Unexpected OpenAI error: {type(e).__name__}"
                    )
                logger.warning("Unexpected error on attempt %d: %s, retrying...", attempt + 1, e)
                await asyncio.sleep(1)

        raise HTTPException(status_code=500, detail="OpenAI generation failed after all retries")

    async def _generate_with_perplexity(
        self, prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Generate text using Perplexity as fallback."""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.perplexity_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "sonar",  # Perplexity's sonar model
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        base_url = os.getenv("PERPLEXITY_API_BASE", "https://api.perplexity.ai")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()

            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]

            raise ValueError("Perplexity API returned unexpected format")
