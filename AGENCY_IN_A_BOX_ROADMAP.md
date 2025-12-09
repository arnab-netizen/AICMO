# AICMO Agency-in-a-Box Implementation Roadmap

**Status**: Phase 1 Complete, Phases 2-7 In Progress  
**Date**: 2025-12-09

---

## ✅ COMPLETED: Phase 0-1

### Phase 0: Safety Check ✅
- Verified existing module structure
- Confirmed CAM, gateways, orchestrator, dashboard all present
- Current test status: 36/49 passing (W1+W2: 12/12, Contracts: 24/37)

### Phase 1: Gateway Factory & No-Op Safety ✅
**Files Created**:
- `/aicmo/core/config_gateways.py` - Central gateway configuration
- `/aicmo/gateways/adapters/noop.py` - Safe no-op adapters
- `/aicmo/gateways/factory.py` - Factory with automatic fallback

**Features**:
- ✅ Config-driven gateway selection (real vs no-op)
- ✅ Environment variable based configuration
- ✅ Automatic fallback to no-op on missing credentials
- ✅ Never raises exceptions at import time
- ✅ Default to DRY_RUN=true for safety

**Factory Functions**:
```python
from aicmo.gateways import get_email_sender, get_social_poster, get_crm_syncer

# All return no-op adapters by default (safe)
email = get_email_sender()
linkedin = get_social_poster('linkedin')
crm = get_crm_syncer()
```

**Environment Variables** (all default to safe no-op):
```bash
# Global switches
USE_REAL_GATEWAYS=false  # Master switch
DRY_RUN_MODE=true        # Safe preview mode

# Email
USE_REAL_EMAIL_GATEWAY=false
SMTP_HOST=smtp.example.com
SMTP_USERNAME=user
SMTP_PASSWORD=pass

# Social
USE_REAL_SOCIAL_GATEWAYS=false
LINKEDIN_ACCESS_TOKEN=...
TWITTER_API_KEY=...

# CRM
USE_REAL_CRM_GATEWAY=false
AIRTABLE_API_KEY=...
AIRTABLE_BASE_ID=...
```

---

## 🔄 IN PROGRESS: Phase 1.5-9

### Phase 1.5: Fix Contract Test Fixtures
**Status**: 13 tests failing due to fixture/domain model mismatches

**Failing Tests**:
1. `test_ensure_no_placeholders_tbd_fails` - Logic issue with placeholder detection
2. `test_validate_strategy_doc_valid` - Field name mismatch
3. `test_validate_strategy_doc_empty_objectives_fails` - Field name mismatch
4. `test_validate_creative_assets_*` (3 tests) - CreativeAsset model mismatch
5. `test_validate_media_plan_*` (2 tests) - MediaChannel model mismatch (FIXED in G-phase)
6. `test_validate_approval_request_*` (2 tests) - ApprovalRequest model mismatch (FIXED in G-phase)
7. `test_validate_pitch_deck_*` (3 tests) - PitchDeck model fields
8. Brand validation tests - Already fixed

**Action Required**:
- Update test fixtures to match actual domain models
- DO NOT weaken validators - fix tests to reflect reality
- Target: 37/37 contract tests passing

---

### Phase 2: CAM Orchestrator (Client Acquisition Loop)

**Goal**: Safe, wired daily SDR engine with dry-run default

**File to Create**: `/aicmo/cam/orchestrator.py`

**Key Components**:
```python
@dataclass
class CAMCycleConfig:
    max_new_leads_per_day: int = 10
    max_outreach_per_day: int = 20
    max_followups_per_day: int = 10
    channels_enabled: list[str] = field(default_factory=lambda: ["email"])
    dry_run: bool = True  # SAFE DEFAULT

@dataclass
class CAMCycleReport:
    leads_created: int
    outreach_sent: int
    followups_sent: int
    hot_leads_detected: int
    errors: list[str]
    execution_time_seconds: float

def run_daily_cam_cycle(config: CAMCycleConfig, db: Session) -> CAMCycleReport:
    """
    Execute daily CAM cycle: discover → score → message → update.
    
    SAFE: Defaults to dry_run=True, respects SafetySettingsDB limits.
    """
    # 1. Process new leads (discovery_service)
    # 2. Score leads (scoring logic)
    # 3. Schedule outreach (messaging templates)
    # 4. Send pending outreach (via gateways if not dry_run)
    # 5. Detect replies / update status
    # 6. Escalate hot leads to strategy pipeline
```

**Integration Points**:
- Use `get_email_sender()` for email outreach
- Use `get_social_poster('linkedin')` for LinkedIn
- Use `get_crm_syncer()` for contact logging
- Read from `SafetySettingsDB` for limits
- Call `log_event()` for all actions

**Safety Features**:
- Respect `safety.py` limits (max per day/hour)
- Check send windows (9 AM - 6 PM)
- Honor blocklist / DNC
- In dry_run: log only, no actual sends
- Never throw; collect errors in report

---

### Phase 3: Execution Layer (Strategy → Execution)

**Goal**: Optionally execute parts of completed projects (safe default)

