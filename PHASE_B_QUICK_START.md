# PHASE B: OUTREACH CHANNELS — QUICK REFERENCE

**Status**: ✅ Complete | **Lines**: ~1,300 | **Components**: 5 services + sequencer + API

---

## 🎯 WHAT PHASE B DOES

Multi-channel outreach orchestration with intelligent fallback:
- **Primary**: Email
- **Fallback 1**: LinkedIn
- **Fallback 2**: Contact Form

Intelligently routes to next channel if current fails.

---

## 📦 WHAT'S INCLUDED

### Services (5 implementations)
1. **EmailOutreachService** - Send emails, track bounces
2. **LinkedInOutreachService** - DM + connection requests
3. **ContactFormOutreachService** - Auto-submit forms
4. **ChannelSequencer** - Orchestrate Email → LinkedIn → Form
5. **RateLimiter** - Per-channel/per-lead limits

### Database (3 tables + extensions)
- `ChannelConfigDB` - Channel settings
- `SequenceConfigDB` - Sequence definitions
- `OutreachMessageDB` - Message history
- Extensions: LeadDB, OutreachAttemptDB

### API (5 operator functions)
- `send_outreach_message()` - Trigger multi-channel send
- `get_channel_config()` - Retrieve settings
- `update_channel_config()` - Update settings
- `get_outreach_history()` - Audit trail
- `get_channel_metrics()` - Performance stats

### Tests (25+ cases)
- Domain model tests
- Service tests (Email, LinkedIn, Form)
- Sequencer tests
- Rate limiter tests
- Integration tests
- Edge case tests

---

## 🚀 BASIC USAGE

```python
from aicmo.cam.outreach.sequencer import ChannelSequencer
from aicmo.cam.domain import OutreachMessage, ChannelType

# Create sequencer
seq = ChannelSequencer()

# Create message
msg = OutreachMessage(
    channel=ChannelType.EMAIL,
    message_type="cold_outreach",
    body="Hi John, I wanted to reach out...",
    subject="Quick question"
)

# Send via multi-channel sequence
result = seq.execute_sequence(
    message=msg,
    recipient_email="john@example.com",
    recipient_linkedin_id="john-id",
    form_url="https://example.com/contact"
)

# Result structure
{
    'success': True,
    'message_id': 'uuid-string',
    'channel_used': 'EMAIL',
    'attempts': [
        {
            'channel': 'EMAIL',
            'success': True,
            'status': 'SENT',
            'timestamp': '2024-01-01T12:00:00'
        }
    ]
}
```

---

## 📋 OPERATOR API USAGE

```python
from aicmo import operator_services

# Send outreach
result = operator_services.send_outreach_message(
    db=session,
    lead_id=123,
    message_body="Let's connect!",
    subject="Partnership"
)

# Get channel config
config = operator_services.get_channel_config(db, 'EMAIL')

# Update channel config
updated = operator_services.update_channel_config(
    db=session,
    channel_name='EMAIL',
    enabled=True,
    rate_limit_per_hour=100,
    rate_limit_per_day=500
)

# Get outreach history
history = operator_services.get_outreach_history(db, lead_id=123, limit=10)

# Get metrics
metrics = operator_services.get_channel_metrics(db, campaign_id=42, days=7)
# Returns: {
#   'email': {'delivery_rate': 85.5, 'reply_rate': 12.3, 'bounce_rate': 2.1},
#   'linkedin': {...},
#   'contact_form': {...}
# }
```

---

## 🔧 CONFIGURATION

### Channel Config Example

```python
{
    'channel': 'email',
    'enabled': True,
    'max_per_hour': 100,
    'max_per_day': 500,
    'max_per_lead': 3,
    'max_retries': 2,
    'retry_backoff_hours': [24, 48],
    'templates': {
        'cold_outreach': 'email_template_1',
        'follow_up': 'email_template_2'
    },
    'settings': {
        'from_email': 'outreach@company.com',
        'from_name': 'Sales Team'
    }
}
```

### Sequence Config Example

```python
{
    'name': 'default_sequence',
    'description': 'Email → LinkedIn → Form',
    'steps': [
        {
            'order': 1,
            'channel': 'email',
            'message_template': 'email_intro',
            'max_retries': 2,
            'retry_delay_hours': 24
        },
        {
            'order': 2,
            'channel': 'linkedin',
            'message_template': 'linkedin_dm',
            'max_retries': 1,
            'retry_delay_hours': 48
        },
        {
            'order': 3,
            'channel': 'contact_form',
            'message_template': 'contact_form_submit',
            'max_retries': 0
        }
    ]
}
```

