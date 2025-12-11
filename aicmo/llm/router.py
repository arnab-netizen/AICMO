"""
Phase 8: Multi-provider LLM routing layer.

Routes LLM requests to appropriate provider/model based on use-case and profile.

Profiles (cost/capability tradeoff):
- cheap: Budget-friendly, low-latency (gpt-4.1-mini, claude-3.5-haiku, gemini-1.5-flash, etc)
- standard: Balanced, production-quality (gpt-4.1, claude-3.5-sonnet, gemini-1.5-pro, etc)
- premium: Top-tier (o3-mini, claude-opus, command-r-plus)
- research: Web search + deep reasoning (perplexity, sonar, gemini-pro)

Use-cases map to default profiles + override from environment.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)


# ==============================================================================
# PROFILE & USE-CASE ENUMS
# ==============================================================================

class LLMProfile(str, Enum):
    """LLM capability profile."""
    CHEAP = "cheap"
    STANDARD = "standard"
    PREMIUM = "premium"
    RESEARCH = "research"


class LLMUseCase(str, Enum):
    """LLM use-case categories."""
    SOCIAL_CONTENT = "SOCIAL_CONTENT"
    EMAIL_COPY = "EMAIL_COPY"
    STRATEGY_DOC = "STRATEGY_DOC"
    WEBSITE_COPY = "WEBSITE_COPY"
    CONVERSION_AUDIT = "CONVERSION_AUDIT"
    RESEARCH_WEB = "RESEARCH_WEB"
    CREATIVE_IDEATION = "CREATIVE_IDEATION"
    CREATIVE_SPEC = "CREATIVE_SPEC"
    LEAD_REASONING = "LEAD_REASONING"
    KAIZEN_QA = "KAIZEN_QA"
    ORCHESTRATOR = "ORCHESTRATOR"
    MULTIMODAL_ANALYSIS = "MULTIMODAL_ANALYSIS"


# ==============================================================================
# PROFILE → PROVIDER/MODEL MAPPING
# ==============================================================================

PROFILE_PROVIDER_MAP: Dict[str, List[Dict[str, str]]] = {
    "cheap": [
        {"provider": "openai", "model": "gpt-4.1-mini"},
        {"provider": "anthropic", "model": "claude-3.5-haiku"},
        {"provider": "google", "model": "gemini-1.5-flash"},
        {"provider": "mistral", "model": "mistral-small"},
        {"provider": "groq", "model": "llama-3.1-70b-instruct"},
        {"provider": "deepseek", "model": "deepseek-chat"},
    ],
    "standard": [
        {"provider": "openai", "model": "gpt-4.1"},
        {"provider": "anthropic", "model": "claude-3.5-sonnet"},
        {"provider": "google", "model": "gemini-1.5-pro"},
        {"provider": "mistral", "model": "mistral-large"},
        {"provider": "cohere", "model": "command-r"},
    ],
    "premium": [
        {"provider": "openai", "model": "o3-mini"},
        {"provider": "anthropic", "model": "claude-opus"},
        {"provider": "cohere", "model": "command-r-plus"},
    ],
    "research": [
        {"provider": "openai", "model": "gpt-4.1"},
        {"provider": "google", "model": "gemini-1.5-pro"},
        {"provider": "perplexity", "model": "sonar"},
        {"provider": "perplexity", "model": "sonar-reasoning"},
        # NOTE: sonar-deep-research added only when deep_research=True + flag enabled
    ],
}


# ==============================================================================
# USE-CASE → PROFILE MAPPING
# ==============================================================================

USECASE_PROFILE_MAP: Dict[str, str] = {
    "SOCIAL_CONTENT": "cheap",
    "EMAIL_COPY": "cheap",
    "STRATEGY_DOC": "standard",
    "WEBSITE_COPY": "standard",
    "CONVERSION_AUDIT": "standard",
    "RESEARCH_WEB": "research",
    "CREATIVE_IDEATION": "cheap",
    "CREATIVE_SPEC": "cheap",
    "LEAD_REASONING": "cheap",
    "KAIZEN_QA": "cheap",
    "ORCHESTRATOR": "standard",
    "MULTIMODAL_ANALYSIS": "standard",
}


# ==============================================================================
# ENVIRONMENT-BASED PROFILE OVERRIDES
# ==============================================================================

def get_profile_for_usecase(use_case: str, profile_override: Optional[str] = None) -> str:
    """
    Determine effective LLM profile for a use-case.
    
    Priority:
    1. profile_override (if provided)
    2. LLM_PROFILE_<USE_CASE> env var (if set)
    3. Default from USECASE_PROFILE_MAP
    
    Args:
        use_case: Use-case string (e.g., "SOCIAL_CONTENT")
        profile_override: Explicit profile to use (overrides defaults)
    
    Returns:
        Effective profile string
    """
    if profile_override:
        return profile_override
    
    # Check env var override: LLM_PROFILE_SOCIAL_CONTENT, etc.
    env_var = f"LLM_PROFILE_{use_case.upper()}"
    env_profile = os.getenv(env_var)
    if env_profile:
        return env_profile
    
    # Default from mapping
    default = USECASE_PROFILE_MAP.get(use_case.upper(), "standard")
    return default


# ==============================================================================
# PROVIDER CONFIGURATION & FILTERING
# ==============================================================================

def build_provider_config(
    profile: str,
    use_case: str,
    deep_research: bool = False,
    multimodal: bool = False,
) -> List[Dict[str, str]]:
    """
    Build provider configuration list for use-case.
    
    Steps:
    1. Get providers from profile
    2. Filter by availability (API keys set)
    3. Filter by feature flags (e.g., ENABLE_PROVIDER_OPENAI)
    4. For research: add deep-research if flag + limit enabled
    5. For multimodal: reorder to favor vision-capable models
    
    Args:
        profile: LLM profile (cheap, standard, premium, research)
        use_case: Use-case string
        deep_research: If True & enabled, include Perplexity deep-research
        multimodal: If True, reorder to favor multimodal models
    
    Returns:
        List of provider configs with {provider, model}
    """
    providers = PROFILE_PROVIDER_MAP.get(profile, [])
    
    # TODO: Filter by API key availability
    # TODO: Filter by feature flags (e.g., ENABLE_PROVIDER_OPENAI)
    
    # Special handling for research + deep_research
    if use_case == "RESEARCH_WEB" and deep_research:
        deep_research_enabled = os.getenv("ENABLE_PERPLEXITY_DEEP_RESEARCH", "false").lower() == "true"
        if deep_research_enabled:
            # Add deep-research provider at end (lowest priority)
            providers_copy = list(providers)
            providers_copy.append({"provider": "perplexity", "model": "sonar-deep-research"})
            providers = providers_copy
    
    # Special handling for multimodal: reorder vision-capable first
    if multimodal:
        multimodal_first = ["gemini-1.5-pro", "gpt-4.1", "gpt-4.1-mini"]
        # TODO: Reorder based on multimodal_first list
    
    return providers


# ==============================================================================
# PROVIDER INSTANTIATION & CHAIN CREATION
# ==============================================================================

def _instantiate_adapter(provider: str, api_key: Optional[str] = None) -> Optional[Any]:
    """
    Instantiate LLM adapter for given provider.
    
    Imports are done lazily to avoid circular imports and unnecessary dependencies.
    
    Args:
        provider: Provider name (openai, anthropic, google, mistral, etc.)
        api_key: Optional API key (will use env var if not provided)
    
    Returns:
        Instantiated adapter, or None if unavailable
    """
    # We import adapters lazily to avoid circular imports
    # and to allow missing optional dependencies
    try:
        provider_lower = provider.lower()
        
        if provider_lower == "mistral":
            from .adapters.mistral_llm import MistralLLMAdapter
            return MistralLLMAdapter(api_key=api_key, dry_run=False)
        
        elif provider_lower == "cohere":
            from .adapters.cohere_llm import CohereLLMAdapter
            return CohereLLMAdapter(api_key=api_key, dry_run=False)
        
        elif provider_lower == "deepseek":
            from .adapters.deepseek_llm import DeepSeekLLMAdapter
            return DeepSeekLLMAdapter(api_key=api_key, dry_run=False)
        
        elif provider_lower == "groq":
            from .adapters.llama_llm import LlamaLLMAdapter
            return LlamaLLMAdapter(api_key=api_key, dry_run=False)
        
        elif provider_lower == "perplexity":
            from .adapters.perplexity_llm import PerplexityLLMAdapter
            return PerplexityLLMAdapter(api_key=api_key, dry_run=False)
        
        elif provider_lower == "grok":
            from .adapters.grok_llm import GrokLLMAdapter
            return GrokLLMAdapter(api_key=api_key, dry_run=False)
        
        elif provider_lower in ("openai", "google", "anthropic"):
            # TODO: Wire OpenAI, Google, Anthropic adapters
            # For now, log and return None to use fallback
            logger.debug(f"LLM adapter for {provider} not yet wired (will be added in future)")
            return None
        
        else:
            logger.warning(f"Unknown LLM provider: {provider}")
            return None
    
    except ImportError as e:
        logger.warning(f"Could not import adapter for {provider}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error instantiating adapter for {provider}: {e}")
        return None


def get_llm_client(
    use_case: str,
    profile_override: Optional[str] = None,
    deep_research: bool = False,
    multimodal: bool = False,
):
    """
    Get LLM ProviderChain for specified use-case.
    
    Steps:
    1. Determine effective profile (override → env var → default)
    2. Build provider config from profile
    3. Instantiate adapters for each provider
    4. Wrap adapters in ProviderWrapper
    5. Register with self_check_registry (if available)
    6. Create & return ProviderChain
    
    Args:
        use_case: Use-case string (e.g., "SOCIAL_CONTENT")
        profile_override: Explicit profile to use (optional)
        deep_research: If True, enable deep-research providers (for RESEARCH_WEB use-case)
        multimodal: If True, prioritize multimodal-capable models
    
    Returns:
        ProviderChain instance configured for the use-case
    """
    effective_profile = get_profile_for_usecase(use_case, profile_override)
    
    logger.info(
        f"Creating LLM chain for {use_case} with profile={effective_profile} "
        f"(deep_research={deep_research}, multimodal={multimodal})"
    )
    
    # Build provider configuration
    providers_config = build_provider_config(
        profile=effective_profile,
        use_case=use_case,
        deep_research=deep_research,
        multimodal=multimodal,
    )
    
    if not providers_config:
        logger.warning(f"No providers available for profile {effective_profile}")
        # TODO: Return no-op chain or raise error depending on requirements
        raise ValueError(f"No LLM providers available for profile {effective_profile}")
    
    # Instantiate and wrap adapters
    wrappers = []
    for provider_config in providers_config:
        provider_name = provider_config.get("provider")
        model = provider_config.get("model")
        
        # Instantiate adapter
        adapter = _instantiate_adapter(provider_name)
        if adapter is None:
            logger.debug(f"Skipping {provider_name}: adapter not available")
            continue
        
        # Wrap in ProviderWrapper for chain integration
        wrapper = _wrap_adapter(adapter, provider_name, model)
        wrappers.append(wrapper)
    
    if not wrappers:
        logger.error(f"No working adapters available for profile {effective_profile}")
        # TODO: Return no-op chain or raise error
        raise RuntimeError(f"No working LLM adapters for profile {effective_profile}")
    
    # TODO: Register with self_check_registry if available
    # for wrapper in wrappers:
    #     register_provider_chain("llm", wrapper)
    
    # Create and return ProviderChain
    try:
        from aicmo.gateways.provider_chain import ProviderChain
        chain = ProviderChain(
            capability_name="llm",  # ← Correct parameter name
            providers=wrappers,
            is_dry_run=False,
            max_fallback_attempts=None,  # Try all providers
        )
        return chain
    except ImportError:
        logger.error("ProviderChain not available, cannot create LLM chain")
        raise


def _wrap_adapter(adapter: Any, provider_name: str, model: str):
    """
    Wrap LLM adapter in ProviderWrapper for ProviderChain integration.
    
    Args:
        adapter: Instantiated LLM adapter
        provider_name: Provider name (for logging)
        model: Model name (for logging)
    
    Returns:
        ProviderWrapper instance
    """
    from aicmo.gateways.provider_chain import ProviderWrapper
    
    logger.debug(f"Wrapping {provider_name}/{model} adapter in ProviderWrapper")
    
    # Create wrapper with adapter instance
    wrapper = ProviderWrapper(
        provider=adapter,
        provider_name=f"{provider_name}/{model}",
        is_dry_run=adapter.dry_run,  # Respect adapter's dry_run setting
        health_threshold_failures=3,  # Mark unhealthy after 3 consecutive failures
        health_threshold_successes=5,  # Mark healthy after 5 consecutive successes
    )
    
    return wrapper
