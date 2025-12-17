# AICMO Multi-Provider Implementation Roadmap

**Baseline**: Current wiring audit complete  
**Goal**: Full multi-provider system (LLM, Search, Image, Lead, Email)  
**Timeline**: 20-25 hours estimated

---

## Phase 1: Critical Fix - CreativeService ProviderChain Integration [2h]

### Issue
Backend generation uses CreativeService which calls OpenAI SDK directly instead of ProviderChain, preventing multi-provider fallback.

### Current Architecture
```python
# backend/services/creative_service.py:130-150
response = self.client.chat.completions.create(
    model=self.config.model,  # gpt-4o-mini
    messages=[...],  # Direct OpenAI SDK
)
```

### Fix
```python
# Change from direct SDK to ProviderChain
from aicmo.llm.router import get_llm_client
from aicmo.llm.constants import LLMUseCase

def polish_section(self, template_text, brief, research, section_type):
    if not self.config.enable_polish:
        return template_text
    
    # Use ProviderChain instead of direct SDK
    chain = get_llm_client(
        use_case=LLMUseCase.CONTENT_POLISH,
        deep_research=False
    )
    
    prompt = self._build_polish_prompt(template_text, brief, research, section_type)
    success, result, provider = asyncio.run(
        chain.invoke("generate", prompt=prompt)
    )
    
    if success and result:
        return result if isinstance(result, str) else result.get("content", template_text)
    return template_text  # Fallback
```

### Files to Modify
- [backend/services/creative_service.py](backend/services/creative_service.py) (lines 60-160)

### Verification
```bash
# Test that CreativeService uses ProviderChain
grep -n "chain.invoke\|get_llm_client" backend/services/creative_service.py
# Should find: get_llm_client() call and chain.invoke() method
```

**Impact**: Unlocks multi-provider LLM for all 50+ backend generators

---

## Phase 2: Search Provider Integration [4h]

### Current State
- ❌ SERPAPI adapter: Missing
- ❌ Jina adapter: Missing
- ✅ Perplexity: Present (4 usages) but not integrated into pipeline

### Implementation

#### Step 1: Create SerpAPI Adapter
**File**: [aicmo/gateways/adapters/serpapi_searcher.py](aicmo/gateways/adapters/serpapi_searcher.py) (NEW)

```python
"""SerpAPI Web Search Adapter"""
import os
import logging
from typing import Dict, Any, Tuple
import aiohttp

log = logging.getLogger("serpapi_searcher")

class SerpAPISearcher:
    """Web search via SerpAPI"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        self.base_url = "https://serpapi.com/search"
    
    async def search(self, query: str, num_results: int = 5) -> Tuple[bool, Dict[str, Any], str]:
        """Execute web search"""
        if not self.api_key:
            return False, {}, "SERPAPI_API_KEY not configured"
        
        try:
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": num_results,
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("organic_results", [])
                        formatted = [
                            {"title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet")}
                            for r in results
                        ]
                        return True, {"results": formatted}, "serpapi"
                    else:
                        return False, {}, f"HTTP {resp.status}"
        except Exception as e:
            log.error(f"SerpAPI search failed: {e}")
            return False, {}, str(e)
```

#### Step 2: Create Jina Adapter
**File**: [aicmo/gateways/adapters/jina_scraper.py](aicmo/gateways/adapters/jina_scraper.py) (NEW)

```python
"""Jina Web Scraping Adapter"""
import os
import logging
from typing import Dict, Any, Tuple
import aiohttp

log = logging.getLogger("jina_scraper")

class JinaReader:
    """Web content reading via Jina.ai"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("JINA_API_KEY")
        self.base_url = "https://r.jina.ai"
    
    async def read_url(self, url: str) -> Tuple[bool, Dict[str, Any], str]:
        """Read webpage content"""
        if not self.api_key:
            return False, {}, "JINA_API_KEY not configured"
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
            
            async with aiohttp.ClientSession() as session:
                target_url = f"{self.base_url}/{url}"
                async with session.get(target_url, headers=headers, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return True, data, "jina"
                    else:
                        return False, {}, f"HTTP {resp.status}"
        except Exception as e:
            log.error(f"Jina read failed: {e}")
            return False, {}, str(e)
```

#### Step 3: Update Gateway Factory
**File**: [aicmo/gateways/factory.py](aicmo/gateways/factory.py) (new section ~line 450)