---

## 📊 CHANNEL TYPES & STATUSES

### Channels
- `EMAIL` - Email delivery
- `LINKEDIN` - LinkedIn DM or connection request
- `CONTACT_FORM` - Form submission
- `PHONE` - Phone calls (future)

### Statuses
- `PENDING` - Scheduled
- `SENT` - Successfully sent
- `DELIVERED` - Reached recipient
- `REPLIED` - Got response
- `BOUNCED` - Hard failure
- `FAILED` - Soft failure (retry eligible)
- `SKIPPED` - Skipped per logic

---

## ⚙️ INTEGRATION WITH PHASE A

**Phase A → Phase B Flow**:

```
Lead (Phase A)
  ↓
LeadGradeService (auto-grade)
  ↓
generate_personalized_messages_for_lead()
  ↓
run_auto_multichannel_batch() [NEW Phase B]
  ├─ OutreachMessage creation
  ├─ ChannelSequencer.execute_sequence()
  └─ Return: {success, channel_used, attempts}
  ↓
Update lead status + last_outreach_at
```

---

## 🔍 TROUBLESHOOTING

### Issue: All emails bouncing
```python
# Check bounce rate
rate = email_service.get_bounce_rate()
if rate > 0.1:  # 10%+
    # Check email addresses in database
    # Consider adding bounce handling
```

### Issue: Fallback not working
```python
# Check sequence config has multiple steps
config = db.query(SequenceConfigDB).first()
assert len(config.steps) > 1  # Must have fallback

# Check step order is sequential
for step in config.steps:
    assert step.order == expected_order
```

### Issue: Rate limiter blocking
```python
# Increase rate limits
operator_services.update_channel_config(
    db=session,
    channel_name='EMAIL',
    max_per_hour=200,  # Increase from 100
    max_per_day=1000   # Increase from 500
)
```

---

## 📈 METRICS & KPIs

### Key Metrics
- **Channel Distribution**: % of leads per channel
- **Delivery Rate**: Successfully sent / total attempts
- **Reply Rate**: Replies / delivered messages
- **Bounce Rate**: Bounced / sent emails
- **Fallback Rate**: Fallback attempts / total attempts

### Dashboard Query
```python
metrics = get_channel_metrics(db, campaign_id=42, days=7)
for channel, stats in metrics.items():
    print(f"{channel}:")
    print(f"  Delivery: {stats['delivery_rate']:.1f}%")
    print(f"  Reply: {stats['reply_rate']:.1f}%")
    print(f"  Bounce: {stats['bounce_rate']:.1f}%")
```

---

## 🧪 TESTING

Run tests:
```bash
# All Phase B tests
pytest tests/test_phase_b_outreach.py -v

# Specific test class
pytest tests/test_phase_b_outreach.py::TestEmailOutreachService -v

# With coverage
pytest tests/test_phase_b_outreach.py --cov=aicmo.cam.outreach
```

---

## 📁 FILE STRUCTURE

```
aicmo/cam/
├── domain.py                    [+200 lines] Phase B enums + classes
├── db_models.py                 [+140 lines] New tables + extensions
├── auto.py                      [+150 lines] Multi-channel orchestration
├── outreach/                    [NEW DIRECTORY]
│   ├── __init__.py             [150 lines]  Base classes
│   ├── email_outreach.py       [145 lines]  Email service
│   ├── linkedin_outreach.py    [140 lines]  LinkedIn service
│   ├── contact_form_outreach.py [145 lines] Form service
│   └── sequencer.py            [367 lines]  Orchestrator
├── operator_services.py         [+210 lines] Channel API
└── tests/
    └── test_phase_b_outreach.py [~500 lines] 25+ tests
```

---

## ✅ VERIFICATION CHECKLIST

- ✅ All 5 services tested and working
- ✅ Sequencer executes multi-channel flow
- ✅ Rate limiting enforced
- ✅ Retry scheduling operational
- ✅ Database schema extended (additive only)
- ✅ Operator API functions available
- ✅ Zero breaking changes from Phase A
- ✅ All Phase A tests still pass
- ✅ Documentation complete

---

## 🔗 RELATED DOCUMENTATION

- **Phase A**: `PHASE_A_IMPLEMENTATION_COMPLETE.md`
- **Phase B Plan**: `PHASE_B_OUTREACH_PLAN.md`
- **Full Roadmap**: `AGENCY_IN_A_BOX_ROADMAP.md`

---

**Status**: Ready for Production ✅  
**Version**: Phase B  
**Last Updated**: Current Session
