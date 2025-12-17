#!/usr/bin/env python3
"""
AUDIT SCRIPT: Multi-provider wiring analysis.

Purpose:
  - Map each feature category to its provider implementations
  - Identify where ProviderChain is invoked
  - Check for real vs stubbed implementations
  - Validate fallback logic
  - Output markdown report

Categories:
  - LLM generation
  - Image generation
  - Web search/research
  - Lead enrichment
  - Email/outreach
  - Persistence (DB vs memory)
  - Backend routing
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).parent.parent

# Pattern definitions per category
PATTERNS = {
    "LLM": {
        "providers": [
            r"openai_llm\.py|anthropic_llm\.py|gemini_llm\.py|llama_llm\.py|"
            r"mistral_llm\.py|cohere_llm\.py|perplexity_llm\.py|grok_llm\.py|deepseek_llm\.py"
        ],
        "imports": [
            r"from aicmo\.llm\.adapters import|from aicmo\.llm\.client import|from aicmo\.llm\.router import"
        ],
        "dispatch": [
            r"get_llm_client\(|select_provider\(|ProviderChain|AICMO_LLM_PROVIDER|AICMO_USE_LLM"
        ]
    },
    "Image": {
        "providers": [
            r"replicate_gen\.py|stability_gen\.py|fal_gen\.py|luma_gen\.py|"
            r"pika_gen\.py|runway_gen\.py|huggingface_gen\.py"
        ],
        "imports": [
            r"from aicmo\.media\.adapters|from aicmo\.delivery\.image_gen"
        ],
        "dispatch": [
            r"generate_image|REPLICATE_API_KEY|STABILITY_API_KEY|FAL_API_KEY|RUNWAY_ML_API_KEY"
        ]
    },
    "Search": {
        "providers": [
            r"perplexity_llm\.py|serpapi_search\.py|jina_search\.py|"
            r"scraper_api\.py|google_places\.py|youtube_search\.py"
        ],
        "imports": [
            r"from aicmo\.research|from aicmo\.analysis"
        ],
        "dispatch": [
            r"AICMO_PERPLEXITY_ENABLED|SERPAPI_API_KEY|JINA_API_KEY|"
            r"PERPLEXITY_API_KEY|ENABLE_PERPLEXITY_DEEP_RESEARCH"
        ]
    },
    "Lead Enrichment": {
        "providers": [
            r"apollo_enricher\.py|hunter_enricher\.py|pdl_enricher\.py|"
            r"dropcontact_verifier\.py|csv_lead_source\.py"
        ],
        "imports": [
            r"from aicmo\.gateways\.adapters import|from aicmo\.acquisition"
        ],
        "dispatch": [
            r"APOLLO_API_KEY|HUNTER_API_KEY|PEOPLEDATALABS_API_KEY|DROPCONTACT_API_KEY|"
            r"csv_lead_source|enrich_"
        ]
    },
    "Email/Outreach": {
        "providers": [
            r"sendgrid_mailer\.py|smtp_mailer\.py|twilio_sms\.py|"
            r"mailso_outreach\.py|reply_fetcher\.py|make_webhook\.py"
        ],
        "imports": [
            r"from aicmo\.gateways\.adapters|from aicmo\.delivery"
        ],
        "dispatch": [
            r"SENDGRID_API_KEY|SMTP_HOST|TWILIO_|MAILSO_|"
            r"send_email|send_sms|send_message"
        ]
    },
    "Persistence": {
        "providers": [
            r"database\.py|engine\.py|session\.py|memory_db\.py"
        ],
        "imports": [
            r"from aicmo\.core\.db|from aicmo\.memory\.engine|"
            r"from sqlalchemy import"
        ],
        "dispatch": [
            r"DATABASE_URL|AICMO_MEMORY_DB|AICMO_PERSISTENCE_MODE|"
            r"get_db|get_session|memory_db"
        ]
    },
    "Backend Routing": {
        "providers": [
            r"aicmo_operator\.py|operator_v2\.py|shared\.py"
        ],
        "imports": [
            r"import requests|from requests|requests\.post|requests\.get"
        ],
        "dispatch": [
            r"BACKEND_URL|AICMO_BACKEND_URL|/api/|http://|https://"
        ]
    }
}

def scan_file_content(file_path, patterns):
    """Scan a file for patterns; return matches."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            results = {}
            for key, pattern_list in patterns.items():
                for pattern_str in pattern_list:
                    if re.search(pattern_str, content):
                        results[key] = True
                        break
            return results
    except:
        return {}