```python
def setup_search_providers(is_dry_run: bool = False):
    """Set up search provider chain (SerpAPI, Jina, fallback to Perplexity)"""
    try:
        from aicmo.gateways.adapters.serpapi_searcher import SerpAPISearcher
        from aicmo.gateways.adapters.jina_scraper import JinaReader
        from aicmo.gateways.adapters.noop_searcher import NoOpSearcher
        
        search_providers = []
        
        # Primary: SerpAPI
        if os.getenv("SERPAPI_API_KEY"):
            search_providers.append(
                ProviderWrapper(SerpAPISearcher(), "serpapi", is_dry_run)
            )
        
        # Secondary: Jina
        if os.getenv("JINA_API_KEY"):
            search_providers.append(
                ProviderWrapper(JinaReader(), "jina", is_dry_run)
            )
        
        # Fallback: No-op
        search_providers.append(
            ProviderWrapper(NoOpSearcher(), "noop_search", is_dry_run)
        )
        
        search_chain = ProviderChain(
            capability_name="web_search",
            providers=search_providers,
            is_dry_run=is_dry_run,
        )
        register_provider_chain(search_chain)
        logger.info(f"Registered ProviderChain: web_search ({len(search_providers)} providers)")
    except Exception as e:
        logger.error(f"Failed to setup web_search ProviderChain: {e}")
```

#### Step 4: Integrate into Research Service
**File**: [backend/services/research_service.py](backend/services/research_service.py) (modify)

```python
# Add search provider chain calls
from aicmo.gateways.factory import get_provider_chain

async def conduct_web_research(query: str) -> Dict[str, Any]:
    """Conduct web research using search provider chain"""
    chain = get_provider_chain("web_search")
    if chain:
        success, results, provider = await chain.invoke("search", query=query, num_results=10)
        if success:
            return {"results": results, "provider": provider}
    
    return {"results": [], "provider": "noop"}
```

### Files to Create
- [aicmo/gateways/adapters/serpapi_searcher.py](aicmo/gateways/adapters/serpapi_searcher.py)
- [aicmo/gateways/adapters/jina_scraper.py](aicmo/gateways/adapters/jina_scraper.py)
- [aicmo/gateways/adapters/noop_searcher.py](aicmo/gateways/adapters/noop_searcher.py)

### Files to Modify
- [aicmo/gateways/factory.py](aicmo/gateways/factory.py) - Add setup_search_providers()
- [backend/services/research_service.py](backend/services/research_service.py) - Integrate chain calls

### Environment Variables Required
- SERPAPI_API_KEY (optional, if using SerpAPI)
- JINA_API_KEY (optional, if using Jina)

---

## Phase 3: Image Generation Multi-Provider [6h]

### Current State
- ❌ Replicate: Only 1 usage
- ❌ Stability AI: 0 usages
- ❌ FAL: 0 usages
- ✅ OpenAI: Present but not in chain

### Implementation

#### Step 1: Create Image Adapters

**Replicate**: [aicmo/media/adapters/replicate_image_generator.py](aicmo/media/adapters/replicate_image_generator.py) (NEW)
**Stability AI**: [aicmo/media/adapters/stability_image_generator.py](aicmo/media/adapters/stability_image_generator.py) (NEW)
**FAL**: [aicmo/media/adapters/fal_image_generator.py](aicmo/media/adapters/fal_image_generator.py) (NEW)
**OpenAI**: Update [aicmo/media/adapters/openai_image_adapter.py](aicmo/media/adapters/openai_image_adapter.py)

#### Step 2: Create Image Provider Chain
**File**: [aicmo/gateways/factory.py](aicmo/gateways/factory.py) (new section ~line 480)

```python
def setup_image_providers(is_dry_run: bool = False):
    """Set up image generation provider chain"""
    try:
        from aicmo.media.adapters.replicate_image_generator import ReplicateGenerator
        from aicmo.media.adapters.stability_image_generator import StabilityGenerator
        from aicmo.media.adapters.fal_image_generator import FALGenerator
        from aicmo.media.adapters.openai_image_adapter import OpenAIImageGenerator
        
        image_providers = []
        
        # Priority 1: Replicate (fast, cheap)
        if os.getenv("REPLICATE_API_KEY"):
            image_providers.append(
                ProviderWrapper(ReplicateGenerator(), "replicate", is_dry_run)
            )
        
        # Priority 2: Stability AI
        if os.getenv("STABILITY_API_KEY"):
            image_providers.append(
                ProviderWrapper(StabilityGenerator(), "stability", is_dry_run)
            )
        
        # Priority 3: FAL
        if os.getenv("FAL_API_KEY"):
            image_providers.append(
                ProviderWrapper(FALGenerator(), "fal", is_dry_run)
            )
        
        # Fallback: OpenAI DALL-E
        if os.getenv("OPENAI_API_KEY"):
            image_providers.append(
                ProviderWrapper(OpenAIImageGenerator(), "openai_images", is_dry_run)
            )
        
        image_chain = ProviderChain(
            capability_name="image_generation",
            providers=image_providers,
            is_dry_run=is_dry_run,
        )
        register_provider_chain(image_chain)
        logger.info(f"Registered ProviderChain: image_generation ({len(image_providers)} providers)")
    except Exception as e:
        logger.error(f"Failed to setup image_generation ProviderChain: {e}")
```

