# Phase B: Outreach Channels — Implementation Plan

**Objective:** Implement multi-channel outreach coordination (Email + LinkedIn + Contact Forms)  
**Timeline:** 2-3 days  
**Expected Effort:** ~500 lines of code + 20+ tests  
**Status:** Ready to implement

---

## Overview

Phase B builds on Phase A's CRM foundation to add **multi-channel outreach capabilities**:

1. **Email Channel** — Enhanced email sending with templates & tracking
2. **LinkedIn Channel** — LinkedIn messaging with connection requests
3. **Contact Form Channel** — Auto-fill & submit web contact forms
4. **Channel Sequencing** — Intelligent fallback (if email fails, try LinkedIn)
5. **Rate Limiting** — Per-channel rate limits + global daily caps
6. **Templates** — Channel-specific message templates

---

## Implementation Breakdown

### Step 1: Channel Domain Models (`aicmo/cam/domain.py`)

**New Enums:**
- `ChannelType`: EMAIL, LINKEDIN, CONTACT_FORM, PHONE
- `OutreachStatus`: PENDING, SENT, DELIVERED, REPLIED, BOUNCED, FAILED
- `LinkedInConnectionStatus`: NOT_CONNECTED, CONNECTED, CONNECTION_REQUESTED

**New Classes:**
- `OutreachMessage`: message content + metadata
- `ChannelConfig`: channel-specific settings (rate limit, retry policy)
- `SequenceConfig`: multi-channel outreach sequence definition

### Step 2: Database Models (`aicmo/cam/db_models.py`)

**New Tables:**
- `ChannelConfig` — channel-specific settings per campaign
- `OutreachMessage` — message templates + content
- `SequenceConfig` — sequence definitions
- `SequenceStep` — individual steps in sequence

**Schema Extensions:**
- `OutreachAttemptDB` — add channel_type, retry_count, next_retry_at
- `LeadDB` — add linkedin_status, contact_form_url

### Step 3: Outreach Services (`aicmo/cam/outreach/`)

**New Directory Structure:**
```
aicmo/cam/outreach/
  __init__.py
  email_outreach.py          (EmailOutreachService)
  linkedin_outreach.py       (LinkedInOutreachService)
  contact_form_outreach.py   (ContactFormOutreachService)
  sequencer.py               (ChannelSequencer)
  templates.py               (MessageTemplateManager)
```

**Services:**
1. `EmailOutreachService.send()` — Send email with tracking
2. `LinkedInOutreachService.send_message()` — Send LinkedIn DM
3. `LinkedInOutreachService.send_connection_request()` — Send connection request
4. `ContactFormOutreachService.submit()` — Auto-fill & submit forms
5. `ChannelSequencer.execute_sequence()` — Run multi-channel sequence

### Step 4: Integration (`aicmo/cam/auto.py`, `aicmo/cam/orchestrator.py`)

**Modified:** Outreach execution to use new channel services

**Before:** `run_auto_email_batch()` only sends emails
**After:** Uses sequencer to try multiple channels

### Step 5: Operator API (`aicmo/operator_services.py`)

**New Functions:**
- `get_channel_config(campaign_id) → Dict`
- `update_channel_config(campaign_id, config) → Dict`
- `send_outreach_message(campaign_id, lead_id, channels) → Dict`
- `get_outreach_history(lead_id) → List[Dict]`
- `get_channel_metrics(campaign_id) → Dict`

### Step 6: Test Suite (`tests/test_phase_b_outreach.py`)

**Test Coverage (20+ tests):**
- Email service tests (5 tests)
- LinkedIn service tests (5 tests)
- Contact form service tests (5 tests)
- Channel sequencer tests (5 tests)
- Integration tests (3 tests)
- Edge cases (2 tests)

---

## Code Architecture

### Service Pattern

All outreach services follow same interface:

```python
class OutreachServiceBase:
    def send(self, lead: Lead, message: str, config: ChannelConfig) → Dict:
        """
        Send outreach message via channel.
        
        Returns:
            {
                "success": bool,
                "channel": str,
                "status": OutreachStatus,
                "message_id": str,
                "error": str (if failed)
            }
        """
        pass
```

### Sequencer Pattern

```python
class ChannelSequencer:
    def execute_sequence(
        self, 
        lead: Lead,
        sequence: SequenceConfig,
        db: Session
    ) → Dict:
        """
        Execute multi-channel sequence.
        
        Logic:
        1. Try channel 1 (email)
        2. If fails, try channel 2 (LinkedIn)
        3. If fails, try channel 3 (form)
        4. Record all attempts
        
        Returns: {"success": bool, "attempts": [...]}
        """
        pass
```

---

## Configuration

### Channel Sequencer Config Example

```python
sequence_config = SequenceConfig(
    name="Standard 3-Channel",
    steps=[
        SequenceStep(
            order=1,
            channel=ChannelType.EMAIL,
            retry_count=2,
            retry_delay_hours=24,
            message_template="email_intro"
        ),
        SequenceStep(
            order=2,
            channel=ChannelType.LINKEDIN,
            condition="if email_failed",
            message_template="linkedin_intro"
        ),
        SequenceStep(
            order=3,
            channel=ChannelType.CONTACT_FORM,
            condition="if linkedin_failed",
            message_template="form_submission"
        ),
    ]
)
```

---

## File Sizes Estimate

| File | Lines | Type |
|------|-------|------|
| outreach/email_outreach.py | 120 | New |
| outreach/linkedin_outreach.py | 140 | New |
| outreach/contact_form_outreach.py | 100 | New |
| outreach/sequencer.py | 180 | New |
| outreach/templates.py | 80 | New |
| domain.py (extensions) | 50 | Modified |
| db_models.py (extensions) | 80 | Modified |
| auto.py (integration) | 30 | Modified |
| operator_services.py (API) | 120 | Modified |
| test_phase_b_outreach.py | 450 | New |
| **Total** | **~1,350 lines** | — |

---

## Testing Strategy

### Unit Tests (15 tests)
- Email sending logic
- LinkedIn API integration
- Contact form submission
- Template rendering
- Rate limiting

### Integration Tests (5 tests)
- End-to-end sequencing
- Database persistence
- Orchestrator wiring
- Error handling

### Edge Cases (3 tests)
- Retry logic
- Channel failures
- Rate limit exceeded

---

## Success Criteria

✅ All 20+ tests passing  
✅ No regressions in Phase A tests (22 still passing)  
✅ Email channel fully functional  
✅ LinkedIn channel integrated (with fallback)  
✅ Contact form channel functional  
✅ Channel sequencer working (multi-channel fallback)  
✅ Rate limiting enforced per channel  
✅ Metrics tracked for each channel  

---

## Dependencies

### Existing (Already in codebase)
- SQLAlchemy ORM
- Pydantic domain models
- Existing Outreach services (partial)

### New Libraries Needed
- `linkedin-api` (LinkedIn messaging)
- `selenium` (Contact form automation)
- These should already be available in requirements

### APIs
- Email: SMTP (uses existing gateway pattern)
- LinkedIn: LinkedIn API v2 (needs auth token)
- Contact Forms: Browser automation or direct HTTP

---

## Next Phase Hint

After Phase B completion, Phase C (Follow-Up Sequencer) will:
- Add conditional logic to sequences
- Implement waiting between attempts
- Add smart branching based on replies
- Create sequence templates

---

## Rollback Plan

If Phase B has issues:
1. All changes are additive (existing code unchanged)
2. New services can be disabled via config
3. Revert to Phase A via git branch
4. No database migrations needed (new tables only)

---

**Ready to implement Phase B: Outreach Channels**

Start with Step 1: Create Channel Domain Models
