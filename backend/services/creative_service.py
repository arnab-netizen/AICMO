"""
Centralized Creative Service - OpenAI Integration Layer

This module provides a unified interface for all creative/narrative operations,
consolidating OpenAI API calls and ensuring consistent prompt engineering
across the AICMO platform.

Architecture:
    Template Draft + Research Data → CreativeService → OpenAI API → Polished Output
    
Usage:
    creative_service = CreativeService()
    polished_text = creative_service.polish_section(template_text, brief, research)
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

from backend.utils.config import is_stub_mode
from aicmo.io.client_reports import ClientInputBrief

# Import research types
try:
    from backend.services.research_service import ComprehensiveResearchData
except ImportError:
    ComprehensiveResearchData = Any  # type: ignore

log = logging.getLogger("creative_service")


@dataclass
class CreativeConfig:
    """Configuration for creative generation."""

    temperature: float = 0.7
    max_tokens: int = 2000
    model: str = "gpt-4o-mini"
    enable_polish: bool = True
    enable_degenericize: bool = True
    enable_research_injection: bool = True


class CreativeService:
    """
    Unified service for all OpenAI-backed creative operations.

    Responsibilities:
    - Consolidate all OpenAI API calls for creative work
    - Provide consistent prompt engineering patterns
    - Handle narrative generation, polishing, de-genericization
    - Integrate research data into creative outputs
    - Respect configuration flags (AICMO_USE_LLM, stub mode)

    Design Principles:
    - Always returns text (never throws on API failure, falls back to input)
    - Uses template-first approach (LLM enhances, doesn't replace)
    - Testable via dependency injection
    - Config-driven behavior
    """

    def __init__(
        self,
        client: Optional[OpenAI] = None,
        config: Optional[CreativeConfig] = None,
    ):
        """
        Initialize creative service.

        Args:
            client: Optional OpenAI client for testing. If None, creates default.
            config: Optional configuration. Uses defaults if None.
        """
        self.config = config or CreativeConfig()

        # Initialize ProviderChain client where possible (preferred)
        self.chain = None
        self.client = None
        if is_stub_mode():
            self.enabled = False
            log.debug("[CreativeService] Running in stub mode - LLM disabled")
        else:
            try:
                from aicmo.llm.router import get_llm_client, LLMUseCase

                # Obtain ProviderChain client for creative use case
                self.chain = get_llm_client(use_case=LLMUseCase.CREATIVE_SPEC)
                self.enabled = True
                log.debug("[CreativeService] ProviderChain client configured")
            except Exception as e:
                # ProviderChain not available; mark disabled but keep option to fallback
                self.chain = None
                self.enabled = False
                log.warning(f"[CreativeService] ProviderChain unavailable: {e}")
                # Note: direct SDK fallback only allowed when explicitly enabled
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key and os.getenv("AICMO_ALLOW_DIRECT_SDK_FALLBACK") == "1":
                    try:
                        from openai import OpenAI

                        self.client = OpenAI(api_key=api_key)
                        self.enabled = True
                        log.warning("[CreativeService] Direct OpenAI SDK fallback enabled (AICMO_ALLOW_DIRECT_SDK_FALLBACK=1)")
                    except Exception as ex:
                        log.error(f"[CreativeService] Direct OpenAI SDK initialization failed: {ex}")

    def is_enabled(self) -> bool:
        """Check if creative service is enabled and configured."""
        return self.enabled and self.client is not None

    def polish_section(
        self,
        template_text: str,
        brief: ClientInputBrief,
        research: Optional[Any] = None,  # ComprehensiveResearchData
        section_type: str = "general",
    ) -> str:
        """
        Polish template-generated text with LLM enhancement.

        This is the primary entry point for enhancing section outputs.

        Args:
            template_text: The raw template-generated markdown
            brief: Client input brief for context
            research: Optional research data to inject
            section_type: Type of section (strategy, creative, tactical)

        Returns:
            Polished text, or original if service disabled
        """
        if not self.is_enabled() or not self.config.enable_polish:
            log.debug("[CreativeService] Polish disabled, returning template text")
            return template_text

        if not template_text or len(template_text.strip()) < 50:
            log.debug("[CreativeService] Text too short to polish, returning as-is")
            return template_text

        log.info(f"[CreativeService] Polishing {section_type} section ({len(template_text)} chars)")

        try:
            # Build context-aware polish prompt
            prompt = self._build_polish_prompt(template_text, brief, research, section_type)

            # Primary: try ProviderChain via configured chain or router
            try:
                import asyncio
                chain = self.chain
                if chain is None:
                    # Try to create on-demand
                    from aicmo.llm.router import get_llm_client, LLMUseCase
                    chain = get_llm_client(use_case=LLMUseCase.CREATIVE_SPEC)

                success, result, provider = asyncio.run(chain.invoke("generate", prompt=prompt))
                if success and result:
                    polished_text = result if isinstance(result, str) else result.get("content", template_text)
                    log.info(f"[CreativeService] Successfully polished via {provider} ({len(polished_text)} chars)")
                    return polished_text
                else:
                    log.warning(f"[CreativeService] ProviderChain invoke returned no result or failed: {result}")
                    # fall through to fallback logic
            except Exception as e:
                log.warning(f"[CreativeService] ProviderChain invocation failed: {e}")

            # FALLBACK: If allowed, use direct OpenAI SDK as last resort for runtime failures
            if self.client:
                try:
                    response = self.client.chat.completions.create(
                        model=self.config.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert marketing strategist polishing content for client deliverables. Maintain structure, improve clarity, remove generic language, add specificity.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                    )
                    polished_text = response.choices[0].message.content
                    log.info(f"[CreativeService] Successfully polished via direct OpenAI ({len(polished_text)} chars)")
                    return polished_text
                except Exception as e:
                    log.error(f"[CreativeService] Direct OpenAI fallback failed: {e}")

            # Final fallback: return template text unchanged
            log.warning("[CreativeService] All generation attempts failed - returning template text")
            return template_text

        except Exception as e:
            log.warning(f"[CreativeService] Polish failed: {e}, returning template text")
            return template_text

    def degenericize_text(
        self,
        text: str,
        brief: ClientInputBrief,
        research: Optional[Any] = None,  # ComprehensiveResearchData
    ) -> str:
        """
        Remove generic language and add brand-specific details.

        Args:
            text: Input text to degenericize
            brief: Client brief for brand context
            research: Optional research data for specificity

        Returns:
            Degenericized text, or original if service disabled
        """
        if not self.is_enabled() or not self.config.enable_degenericize:
            return text

        log.info(f"[CreativeService] Degenericizing text ({len(text)} chars)")

        try:
            brand_name = brief.brand.brand_name
            industry = brief.brand.industry

            # Build competitor context from research
            competitor_context = ""
            if (
                research
                and hasattr(research, "competitor_research")
                and research.competitor_research
            ):
                comp_names = [c.name for c in research.competitor_research.competitors[:3]]
                if comp_names:
                    competitor_context = f"\nKey competitors: {', '.join(comp_names)}"

            prompt = f"""Remove generic marketing language and add specific details for {brand_name} in {industry}.{competitor_context}

ORIGINAL TEXT:
{text}

INSTRUCTIONS:
- Replace generic phrases ("leading provider", "best in class") with specific details
- Add concrete examples where possible
- Keep the structure and markdown formatting
- Maintain professional tone
- Do NOT add claims not supported by context

Return ONLY the improved text, no explanations."""

            # Primary: try ProviderChain
            try:
                import asyncio
                chain = self.chain
                if chain is None:
                    from aicmo.llm.router import get_llm_client, LLMUseCase
                    chain = get_llm_client(use_case=LLMUseCase.CREATIVE_SPEC)

                success, result, provider = asyncio.run(chain.invoke("generate", prompt=prompt))
                if success and result:
                    degenericized_text = result if isinstance(result, str) else result.get("content", text)
                    log.info(f"[CreativeService] Successfully degenericized via {provider} ({len(degenericized_text)} chars)")
                    return degenericized_text
                else:
                    log.warning(f"[CreativeService] ProviderChain invoke failed or empty result: {result}")
            except Exception as e:
                log.warning(f"[CreativeService] ProviderChain invocation failed: {e}")

            # FALLBACK: direct OpenAI if explicitly configured
            if self.client:
                try:
                    response = self.client.chat.completions.create(
                        model=self.config.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.6,
                        max_tokens=self.config.max_tokens,
                    )
                    result = response.choices[0].message.content
                    log.info("[CreativeService] Successfully degenericized via direct OpenAI")
                    return result
                except Exception as e:
                    log.error(f"[CreativeService] Direct OpenAI fallback failed: {e}")

            log.warning(f"[CreativeService] Degenericize failed: returning original text")
            return text

        except Exception as e:
            log.warning(f"[CreativeService] Degenericize failed: {e}, returning original")
            return text

    def generate_narrative(
        self,
        topic: str,
        brief: ClientInputBrief,
        research: Optional[Any] = None,  # ComprehensiveResearchData
        style: str = "strategic",
        max_paragraphs: int = 3,
    ) -> str:
        """
        Generate narrative content from scratch (not template-based).

        Use sparingly - prefer template-first approach for predictability.

        Args:
            topic: What to write about
            brief: Client brief for context
            research: Optional research data
            style: Narrative style (strategic, creative, tactical)
            max_paragraphs: Maximum paragraphs to generate

        Returns:
            Generated narrative, or fallback text if service disabled
        """
        if not self.is_enabled():
            return f"## {topic}\n\n[Content generation requires OpenAI API key]"

        log.info(f"[CreativeService] Generating {style} narrative on '{topic}'")

        try:
            brand_name = brief.brand.brand_name
            industry = brief.brand.industry
            audience = brief.audience.primary_customer
            goal = brief.goal.primary_goal

            # Inject research context if available
            research_context = ""
            if research and hasattr(research, "brand_research") and research.brand_research:
                research_context = (
                    f"\n\nResearch insights:\n- {research.brand_research.brand_summary}"
                )
                if research.brand_research.local_competitors:
                    comp_names = [c.name for c in research.brand_research.local_competitors[:2]]
                    research_context += f"\n- Competes with: {', '.join(comp_names)}"

            prompt = f"""Write a {style} narrative about {topic} for {brand_name}.

CONTEXT:
- Brand: {brand_name}
- Industry: {industry}
- Audience: {audience}
- Goal: {goal}{research_context}

REQUIREMENTS:
- Write {max_paragraphs} focused paragraphs
- Use specific details, not generic marketing speak
- Maintain {style} tone
- No placeholder text or TBDs
- Return ONLY the narrative, no preamble

Topic: {topic}"""

            # Primary: ProviderChain
            try:
                import asyncio
                chain = self.chain
                if chain is None:
                    from aicmo.llm.router import get_llm_client, LLMUseCase
                    chain = get_llm_client(use_case=LLMUseCase.CREATIVE_SPEC)

                success, result, provider = asyncio.run(chain.invoke("generate", prompt=prompt))
                if success and result:
                    narrative = result if isinstance(result, str) else result.get("content", "")
                    if narrative:
                        log.info(f"[CreativeService] Successfully generated narrative via {provider}")
                        return narrative
                    else:
                        log.warning("[CreativeService] ProviderChain returned empty narrative")
                else:
                    log.warning(f"[CreativeService] ProviderChain invoke failed: {result}")
            except Exception as e:
                log.warning(f"[CreativeService] ProviderChain invocation failed: {e}")

            # FALLBACK: direct OpenAI if explicitly allowed
            if self.client:
                try:
                    response = self.client.chat.completions.create(
                        model=self.config.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=self.config.temperature,
                        max_tokens=self.config.max_tokens,
                    )
                    result = response.choices[0].message.content
                    log.info("[CreativeService] Successfully generated narrative via direct OpenAI")
                    return result
                except Exception as e:
                    log.error(f"[CreativeService] Direct OpenAI fallback failed: {e}")

            log.warning(f"[CreativeService] Narrative generation failed, returning fallback text")
            return f"## {topic}\n\n{brand_name} focuses on delivering value to {audience} in the {industry} space."

        except Exception as e:
            log.warning(f"[CreativeService] Narrative generation failed: {e}")
            return f"## {topic}\n\n[Unable to generate narrative at this time]"

    def enhance_calendar_posts(
        self,
        posts: List[Dict[str, str]],
        brief: ClientInputBrief,
        research: Optional[Any] = None,  # ComprehensiveResearchData
    ) -> List[Dict[str, str]]:
        """
        Enhance calendar post hooks and captions with creative polish.

        Args:
            posts: List of post dicts with 'hook', 'caption', etc.
            brief: Client brief for context
            research: Optional research data

        Returns:
            Enhanced posts with improved hooks/captions
        """
        if not self.is_enabled():
            return posts  # Return unchanged

        log.info(f"[CreativeService] Enhancing {len(posts)} calendar posts")

        # Enhance in batches to minimize API calls
        enhanced_posts = []
        for post in posts:
            try:
                # Only enhance if hook seems generic
                if self._is_generic_hook(post.get("hook", "")):
                    enhanced_hook = self._enhance_hook(post["hook"], brief, research)
                    post["hook"] = enhanced_hook

                enhanced_posts.append(post)

            except Exception as e:
                log.warning(f"[CreativeService] Post enhancement failed: {e}")
                enhanced_posts.append(post)  # Use original

        return enhanced_posts

    def _build_polish_prompt(
        self,
        text: str,
        brief: ClientInputBrief,
        research: Optional[Any],
        section_type: str,
    ) -> str:
        """Build context-aware polish prompt."""
        brand_name = brief.brand.brand_name
        industry = brief.brand.industry

        # Add research context if available
        research_context = ""
        if research and hasattr(research, "brand_research") and research.brand_research:
            if research.brand_research.current_positioning:
                research_context += (
                    f"\n- Current positioning: {research.brand_research.current_positioning}"
                )
            if research.brand_research.local_competitors:
                comp_names = [c.name for c in research.brand_research.local_competitors[:2]]
                research_context += f"\n- Competitors: {', '.join(comp_names)}"

        return f"""Polish this {section_type} section for {brand_name} ({industry}).{research_context}

ORIGINAL SECTION:
{text}

INSTRUCTIONS:
- Improve clarity and readability
- Remove generic marketing language
- Add specific details where appropriate
- Maintain all structure, headings, and formatting
- Keep bullet points and lists intact
- Do NOT add claims not in original
- Return ONLY the polished section

Polished version:"""

    def _is_generic_hook(self, hook: str) -> bool:
        """Check if a hook seems generic and needs enhancement."""
        generic_patterns = [
            "discover",
            "learn more",
            "find out",
            "check out",
            "see how",
            "get started",
        ]
        hook_lower = hook.lower()
        return any(pattern in hook_lower for pattern in generic_patterns)

    def _enhance_hook(
        self,
        hook: str,
        brief: ClientInputBrief,
        research: Optional[Any],
    ) -> str:
        """Enhance a single social media hook."""
        try:
            brand_name = brief.brand.brand_name

            prompt = f"""Improve this social media hook for {brand_name}:

ORIGINAL: {hook}

Make it:
- More specific to {brand_name}
- More engaging and curiosity-driven
- Under 120 characters
- Avoid generic language

Return ONLY the improved hook, no explanation."""

            # Primary: ProviderChain
            try:
                import asyncio
                chain = self.chain
                if chain is None:
                    from aicmo.llm.router import get_llm_client, LLMUseCase
                    chain = get_llm_client(use_case=LLMUseCase.CREATIVE_SPEC)

                success, result, provider = asyncio.run(chain.invoke("generate", prompt=prompt))
                if success and result:
                    enhanced_hook = result if isinstance(result, str) else result.get("content", hook)
                    log.debug(f"[CreativeService] Successfully enhanced hook via {provider}")
                    return enhanced_hook.strip()
                else:
                    log.warning("[CreativeService] ProviderChain failed to enhance hook")
            except Exception as e:
                log.debug(f"[CreativeService] ProviderChain invocation failed: {e}")

            # FALLBACK: direct OpenAI if configured
            if self.client:
                try:
                    response = self.client.chat.completions.create(
                        model=self.config.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.8,
                        max_tokens=100,
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    log.debug(f"[CreativeService] Direct OpenAI fallback failed: {e}")

            return hook  # Fallback to original

        except Exception:
            return hook  # Fallback to original
