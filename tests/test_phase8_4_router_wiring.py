"""
Phase 8.4 Tests: Router Wiring Verification

Tests that all generators are using the new Phase 8.4 LLM router
instead of direct provider calls.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock


class TestPhase84RouterWiring:
    """Verify all generators use Phase 8.4 LLM router."""

    def test_swot_generator_imports_router(self):
        """Test that generate_swot imports get_llm_client from router."""
        with open("/workspaces/AICMO/aicmo/generators/swot_generator.py") as f:
            content = f.read()
        # Verify it imports from router, not old clients
        assert "from aicmo.llm.router import get_llm_client" in content
        assert "_get_openai_client" not in content.split("def _generate_swot_with_llm")[1].split("except")[0]

    def test_persona_generator_imports_router(self):
        """Test that generate_persona imports get_llm_client from router."""
        with open("/workspaces/AICMO/aicmo/generators/persona_generator.py") as f:
            content = f.read()
        # Verify it imports from router
        assert "from aicmo.llm.router import get_llm_client" in content
        func_content = content.split("def _generate_persona_with_llm")[1].split("except")[0]
        assert "_get_openai_client" not in func_content

    def test_messaging_pillars_imports_router(self):
        """Test that generate_messaging_pillars imports router."""
        with open("/workspaces/AICMO/aicmo/generators/messaging_pillars_generator.py") as f:
            content = f.read()
        assert "from aicmo.llm.router import get_llm_client" in content
        func_content = content.split("def _generate_messaging_pillars_with_llm")[1].split("except")[0]
        assert "_get_llm_provider" not in func_content

    def test_social_calendar_imports_router(self):
        """Test that social calendar generator imports router."""
        with open("/workspaces/AICMO/aicmo/generators/social_calendar_generator.py") as f:
            content = f.read()
        assert "from aicmo.llm.router import get_llm_client" in content
        # Check the _generate_llm_caption_for_day function
        func_content = content.split("def _generate_llm_caption_for_day")[1].split("\n        return None")[0]
        assert "asyncio.run" in func_content

    def test_directions_engine_imports_router(self):
        """Test that directions_engine imports router not openai."""
        with open("/workspaces/AICMO/aicmo/creative/directions_engine.py") as f:
            content = f.read()
        # Should import from router
        assert "from aicmo.llm.router import get_llm_client" in content
        # Should not have direct OpenAI import at start
        func_content = content.split("def generate_creative_directions")[1].split("\n    except")[0]
        assert "OpenAI(api_key=" not in func_content


class TestPhase84UseCaseMappings:
    """Verify correct use-case mappings for each generator."""

    def test_use_cases_exist(self):
        """Verify all use-case enums exist."""
        from aicmo.llm.router import LLMUseCase
        
        assert LLMUseCase.STRATEGY_DOC.value == "STRATEGY_DOC"
        assert LLMUseCase.CREATIVE_SPEC.value == "CREATIVE_SPEC"
        assert LLMUseCase.SOCIAL_CONTENT.value == "SOCIAL_CONTENT"

    def test_swot_uses_strategy_doc(self):
        """Verify SWOT generator uses STRATEGY_DOC use case."""
        with open("/workspaces/AICMO/aicmo/generators/swot_generator.py") as f:
            content = f.read()
        func = content.split("def _generate_swot_with_llm")[1].split("\n    except")[0]
        assert "LLMUseCase.STRATEGY_DOC" in func or "use_case=LLMUseCase.STRATEGY_DOC" in func or 'use_case="STRATEGY_DOC"' in func

    def test_persona_uses_creative_spec(self):
        """Verify Persona generator uses CREATIVE_SPEC use case."""
        with open("/workspaces/AICMO/aicmo/generators/persona_generator.py") as f:
            content = f.read()
        func = content.split("def _generate_persona_with_llm")[1].split("\n    except")[0]
        assert "LLMUseCase.CREATIVE_SPEC" in func or "use_case=LLMUseCase.CREATIVE_SPEC" in func or 'use_case="CREATIVE_SPEC"' in func

    def test_pillars_uses_strategy_doc(self):
        """Verify Messaging Pillars generator uses STRATEGY_DOC use case."""
        with open("/workspaces/AICMO/aicmo/generators/messaging_pillars_generator.py") as f:
            content = f.read()
        func = content.split("def _generate_messaging_pillars_with_llm")[1].split("\n    except")[0]
        assert "LLMUseCase.STRATEGY_DOC" in func or "use_case=LLMUseCase.STRATEGY_DOC" in func or 'use_case="STRATEGY_DOC"' in func

    def test_social_uses_social_content(self):
        """Verify Social Calendar generator uses SOCIAL_CONTENT use case."""
        with open("/workspaces/AICMO/aicmo/generators/social_calendar_generator.py") as f:
            content = f.read()
        func = content.split("def _generate_llm_caption_for_day")[1].split("\n        return None")[0]
        assert "LLMUseCase.SOCIAL_CONTENT" in func or "use_case=LLMUseCase.SOCIAL_CONTENT" in func or 'use_case="SOCIAL_CONTENT"' in func

    def test_directions_uses_creative_spec(self):
        """Verify Creative Directions generator uses CREATIVE_SPEC use case."""
        with open("/workspaces/AICMO/aicmo/creative/directions_engine.py") as f:
            content = f.read()
        func = content.split("def generate_creative_directions")[1].split("\n    except")[0]
        assert "LLMUseCase.CREATIVE_SPEC" in func or "use_case=LLMUseCase.CREATIVE_SPEC" in func or 'use_case="CREATIVE_SPEC"' in func


class TestPhase84AsyncCalls:
    """Verify async/await pattern is used correctly."""

    def test_swot_uses_async_invoke(self):
        """Verify SWOT uses async invoke with asyncio.run."""
        with open("/workspaces/AICMO/aicmo/generators/swot_generator.py") as f:
            content = f.read()
        func = content.split("def _generate_swot_with_llm")[1].split("\n    except")[0]
        assert "asyncio.run" in func
        assert "chain.invoke" in func

    def test_persona_uses_async_invoke(self):
        """Verify Persona uses async invoke."""
        with open("/workspaces/AICMO/aicmo/generators/persona_generator.py") as f:
            content = f.read()
        func = content.split("def _generate_persona_with_llm")[1].split("\n    except")[0]
        assert "asyncio.run" in func
        assert "chain.invoke" in func

    def test_pillars_uses_async_invoke(self):
        """Verify Messaging Pillars uses async invoke."""
        with open("/workspaces/AICMO/aicmo/generators/messaging_pillars_generator.py") as f:
            content = f.read()
        func = content.split("def _generate_messaging_pillars_with_llm")[1].split("\n    except")[0]
        assert "asyncio.run" in func
        assert "chain.invoke" in func

    def test_social_uses_async_invoke(self):
        """Verify Social Calendar uses async invoke pattern."""
        with open("/workspaces/AICMO/aicmo/generators/social_calendar_generator.py") as f:
            content = f.read()
        func = content.split("def _generate_llm_caption_for_day")[1].split("\n        return None")[0]
        assert "asyncio.run" in func
        assert "chain.invoke" in func

    def test_directions_uses_async_invoke(self):
        """Verify Creative Directions uses async invoke."""
        with open("/workspaces/AICMO/aicmo/creative/directions_engine.py") as f:
            content = f.read()
        func = content.split("def generate_creative_directions")[1].split("\n    except")[0]
        assert "asyncio.run" in func
        assert "chain.invoke" in func


class TestPhase84NoOldClientsRemain:
    """Verify old provider clients are completely removed from generator logic."""

    def test_no_old_imports_in_swot(self):
        """Verify swot_generator doesn't import old clients."""
        with open("/workspaces/AICMO/aicmo/generators/swot_generator.py") as f:
            content = f.read()
        llm_func = content.split("def _generate_swot_with_llm")[1].split("def _sanitize")[0]
        assert "_get_openai_client" not in llm_func
        assert "_get_claude_client" not in llm_func

    def test_no_old_imports_in_persona(self):
        """Verify persona_generator doesn't import old clients."""
        with open("/workspaces/AICMO/aicmo/generators/persona_generator.py") as f:
            content = f.read()
        llm_func = content.split("def _generate_persona_with_llm")[1].split("def _parse_persona")[0]
        assert "_get_openai_client" not in llm_func
        assert "_get_claude_client" not in llm_func

    def test_no_old_imports_in_pillars(self):
        """Verify pillars generator doesn't import old clients."""
        with open("/workspaces/AICMO/aicmo/generators/messaging_pillars_generator.py") as f:
            content = f.read()
        llm_func = content.split("def _generate_messaging_pillars_with_llm")[1].split("def _sanitize_messaging_pillars")[0]
        assert "_get_openai_client" not in llm_func
        assert "_get_llm_provider" not in llm_func

    def test_no_old_imports_in_social(self):
        """Verify social_calendar doesn't import old clients in LLM func."""
        with open("/workspaces/AICMO/aicmo/generators/social_calendar_generator.py") as f:
            content = f.read()
        llm_func = content.split("def _generate_llm_caption_for_day")[1].split("def _stub_")[0]
        assert "_get_openai_client" not in llm_func
        assert "_get_claude_client" not in llm_func

    def test_no_openai_direct_in_directions(self):
        """Verify directions doesn't use OpenAI directly."""
        with open("/workspaces/AICMO/aicmo/creative/directions_engine.py") as f:
            content = f.read()
        func = content.split("def generate_creative_directions")[1].split("except")[0]
        assert "OpenAI(api_key=" not in func


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
