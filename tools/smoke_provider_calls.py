#!/usr/bin/env python3
"""
AUDIT SCRIPT: Safe runtime provider availability check.

Purpose:
  - Import provider chain and adapters
  - Check which providers are configured (env vars present)
  - Verify no actual API calls (health check stubs only)
  - Output provider readiness matrix without leaking secrets

Rules:
  - No secret values printed
  - No actual external API calls
  - Safe to run in any environment
  - Machine-readable output for reporting
"""

import os
import sys
from pathlib import Path

# Repository root
REPO_ROOT = Path(__file__).parent.parent

def check_env_var_present(var_name: str) -> bool:
    """Check if env var exists without printing value."""
    return var_name in os.environ

def audit_llm_providers():
    """Check LLM provider availability."""
    print("\n" + "="*80)
    print("LLM PROVIDERS")
    print("="*80)
    
    providers = {
        "OpenAI": "OPENAI_API_KEY",
        "Anthropic (Claude)": "ANTHROPIC_API_KEY",
        "Gemini": "GOOGLE_API_KEY",
        "Groq": "GROQ_API_KEY",
        "Mistral": "MISTRAL_API_KEY",
        "Cohere": "COHERE_API_KEY",
        "Perplexity": "PERPLEXITY_API_KEY",
        "DeepSeek": "DEEPSEEK_API_KEY",
        "Grok": "GROK_API_KEY",
        "Llama (via API)": "LLAMA_API_KEY",
    }
    
    configured = []
    for name, env_var in providers.items():
        present = check_env_var_present(env_var)
        status = "✅ CONFIGURED" if present else "❌ NOT CONFIGURED"
        print(f"{name:20} | {env_var:25} | {status}")
        if present:
            configured.append(name)
    
    print(f"\nConfigured LLM Providers: {len(configured)}/{len(providers)}")
    if configured:
        print(f"Available: {', '.join(configured)}")
    else:
        print("⚠️ No LLM providers configured - fallback to stubs")
    
    return configured

def audit_image_providers():
    """Check image generation provider availability."""
    print("\n" + "="*80)
    print("IMAGE GENERATION PROVIDERS")
    print("="*80)
    
    providers = {
        "Replicate": "REPLICATE_API_KEY",
        "Stability AI": "STABILITY_API_KEY",
        "FAL": "FAL_API_KEY",
        "Hugging Face": "HUGGINGFACE_API_KEY",
        "Runway ML": "RUNWAY_ML_API_KEY",
        "Pika Labs": "PIKA_LABS_API_KEY",
        "Luma Dream": "LUMA_DREAM_API_KEY",
        "SDXL": "SDXL_API_KEY",
    }
    
    configured = []
    for name, env_var in providers.items():
        present = check_env_var_present(env_var)
        status = "✅ CONFIGURED" if present else "❌ NOT CONFIGURED"
        print(f"{name:20} | {env_var:25} | {status}")
        if present:
            configured.append(name)
    
    print(f"\nConfigured Image Providers: {len(configured)}/{len(providers)}")
    if configured:
        print(f"Available: {', '.join(configured)}")
    else:
        print("⚠️ No image providers configured - fallback to stubs")
    
    return configured

def audit_search_providers():
    """Check web search/research provider availability."""
    print("\n" + "="*80)
    print("SEARCH & RESEARCH PROVIDERS")
    print("="*80)
    
    providers = {
        "Perplexity (Research)": "PERPLEXITY_API_KEY",
        "SerpAPI": "SERPAPI_API_KEY",
        "Jina": "JINA_API_KEY",
        "ScrapingBee": "SCRAPINGBEE_KEY",
        "ScraperAPI": "SCRAPERAPI_KEY",
        "Google Places": "GOOGLE_PLACES_API_KEY",
        "YouTube Data": "YOUTUBE_DATA_API_KEY",
    }
    
    configured = []
    for name, env_var in providers.items():
        present = check_env_var_present(env_var)
        status = "✅ CONFIGURED" if present else "❌ NOT CONFIGURED"
        print(f"{name:20} | {env_var:25} | {status}")
        if present:
            configured.append(name)
    
    print(f"\nConfigured Search Providers: {len(configured)}/{len(providers)}")
    if configured:
        print(f"Available: {', '.join(configured)}")
    else:
        print("⚠️ No search providers configured - fallback to stubs")
    
    return configured

def audit_lead_providers():
    """Check lead enrichment provider availability."""
    print("\n" + "="*80)
    print("LEAD ENRICHMENT PROVIDERS")
    print("="*80)
    
    providers = {
        "Apollo": "APOLLO_API_KEY",
        "Hunter": "HUNTER_API_KEY",
        "People Data Labs": "PEOPLEDATALABS_API_KEY",
        "Dropcontact": "DROPCONTACT_API_KEY",
    }
    
    configured = []
    for name, env_var in providers.items():
        present = check_env_var_present(env_var)
        status = "✅ CONFIGURED" if present else "❌ NOT CONFIGURED"
        print(f"{name:20} | {env_var:25} | {status}")
        if present:
            configured.append(name)
    
    print(f"\nConfigured Lead Providers: {len(configured)}/{len(providers)}")
    if configured:
        print(f"Available: {', '.join(configured)}")
    else:
        print("⚠️ No lead providers configured - fallback to stubs")
    
    return configured