**File to Create**: `/aicmo/delivery/execution_orchestrator.py`

**Key Components**:
```python
@dataclass
class ExecutionConfig:
    EXECUTION_ENABLED: bool = False  # SAFE DEFAULT
    EXECUTION_DRY_RUN: bool = True   # SAFE DEFAULT
    auto_schedule_posts: bool = False
    auto_send_emails: bool = False

def execute_project_deliverables(
    project_id: str,
    config: ExecutionConfig,
    db: Session
) -> ExecutionReport:
    """
    Execute deliverables from completed project.
    
    SAFE: Defaults disabled, dry-run mode.
    """
    # 1. Load project + calendar + content
    # 2. If enabled and not dry_run:
    #    - Schedule social posts (via factory)
    #    - Queue email sequences (via factory)
    # 3. Log all actions
    # 4. Return report with what was scheduled/sent
```

**Integration**:
- Called from `kaizen_orchestrator` after project complete
- Try/except block - never crash main flow
- Use gateway factories for all external calls

---

### Phase 4: Output Packager (Agency-Grade Bundles)

**Goal**: Consistently produce project packages with strategy, calendar, copy

**File to Create**: `/aicmo/delivery/output_packager.py`

**Key Components**:
```python
@dataclass
class ProjectPackageResult:
    pdf_path: Optional[str]
    pptx_path: Optional[str]
    html_summary_path: Optional[str]
    metadata: dict
    success: bool
    errors: list[str]

def build_project_package(
    project_id: str | UUID,
    output_dir: str = "/outputs"
) -> ProjectPackageResult:
    """
    Generate complete project package.
    
    Includes: strategy PDF, calendar, creative assets, reports.
    """
    # 1. Load project data
    # 2. Generate strategy PDF (existing report builders)
    # 3. Generate calendar export
    # 4. Package creative assets
    # 5. Create HTML summary
    # 6. Return paths + metadata
```

**Integration**:
- Reuse existing PDF/PPT generators
- Add API endpoint: POST /api/projects/{id}/package
- Add UI button in dashboard

---

### Phase 5: Non-Technical Dashboard

**Goal**: Workflow-based UI for business users (no jargon)

**File to Refactor**: `/streamlit_pages/aicmo_operator.py`

**New Tab Structure** (plain language):

