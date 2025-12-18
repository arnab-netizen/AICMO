# AICMO System Health Report

**Generated:** 2025-12-18 05:33:45 UTC

**Mode:** Deterministic ✅ (stub outputs, fixed seeds)

## Summary

- **Features Tested:** 34
- **Passed:** 30 ✅
- **Failed:** 4 ❌
- **Skipped:** 0 ⏭️
- **Status:** 🔴 ISSUES DETECTED

## Performance & Flakiness

**Feature Runtimes:**

- generate_full_deck_pptx: 0.009s
- generate_html_summary: 0.005s
- persona_generator: 0.001s
- social_calendar_generator: 0.001s
- language_filters: 0.001s
- swot_generator: 0.001s
- messaging_pillars_generator: 0.001s
- situation_analysis_generator: 0.001s
- reasoning_trace: 0.000s
- utils: 0.000s
- output_formatter: 0.000s
- agency_grade_processor: 0.000s
- generate_strategy_pdf: 0.000s
- build_kaizen_context: 0.000s
- create_approval_request: 0.000s
- create_project_task: 0.000s
- generate_performance_dashboard: 0.000s
- generate_pitch_deck: 0.000s
- build_project_package: 0.000s
- generate_brand_core: 0.000s
- generate_strategy: 0.000s
- generate_brand_positioning: 0.000s
- generate_media_plan: 0.000s
- generate_strategy: 0.000s
- generate_creatives: 0.000s

**Flakiness Check:** No inconsistencies detected ✅

## Benchmark Coverage

**Global Coverage Summary**

- **Total Benchmarks:** 5
- **Mapped Benchmarks:** 5
- **Enforced Benchmarks:** 5
- **Unenforced Benchmarks:** 0
- **Unmapped Benchmarks:** 0

**Enforcement Rate:** 100.0% (5/5)

**Coverage Notes**

- PDF layout checks not implemented (no PDF parser)

## Layout Checks

Validation of client-facing output structure and organization:

### HTML Summary Validation

**✅ generate_html_summary**

- **Headings Found:** 5
- **Has Overview Section:** True
- **Has Deliverables Section:** True
- **Heading Order Valid:** True



## Content Quality & Genericity

Assessment of content originality, diversity, and placeholder detection:

**✅ language_filters**

- **Genericity Score:** 1.00/1.0 (lower = less generic)
- **Lexical Diversity:** 0/0 unique words
- **Quality Assessment:** excellent
- **Status:** PASS

**✅ persona_generator**

- **Genericity Score:** 1.00/1.0 (lower = less generic)
- **Lexical Diversity:** 0/0 unique words
- **Quality Assessment:** excellent
- **Status:** PASS

**✅ swot_generator**

- **Genericity Score:** 1.00/1.0 (lower = less generic)
- **Lexical Diversity:** 0/0 unique words
- **Quality Assessment:** excellent
- **Status:** PASS

## External Integrations Health Matrix

Status of external services and APIs:

| Service | Configured | Status | Criticality |
|---------|-----------|--------|-------------|
| OpenAI LLM (GPT-4, etc.) | ❌ | NOT CONFIGURED | CRITICAL |
| Apollo Lead Enricher | ❌ | NOT CONFIGURED | OPTIONAL |
| Dropcontact Email Verifier | ❌ | NOT CONFIGURED | OPTIONAL |
| Airtable CRM Sync | ❌ | NOT CONFIGURED | OPTIONAL |
| Email Gateway | ❌ | NOT CONFIGURED | OPTIONAL |
| IMAP Reply Fetcher | ❌ | NOT CONFIGURED | OPTIONAL |
| LinkedIn Social Posting | ❌ | NOT CONFIGURED | OPTIONAL |
| Twitter/X Social Posting | ❌ | NOT CONFIGURED | OPTIONAL |
| Make.com Webhook | ❌ | NOT CONFIGURED | OPTIONAL |
| SDXL Media Generation | ❌ | NOT CONFIGURED | OPTIONAL |
| Figma API | ❌ | NOT CONFIGURED | OPTIONAL |
| Runway ML Video Generation | ❌ | NOT CONFIGURED | OPTIONAL |

**Summary:** 0/12 configured, 0 reachable, 1 critical

⚠️ **Warning:** The following CRITICAL services are not configured:

- **OpenAI LLM (GPT-4, etc.)** - Set `False` to enable

## Semantic Alignment vs Brief

Verification that output aligns with ClientInputBrief:

**✅ language_filters**

- **Status:** ALIGNED

**❌ messaging_pillars_generator**

- **Status:** CRITICAL MISMATCH
- **Mismatches:**
  - Industry 'SaaS' not mentioned in messaging_pillars_generator
