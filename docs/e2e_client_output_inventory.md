# Client-Facing Output Inventory

**Version:** 1.0.0  
**Last Updated:** 2025-12-15  
**Scope:** Exhaustive enumeration of all client-visible outputs

## Output Categories

### 1. Marketing Reports (PDF)

#### 1.1 Full Marketing Strategy Report
- **Output Name:** `marketing_strategy_report.pdf`
- **Format:** PDF
- **Producing Module:** `aicmo.generators.report_generator`
- **Code Path:** `aicmo/generators/report_generator.py::generate_full_report()`
- **Preview Location:** `/dashboard` → Export tab → "View Report Preview"
- **Download Mechanism:** Streamlit download button `st.download_button()`
- **Pack/Preset:** All packs (4-layer, agency, acquisition)
- **Standalone:** Yes
- **Message-like:** No
- **Client-Visible Sections:**
  - Executive Summary
  - Market Analysis
  - Competitive Landscape
  - Target Audience Insights
  - Strategic Recommendations
  - Budget Allocation
  - Implementation Timeline
  - KPI Framework
  - Appendices

#### 1.2 Campaign Report
- **Output Name:** `campaign_<campaign_id>_report_<timestamp>.txt`
- **Format:** Plain text
- **Producing Module:** `aicmo.cam.reporting`
- **Code Path:** `aicmo/cam/reporting.py::generate_campaign_report()`
- **Preview Location:** Revenue Engine UI (E2E mode)
- **Download Mechanism:** File system write, then manual retrieval
- **Pack/Preset:** Revenue Marketing Engine
- **Standalone:** Yes
- **Message-like:** No
- **Client-Visible Sections:**
  - Executive Summary
  - Campaign Performance
  - Lead Attribution Analysis
  - Revenue Impact
  - Next Actions

### 2. Presentations (PPTX)

#### 2.1 Marketing Strategy Deck
- **Output Name:** `marketing_strategy_<client>_<timestamp>.pptx`
- **Format:** PPTX
- **Producing Module:** `aicmo.generators.pptx_generator`
- **Code Path:** `aicmo/generators/pptx_generator.py::generate_strategy_deck()`
- **Preview Location:** `/dashboard` → Gallery tab → "Preview Deck"
- **Download Mechanism:** Streamlit download button
- **Pack/Preset:** All packs
- **Standalone:** Yes
- **Message-like:** No
- **Client-Visible Elements:**
  - Title slide with client branding
  - Executive summary slide
  - Market overview slides (3-5)
  - Strategy slides (5-7)
  - Implementation roadmap
  - Budget breakdown slide
  - Next steps slide
  - Speaker notes on all slides

### 3. Documents (DOCX)

#### 3.1 Marketing Brief
- **Output Name:** `marketing_brief_<client>.docx`
- **Format:** DOCX
- **Producing Module:** `aicmo.generators.brief_generator`
- **Code Path:** `aicmo/generators/brief_generator.py::generate_brief_document()`
- **Preview Location:** `/dashboard` → Brief & Generate tab
- **Download Mechanism:** Streamlit download button
- **Pack/Preset:** All packs
- **Standalone:** Yes
- **Message-like:** No
- **Client-Visible Sections:**
  - Client Overview
  - Business Objectives
  - Target Market
  - Competitive Context
  - Brand Guidelines
  - Campaign Requirements

### 4. Data Exports (CSV)

#### 4.1 Lead Export
- **Output Name:** `leads_export_<timestamp>.csv`
- **Format:** CSV
- **Producing Module:** `aicmo.cam.lead_management`
- **Code Path:** Revenue Engine UI → Export Leads button
- **Preview Location:** Revenue Engine UI (E2E mode)
- **Download Mechanism:** Streamlit download button with pandas DataFrame
- **Pack/Preset:** Revenue Marketing Engine
- **Standalone:** Yes
- **Message-like:** No
- **Client-Visible Columns:**
  - Email
  - Name
  - Status
  - Source Channel
  - Campaign ID
  - Consent Status
  - Created Date

### 5. Email/Message Previews

