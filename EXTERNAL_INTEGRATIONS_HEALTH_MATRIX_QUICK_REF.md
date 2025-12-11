# External Integrations Health Matrix - Quick Reference

## What It Does

The External Integrations Health Matrix automatically checks the status of 12 external services used by AICMO:

- **Detects** if each service is configured (env vars present)
- **Checks** if each service is reachable (safe format validation)
- **Marks** if each service is CRITICAL or OPTIONAL
- **Reports** status in markdown with clear warnings

---

## The 12 Services Checked

### CRITICAL (Must be available)
1. **OpenAI LLM** - Main AI provider for content generation

### OPTIONAL (Nice to have)
2. **Apollo Lead Enricher** - Lead data enrichment
3. **Dropcontact Email Verifier** - Email validation
4. **Airtable CRM Sync** - Contact management
5. **Email Gateway** - Email sending
6. **IMAP Reply Fetcher** - Email reply reading
7. **LinkedIn Social Posting** - Social media
8. **Twitter/X Social Posting** - Social media
9. **Make.com Webhook** - Workflow automation
10. **SDXL Media Generation** - Image generation
11. **Figma API** - Design generation
12. **Runway ML Video Generation** - Video generation

---

## How to Use

### View in Reports
```bash
# Run self-test
python -m aicmo.self_test.cli

# Check report
cat self_test_artifacts/AICMO_SELF_TEST_REPORT.md
# Look for "## External Integrations Health Matrix" section
```

### What to Look For

**Configuration Status (❌ = Not Configured)**
- ❌ Service is not configured (env vars not set)
- ✅ Service is configured

**Reachability Status**
- UNCHECKED = Configured but not checked yet
- ✅ REACHABLE = Configuration looks valid
- ❌ UNREACHABLE = Configuration invalid/format error

**Criticality**
- CRITICAL = Must be available for core operations
- OPTIONAL = Nice to have but not required

### Example Report Output

```markdown
## External Integrations Health Matrix

| Service | Configured | Status | Criticality |
|---------|-----------|--------|-------------|
| OpenAI LLM (GPT-4, etc.) | ❌ | NOT CONFIGURED | CRITICAL |
| Apollo Lead Enricher | ❌ | NOT CONFIGURED | OPTIONAL |
| ...more services... |

**Summary:** 0/12 configured, 0 reachable, 1 critical

⚠️ **Warning:** The following CRITICAL services are not configured:
- **OpenAI LLM (GPT-4, etc.)** - Set `OPENAI_API_KEY` to enable
```

---

## Setting Up Services

### To Enable OpenAI (CRITICAL)
```bash
export OPENAI_API_KEY="sk-..."
```

### To Enable Apollo
```bash
export APOLLO_API_KEY="key_..."
```

### To Enable Dropcontact
```bash
export DROPCONTACT_API_KEY="dctoken_..."
```

### To Enable Airtable
```bash
export AIRTABLE_API_KEY="pat..."
export AIRTABLE_BASE_ID="appXXXX"
```

### To Enable Email
```bash
# Gmail
export GMAIL_CREDENTIALS_PATH="/path/to/credentials.json"
export GMAIL_TOKEN_PATH="/path/to/token.json"

# Or SMTP
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="your@email.com"
export SMTP_PASSWORD="password"
export SMTP_FROM_EMAIL="sender@email.com"
```

### To Enable IMAP (Reply Fetcher)
```bash
export IMAP_HOST="imap.gmail.com"
export IMAP_USER="your@email.com"
export IMAP_PASSWORD="password"
```

### To Enable LinkedIn
```bash
export LINKEDIN_ACCESS_TOKEN="your_token"
export USE_REAL_SOCIAL_GATEWAYS="true"
```

### To Enable Twitter
```bash
export TWITTER_API_KEY="your_key"
export TWITTER_API_SECRET="your_secret"
export TWITTER_ACCESS_TOKEN="your_token"
export TWITTER_ACCESS_SECRET="your_token_secret"
export USE_REAL_SOCIAL_GATEWAYS="true"
```

### To Enable Make.com
```bash
export MAKE_WEBHOOK_URL="https://..."
```

### To Enable SDXL
```bash
export SDXL_API_KEY="your_key"
```

### To Enable Figma
```bash
export FIGMA_API_TOKEN="your_token"
```