#### Step 3: Integrate into Media Service
Create: [backend/services/media_service.py](backend/services/media_service.py) (NEW)

```python
from aicmo.gateways.factory import get_provider_chain

async def generate_image(prompt: str, style: str = None) -> Dict[str, Any]:
    """Generate image using provider chain"""
    chain = get_provider_chain("image_generation")
    if chain:
        success, result, provider = await chain.invoke(
            "generate", 
            prompt=prompt, 
            style=style
        )
        if success:
            return {"url": result, "provider": provider}
    
    return {"url": None, "provider": "noop"}
```

### Files to Create
- [aicmo/media/adapters/replicate_image_generator.py](aicmo/media/adapters/replicate_image_generator.py)
- [aicmo/media/adapters/stability_image_generator.py](aicmo/media/adapters/stability_image_generator.py)
- [aicmo/media/adapters/fal_image_generator.py](aicmo/media/adapters/fal_image_generator.py)
- [backend/services/media_service.py](backend/services/media_service.py)

### Files to Modify
- [aicmo/gateways/factory.py](aicmo/gateways/factory.py) - Add setup_image_providers()
- [aicmo/media/adapters/openai_image_adapter.py](aicmo/media/adapters/openai_image_adapter.py) - Ensure ProviderWrapper compatible

### Environment Variables Required
- REPLICATE_API_KEY (optional)
- STABILITY_API_KEY (optional)
- FAL_API_KEY (optional)
- OPENAI_API_KEY (fallback)

---

## Phase 4: Email Provider Completion [4h]

### Current State
- ✅ SMTP: Present
- ✅ Make Webhook: Present
- ❌ SendGrid: Missing
- ❌ Twilio: Missing
- ❌ Mailso: Missing

### Implementation

#### Step 1: Create SendGrid Adapter
**File**: [aicmo/gateways/adapters/sendgrid_mailer.py](aicmo/gateways/adapters/sendgrid_mailer.py) (NEW)

```python
"""SendGrid Email Sending Adapter"""
import os
import logging
from typing import Tuple, Dict, Any

log = logging.getLogger("sendgrid_mailer")

class SendGridMailer:
    """Send emails via SendGrid"""
    
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str = None,
    ) -> Tuple[bool, str, str]:
        """Send email via SendGrid"""
        if not self.api_key:
            return False, "", "SENDGRID_API_KEY not configured"
        
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            mail = Mail(
                from_email=from_email or os.getenv("SENDGRID_FROM_EMAIL", "noreply@aicmo.ai"),
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
            )
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(mail)
            
            if response.status_code in [200, 201, 202]:
                return True, response.headers.get("X-Message-Id", ""), "sendgrid"
            else:
                return False, "", f"HTTP {response.status_code}"
        except Exception as e:
            log.error(f"SendGrid send failed: {e}")
            return False, "", str(e)
```

#### Step 2: Create Twilio Adapter
**File**: [aicmo/gateways/adapters/twilio_messenger.py](aicmo/gateways/adapters/twilio_messenger.py) (NEW)

```python
"""Twilio SMS/Voice Adapter"""
import os
import logging
from typing import Tuple, Dict, Any

log = logging.getLogger("twilio_messenger")

class TwilioMessenger:
    """Send SMS via Twilio"""
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")
    
    async def send_sms(
        self,
        to_number: str,
        message: str,
    ) -> Tuple[bool, str, str]:
        """Send SMS via Twilio"""
        if not all([self.account_sid, self.auth_token, self.from_number]):
            return False, "", "Twilio credentials not configured"
        
        try:
            from twilio.rest import Client
            
            client = Client(self.account_sid, self.auth_token)
            msg = client.messages.create(
                from_=self.from_number,
                to=to_number,
                body=message,
            )
            
            return True, msg.sid, "twilio"
        except Exception as e:
            log.error(f"Twilio send failed: {e}")
            return False, "", str(e)
```

#### Step 3: Update Email Chain in Factory
**File**: [aicmo/gateways/factory.py](aicmo/gateways/factory.py) - Modify email_chain setup (~line 304)