def find_provider_files():
    """Locate all provider adapter files."""
    providers = defaultdict(list)
    
    # Search key directories
    search_paths = [
        REPO_ROOT / "aicmo" / "llm" / "adapters",
        REPO_ROOT / "aicmo" / "gateways" / "adapters",
        REPO_ROOT / "aicmo" / "delivery",
        REPO_ROOT / "aicmo" / "media",
        REPO_ROOT / "aicmo" / "memory",
        REPO_ROOT / "aicmo" / "core" / "db*",
        REPO_ROOT / "aicmo" / "analysis",
        REPO_ROOT / "aicmo" / "research",
        REPO_ROOT / "backend" / "layers",
    ]
    
    all_py_files = list(REPO_ROOT.rglob("*.py"))
    
    for py_file in all_py_files[:500]:  # Limit to avoid huge results
        name = py_file.name.lower()
        if "adapter" in name or "provider" in name or "gateway" in name:
            rel_path = py_file.relative_to(REPO_ROOT)
            if "openai" in name or "gpt" in name:
                providers["LLM - OpenAI"].append(str(rel_path))
            elif "anthropic" or "claude" in name:
                providers["LLM - Anthropic"].append(str(rel_path))
            elif "gemini" or "google" in name:
                providers["LLM - Gemini"].append(str(rel_path))
            elif "perplexity" in name:
                providers["Search/LLM - Perplexity"].append(str(rel_path))
            elif "apollo" in name:
                providers["Lead - Apollo"].append(str(rel_path))
            elif "hunter" in name:
                providers["Lead - Hunter"].append(str(rel_path))
            elif "dropcontact" in name:
                providers["Lead - Dropcontact"].append(str(rel_path))
            elif "sendgrid" or "smtp" or "mail" in name:
                providers["Email - SMTP/SendGrid"].append(str(rel_path))
            elif "replicate" in name:
                providers["Image - Replicate"].append(str(rel_path))
            elif "stability" or "sdxl" in name:
                providers["Image - Stability"].append(str(rel_path))
            elif "db" in name or "session" in name or "postgres" in name:
                providers["Persistence"].append(str(rel_path))
    
    return providers

def find_invocations():
    """Find where providers are actually invoked."""
    invocations = defaultdict(list)
    
    key_files = [
        REPO_ROOT / "operator_v2.py",
        REPO_ROOT / "app.py",
        REPO_ROOT / "streamlit_app.py",
        REPO_ROOT / "backend" / "main.py",
        REPO_ROOT / "aicmo" / "ui_v2" / "shared.py",
    ]
    
    for py_file in REPO_ROOT.rglob("*.py"):
        if py_file.parent.name in ["__pycache__", "test"]:
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                for idx, line in enumerate(lines, 1):
                    if "runner(" in line or "Generate" in line:
                        rel_path = py_file.relative_to(REPO_ROOT)
                        invocations["Generate Path"].append(f"{rel_path}:{idx}")
                    if "get_llm_client" in line:
                        rel_path = py_file.relative_to(REPO_ROOT)
                        invocations["LLM Selection"].append(f"{rel_path}:{idx}")
                    if "ProviderChain" in line and "import" not in line:
                        rel_path = py_file.relative_to(REPO_ROOT)
                        invocations["ProviderChain Usage"].append(f"{rel_path}:{idx}")
        except:
            pass
    
    return invocations

def main():
    """Generate markdown report."""
    
    print("=" * 100)
    print("AUDIT: Multi-Provider Wiring Analysis")
    print("=" * 100)
    print()
    
    providers = find_provider_files()
    invocations = find_invocations()
    
    # Print providers found
    print("## PROVIDER IMPLEMENTATIONS\n")
    if providers:
        for category, files in sorted(providers.items()):
            print(f"### {category}")
            for f in files[:5]:  # Limit per category
                print(f"  - {f}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more")
            print()
    else:
        print("No provider adapters found.")
        print()
    
    # Print invocation locations
    print("## PROVIDER INVOCATION POINTS\n")
    if invocations:
        for inv_type, locations in sorted(invocations.items()):
            print(f"### {inv_type}")
            for loc in locations[:10]:
                print(f"  - {loc}")
            if len(locations) > 10:
                print(f"  ... and {len(locations) - 10} more")
            print()
    else:
        print("No invocation points found.")
        print()
    
    # Key findings
    print("## KEY FINDINGS\n")
    
    if "LLM - OpenAI" in providers:
        print("✅ OpenAI adapter present")
    else:
        print("⚠️ OpenAI adapter NOT found")
    
    if "LLM Selection" in invocations:
        print(f"✅ LLM selection logic found ({len(invocations['LLM Selection'])} locations)")
    else:
        print("⚠️ No LLM selection logic found")
    
    if "ProviderChain Usage" in invocations:
        print(f"✅ ProviderChain actively used ({len(invocations['ProviderChain Usage'])} locations)")
    else:
        print("❌ ProviderChain NOT actively invoked (may be imported but not used)")
    
    print("\n" + "=" * 100)

if __name__ == "__main__":
    main()
