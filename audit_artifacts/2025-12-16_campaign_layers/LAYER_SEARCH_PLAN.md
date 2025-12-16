# Campaign Layer Search Plan

## Layer 1: Campaign Definition Layer
**What to find**: Data model for campaigns (platform list, cadence, content types, objectives, dates, owner)
**Search for**: 
  - cam_campaigns table
  - CAMCampaign model
  - campaign schema

## Layer 2: Content Calendar / Scheduling Layer
**What to find**: Logic to schedule posts (calendar, cadence, timing)
**Search for**:
  - schedule_outreach
  - content_calendar
  - posting schedule
  - ChannelSequencer
  - timing/cadence logic

## Layer 3: Publishing Layer (Platform Adapters)
**What to find**: Code that posts to LinkedIn/Instagram/X/Facebook/TikTok
**Search for**:
  - gateways/social.py
  - SocialPoster
  - platform adapters
  - send_to_platform
  - API auth tokens

## Layer 4: Monitoring / Analytics Layer
**What to find**: Fetches metrics from platforms, persists, triggers feedback
**Search for**:
  - analytics_event table
  - campaign_metrics
  - channel_metrics
  - monitor/fetch/metrics
  - webhook handlers

## Layer 5: Lead Capture + Attribution Layer
**What to find**: Ingest leads from DM/email/forms, link to campaign
**Search for**:
  - cam_leads table
  - lead_attribution
  - inbound_email/dm
  - lead capture
  - webhook listeners

## Layer 6: Review / HITL Gate Layer
**What to find**: Approve/reject before publish, pause/override, review queue
**Search for**:
  - publish_status (DRAFT/APPROVED/SCHEDULED/PUBLISHED)
  - review/approval
  - HITL
  - review_queue
  - approval workflow

## Layer 7: Idempotency / Safety Layer
**What to find**: Dedup keys, safe retries, prevent double-posting
**Search for**:
  - idempotency_key
  - unique constraints
  - dedup
  - external_id
  - idempotent retry

## Layer 8: Persistence Layer for Campaign State
**What to find**: Persist campaign state, outputs, external IDs, logs
**Search for**:
  - campaign state tables
  - execution logs
  - external_id tracking
  - crash recovery

