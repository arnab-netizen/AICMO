# 🎯 OPERATOR WORKFLOW GUIDE - Amendment, Approval, Export

## Quick Start (5 Steps to Export)

### Step 1️⃣: Generate
```
1. Fill form inputs for your tab (e.g., Topic, Platforms)
2. Click "🚀 Generate" button
3. Backend processes request
4. See "📤 Output" section appear
```

**Result:** Markdown draft created and displayed

---

### Step 2️⃣: Preview
```
Click on "📋 Output Preview" (expander)
→ See the generated markdown
→ This is what you'll edit/export
```

**Shows:** Current draft in read-only format

---

### Step 3️⃣: Amend
```
1. Click on "✏️ Amend Deliverable" section
2. Edit markdown in the text area
3. Add notes, revise copy, make changes
4. Click "💾 Save Amendments" button
→ See: "✅ Amendments saved!"
→ See: "Saved at: 2025-12-16 14:30:45"
```

**Options:**
- `💾 Save Amendments` - Keep your changes
- `↩️ Reset to Generated` - Start over from original

---

### Step 4️⃣: Approve
```
1. Review your amendments one more time
2. Click "✅ Approval" section
3. Click "👍 Approve Deliverable" button
→ See: "✅ Approved at: 2025-12-16 14:31:12"
→ See: "Approved by: operator"
```

**Status Changes:**
- Before: "Ready to approve?" (blue button)
- After: "✅ Approved - Ready for export" (green badge)

**To Undo:**
- Click "🔄 Revoke Approval" button
- Returns to amendment mode

---

### Step 5️⃣: Export
```
1. Click "📥 Export" section
2. Choose export format:
   - "⬇️ Download Markdown" (main option)
   - "⬇️ Download JSON" (backup)
3. File downloads to your computer
   Filename: aicmo_{tab}_{date}_{time}.md
   Example: aicmo_creatives_20251216_1431.md
```

**File Contents:**
- Your amendments (not raw JSON)
- All edits you made
- Ready to send/archive

---

## Tab-Specific Workflows

### 📥 Intake Tab
```
Generate → Creates lead submission markdown
↓
Amend → Edit name, email, company, notes
↓
Approve → Finalize lead entry
↓
Export → Download lead record as markdown
```

### 🎨 Creatives Tab
```
Generate → Creates creative list with copy
↓
Amend → Edit posts, hashtags, captions
↓
Approve → Finalize creative set
↓
Export → Download approved creative deck
```

### 📊 Strategy Tab
```
Generate → Creates campaign strategy document
↓
Amend → Revise objectives, budget, timeline
↓
Approve → Lock strategy
↓
Export → Download strategy document
```

### 🚀 Execution Tab
```
Generate → Creates posting schedule
↓
Amend → Adjust timing, platforms, content
↓
Approve → Finalize schedule
↓
Export → Download execution plan
```

---

## File Naming Convention

**Format:**
```
aicmo_{TAB_NAME}_{YYYYMMDD}_{HHMM}.md
```

**Examples:**
```
aicmo_intake_20251216_1431.md       (2:31 PM on Dec 16)
aicmo_creatives_20251216_1500.md    (3:00 PM on Dec 16)
aicmo_strategy_20251217_0900.md     (9:00 AM on Dec 17)
```

**Purpose:** Easy to identify which tab and when it was exported

---

## Session State Tracking

Your work is saved in session state. This means:

✅ **Persistent Across Tab Switches**
- You can switch to another tab
- Come back to find your draft saved

✅ **Amendment History** (via timestamps)
- See when you last amended
- See when you approved
- See export ready status

✅ **Approval Lock**
- Cannot export until approved
- Approved text is locked for consistency
- Can revoke to edit again

---

## Common Workflows

### Scenario 1: Quick Approval
```
Generate → Approve → Export
(No amendments needed)
```
**Time:** < 1 minute

### Scenario 2: Heavy Editing
```
Generate → Amend (multiple times) → Approve → Export
(Each amendment: Save → Review → Save again)
```
**Time:** 5-10 minutes

### Scenario 3: Rejected & Revise
```
Generate → Approve → Export
→ Revoke Approval → Amend → Save → Approve → Export
(Re-do after feedback)
```
**Time:** 5-15 minutes

### Scenario 4: Template from Previous
```
Generate → Amend (using previous export as template) → Approve → Export
(Copy-paste from old file + modify)
```
**Time:** 3-5 minutes

---

## Buttons & Controls

### Generate Section
- `🚀 Generate` - Create output (blue button, enables after form filled)
- `🔄 Reset` - Clear all form inputs
- Status indicator - Shows "⏳ Running" or "✅ timestamp"

### Output Preview Section
- `📋 Output Preview` (expander) - Read-only draft view

### Amendment Section
- `💾 Save Amendments` - Store your changes (blue)
- `↩️ Reset to Generated` - Revert to original (gray)

### Approval Section
- `👍 Approve Deliverable` - Gate export (primary green)
- `�� Revoke Approval` - Unlock draft (gray, after approved)

### Export Section
- `⬇️ Download Markdown` - Main export (enabled after approval)
- `⬇️ Download JSON` - Backup format (enabled after approval)
- Warning message if not approved (yellow alert)

### Debug Section
- `📋 Raw response (debug)` (expander) - Raw JSON data (for developers)

---

## Approval Status Indicators

| Status | UI Display | Action Needed |
|--------|-----------|---|
| **Not Yet Approved** | ⚠️ "Ready to approve?" + Blue button | Click "Approve" |
| **Approved** | ✅ "Approved at: [timestamp]" + Green badge | Ready to export |
| **Export Ready** | ✅ Download buttons enabled | Click to download |
| **Amendments Made** | "Saved at: [timestamp]" | Review, then Approve |

---

## Troubleshooting

### Issue: No output after Generate
**Solution:** Output always appears. If blank, check debug expander for errors.

### Issue: Can't export - buttons disabled
**Solution:** Click "Approve Deliverable" first. Export buttons only enable after approval.

### Issue: Want to edit after approval
**Solution:** Click "🔄 Revoke Approval" button, then edit as before.

### Issue: Lost my amendments
**Solution:** Click "↩️ Reset to Generated" resets to original. Amendments auto-save when you click "Save".

### Issue: Wrong timestamp on export
**Solution:** Timestamp is from when you export, not when you saved. If you need different time, revoke/re-amend/export.

---

## Best Practices

✅ **Do:**
- Review draft before approving
- Use "Save Amendments" after making changes
- Revoke and re-edit if feedback comes in
- Export once approved (no unsaved amendments)

❌ **Don't:**
- Export without approving (buttons disabled anyway)
- Make amendments after approval (revoke first)
- Skip the Output Preview (always review)
- Assume export is in raw JSON format (it's markdown)

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Generate | Ctrl+Enter (in form) or click button |
| Save Amendments | Ctrl+S or click button |
| Approve | Click button (no shortcut) |
| Export | Click button (standard download) |

---

## Getting Help

- **Red Error Box** → Check "🔍 Debug Details" expander
- **Raw Data** → Check "📋 Raw response (debug)" expander
- **Questions** → Refer to this guide
- **Bugs** → Contact admin with export file + error message

---

**Last Updated:** December 16, 2025  
**Status:** ✅ Ready for use  
**Version:** 1.0