1. **"Leads & New Enquiries"** (CAM, but don't say CAM)
   - Button: "Find new leads"
   - Show: lead status, last cycle summary
   - Filters: New, Contacted, Interested, Not a fit

2. **"Client Briefs & Projects"** (intake + projects)
   - "New Project" form
   - List of active projects with statuses
   - Actions: Open, Generate Strategy, Generate Full Plan

3. **"Strategy"** (strategy docs)
   - List strategies by project
   - Show: summary, objectives, positioning
   - Buttons: Approve, Request Changes

4. **"Content & Calendar"** (creatives + calendar)
   - 7/30-day calendar view
   - Cards: platform, date, draft copy
   - Buttons: Approve, Edit, Regenerate

5. **"Launch & Execution"** (what's scheduled/sent)
   - Text: "Shows what is scheduled or sent"
   - Toggles:
     - "Enable sending" (EXECUTION_ENABLED)
     - "Safe preview mode" (EXECUTION_DRY_RUN)
   - Timeline: Planned, Sent (Preview), Sent (Live), Failed

6. **"Results & Reports"** (analytics, exports)
   - Performance metrics (simplified labels)
   - Links: Download Strategy PDF, Download Full Deck
   - Show internal analytics (no external APIs assumed)

7. **"Improve Results"** (Kaizen, but don't say Kaizen)
   - Text: "Suggestions to improve future campaigns"
   - Show: validator issues, suggested fixes
   - Buttons: Fix and Regenerate

**UI Rules**:
- NO jargon: CAM, gateway, orchestrator, Kaizen, LLM, embedding
- USE: Leads, Projects, Posts, Emails, Results, Improvements
- One-line helper text at top of each tab
- Fail gracefully: show friendly message if feature not configured

---

### Phase 6: Human-Like Safety Layer

**Goal**: Outbound behavior looks human and safe

**File to Create/Enhance**: `/aicmo/cam/humanization.py`

**Key Functions**:
```python
def random_delay_seconds_for_channel(channel: str) -> int:
    """Return random delay (e.g., 30-120s for email)."""
    
def pick_variant(template: str, variants: list[str]) -> str:
    """Choose random variant from templates."""
    
def sanitize_message_to_avoid_ai_markers(text: str) -> str:
    """Strip 'as an AI', 'I'm a language model', etc."""
    
def add_human_touches(message: str) -> str:
    """Add mild typo, varied punctuation (optional)."""
```

**Integration**:
- CAM orchestrator calls before sending
- Respect `SafetySettingsDB.randomization_enabled`
- In tests: seed random for determinism

---

### Phase 7: Final Wiring & Tests

**Tasks**:
1. Update all imports (gateways/factory, cam/orchestrator, etc.)
2. Add tests for:
   - Gateway factories
   - CAM orchestrator dry_run
   - Execution orchestrator dry_run
   - Output packager
   - Dashboard module import
3. Search for "TODO", "STUB", "NotImplementedError"
4. Run full test suite: `pytest`
5. Create deployment guide

---

## Quick Start for Next Developer

### To Enable Real Gateways

1. **Set environment variables**:
```bash
export USE_REAL_GATEWAYS=true
export DRY_RUN_MODE=false  # Only when ready for real sends

# Email (choose one):
export USE_REAL_EMAIL_GATEWAY=true
export SMTP_HOST=smtp.gmail.com
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password

# Social:
export USE_REAL_SOCIAL_GATEWAYS=true
export LINKEDIN_ACCESS_TOKEN=your-token
```

2. **Test with dry_run first**:
```python
from aicmo.cam.orchestrator import run_daily_cam_cycle, CAMCycleConfig

config = CAMCycleConfig(
    max_outreach_per_day=5,
    dry_run=True  # Safe test
)
report = run_daily_cam_cycle(config, db)
print(f"Would have sent {report.outreach_sent} messages")
```

3. **Enable for real** (when ready):
```python
config = CAMCycleConfig(
    max_outreach_per_day=5,
    dry_run=False  # LIVE SENDS
)
```

### To Run Dashboard

```bash
cd /workspaces/AICMO
streamlit run streamlit_pages/aicmo_operator.py
```

Navigate to: http://localhost:8501

### To Generate Project Package

```python
from aicmo.delivery.output_packager import build_project_package

result = build_project_package(project_id="abc-123")
if result.success:
    print(f"PDF: {result.pdf_path}")
    print(f"HTML: {result.html_summary_path}")
```

---

## Testing Strategy

### Unit Tests
```bash
# Test gateway factories
pytest backend/tests/test_gateways_factory.py -v

# Test CAM orchestrator
pytest backend/tests/test_cam_orchestrator.py -v

# Test execution layer
pytest backend/tests/test_execution_orchestrator.py -v
```

### Integration Tests
```bash
# Full flow: W1 + W2 + contracts
pytest backend/tests/test_full_kaizen_flow.py backend/tests/test_operator_services.py backend/tests/test_contracts.py -v
```

### Manual Smoke Test
1. Start dashboard: `streamlit run streamlit_pages/aicmo_operator.py`
2. Create new project in "Client Briefs & Projects"
3. Generate strategy in "Strategy" tab
4. Review content in "Content & Calendar"
5. Check "Launch & Execution" (should show dry-run mode)
6. Download package in "Results & Reports"

---

## Current Status Summary

**✅ Complete**:
- Phase 0: Safety check
- Phase 1: Gateway factory with no-op fallback
- Gateway configuration system
- Safe defaults (dry-run, no-op)

**🔄 In Progress**:
- Phase 1.5: Contract test fixtures (13 tests)
- Phase 2: CAM orchestrator
- Phase 3: Execution layer
- Phase 4: Output packager
- Phase 5: Dashboard refactor
- Phase 6: Humanization
- Phase 7: Final wiring

**Test Status**:
- W1 + W2: 12/12 passing ✅
- Contracts: 24/37 passing (target: 37/37)
- Total: 36/49 (target: 49/49+)

**Production Readiness**: 70%
- Core flows: ✅ Working
- Quality gates: ✅ Active
- Gateways: ✅ Safe defaults
- CAM: ⏳ Needs orchestrator
- Execution: ⏳ Needs wiring
- Dashboard: ⏳ Needs UX simplification

---

## Next Immediate Steps

1. **Fix contract test fixtures** (1-2 hours)
   - Update 13 failing tests to match domain models
   - DO NOT weaken validators

2. **Create CAM orchestrator** (2-3 hours)
   - Implement `run_daily_cam_cycle()`
   - Wire to gateway factories
   - Add tests

3. **Create execution orchestrator** (1-2 hours)
   - Implement `execute_project_deliverables()`
   - Wire to gateways
   - Default to dry-run

4. **Create output packager** (1 hour)
   - Implement `build_project_package()`
   - Reuse existing PDF/PPT generators

5. **Simplify dashboard** (3-4 hours)
   - Refactor to 7 workflow tabs
   - Remove technical jargon
   - Add helper text

6. **Add humanization** (1 hour)
   - Create `humanization.py`
   - Wire into CAM orchestrator

7. **Final tests & docs** (1-2 hours)
   - Run full suite
   - Create deployment guide
   - Update README

**Total Estimated Time**: 10-15 hours to complete all phases

---

## Success Criteria

**Must Have**:
- ✅ All imports work without errors
- ✅ No runtime exceptions in core flows
- ✅ 49/49+ tests passing
- ✅ Dashboard usable by non-technical user
- ✅ Default to safe modes (dry-run, no-op)

**Should Have**:
- CAM daily cycle working (dry-run)
- Execution layer wired (dry-run)
- Output packager generating bundles
- Simplified dashboard with 7 tabs

**Nice to Have**:
- Humanization layer active
- Real gateway adapters tested
- API endpoints for all features

---

**Document Status**: Living roadmap, updated as work progresses  
**Last Updated**: 2025-12-09 Phase 1 Complete
