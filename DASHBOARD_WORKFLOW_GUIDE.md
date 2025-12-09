---
title: AICMO Dashboard Workflow Guide
phase: 5-7 Final
date: 2025-01-17
---

# AICMO Dashboard Workflow Guide

## Overview

The AICMO dashboard is organized into **7 workflow tabs** that guide you through running a complete marketing campaign from start to finish.

Each tab represents one step in the process. You can navigate them in order or jump between tabs as needed.

---

## The 7 Steps

### 1️⃣ **Leads & New Enquiries**
**Find new potential clients and track their status.**

- Use the lead finder to search for prospects
- Specify how many leads you want to find and on which channels
- Preview messages before they go out (safe mode by default)
- See a list of all current leads and their engagement status

**Key Point**: Everything is in preview mode. No real messages are sent unless you explicitly enable sending.

---

### 2️⃣ **Client Briefs & Projects**
**Start new client projects and manage their briefs.**

- Create a new project by filling in client details (brand name, business goal, target audience, channels)
- The system generates a starter brief and project ID
- See all your existing projects and their status
- Quick-select a project to work on in other tabs

**Key Point**: A project is your working container for everything—strategy, content, campaigns, results.

---

### 3️⃣ **Strategy**
**Review and approve your marketing plan.**

- Select a project
- Generate or update the marketing strategy
- Review key pillars, positioning, and timeline
- Approve the strategy or request changes
- Download the strategy PDF for your records

**Key Point**: Your strategy is the foundation. Everything else (content, execution) flows from it.

---

### 4️⃣ **Content & Calendar**
**Review the content calendar and approve posts before launch.**

- See all planned posts/emails with their publish dates, channels, and preview text
- Review hooks, captions, and full copy for each item
- Approve content, request edits, or see full details
- Track which items are ready, approved, or need changes

**Key Point**: This is where you ensure all messaging is on-brand and ready to go.

---

### 5️⃣ **Launch & Execution**
**Control whether campaigns are actually sent or just previewed.**

- **Execution Settings**: Toggle whether sending is enabled. By default, it's OFF (safe preview mode).
- **Run Execution**: Select a project and start the campaign. Messages are either previewed (safe) or sent (enabled).
- **Schedule & Log**: See a timeline of when each post/email is planned and its current status.

**Key Point**: This is where the rubber meets the road. Safe mode means nothing goes out. When you enable sending, campaigns go live.

---

### 6️⃣ **Results & Reports**
**See key results and download reports for your clients.**

- View metrics like total reach, clicks, leads generated, and conversions
- Build a report package with:
  - Strategy PDF (the full marketing plan)
  - Campaign Deck (presentations and creative assets)
  - HTML Summary (a web-friendly overview)
- Send reports directly to clients

**Key Point**: This is your deliverable to the client—everything they need to understand what was done and what results were achieved.

---

### 7️⃣ **Improve Results**
**See suggestions and fix issues in your campaigns.**

- View a list of issues or suggestions flagged by the system
  - Examples: "Captions too short," "Strategy needs more specifics," "Missing value proposition"
- Each issue shows which section it affects and its severity
- Click "Fix and regenerate" to automatically improve that section
- Re-run the workflow to see updated content

**Key Point**: This is how the system learns and improves. Use these suggestions to refine campaigns continuously.

---

## Important Safety Features

### 🔒 Safe by Default
- **Execution is OFF by default**: No messages will ever be sent unless you explicitly enable it.
- **Preview mode**: All runs are previewed first. Real sending requires active approval.
- **No surprises**: Every action is logged and can be reviewed before it happens.

### 🔓 Enabling Real Sending (When Ready)
When you're confident in your campaign:
1. Go to **Launch & Execution** tab
2. Toggle **"Enable sending to real channels"**
3. Uncheck **"Safe preview mode"** (if desired)
4. Run execution

After this, messages will go to real channels immediately. Be careful!

---

## Workflow Checklist

**For a New Campaign:**

- [ ] **Leads & New Enquiries**: Find prospects
- [ ] **Client Briefs & Projects**: Create project + brief
- [ ] **Strategy**: Generate and approve marketing plan
- [ ] **Content & Calendar**: Create and approve content
- [ ] **Launch & Execution**: Preview and execute (safe mode)
- [ ] **Results & Reports**: Download and send deliverables
- [ ] **Improve Results**: Review feedback and refine

**For Ongoing Campaigns:**

- [ ] **Results & Reports**: Check metrics
- [ ] **Improve Results**: Address suggestions
- [ ] **Content & Calendar**: Add new posts/emails
- [ ] **Launch & Execution**: Execute new content
- [ ] **Results & Reports**: Download updated reports

---

## What Happens Behind the Scenes

The dashboard uses several "orchestrators"—backend systems that handle the heavy lifting:

- **CAM Orchestrator**: Finds leads, scores them, sends outreach
- **Strategy Orchestrator**: Generates marketing plans using AI
- **Execution Orchestrator**: Sends posts, emails, and CRM updates (safely!)
- **Output Packager**: Generates PDFs, presentations, and reports

You don't need to know the details—just use the tabs and let them do the work.

---

## Tips & Best Practices

1. **Always preview first**: Use safe mode to test before going live.
2. **Iterate in the Improve tab**: Fix issues as they're flagged.
3. **Keep briefs detailed**: The more info you provide, the better the strategy.
4. **Review metrics weekly**: Check Results & Reports to see what's working.
5. **Approve content carefully**: This is your brand—make sure it's right.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Lead finder is not available" | Check your backend configuration and database connection. |
| "Execution failed" | Review error messages in the tab. May need to check content is approved. |
| "No metrics showing" | Run execution first, then wait for data to sync. |
| "Can't download reports" | Make sure the project has been fully executed with results. |

---

## Need Help?

Each tab has built-in guidance and explanations. If you're stuck:

1. Read the helper text at the top of each tab
2. Hover over form fields for tooltips
3. Use the "Details" buttons to see more info
4. Check the status messages (green = success, red = error, blue = info)

---

## Summary

The AICMO dashboard makes marketing automation simple:

✅ **Find clients** → **Brief them** → **Plan strategy** → **Create content** → **Execute & send** → **Track results** → **Improve**

Everything is safe by default, fully logged, and designed to be used by non-technical marketers.

---

*For technical details or to report bugs, please contact the development team.*
