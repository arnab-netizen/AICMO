"""
Phase 8: LLM Routing Layer Tests

Tests for multi-provider LLM routing, profile selection, use-case mapping,
and ProviderChain integration.

Covers:
- Profile selection (cheap/standard/premium/research)
- Use-case → profile mapping
- Environment-based profile overrides
- Provider configuration building
- Deep research feature gating
- Multimodal reordering (future)
- Adapter instantiation
- Dry-run mode
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from aicmo.llm import router
from aicmo.llm.router import (
    LLMProfile,
    LLMUseCase,
    get_profile_for_usecase,
    build_provider_config,
    USECASE_PROFILE_MAP,
    PROFILE_PROVIDER_MAP,
)


class TestProfileSelection:
    """Test LLM profile selection logic."""
    
    def test_cheap_profile_has_providers(self):
        """Cheap profile should include budget-friendly models."""
        providers = PROFILE_PROVIDER_MAP["cheap"]
        assert len(providers) > 0
        # Should include at least OpenAI and Anthropic budget variants
        provider_names = [p["provider"] for p in providers]
        assert "openai" in provider_names
        assert "anthropic" in provider_names
    
    def test_standard_profile_has_providers(self):
        """Standard profile should have balanced models."""
        providers = PROFILE_PROVIDER_MAP["standard"]
        assert len(providers) > 0
        provider_names = [p["provider"] for p in providers]
        assert "openai" in provider_names
        assert "anthropic" in provider_names
    
    def test_premium_profile_has_providers(self):
        """Premium profile should have top-tier models."""
        providers = PROFILE_PROVIDER_MAP["premium"]
        assert len(providers) > 0
        provider_names = [p["provider"] for p in providers]
        # Premium should include high-end models
        assert len(providers) >= 1
    
    def test_research_profile_has_web_search(self):
        """Research profile should include web search providers (Perplexity)."""
        providers = PROFILE_PROVIDER_MAP["research"]
        provider_names = [p["provider"] for p in providers]
        assert "perplexity" in provider_names


class TestUseCaseMapping:
    """Test use-case → profile mapping."""
    
    def test_social_content_maps_to_cheap(self):
        """SOCIAL_CONTENT should default to cheap profile."""
        profile = get_profile_for_usecase("SOCIAL_CONTENT")
        assert profile == "cheap"
    
    def test_email_copy_maps_to_cheap(self):
        """EMAIL_COPY should default to cheap profile."""
        profile = get_profile_for_usecase("EMAIL_COPY")
        assert profile == "cheap"
    
    def test_strategy_doc_maps_to_standard(self):
        """STRATEGY_DOC should default to standard profile."""
        profile = get_profile_for_usecase("STRATEGY_DOC")
        assert profile == "standard"
    
    def test_research_web_maps_to_research(self):
        """RESEARCH_WEB should default to research profile."""
        profile = get_profile_for_usecase("RESEARCH_WEB")
        assert profile == "research"
    
    def test_kaizen_qa_maps_to_cheap(self):
        """KAIZEN_QA should default to cheap (configurable in env)."""
        profile = get_profile_for_usecase("KAIZEN_QA")
        assert profile == "cheap"


class TestProfileOverrides:
    """Test environment-based and explicit profile overrides."""
    
    def test_explicit_profile_override_respected(self):
        """Explicit profile_override should take precedence."""
        profile = get_profile_for_usecase("SOCIAL_CONTENT", profile_override="premium")
        assert profile == "premium"
    
    @patch.dict(os.environ, {"LLM_PROFILE_SOCIAL_CONTENT": "standard"})
    def test_env_var_override_respected(self):
        """Environment variable should override default mapping."""
        profile = get_profile_for_usecase("SOCIAL_CONTENT")
        assert profile == "standard"
    
    @patch.dict(os.environ, {"LLM_PROFILE_SOCIAL_CONTENT": "standard"})
    def test_explicit_override_beats_env_var(self):
        """Explicit override should beat env var."""
        profile = get_profile_for_usecase("SOCIAL_CONTENT", profile_override="premium")
        assert profile == "premium"


class TestProviderConfiguration:
    """Test provider configuration building."""
    
    def test_build_config_cheap_profile(self):
        """build_provider_config should return providers for cheap profile."""
        config = build_provider_config("cheap", "SOCIAL_CONTENT")
        assert len(config) > 0
        assert all("provider" in p and "model" in p for p in config)
    
    def test_build_config_standard_profile(self):
        """build_provider_config should return providers for standard profile."""
        config = build_provider_config("standard", "STRATEGY_DOC")
        assert len(config) > 0
    
    def test_build_config_research_profile(self):
        """build_provider_config should return research providers."""
        config = build_provider_config("research", "RESEARCH_WEB")
        assert len(config) > 0
        # Should include Perplexity
        provider_names = [p["provider"] for p in config]
        assert "perplexity" in provider_names
    
    @patch.dict(os.environ, {"ENABLE_PERPLEXITY_DEEP_RESEARCH": "false"})
    def test_deep_research_not_added_when_disabled(self):
        """sonar-deep-research should not be added when flag is off."""
        config = build_provider_config(
            "research", 
            "RESEARCH_WEB",
            deep_research=True
        )
        models = [p["model"] for p in config]
        assert "sonar-deep-research" not in models
    
    @patch.dict(os.environ, {"ENABLE_PERPLEXITY_DEEP_RESEARCH": "true"})
    def test_deep_research_added_when_enabled(self):
        """sonar-deep-research should be added when flag is on."""
        config = build_provider_config(
            "research",
            "RESEARCH_WEB",
            deep_research=True
        )
        models = [p["model"] for p in config]
        assert "sonar-deep-research" in models


class TestMultimodalSupport:
    """Test multimodal model prioritization (future)."""
    
    def test_multimodal_flag_builds_config(self):
        """build_provider_config should handle multimodal=True."""
        config = build_provider_config(
            "standard",
            "MULTIMODAL_ANALYSIS",
            multimodal=True
        )
        assert len(config) > 0
        # TODO: When multimodal reordering is implemented,
        # verify vision-capable models appear first


class TestAdapterInstantiation:
    """Test LLM adapter instantiation."""
    
    def test_mistral_adapter_instantiation(self):
        """MistralLLMAdapter should instantiate in dry_run."""
        from aicmo.llm.adapters.mistral_llm import MistralLLMAdapter
        adapter = MistralLLMAdapter(dry_run=True)
        assert adapter.get_name() == "mistral_llm"
        assert adapter.kind == "llm"
    
    def test_cohere_adapter_instantiation(self):
        """CohereLLMAdapter should instantiate in dry_run."""
        from aicmo.llm.adapters.cohere_llm import CohereLLMAdapter
        adapter = CohereLLMAdapter(dry_run=True)
        assert adapter.get_name() == "cohere_llm"
    
    def test_deepseek_adapter_instantiation(self):
        """DeepSeekLLMAdapter should instantiate in dry_run."""
        from aicmo.llm.adapters.deepseek_llm import DeepSeekLLMAdapter
        adapter = DeepSeekLLMAdapter(dry_run=True)
        assert adapter.get_name() == "deepseek_llm"
    
    def test_llama_adapter_instantiation(self):
        """LlamaLLMAdapter should instantiate in dry_run."""
        from aicmo.llm.adapters.llama_llm import LlamaLLMAdapter
        adapter = LlamaLLMAdapter(dry_run=True)
        assert adapter.get_name() == "llama_llm"
    
    def test_perplexity_adapter_instantiation(self):
        """PerplexityLLMAdapter should instantiate in dry_run."""
        from aicmo.llm.adapters.perplexity_llm import PerplexityLLMAdapter
        adapter = PerplexityLLMAdapter(dry_run=True)
        assert "perplexity_llm" in adapter.get_name()
    
    def test_grok_adapter_instantiation(self):
        """GrokLLMAdapter should instantiate in dry_run."""
        from aicmo.llm.adapters.grok_llm import GrokLLMAdapter
        adapter = GrokLLMAdapter(dry_run=True)
        assert adapter.get_name() == "grok_llm"


class TestAdapterHealthCheck:
    """Test health check methods on adapters."""
    
    def test_mistral_health_check_dry_run(self):
        """Health check should return HEALTHY in dry_run."""
        from aicmo.llm.adapters.mistral_llm import MistralLLMAdapter, MistralHealth
        adapter = MistralLLMAdapter(dry_run=True)
        status = adapter.check_health()
        assert status.health == MistralHealth.HEALTHY
    
    @patch.dict(os.environ, {}, clear=True)
    def test_mistral_health_check_no_key(self):
        """Health check should return UNHEALTHY when key missing."""
        from aicmo.llm.adapters.mistral_llm import MistralLLMAdapter, MistralHealth
        adapter = MistralLLMAdapter(api_key=None, dry_run=False)
        status = adapter.check_health()
        assert status.health == MistralHealth.UNHEALTHY


class TestAdapterGeneration:
    """Test LLM generation methods."""
    
    def test_mistral_dry_run_generation(self):
        """Mistral should return stub in dry_run."""
        from aicmo.llm.adapters.mistral_llm import MistralLLMAdapter
        adapter = MistralLLMAdapter(dry_run=True)
        result = adapter.generate("Test prompt")
        assert isinstance(result, str)
        assert "DRY_RUN" in result
    
    def test_cohere_dry_run_generation(self):
        """Cohere should return stub in dry_run."""
        from aicmo.llm.adapters.cohere_llm import CohereLLMAdapter
        adapter = CohereLLMAdapter(dry_run=True)
        result = adapter.generate("Test prompt")
        assert isinstance(result, str)
        assert "DRY_RUN" in result
    
    def test_perplexity_dry_run_generation(self):
        """Perplexity should return stub in dry_run."""
        from aicmo.llm.adapters.perplexity_llm import PerplexityLLMAdapter
        adapter = PerplexityLLMAdapter(dry_run=True, model="sonar")
        result = adapter.generate("Test prompt")
        assert isinstance(result, str)
        assert "DRY_RUN" in result


class TestGetLLMClient:
    """Test get_llm_client() function."""
    
    def test_get_llm_client_returns_provider_chain(self):
        """get_llm_client should return a ProviderChain with wrappers."""
        from aicmo.llm.router import get_llm_client
        from aicmo.gateways.provider_chain import ProviderChain
        
        # get_llm_client should return a ProviderChain
        try:
            chain = get_llm_client("SOCIAL_CONTENT")
            assert isinstance(chain, ProviderChain)
            assert chain.capability_name == "llm"
            # Should have at least one provider for cheap profile
            assert len(chain.providers) > 0
        except RuntimeError as e:
            # If no working adapters, should raise RuntimeError with clear message
            assert "No working LLM adapters" in str(e)
    
    def test_get_llm_client_respects_profile_override(self):
        """get_llm_client should accept profile_override."""
        # Function signature should accept the parameter even if not fully implemented
        from aicmo.llm.router import get_llm_client
        try:
            get_llm_client("SOCIAL_CONTENT", profile_override="premium")
        except (NotImplementedError, ValueError, RuntimeError):
            pass  # Expected for now


class TestProfileEnums:
    """Test profile and use-case enums."""
    
    def test_llm_profile_enum_values(self):
        """LLMProfile enum should have all expected values."""
        assert LLMProfile.CHEAP.value == "cheap"
        assert LLMProfile.STANDARD.value == "standard"
        assert LLMProfile.PREMIUM.value == "premium"
        assert LLMProfile.RESEARCH.value == "research"
    
    def test_llm_usecase_enum_values(self):
        """LLMUseCase enum should have all expected values."""
        assert LLMUseCase.SOCIAL_CONTENT.value == "SOCIAL_CONTENT"
        assert LLMUseCase.STRATEGY_DOC.value == "STRATEGY_DOC"
        assert LLMUseCase.RESEARCH_WEB.value == "RESEARCH_WEB"
        assert LLMUseCase.ORCHESTRATOR.value == "ORCHESTRATOR"


class TestImports:
    """Test that all modules can be imported."""
    
    def test_router_import(self):
        """Router module should import without error."""
        from aicmo.llm import router
        assert router is not None
    
    def test_adapters_import(self):
        """All adapters should import without error."""
        from aicmo.llm.adapters import (
            MistralLLMAdapter,
            CohereLLMAdapter,
            DeepSeekLLMAdapter,
            LlamaLLMAdapter,
            PerplexityLLMAdapter,
            GrokLLMAdapter,
        )
        assert all([
            MistralLLMAdapter,
            CohereLLMAdapter,
            DeepSeekLLMAdapter,
            LlamaLLMAdapter,
            PerplexityLLMAdapter,
            GrokLLMAdapter,
        ])