```python
# Add to email chain setup
from aicmo.gateways.adapters.sendgrid_mailer import SendGridMailer
from aicmo.gateways.adapters.twilio_messenger import TwilioMessenger

email_providers = []

# Priority 1: SendGrid (most reliable for bulk)
if os.getenv("SENDGRID_API_KEY"):
    email_providers.append(
        ProviderWrapper(SendGridMailer(), "sendgrid", is_dry_run)
    )

# Priority 2: Twilio (SMS backup)
if os.getenv("TWILIO_ACCOUNT_SID"):
    email_providers.append(
        ProviderWrapper(TwilioMessenger(), "twilio", is_dry_run)
    )

# Priority 3: SMTP
if os.getenv("SMTP_HOST"):
    email_providers.append(
        ProviderWrapper(SMTPMailer(), "smtp", is_dry_run)
    )

# Fallback: Make Webhook
email_providers.append(
    ProviderWrapper(MakeWebhookSender(), "make_webhook", is_dry_run)
)

# Update chain with full provider list
```

### Files to Create
- [aicmo/gateways/adapters/sendgrid_mailer.py](aicmo/gateways/adapters/sendgrid_mailer.py)
- [aicmo/gateways/adapters/twilio_messenger.py](aicmo/gateways/adapters/twilio_messenger.py)

### Files to Modify
- [aicmo/gateways/factory.py](aicmo/gateways/factory.py) - Update email chain setup

### Environment Variables Required
- SENDGRID_API_KEY (optional)
- SENDGRID_FROM_EMAIL (optional, defaults to noreply@aicmo.ai)
- TWILIO_ACCOUNT_SID (optional)
- TWILIO_AUTH_TOKEN (optional)
- TWILIO_FROM_NUMBER (optional)

---

## Phase 5: Lead Enricher Completion [3h]

### Current State
- ✅ Apollo: 3 usages
- ✅ Dropcontact: 3 usages
- ❌ Hunter: Missing
- ❌ PeopleDataLabs: Missing

### Implementation

#### Step 1: Create Hunter Adapter
**File**: [aicmo/gateways/adapters/hunter_enricher.py](aicmo/gateways/adapters/hunter_enricher.py) (NEW)

```python
"""Hunter.io Lead Enrichment Adapter"""
import os
import logging
from typing import Tuple, Dict, Any

log = logging.getLogger("hunter_enricher")

class HunterEnricher:
    """Enrich lead data via Hunter.io"""
    
    def __init__(self):
        self.api_key = os.getenv("HUNTER_API_KEY")
        self.base_url = "https://api.hunter.io/v2"
    
    async def enrich_lead(
        self,
        email: str = None,
        domain: str = None,
        name: str = None,
    ) -> Tuple[bool, Dict[str, Any], str]:
        """Enrich lead information"""
        if not self.api_key:
            return False, {}, "HUNTER_API_KEY not configured"
        
        # Implementation similar to Apollo/Dropcontact pattern
        # ... API call logic ...
```

#### Step 2: Create PeopleDataLabs Adapter
**File**: [aicmo/gateways/adapters/pdl_enricher.py](aicmo/gateways/adapters/pdl_enricher.py) (NEW)

```python
"""PeopleDataLabs Lead Enrichment Adapter"""
import os
import logging
from typing import Tuple, Dict, Any

log = logging.getLogger("pdl_enricher")

class PDLEnricher:
    """Enrich lead data via PeopleDataLabs"""
    
    def __init__(self):
        self.api_key = os.getenv("PEOPLEDATALABS_API_KEY")
        self.base_url = "https://api.peopledatalabs.com/v5"
    
    async def enrich_lead(
        self,
        email: str = None,
        linkedin_url: str = None,
        name: str = None,
    ) -> Tuple[bool, Dict[str, Any], str]:
        """Enrich lead information"""
        if not self.api_key:
            return False, {}, "PEOPLEDATALABS_API_KEY not configured"
        
        # Implementation similar to Apollo/Dropcontact pattern
        # ... API call logic ...
```

#### Step 3: Update Enricher Chain in Factory
**File**: [aicmo/gateways/factory.py](aicmo/gateways/factory.py) - Modify enricher_chain setup (~line 377)

```python
# Add to enricher setup
from aicmo.gateways.adapters.hunter_enricher import HunterEnricher
from aicmo.gateways.adapters.pdl_enricher import PDLEnricher

enricher_providers = []

# Existing
if config.USE_APOLLO:
    enricher_providers.append(ProviderWrapper(ApolloEnricher(), "apollo", is_dry_run))
if config.USE_DROPCONTACT:
    enricher_providers.append(ProviderWrapper(DropcontactVerifier(), "dropcontact", is_dry_run))

# New
if os.getenv("HUNTER_API_KEY"):
    enricher_providers.append(ProviderWrapper(HunterEnricher(), "hunter", is_dry_run))
if os.getenv("PEOPLEDATALABS_API_KEY"):
    enricher_providers.append(ProviderWrapper(PDLEnricher(), "pdl", is_dry_run))
```

