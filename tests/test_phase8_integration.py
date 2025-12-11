"""
Integration tests for Phase 8 - Multi-provider LLM routing layer.

Tests the complete end-to-end flow from use-case to ProviderChain.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from aicmo.llm.router import (
    get_llm_client,
    get_profile_for_usecase,
    build_provider_config,
    LLMUseCase,
    LLMProfile,
)
from aicmo.gateways.provider_chain import ProviderChain


class TestPhase8Integration:
    """Integration tests for complete routing flow."""
    
    def test_complete_flow_social_content(self):
        """Test complete flow: use-case → profile → providers → adapters → chain."""
        # Step 1: Get profile for use-case
        profile = get_profile_for_usecase(LLMUseCase.SOCIAL_CONTENT)
        assert profile == LLMProfile.CHEAP
        
        # Step 2: Build provider config
        config = build_provider_config(profile=profile, use_case=LLMUseCase.SOCIAL_CONTENT)
        assert isinstance(config, list)
        assert len(config) > 0
        
        # Each config should have provider and model
        for provider_config in config:
            assert "provider" in provider_config
            assert "model" in provider_config
            assert isinstance(provider_config["provider"], str)
            assert isinstance(provider_config["model"], str)
    
    def test_complete_flow_strategy_doc(self):
        """Test complete flow for strategy doc (standard profile)."""
        profile = get_profile_for_usecase(LLMUseCase.STRATEGY_DOC)
        assert profile == LLMProfile.STANDARD
        
        config = build_provider_config(profile=profile, use_case=LLMUseCase.STRATEGY_DOC)
        assert len(config) > 0
        
        # Standard profile should have more capable models
        providers = [c["provider"] for c in config]
        assert len(set(providers)) >= 2  # At least 2 different providers
    
    def test_complete_flow_research_web(self):
        """Test complete flow for research (research profile with web search)."""
        profile = get_profile_for_usecase(LLMUseCase.RESEARCH_WEB)
        assert profile == LLMProfile.RESEARCH
        
        # Enable deep research
        config = build_provider_config(
            profile=profile,
            use_case=LLMUseCase.RESEARCH_WEB,
            deep_research=True
        )
        assert len(config) > 0
        
        # Should include perplexity variants
        providers = [c["provider"] for c in config]
        assert "perplexity" in providers or any("perplexity" in p.lower() for p in providers)
    
    def test_env_var_override_in_flow(self):
        """Test that environment variables override default profiles."""
        with patch.dict(os.environ, {"LLM_PROFILE_SOCIAL_CONTENT": "premium"}):
            profile = get_profile_for_usecase(LLMUseCase.SOCIAL_CONTENT)
            assert profile == LLMProfile.PREMIUM
            
            config = build_provider_config(profile=profile, use_case=LLMUseCase.SOCIAL_CONTENT)
            # Premium profile should have fewer, higher-quality providers
            assert len(config) <= 3
    
    def test_explicit_override_in_flow(self):
        """Test that explicit overrides work in flow."""
        profile = get_profile_for_usecase(
            LLMUseCase.SOCIAL_CONTENT,
            profile_override=LLMProfile.PREMIUM
        )
        assert profile == LLMProfile.PREMIUM
    
    def test_get_llm_client_returns_chain(self):
        """Test that get_llm_client returns a ProviderChain instance."""
        chain = get_llm_client(use_case=LLMUseCase.SOCIAL_CONTENT)
        
        assert isinstance(chain, ProviderChain)
        assert chain.capability_name == "llm"
        assert len(chain.providers) > 0
    
    def test_get_llm_client_with_profile_override(self):
        """Test get_llm_client with profile override."""
        chain = get_llm_client(
            use_case=LLMUseCase.SOCIAL_CONTENT,
            profile_override=LLMProfile.PREMIUM
        )
        
        assert isinstance(chain, ProviderChain)
        # Premium profile should have fewer providers
        premium_count = len(chain.providers)
        
        # Compare with cheap profile
        cheap_chain = get_llm_client(
            use_case=LLMUseCase.SOCIAL_CONTENT,
            profile_override=LLMProfile.CHEAP
        )
        cheap_count = len(cheap_chain.providers)
        
        assert premium_count <= cheap_count
    
    def test_get_llm_client_with_deep_research(self):
        """Test get_llm_client with deep_research flag."""
        with patch.dict(os.environ, {"ENABLE_PERPLEXITY_DEEP_RESEARCH": "true"}):
            chain = get_llm_client(
                use_case=LLMUseCase.RESEARCH_WEB,
                deep_research=True
            )
            
            assert isinstance(chain, ProviderChain)
            assert len(chain.providers) > 0
            
            # Check that perplexity is in providers if available
            provider_names = [w.provider_name for w in chain.providers]
            # At least some perplexity variant should be there
            assert any("perplexity" in name.lower() for name in provider_names)
    
    def test_get_llm_client_with_multimodal(self):
        """Test get_llm_client with multimodal flag."""
        chain = get_llm_client(
            use_case=LLMUseCase.MULTIMODAL_ANALYSIS,
            multimodal=True
        )
        
        assert isinstance(chain, ProviderChain)
        assert len(chain.providers) > 0
        
        # Multimodal analysis should have capable providers
        provider_names = [w.provider_name for w in chain.providers]
        assert len(provider_names) > 0
    
    def test_all_use_cases_map_to_profiles(self):
        """Test that all use-cases map to valid profiles."""
        for use_case in LLMUseCase:
            profile = get_profile_for_usecase(use_case)
            assert profile in [
                LLMProfile.CHEAP,
                LLMProfile.STANDARD,
                LLMProfile.PREMIUM,
                LLMProfile.RESEARCH,
            ]
    
    def test_all_use_cases_get_provider_config(self):
        """Test that all use-cases get valid provider configuration."""
        for use_case in LLMUseCase:
            profile = get_profile_for_usecase(use_case)
            config = build_provider_config(profile=profile, use_case=use_case)
            
            assert isinstance(config, list)
            assert len(config) > 0
            
            for provider_config in config:
                assert "provider" in provider_config
                assert "model" in provider_config
    
    def test_all_use_cases_get_llm_client(self):
        """Test that all use-cases can get an LLM client."""
        for use_case in LLMUseCase:
            try:
                chain = get_llm_client(use_case=use_case)
                assert isinstance(chain, ProviderChain)
                assert chain.capability_name == "llm"
                assert len(chain.providers) > 0
            except RuntimeError as e:
                # Should not happen, but if it does, it should have clear message
                assert "No working LLM adapters" in str(e)
    
    def test_provider_chain_has_fallback_enabled(self):
        """Test that ProviderChain is configured for fallback."""
        chain = get_llm_client(use_case=LLMUseCase.SOCIAL_CONTENT)
        
        # max_fallback_attempts should be set to allow fallback
        assert chain.max_fallback_attempts is not None
        assert chain.max_fallback_attempts >= len(chain.providers)
    
    def test_providers_are_wrapped(self):
        """Test that all providers are ProviderWrapper instances."""
        from aicmo.gateways.provider_chain import ProviderWrapper
        
        chain = get_llm_client(use_case=LLMUseCase.SOCIAL_CONTENT)
        
        for provider in chain.providers:
            assert isinstance(provider, ProviderWrapper)
            assert provider.provider_name is not None
            assert provider.provider is not None
    
    def test_wrapper_respects_dry_run(self):
        """Test that ProviderWrapper respects dry_run setting from adapter."""
        chain = get_llm_client(use_case=LLMUseCase.SOCIAL_CONTENT)
        
        # All adapters should be in dry_run mode by default
        for wrapper in chain.providers:
            assert hasattr(wrapper, 'provider')
            # The underlying adapter should have dry_run attribute
            if hasattr(wrapper.provider, 'dry_run'):
                # is_dry_run on wrapper should match adapter's setting
                assert wrapper.is_dry_run == wrapper.provider.dry_run


class TestPhase8EdgeCases:
    """Test edge cases and error handling."""
    
    def test_get_llm_client_with_all_parameters(self):
        """Test get_llm_client with all parameters specified."""
        chain = get_llm_client(
            use_case=LLMUseCase.RESEARCH_WEB,
            profile_override=LLMProfile.RESEARCH,
            deep_research=True,
            multimodal=False
        )
        
        assert isinstance(chain, ProviderChain)
        assert chain.capability_name == "llm"
        assert len(chain.providers) > 0
    
    def test_get_llm_client_with_no_optional_params(self):
        """Test get_llm_client with minimal parameters."""
        chain = get_llm_client(use_case=LLMUseCase.SOCIAL_CONTENT)
        
        assert isinstance(chain, ProviderChain)
        assert chain.capability_name == "llm"
        assert len(chain.providers) > 0
    
    def test_multiple_chains_independent(self):
        """Test that multiple chains created independently."""
        chain1 = get_llm_client(use_case=LLMUseCase.SOCIAL_CONTENT)
        chain2 = get_llm_client(use_case=LLMUseCase.STRATEGY_DOC)
        
        # Should be different instances
        assert chain1 is not chain2
        
        # May have different number of providers
        assert isinstance(chain1, ProviderChain)
        assert isinstance(chain2, ProviderChain)