#### 5.1 Outreach Email Preview
- **Output Name:** (In-memory preview, not file)
- **Format:** HTML/Text
- **Producing Module:** `aicmo.cam.dispatcher`
- **Code Path:** `aicmo/cam/dispatcher.py::preview_outreach_email()`
- **Preview Location:** Revenue Engine UI → Job Dispatch section
- **Download Mechanism:** N/A (preview only)
- **Pack/Preset:** Revenue Marketing Engine
- **Standalone:** No
- **Message-like:** Yes
- **Client-Visible Elements:**
  - Subject line
  - Personalized greeting
  - Email body
  - Call-to-action
  - Footer/unsubscribe

### 6. Archives (ZIP)

#### 6.1 Complete Deliverable Package
- **Output Name:** `aicmo_deliverable_<client>_<timestamp>.zip`
- **Format:** ZIP
- **Producing Module:** `aicmo.generators.package_generator`
- **Code Path:** `aicmo/generators/package_generator.py::create_deliverable_package()`
- **Preview Location:** `/dashboard` → Export tab → "Package Preview"
- **Download Mechanism:** Streamlit download button
- **Pack/Preset:** All packs
- **Standalone:** Yes (contains multiple artifacts)
- **Message-like:** No
- **Archive Contents:**
  - marketing_strategy_report.pdf
  - marketing_strategy_deck.pptx
  - marketing_brief.docx
  - supplementary_data/ (CSV exports)
  - README.txt
  - metadata.json

## Non-Client-Facing Outputs (Explicitly Excluded)

The following are NOT considered client-facing and are NOT in scope for E2E validation:

- Internal logs (`logs/`, `*.log`)
- Diagnostics panels (E2E UI, system status)
- Debug traces (`debug_*.json`)
- Internal filenames not exposed (`temp_*.tmp`, `.cache/`)
- Provider adapters (LLM API internal state)
- Raw LLM prompts (stored in `prompts/`)
- System metadata (database schemas, migrations)
- Alembic migration files
- Test fixtures
- CI/CD artifacts

## Validation Requirements by Output Type

### PDF
- Readable (valid PDF structure)
- Correct page count (≥ minimum per contract)
- Metadata present (title, author, creation date)
- No placeholder text
- All required sections present
- Word counts meet minimums

### PPTX
- Readable (valid PPTX structure)
- Correct slide count (≥ minimum per contract)
- All slides have content
- Speaker notes present on required slides
- No placeholder text in slides or notes
- Images have alt text

### DOCX
- Readable (valid DOCX structure)
- Correct paragraph/section count
- Headers/footers properly formatted
- No placeholder text
- All required sections present
- Word counts meet minimums

### CSV
- Valid CSV format (parseable)
- Correct column headers
- No empty required columns
- No PII leakage (if not intended)
- Row count > 0

### ZIP
- Valid archive (no corruption)
- No path traversal (`../`, absolute paths)
- All contained files pass individual validation
- Total uncompressed size ≤ limit
- Only allowlisted file extensions

### HTML/Text (Previews)
- Valid HTML (if HTML)
- No unclosed tags
- No placeholder text
- Required elements present
- Minimum character count met

## Change Management

Any new client-facing output MUST be added to this inventory before implementation.

Any change to an existing output's structure MUST update this inventory and bump the contract schema version.

## Validation Status

| Output | Contract Defined | Validator Implemented | E2E Test Coverage | Status |
|--------|------------------|----------------------|-------------------|--------|
| Marketing Strategy Report PDF | ⏳ | ⏳ | ⏳ | PENDING |
| Campaign Report TXT | ⏳ | ⏳ | ⏳ | PENDING |
| Marketing Strategy PPTX | ⏳ | ⏳ | ⏳ | PENDING |
| Marketing Brief DOCX | ⏳ | ⏳ | ⏳ | PENDING |
| Lead Export CSV | ⏳ | ⏳ | ⏳ | PENDING |
| Outreach Email Preview | ⏳ | ⏳ | ⏳ | PENDING |
| Complete Deliverable ZIP | ⏳ | ⏳ | ⏳ | PENDING |