- **Partial Matches:**
  - Primary goal keywords not strongly reflected in messaging_pillars_generator
  - Product/service context not reflected in messaging_pillars_generator
  - Strategy does not explicitly reference audience: 'Enterprise data teams'
- **Notes:**
  - Output should contain references to 'SaaS' industry context
  - Expected strategy to reference goal: 'Generate 200 qualified leads per quarter'

**❌ persona_generator**

- **Status:** CRITICAL MISMATCH
- **Mismatches:**
  - Industry 'SaaS' not mentioned in persona_generator
- **Notes:**
  - Output should contain references to 'SaaS' industry context

**✅ situation_analysis_generator**

- **Status:** ALIGNED

**❌ social_calendar_generator**

- **Status:** CRITICAL MISMATCH
- **Mismatches:**
  - Industry 'SaaS' not mentioned in social_calendar_generator
- **Partial Matches:**
  - Primary goal keywords not strongly reflected in social_calendar_generator
  - Product/service context not reflected in social_calendar_generator
  - Strategy does not explicitly reference audience: 'Enterprise data teams'
- **Notes:**
  - Output should contain references to 'SaaS' industry context
  - Expected strategy to reference goal: 'Generate 200 qualified leads per quarter'

**❌ swot_generator**

- **Status:** CRITICAL MISMATCH
- **Mismatches:**
  - Industry 'SaaS' not mentioned in swot_generator
- **Partial Matches:**
  - Primary goal keywords not strongly reflected in swot_generator
- **Notes:**
  - Output should contain references to 'SaaS' industry context
  - Expected strategy to reference goal: 'Generate 200 qualified leads per quarter'

## Security & Privacy Scan

Pattern-based scanning for secrets, environment variables, and prompt injection markers:

**✅ language_filters**

- **Secret-like patterns:** ✅ None
- **Env placeholders:** ✅ None
- **Injection markers:** ✅ None

**✅ persona_generator**

- **Secret-like patterns:** ✅ None
- **Env placeholders:** ✅ None
- **Injection markers:** ✅ None

**✅ swot_generator**

- **Secret-like patterns:** ✅ None
- **Env placeholders:** ✅ None
- **Injection markers:** ✅ None

## Format & Word Counts

Validation of text length and word-count requirements:

**⚠️ language_filters**

- **Fields Checked:** 43
- **Validation Status:** ISSUES FOUND
- **Too Short (18):** brand.industry, brand.location, brand.competitors[0], brand.competitors[1], audience.online_hangouts[0], audience.online_hangouts[1], voice.tone_of_voice[0], voice.tone_of_voice[1], voice.tone_of_voice[2], assets_constraints.focus_platforms[0], assets_constraints.focus_platforms[1], operations.approval_frequency, strategy_extras.brand_adjectives[0], strategy_extras.brand_adjectives[1], strategy_extras.brand_adjectives[2], strategy_extras.success_30_days, strategy_extras.must_include_messages, strategy_extras.tagline
- **Details:**
  - brand.industry: 1 words (min: 2, max: 500)
  - brand.location: 1 words (min: 2, max: 500)
  - brand.competitors[0]: 1 words (min: 2, max: 500)
  - brand.competitors[1]: 1 words (min: 2, max: 500)
  - audience.online_hangouts[0]: 1 words (min: 2, max: 500)

**✅ messaging_pillars_generator**

- **Fields Checked:** 0
- **Validation Status:** PASS

**⚠️ persona_generator**

- **Fields Checked:** 23
- **Validation Status:** ISSUES FOUND
- **Too Short (2):** primary_platforms[0], primary_platforms[1]
- **Details:**
  - primary_platforms[0]: 1 words (min: 2, max: 500)
  - primary_platforms[1]: 1 words (min: 2, max: 500)

**✅ situation_analysis_generator**

- **Fields Checked:** 0
- **Validation Status:** PASS

**✅ social_calendar_generator**

- **Fields Checked:** 0
- **Validation Status:** PASS

**✅ swot_generator**

- **Fields Checked:** 8
- **Validation Status:** PASS

## Feature Testing Results

### Generator Features

#### ❌ agency_grade_processor 

- **Scenarios:** 0/2 passed
  - Failed: 2

**Errors:**
- Error on CloudSync AI: inject_frameworks() missing 2 required positional arguments: 'base_draft' and 'learning_context'
- Error on The Harvest Table: inject_frameworks() missing 2 required positional arguments: 'base_draft' and 'learning_context'

#### ✅ language_filters 

- **Scenarios:** 2/2 passed

#### ✅ messaging_pillars_generator 🔴 **CRITICAL**

- **Scenarios:** 2/2 passed

#### ❌ output_formatter 

