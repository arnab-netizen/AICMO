# Phase 4: Quick Reference — Lead Qualification

## Setup

```python
from aicmo.cam.engine import (
    LeadQualifier,
    QualificationRules,
    EmailQualifier,
    IntentDetector
)

# Create rules
rules = QualificationRules(icp_fit_threshold=0.70)

# Create components
email_qualifier = EmailQualifier(rules)
intent_detector = IntentDetector()
lead_qualifier = LeadQualifier(rules, email_qualifier, intent_detector)
```

## Email Validation

```python
# Check email quality across 5 dimensions:
is_valid, reason = email_qualifier.check_email_quality("john@company.com")
# is_valid: bool
# reason: None | RejectionReason

# Specific checks:
email_qualifier.is_valid_format("user@domain.com")      # RFC 5322 validation
email_qualifier.is_spam_bot("noreply@domain.com")       # Spam/bot keywords
email_qualifier.is_role_account("support@domain.com")   # Role accounts
email_qualifier.is_free_email("user@gmail.com")         # Free providers
email_qualifier.is_competitor_domain("user@rival.com")  # Blocklist check
```

## Intent Detection

```python
# Detect buying signals (2+ required):
has_intent = intent_detector.detect_intent(lead)
# True if 2+ signals detected

# Get normalized intent score (0.0-1.0):
score = intent_detector.get_intent_score(lead)
# 0.0 = no signals, 1.0 = all 6 signals present

# Signals tracked:
# - recent_job_change
# - company_funded_recently
# - company_hiring
# - recent_activity
# - is_decision_maker
# - has_budget_authority
```

## Single Lead Qualification

```python
# Qualify one lead:
status, reason, reasoning = lead_qualifier.auto_qualify_lead(lead)

# Returns:
# status: QualificationStatus (QUALIFIED | REJECTED | MANUAL_REVIEW)
# reason: RejectionReason (if rejected) or None
# reasoning: str (human-readable explanation)

# Rejection reasons:
# - LOW_ICP_FIT: ICP score below threshold
# - INVALID_EMAIL: Email format invalid
# - SPAM_BOT: Spam/bot keywords detected
# - ROLE_ACCOUNT: Generic role account
# - COMPETITOR: Competitor domain
# - MULTIPLE_REASONS: Multiple issues
```

## Batch Qualification

```python
# Qualify all enriched leads in campaign:
metrics = lead_qualifier.batch_qualify_leads(
    db=session,
    campaign_id=123,
    max_leads=1000  # Optional limit
)

# Metrics returned:
print(metrics.processed_count)      # Leads evaluated
print(metrics.qualified_count)      # Auto-approved
print(metrics.rejected_count)       # Filtered out
print(metrics.manual_review_count)  # Needs review
print(metrics.qualified_ratio)      # Percent qualified

# Database updates:
# - status: ENRICHED → QUALIFIED/REJECTED
# - notes: Adds qualification reasoning
```

## Customization

```python
# Custom rules:
rules = QualificationRules(
    icp_fit_threshold=0.80,  # Higher threshold
    block_competitor_domains=["acme.com", "evil.com"],
    block_role_accounts=["info", "support", "sales"],
    block_free_email_domains=True,
    free_email_domains=["gmail.com", "yahoo.com"]
)
```

## Common Patterns

### Validate Before Adding to Campaign
```python
is_valid, reason = email_qualifier.check_email_quality(email)
if not is_valid:
    print(f"Email rejected: {reason.value}")
```

### Filter High-Intent Leads
```python
if intent_detector.detect_intent(lead):
    # Lead has 2+ buying signals
    # Schedule aggressive outreach
```

### Decision Maker Targeting
```python
if lead.enrichment_data.get("is_decision_maker"):
    # Prioritize for direct outreach
```

### Manual Review Queue
```python
if status == QualificationStatus.MANUAL_REVIEW:
    # Route to sales team for review
    # Log reasoning for analysis
```

## Testing

```bash
# Run tests
pytest tests/test_phase4_lead_qualification.py -v

# Check coverage
pytest tests/test_phase4_lead_qualification.py --cov=aicmo.cam.engine.lead_qualifier
```

## Performance

- Email validation: ~1ms per lead
- Intent detection: ~0.5ms per lead
- Single qualification: ~2ms per lead
- Batch (1000 leads): ~2 seconds

## Integration

Phase 2 (Harvest) → Phase 3 (Score) → **Phase 4 (Qualify)** → Phase 5 (Route)

Input: Enriched + Scored leads  
Output: QUALIFIED/REJECTED/MANUAL_REVIEW status