### Files to Create
- [aicmo/gateways/adapters/hunter_enricher.py](aicmo/gateways/adapters/hunter_enricher.py)
- [aicmo/gateways/adapters/pdl_enricher.py](aicmo/gateways/adapters/pdl_enricher.py)

### Files to Modify
- [aicmo/gateways/factory.py](aicmo/gateways/factory.py) - Update enricher chain

### Environment Variables Required
- HUNTER_API_KEY (optional)
- PEOPLEDATALABS_API_KEY (optional)

---

## Phase 6: Backend Routing Activation [2h]

### Current State
- Pattern defined in operator_v2.py but runners return mock results
- BACKEND_URL / AICMO_BACKEND_URL not configured

### Fix

#### Step 1: Configure Environment Variable
```bash
export BACKEND_URL="http://localhost:8000"  # Or production URL
# OR
export AICMO_BACKEND_URL="http://localhost:8000"
```

#### Step 2: Remove Mock Returns
**File**: [operator_v2.py](operator_v2.py) - Replace mock runners with real HTTP calls

```python
# Current (mock):
def run_intake_step(inputs):
    return {
        "status": "SUCCESS",
        "content": f"✅ Lead '{inputs['name']}' submitted to intake queue.",
        ...
    }

# Fixed (real HTTP):
def run_intake_step(inputs):
    backend_url = os.getenv("BACKEND_URL") or os.getenv("AICMO_BACKEND_URL")
    if backend_url:
        try:
            response = http_post_json(f"{backend_url}/intake/leads", inputs)
            return response
        except Exception as e:
            # Fallback to mock on error
            return {"status": "FAILED", "error": str(e)}
    # Fallback
    return {...}
```

#### Step 3: Test HTTP Routing
```bash
# Verify backend responds
curl -X POST http://localhost:8000/intake/leads \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "email": "test@example.com"}'
```

### Files to Modify
- [operator_v2.py](operator_v2.py) - Replace mock returns with HTTP calls (all 11 runner functions)

### Environment Variables Required
- BACKEND_URL or AICMO_BACKEND_URL

---

## Implementation Checklist

- [ ] Phase 1: Fix CreativeService ProviderChain integration
  - [ ] Update [backend/services/creative_service.py](backend/services/creative_service.py)
  - [ ] Test multi-provider fallback
  - [ ] Verify all generators use new path

- [ ] Phase 2: Search Provider Integration
  - [ ] Create [aicmo/gateways/adapters/serpapi_searcher.py](aicmo/gateways/adapters/serpapi_searcher.py)
  - [ ] Create [aicmo/gateways/adapters/jina_scraper.py](aicmo/gateways/adapters/jina_scraper.py)
  - [ ] Update [aicmo/gateways/factory.py](aicmo/gateways/factory.py) with search chain
  - [ ] Integrate into research service
  - [ ] Test search provider chain

- [ ] Phase 3: Image Generation Multi-Provider
  - [ ] Create Replicate, Stability AI, FAL adapters
  - [ ] Create media service
  - [ ] Update factory with image chain
  - [ ] Test image generation chain

- [ ] Phase 4: Email Provider Completion
  - [ ] Create SendGrid adapter
  - [ ] Create Twilio adapter
  - [ ] Update email chain in factory
  - [ ] Test email fallback

- [ ] Phase 5: Lead Enricher Completion
  - [ ] Create Hunter adapter
  - [ ] Create PeopleDataLabs adapter
  - [ ] Update enricher chain
  - [ ] Test lead enrichment fallback

- [ ] Phase 6: Backend Routing Activation
  - [ ] Configure BACKEND_URL environment variable
  - [ ] Update operator_v2.py runners
  - [ ] Test HTTP routing
  - [ ] Verify mock fallback still works

## Success Criteria

**After All Phases Complete**:
- ✅ Multi-provider system fully wired
- ✅ All 7 categories implemented (LLM, Search, Image, Lead, Email, Persistence, Routing)
- ✅ Each category has 2-4 providers with fallback
- ✅ All environment variables used actively
- ✅ Smoke tests show configured providers
- ✅ Runtime provider checks pass
- ✅ No single point of failure for critical operations

---

**Next Steps**: Start with Phase 1 (Critical Fix) to unblock multi-provider LLM system.