- **Scenarios:** 0/2 passed
  - Failed: 2

**Errors:**
- Error on CloudSync AI: expected string or bytes-like object, got 'ClientInputBrief'
- Error on The Harvest Table: expected string or bytes-like object, got 'ClientInputBrief'

#### ✅ persona_generator 🔴 **CRITICAL**

- **Scenarios:** 2/2 passed

#### ❌ reasoning_trace 

- **Scenarios:** 0/2 passed
  - Failed: 2

**Errors:**
- Error on CloudSync AI: attach_reasoning_trace() missing 2 required positional arguments: 'brief' and 'frameworks_str'
- Error on The Harvest Table: attach_reasoning_trace() missing 2 required positional arguments: 'brief' and 'frameworks_str'

#### ✅ situation_analysis_generator 🔴 **CRITICAL**

- **Scenarios:** 2/2 passed

#### ✅ social_calendar_generator 🔴 **CRITICAL**

- **Scenarios:** 2/2 passed

#### ✅ swot_generator 🔴 **CRITICAL**

- **Scenarios:** 2/2 passed

#### ❌ utils 

- **Scenarios:** 0/2 passed
  - Failed: 2

**Errors:**
- Error on CloudSync AI: safe_generate() missing 1 required positional argument: 'fn'
- Error on The Harvest Table: safe_generate() missing 1 required positional argument: 'fn'


### Packager Features

#### ✅ build_kaizen_context 

#### ✅ build_project_package 

#### ✅ create_approval_request 

#### ✅ create_project_task 

#### ✅ generate_brand_core 

#### ✅ generate_brand_positioning 

#### ✅ generate_creatives 

#### ✅ generate_full_deck_pptx 🔴 **CRITICAL**

#### ✅ generate_html_summary 🔴 **CRITICAL**

#### ✅ generate_media_plan 

#### ✅ generate_performance_dashboard 

#### ✅ generate_pitch_deck 

#### ✅ generate_strategy 

#### ✅ generate_strategy 

#### ✅ generate_strategy_pdf 


### Gateway Features

#### ✅ airtable_crm 

*Airtable Crm*

#### ✅ apollo_enricher 

*Apollo Enricher*

#### ✅ cam_noop 

*Cam Noop*

#### ✅ csv_lead_source 

*Csv Lead Source*

#### ✅ dropcontact_verifier 

*Dropcontact Verifier*

#### ✅ make_webhook 

*Make Webhook*

#### ✅ manual_lead_source 

*Manual Lead Source*

#### ✅ noop 

*Noop*

#### ✅ reply_fetcher 

*Reply Fetcher*


## Generator Details

### agency_grade_processor

- **Module:** aicmo.generators.agency_grade_processor
- **Status:** ❌ FAIL
- **Scenarios Passed:** 0
- **Scenarios Failed:** 2
- **Scenarios Skipped:** 0
- **Errors:**
  - Error on CloudSync AI: inject_frameworks() missing 2 required positional arguments: 'base_draft' and 'learning_context'
  - Error on The Harvest Table: inject_frameworks() missing 2 required positional arguments: 'base_draft' and 'learning_context'

### language_filters

- **Module:** aicmo.generators.language_filters
- **Status:** ✅ PASS
- **Scenarios Passed:** 2
- **Scenarios Failed:** 0
- **Scenarios Skipped:** 0

### messaging_pillars_generator

- **Module:** aicmo.generators.messaging_pillars_generator
- **Status:** ✅ PASS
- **Scenarios Passed:** 2
- **Scenarios Failed:** 0
- **Scenarios Skipped:** 0

### output_formatter

- **Module:** aicmo.generators.output_formatter
- **Status:** ❌ FAIL
- **Scenarios Passed:** 0
- **Scenarios Failed:** 2
- **Scenarios Skipped:** 0
- **Errors:**
  - Error on CloudSync AI: expected string or bytes-like object, got 'ClientInputBrief'
  - Error on The Harvest Table: expected string or bytes-like object, got 'ClientInputBrief'

### persona_generator

- **Module:** aicmo.generators.persona_generator
- **Status:** ✅ PASS
- **Scenarios Passed:** 2
- **Scenarios Failed:** 0
- **Scenarios Skipped:** 0

### reasoning_trace

- **Module:** aicmo.generators.reasoning_trace
- **Status:** ❌ FAIL
- **Scenarios Passed:** 0
- **Scenarios Failed:** 2
- **Scenarios Skipped:** 0
- **Errors:**
  - Error on CloudSync AI: attach_reasoning_trace() missing 2 required positional arguments: 'brief' and 'frameworks_str'
  - Error on The Harvest Table: attach_reasoning_trace() missing 2 required positional arguments: 'brief' and 'frameworks_str'