### To Enable Runway ML
```bash
export RUNWAY_ML_API_KEY="your_key"
```

---

## Understanding Status Values

### For "Configured" Column
- **❌** = Service not configured (env vars not set)
- **✅** = Service is configured (env vars present)

### For "Status" Column
- **NOT CONFIGURED** = Env vars not set, skipped checks
- **UNCHECKED** = Configured but we didn't verify (safe mode)
- **✅ REACHABLE** = Configuration looks valid
- **❌ UNREACHABLE** = Configuration format invalid

### For "Criticality" Column
- **CRITICAL** = Required for core AICMO operations
- **OPTIONAL** = Extra features, fallback available

---

## Troubleshooting

### Q: Why is OpenAI showing as CRITICAL?
**A:** OpenAI is the main LLM provider used for content generation. If it's not configured, AICMO will use fallback modes but may have reduced quality.

### Q: Can I ignore OPTIONAL services?
**A:** Yes! OPTIONAL services enhance functionality but aren't required. AICMO has fallback/no-op modes for all optional services.

### Q: How often is the matrix checked?
**A:** The matrix is generated fresh every time you run:
```bash
python -m aicmo.self_test.cli
```

### Q: Are there actual API calls made?
**A:** No! The health checks are safe and minimal:
- Just check if env vars are present
- Validate format of API keys
- No actual calls to external APIs
- Can't fail or consume API quota

### Q: Why does my service show UNCHECKED instead of REACHABLE?
**A:** Your configuration is detected, but we haven't verified format yet. This is safe default behavior.

---

## CLI Integration

### Standard Run (includes health check)
```bash
python -m aicmo.self_test.cli
```

### Quick Mode (default)
```bash
python -m aicmo.self_test.cli  # Includes health check
```

### With Other Flags
```bash
python -m aicmo.self_test.cli --deterministic  # Deterministic + health check
python -m aicmo.self_test.cli --full  # Full test + health check
python -m aicmo.self_test.cli -v  # Verbose + health check
```

---

## Report Section Location

In the markdown report, look for:

```markdown
# AICMO System Health Report

...summary section...

## Performance & Flakiness
...performance data...

## External Integrations Health Matrix  ← YOU ARE HERE
...service table and warnings...

## Semantic Alignment vs Brief
...alignment checks...
```

---

## For Developers

### Access Health Data Programmatically

```python
from aicmo.self_test.orchestrator import SelfTestOrchestrator

orchestrator = SelfTestOrchestrator()
result = orchestrator.run_self_test()

# Access external services
for service in result.external_services:
    print(f"{service.name}: {service.status_display}")
    if service.critical and not service.configured:
        print(f"  ⚠️ Critical service needs configuration!")
```

### Check Specific Service

```python
openai = [s for s in result.external_services if "OpenAI" in s.name][0]

if openai.configured:
    print("✅ OpenAI is configured")
else:
    print("❌ OpenAI is not configured")
    print(f"   Set: {openai.details.get('env_vars_present')}")
```

### Get Summary Stats

```python
configured = sum(1 for s in result.external_services if s.configured)
critical = sum(1 for s in result.external_services if s.critical)
total = len(result.external_services)

print(f"Configured: {configured}/{total}")
print(f"Critical: {critical}")
```

---

## Files to Know

- **Models:** [aicmo/self_test/models.py](aicmo/self_test/models.py) - `ExternalServiceStatus` class
- **Health Checks:** [aicmo/self_test/external_integrations_health.py](aicmo/self_test/external_integrations_health.py) - All 12 service checks
- **Orchestrator:** [aicmo/self_test/orchestrator.py](aicmo/self_test/orchestrator.py) - Integration into test engine
- **Reports:** [aicmo/self_test/reporting.py](aicmo/self_test/reporting.py) - Markdown generation
- **Tests:** [tests/test_self_test_engine.py](tests/test_self_test_engine.py#L590) - `TestExternalIntegrationsHealth`

---

## Summary

The External Integrations Health Matrix provides:

✅ **Clear visibility** into which services are available  
✅ **No crashes** - all checks are safe  
✅ **Production ready** - supports all major integrations  
✅ **Easy setup** - guides in reports for each service  
✅ **Automatic detection** - runs on every test  
✅ **Honest reporting** - shows exactly what's available  

The system won't silently ignore unavailable services - it tells you exactly what's missing and what env vars to set.