def audit_email_providers():
    """Check email/outreach provider availability."""
    print("\n" + "="*80)
    print("EMAIL & OUTREACH PROVIDERS")
    print("="*80)
    
    providers = {
        "SendGrid": "SENDGRID_API_KEY",
        "Twilio SMS": "TWILIO_ACCOUNT_SID",
        "SMTP": "SMTP_HOST",
        "Mailso": "MAILSO_API_KEY",
        "ZeroBounce": "ZEROBOUNCE_API_KEY",
        "Gmail": "GMAIL_CREDENTIALS_PATH",
        "Make Webhook": "MAKE_WEBHOOK_URL",
    }
    
    configured = []
    for name, env_var in providers.items():
        present = check_env_var_present(env_var)
        status = "✅ CONFIGURED" if present else "❌ NOT CONFIGURED"
        print(f"{name:20} | {env_var:25} | {status}")
        if present:
            configured.append(name)
    
    print(f"\nConfigured Email Providers: {len(configured)}/{len(providers)}")
    if configured:
        print(f"Available: {', '.join(configured)}")
    else:
        print("⚠️ No email providers configured - fallback to stubs")
    
    return configured

def audit_persistence():
    """Check persistence/database configuration."""
    print("\n" + "="*80)
    print("PERSISTENCE LAYER")
    print("="*80)
    
    has_postgres = check_env_var_present("DATABASE_URL")
    has_memory_mode = os.getenv("AICMO_MEMORY_DB") == "1"
    persistence_mode = os.getenv("AICMO_PERSISTENCE_MODE", "unknown")
    
    print(f"PostgreSQL (DATABASE_URL): {'✅ CONFIGURED' if has_postgres else '❌ NOT CONFIGURED'}")
    print(f"Memory DB Mode: {'✅ ENABLED' if has_memory_mode else '❌ DISABLED'}")
    print(f"Persistence Mode: {persistence_mode}")
    
    if has_postgres:
        print("\n✅ Database persistence enabled")
    elif has_memory_mode:
        print("\n⚠️ Memory-only persistence (data lost on restart)")
    else:
        print("\n❌ No persistence configured")
    
    return has_postgres

def audit_backend_routing():
    """Check backend routing configuration."""
    print("\n" + "="*80)
    print("BACKEND ROUTING")
    print("="*80)
    
    backend_url = os.getenv("BACKEND_URL")
    aicmo_backend_url = os.getenv("AICMO_BACKEND_URL")
    
    if backend_url:
        print(f"BACKEND_URL: ✅ CONFIGURED")
        print(f"  Endpoint: {backend_url[:50]}..." if len(backend_url) > 50 else f"  Endpoint: {backend_url}")
    else:
        print(f"BACKEND_URL: ❌ NOT CONFIGURED")
    
    if aicmo_backend_url:
        print(f"AICMO_BACKEND_URL: ✅ CONFIGURED")
        print(f"  Endpoint: {aicmo_backend_url[:50]}..." if len(aicmo_backend_url) > 50 else f"  Endpoint: {aicmo_backend_url}")
    else:
        print(f"AICMO_BACKEND_URL: ❌ NOT CONFIGURED")
    
    if backend_url or aicmo_backend_url:
        print("\n✅ Backend HTTP routing enabled")
    else:
        print("\n❌ Backend routing not configured")
    
    return backend_url or aicmo_backend_url

def audit_feature_flags():
    """Check feature flag configurations."""
    print("\n" + "="*80)
    print("FEATURE FLAGS")
    print("="*80)
    
    flags = {
        "AICMO_USE_LLM": "LLM Generation",
        "AICMO_PERPLEXITY_ENABLED": "Perplexity Search",
        "AICMO_ENABLE_HUMANIZER": "Humanizer",
        "AICMO_STUB_MODE": "Stub Mode",
        "AICMO_ALLOW_STUBS": "Allow Stubs",
        "EXECUTION_ENABLED": "Campaign Execution",
    }
    
    for env_var, description in flags.items():
        value = os.getenv(env_var, "NOT SET")
        print(f"{description:30} | {env_var:25} | {value}")
    
    return flags

def main():
    """Run comprehensive provider audit."""
    print("\n" + "="*80)
    print("AICMO MULTI-PROVIDER SYSTEM AUDIT")
    print("Safe runtime availability check (no API calls, no secrets)")
    print("="*80)
    
    # Run audits
    llm_configured = audit_llm_providers()
    image_configured = audit_image_providers()
    search_configured = audit_search_providers()
    lead_configured = audit_lead_providers()
    email_configured = audit_email_providers()
    has_db = audit_persistence()
    has_backend = audit_backend_routing()
    audit_feature_flags()
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total_configured = (
        len(llm_configured) + len(image_configured) + len(search_configured)
        + len(lead_configured) + len(email_configured)
    )
    
    print(f"\nTotal Configured Providers: {total_configured}")
    print(f"  LLM: {len(llm_configured)}")
    print(f"  Image: {len(image_configured)}")
    print(f"  Search: {len(search_configured)}")
    print(f"  Lead: {len(lead_configured)}")
    print(f"  Email: {len(email_configured)}")
    
    print(f"\nPersistence: {'✅ Database' if has_db else '⚠️ Memory Only'}")
    print(f"Backend Routing: {'✅ Configured' if has_backend else '❌ Not Configured'}")
    
    print("\n" + "="*80)
    if total_configured == 0:
        print("⚠️ WARNING: No providers configured - system running in stub mode only")
    elif total_configured < 5:
        print("⚠️ PARTIAL: Limited provider coverage - some features may be stubbed")
    else:
        print("✅ GOOD: Multiple providers available - system has fallback options")
    print("="*80)

if __name__ == "__main__":
    main()