### situation_analysis_generator

- **Module:** aicmo.generators.situation_analysis_generator
- **Status:** ✅ PASS
- **Scenarios Passed:** 2
- **Scenarios Failed:** 0
- **Scenarios Skipped:** 0

### social_calendar_generator

- **Module:** aicmo.generators.social_calendar_generator
- **Status:** ✅ PASS
- **Scenarios Passed:** 2
- **Scenarios Failed:** 0
- **Scenarios Skipped:** 0

### swot_generator

- **Module:** aicmo.generators.swot_generator
- **Status:** ✅ PASS
- **Scenarios Passed:** 2
- **Scenarios Failed:** 0
- **Scenarios Skipped:** 0

### utils

- **Module:** aicmo.generators.utils
- **Status:** ❌ FAIL
- **Scenarios Passed:** 0
- **Scenarios Failed:** 2
- **Scenarios Skipped:** 0
- **Errors:**
  - Error on CloudSync AI: safe_generate() missing 1 required positional argument: 'fn'
  - Error on The Harvest Table: safe_generate() missing 1 required positional argument: 'fn'

## Gateway/Adapter Status

### ✅ airtable_crm

- **Provider:** Airtable Crm
- **Configured:** Yes
- **Details:** Module: aicmo.gateways.adapters.airtable_crm

### ✅ apollo_enricher

- **Provider:** Apollo Enricher
- **Configured:** Yes
- **Details:** Module: aicmo.gateways.adapters.apollo_enricher

### ✅ cam_noop

- **Provider:** Cam Noop
- **Configured:** Yes
- **Details:** Module: aicmo.gateways.adapters.cam_noop

### ✅ csv_lead_source

- **Provider:** Csv Lead Source
- **Configured:** Yes
- **Details:** Module: aicmo.gateways.adapters.csv_lead_source

### ✅ dropcontact_verifier

- **Provider:** Dropcontact Verifier
- **Configured:** Yes
- **Details:** Module: aicmo.gateways.adapters.dropcontact_verifier

### ✅ make_webhook

- **Provider:** Make Webhook
- **Configured:** Yes
- **Details:** Module: aicmo.gateways.adapters.make_webhook

### ✅ manual_lead_source

- **Provider:** Manual Lead Source
- **Configured:** Yes
- **Details:** Module: aicmo.gateways.adapters.manual_lead_source

### ✅ noop

- **Provider:** Noop
- **Configured:** Yes
- **Details:** Module: aicmo.gateways.adapters.noop

### ✅ reply_fetcher

- **Provider:** Reply Fetcher
- **Configured:** Yes
- **Details:** Module: aicmo.gateways.adapters.reply_fetcher

## Packager Functions

### ✅ build_kaizen_context

- **Module:** aicmo.delivery.kaizen_orchestrator
- **Status:** PASS

### ✅ build_project_package

- **Module:** aicmo.delivery.output_packager
- **Status:** PASS

### ✅ create_approval_request

- **Module:** aicmo.delivery.kaizen_orchestrator
- **Status:** PASS

### ✅ create_project_task

- **Module:** aicmo.delivery.kaizen_orchestrator
- **Status:** PASS

### ✅ generate_brand_core

- **Module:** aicmo.delivery.kaizen_orchestrator
- **Status:** PASS

### ✅ generate_brand_positioning

- **Module:** aicmo.delivery.kaizen_orchestrator
- **Status:** PASS

### ✅ generate_creatives

- **Module:** aicmo.delivery.kaizen_orchestrator
- **Status:** PASS

### ✅ generate_full_deck_pptx

- **Module:** aicmo.delivery.output_packager
- **Status:** PASS

### ✅ generate_html_summary

- **Module:** aicmo.delivery.output_packager
- **Status:** PASS

### ✅ generate_media_plan

- **Module:** aicmo.delivery.kaizen_orchestrator
- **Status:** PASS

### ✅ generate_performance_dashboard

- **Module:** aicmo.delivery.kaizen_orchestrator
- **Status:** PASS

### ✅ generate_pitch_deck

- **Module:** aicmo.delivery.kaizen_orchestrator
- **Status:** PASS

### ✅ generate_strategy

- **Module:** aicmo.delivery.kaizen_orchestrator
- **Status:** PASS

### ✅ generate_strategy

- **Module:** aicmo.delivery.orchestrator
- **Status:** PASS

### ✅ generate_strategy_pdf

- **Module:** aicmo.delivery.output_packager
- **Status:** PASS

## Recommendations

1. **Review Failed Features:** Check the errors above for details
2. **Check Dependencies:** Ensure all required packages are installed
3. **Verify Configuration:** Check API keys and service configurations
4. **Review Logs:** Check application logs for more details
