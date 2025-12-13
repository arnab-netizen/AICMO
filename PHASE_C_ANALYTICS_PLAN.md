# PHASE C: ANALYTICS & REPORTING — IMPLEMENTATION PLAN

**Status**: Planning phase | **Estimated Duration**: 2-3 days | **Complexity**: High  
**Dependencies**: Phase A ✅ + Phase B ✅  
**Target Completion**: Production-ready analytics engine  

---

## EXECUTIVE SUMMARY

Phase C transforms AICMO into an analytics-driven acquisition engine with campaign dashboards, channel attribution, lead ROI tracking, and A/B testing capabilities.

**Key Goal**: Enable data-driven decision making for acquisition teams.

---

## 8-STEP IMPLEMENTATION BREAKDOWN

### Step 1: Analytics Domain Models (Day 1, Morning)
**Time**: 2-3 hours | **Files**: domain.py | **Lines**: ~250

Create analytics-specific domain models:
- `Campaign` extended with analytics fields
- `CampaignMetrics` - aggregated metrics
- `ChannelMetrics` - per-channel performance
- `LeadAttribution` - which channel got credit
- `ABTestConfig` - A/B test configuration
- `ABTestResult` - test results
- `ROICalculation` - lead cost & value

**Architecture**:
```
Campaign
├── CampaignMetrics (daily/weekly/monthly snapshots)
├── ChannelMetrics (per Email, LinkedIn, Form)
├── LeadAttribution (lead → channel mapping)
├── ABTestConfig (test setup)
└── ROICalculation (cost & revenue)
```

---

### Step 2: Database Analytics Tables (Day 1, Afternoon)
**Time**: 2-3 hours | **Files**: db_models.py | **Lines**: ~180

Create analytics database tables:
- `CampaignMetricsDB` - Daily/weekly/monthly snapshots
- `ChannelMetricsDB` - Channel performance tracking
- `LeadAttributionDB` - Attribution model results
- `ABTestConfigDB` - Test configurations
- `ABTestResultDB` - Test results & statistics
- `ROITrackerDB` - Cost & revenue tracking
- `AnalyticsEventDB` - Raw event stream (for debugging)

**Schema Highlights**:
- Time-series optimized (date-based partitioning)
- Denormalized for fast queries
- Indexes on campaign_id, date, channel
- JSON columns for flexible metrics

---

### Step 3: Metrics Calculation Engine (Day 1, Evening)
**Time**: 3-4 hours | **Files**: analytics/metrics.py | **Lines**: ~400

Create core metrics calculation:
- `MetricsCalculator` - Compute daily metrics
- `ChannelMetricsCalculator` - Per-channel metrics
- `AttributionModelCalculator` - Lead attribution
- `ROICalculator` - Cost/revenue analysis
- `TrendAnalyzer` - Trend detection (MoM, WoW, YoY)

**Metrics Calculated**:
```
Campaign Level:
  - Total leads generated
  - Total leads engaged
  - Total leads converted
  - Cost per lead
  - Cost per conversion
  - Lead velocity (leads/day)
  - Conversion rate

Channel Level:
  - Delivery rate
  - Reply rate
  - Bounce rate
  - Cost per send
  - Cost per reply
  - Cost per conversion
  - Channel efficiency score

Attribution:
  - First-touch attribution
  - Last-touch attribution
  - Multi-touch attribution
  - Channel credit distribution

ROI:
  - Cost per lead
  - Revenue per lead
  - Net ROI per lead
  - Payback period
  - Lifetime value
```

---

### Step 4: A/B Testing Framework (Day 2, Morning)
**Time**: 2-3 hours | **Files**: analytics/ab_testing.py | **Lines**: ~300

Create A/B testing engine:
- `ABTestRunner` - Setup and execute tests
- `StatisticalCalculator` - Calculate significance
- `ABTestAnalyzer` - Analyze results
- `HypothesisValidator` - Validate hypotheses

**A/B Test Types**:
1. **Message Testing**: Compare email subjects/bodies
2. **Channel Testing**: Email vs LinkedIn preference
3. **Timing Testing**: Send time optimization
4. **Segment Testing**: Different audience segments
5. **Template Testing**: Template A vs B

**Statistical Methods**:
- Chi-square test (categorical)
- T-test (continuous)
- Confidence intervals (95%)
- Sample size calculator
- Statistical power analysis

---

### Step 5: Dashboard Data Layer (Day 2, Afternoon)
**Time**: 2-3 hours | **Files**: analytics/dashboard.py | **Lines**: ~350

Create dashboard query layer:
- `DashboardService` - Main dashboard queries
- `CampaignDashboard` - Campaign overview
- `ChannelDashboard` - Channel performance
- `ROIDashboard` - ROI analysis
- `ABTestDashboard` - Test results
- `TrendDashboard` - Historical trends
- `LeadDashboard` - Lead insights

**Dashboard Endpoints** (for API):
```
GET /dashboard/campaigns/:id
GET /dashboard/channels/:campaign_id
GET /dashboard/roi/:campaign_id
GET /dashboard/ab-tests/:campaign_id
GET /dashboard/trends/:campaign_id?period=30d
GET /dashboard/leads/:campaign_id
```

---

### Step 6: Reporting & Export Engine (Day 2, Evening)
**Time**: 2-3 hours | **Files**: analytics/reports.py | **Lines**: ~300

Create report generation:
- `ReportGenerator` - Generate HTML/PDF reports
- `ScheduledReports` - Automate daily/weekly/monthly
- `ExportFormats` - CSV, JSON, PDF, Excel
- `ReportBuilder` - Custom report builder
- `EmailReporter` - Send reports via email

**Report Types**:
1. Executive Summary (high-level metrics)
2. Detailed Campaign Analysis
3. Channel Performance Breakdown
4. ROI Analysis & Projections
5. A/B Test Results Summary
6. Lead Quality Report
7. Anomaly Detection Report

---

### Step 7: Operator Services & APIs (Day 3, Morning)
**Time**: 2-3 hours | **Files**: operator_services.py | **Lines**: ~250

Extend operator services with:
- `get_campaign_metrics()` - Get campaign KPIs
- `get_channel_metrics_detailed()` - Detailed channel analysis
- `get_roi_analysis()` - ROI breakdown
- `get_attribution_model()` - Attribution results
- `create_ab_test()` - Setup A/B test
- `get_ab_test_results()` - Test results
- `generate_report()` - Generate custom report
- `get_trends()` - Trend analysis

**API Response Format**:
```python
{
  'campaign_id': 42,
  'date_range': '2024-11-01 to 2024-12-11',
  'metrics': {
    'total_leads': 1250,
    'engaged_leads': 312,
    'conversion_rate': 24.9,
    'cost_per_lead': 2.50,
    'roi': 3.2,
  },
  'channels': {
    'email': {...},
    'linkedin': {...},
    'contact_form': {...},
  },
  'attribution': {...},
  'timestamp': '2024-12-11T16:00:00Z'
}
```

---

### Step 8: Test Suite & Documentation (Day 3, Afternoon)
**Time**: 2-3 hours | **Files**: tests/test_phase_c_analytics.py | **Lines**: ~400

Create comprehensive testing:
- `TestMetricsCalculation` - Metric accuracy
- `TestAttribution` - Attribution models
- `TestABTesting` - Statistical validity
- `TestDashboardQueries` - Query performance
- `TestReportGeneration` - Report output
- `TestEdgeCases` - Edge cases & errors

**Test Coverage**:
- Unit tests (metrics, attribution, statistics)
- Integration tests (end-to-end flows)
- Performance tests (query speed)
- Edge case tests (zero data, outliers)
- Accuracy tests (metric validation)

**Documentation**:
- PHASE_C_IMPLEMENTATION_COMPLETE.md
- PHASE_C_QUICK_START.md
- Analytics API documentation
- Report templates documentation

---

## TECHNICAL ARCHITECTURE

### Analytics Data Flow

```
Phase B: OutreachAttemptDB (raw events)
          ↓
Phase C: EventAggregator
          ↓
        MetricsCalculator
          ├─ CampaignMetricsDB
          ├─ ChannelMetricsDB
          ├─ LeadAttributionDB
          └─ ROITrackerDB
          ↓
        DashboardService
          ├─ CampaignDashboard
          ├─ ChannelDashboard
          ├─ ROIDashboard
          └─ ABTestDashboard
          ↓
        ReportGenerator
          ├─ HTML Reports
          ├─ PDF Reports
          └─ CSV Exports
```

### Service Layer Architecture

```
AnalyticsServiceBase
├── MetricsCalculator
│   ├── CampaignMetricsCalculator
│   ├── ChannelMetricsCalculator
│   ├── AttributionCalculator
│   └── ROICalculator
│
├── ABTestRunner
│   ├── TestSetup
│   ├── StatisticalAnalysis
│   └── ResultsAnalyzer
│
├── DashboardService
│   ├── CampaignDashboard
│   ├── ChannelDashboard
│   ├── ROIDashboard
│   └── TrendDashboard
│
└── ReportGenerator
    ├── HTMLReporter
    ├── PDFReporter
    ├── CSVExporter
    └── ScheduledReportRunner
```

---

## DATABASE SCHEMA

### New Tables (7)

```sql
-- Campaign metrics (daily snapshots)
CREATE TABLE campaign_metrics_db (
  id INT PRIMARY KEY,
  campaign_id INT,
  metric_date DATE,
  
  -- Counts
  total_leads INT,
  engaged_leads INT,
  replied_leads INT,
  converted_leads INT,
  
  -- Rates
  engagement_rate FLOAT,
  reply_rate FLOAT,
  conversion_rate FLOAT,
  
  -- Costs & ROI
  total_spend DECIMAL,
  cost_per_lead DECIMAL,
  cost_per_conversion DECIMAL,
  revenue_generated DECIMAL,
  net_roi DECIMAL,
  roi_percent FLOAT,
  
  -- Trends
  lead_velocity INT,
  wow_growth FLOAT,
  mom_growth FLOAT,
  
  created_at TIMESTAMP,
  INDEX(campaign_id, metric_date)
);

-- Channel metrics
CREATE TABLE channel_metrics_db (
  id INT PRIMARY KEY,
  campaign_id INT,
  channel_type VARCHAR(50),
  metric_date DATE,
  
  sent_count INT,
  delivered_count INT,
  replied_count INT,
  bounced_count INT,
  
  delivery_rate FLOAT,
  reply_rate FLOAT,
  bounce_rate FLOAT,
  
  cost_per_send DECIMAL,
  cost_per_delivery DECIMAL,
  cost_per_reply DECIMAL,
  
  efficiency_score FLOAT,
  
  created_at TIMESTAMP,
  INDEX(campaign_id, channel_type, metric_date)
);

-- Lead attribution
CREATE TABLE lead_attribution_db (
  id INT PRIMARY KEY,
  lead_id INT,
  campaign_id INT,
  
  first_touch_channel VARCHAR(50),
  last_touch_channel VARCHAR(50),
  conversion_channel VARCHAR(50),
  
  -- Multi-touch attribution (JSON)
  attribution_weights JSON,
  
  -- Timeline
  first_contact_at TIMESTAMP,
  last_contact_at TIMESTAMP,
  conversion_at TIMESTAMP,
  touch_count INT,
  
  created_at TIMESTAMP,
  INDEX(lead_id, campaign_id)
);

-- A/B test config
CREATE TABLE ab_test_config_db (
  id INT PRIMARY KEY,
  campaign_id INT,
  test_name VARCHAR(255),
  hypothesis TEXT,
  
  test_type VARCHAR(50),  -- message, channel, timing, segment, template
  start_date DATE,
  end_date DATE,
  
  -- Test groups (JSON)
  groups JSON,  -- {control: {...}, variant: {...}}
  
  sample_size INT,
  confidence_level FLOAT,  -- 0.95
  
  status VARCHAR(50),  -- draft, running, paused, completed
  
  created_at TIMESTAMP,
  INDEX(campaign_id, status)
);

-- A/B test results
CREATE TABLE ab_test_result_db (
  id INT PRIMARY KEY,
  test_id INT,
  
  control_group_metrics JSON,
  variant_group_metrics JSON,
  
  -- Statistics
  p_value FLOAT,
  confidence_interval JSON,
  statistical_significance BOOLEAN,
  effect_size FLOAT,
  
  winner VARCHAR(50),  -- control, variant, inconclusive
  
  recommendation TEXT,
  
  completed_at TIMESTAMP,
  INDEX(test_id)
);

-- ROI tracking
CREATE TABLE roi_tracker_db (
  id INT PRIMARY KEY,
  lead_id INT,
  campaign_id INT,
  
  -- Cost tracking
  acquisition_cost DECIMAL,
  channel_costs JSON,  -- {email: 0.05, linkedin: 0.10, form: 0.02}
  total_cost DECIMAL,
  
  -- Revenue tracking
  deal_value DECIMAL,
  deal_stage VARCHAR(50),  -- won, lost, pipeline
  close_probability FLOAT,
  expected_revenue DECIMAL,
  
  -- ROI calculation
  roi FLOAT,
  roi_percent FLOAT,
  payback_period_days INT,
  
  notes TEXT,
  
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  INDEX(lead_id, campaign_id)
);

-- Raw analytics events (for debugging & trending)
CREATE TABLE analytics_event_db (
  id INT PRIMARY KEY,
  event_type VARCHAR(50),
  lead_id INT,
  campaign_id INT,
  channel_type VARCHAR(50),
  
  event_data JSON,
  
  created_at TIMESTAMP,
  INDEX(campaign_id, created_at, event_type)
);
```

---

## KEY METRICS & FORMULAS

### Campaign Metrics
```
Lead Velocity = New Leads / Days
Engagement Rate = Engaged Leads / Total Leads
Conversion Rate = Converted Leads / Total Leads
Cost Per Lead = Total Spend / Total Leads
Cost Per Conversion = Total Spend / Converted Leads
ROI = (Revenue - Cost) / Cost
Net Gain = Revenue - Cost
```

### Channel Metrics
```
Delivery Rate = Delivered / Sent
Reply Rate = Replied / Delivered
Bounce Rate = Bounced / Sent
Channel Efficiency = (Replied / Sent) / Average_Cost
Cost Per Delivery = Total Cost / Delivered
Cost Per Reply = Total Cost / Replied
```

### Attribution Models
```
First-Touch: Credit to first channel that reached lead
Last-Touch: Credit to last channel before conversion
Multi-Touch (Linear): Equal credit to all channels
Multi-Touch (Time-Decay): More credit to recent channels
Multi-Touch (Position): 40% first, 40% last, 20% middle
```

### ROI
```
Acquisition Cost = Total Campaign Spend
Revenue = Deal Value (if won) or Expected Revenue (probability-weighted)
Net Gain = Revenue - Acquisition Cost
ROI = Net Gain / Acquisition Cost
Payback Period = Acquisition Cost / (Revenue / Days)
Lifetime Value = Revenue across all campaigns
```

---

## A/B TESTING FRAMEWORK

### Test Types
1. **Message Test**: Subject lines, email bodies
2. **Channel Test**: Email vs LinkedIn priority
3. **Timing Test**: Send time optimization
4. **Segment Test**: Different segments respond differently
5. **Template Test**: Template A vs B performance

### Statistical Methods
- Chi-square test (categorical outcomes)
- T-test (continuous metrics)
- Confidence intervals (95%)
- Sample size calculator
- Statistical power analysis

### Minimum Viable Test
```
Sample Size: At least 100 per group (30 days typical)
Confidence Level: 95% (p < 0.05)
Effect Size: 20% improvement minimum
Duration: 2-4 weeks typical
```

---

## IMPLEMENTATION TIMELINE

| Step | Task | Day | Hours | Status |
|------|------|-----|-------|--------|
| 1 | Domain models | 1 | 2-3 | ⏳ |
| 2 | Database tables | 1 | 2-3 | ⏳ |
| 3 | Metrics engine | 1 | 3-4 | ⏳ |
| 4 | A/B testing | 2 | 2-3 | ⏳ |
| 5 | Dashboard layer | 2 | 2-3 | ⏳ |
| 6 | Reporting engine | 2 | 2-3 | ⏳ |
| 7 | Operator APIs | 3 | 2-3 | ⏳ |
| 8 | Tests & docs | 3 | 2-3 | ⏳ |

**Total Estimated Time**: 18-25 hours (2-3 days)

---

## SUCCESS CRITERIA

✅ **Completion Criteria**:
- [x] All domain models created
- [x] All database tables created
- [x] All metrics calculable
- [x] A/B testing framework working
- [x] Dashboards queryable
- [x] Reports generatable
- [x] Operator APIs functional
- [x] 20+ tests passing
- [x] Zero breaking changes
- [x] Full documentation

---

## INTEGRATION POINTS

### With Phase A
- Uses LeadDB for lead information
- Uses CampaignDB for campaign context
- Tracks LeadGradeService results

### With Phase B
- Uses OutreachAttemptDB for events
- Uses ChannelConfigDB for channel costs
- Calculates channel effectiveness

### New Analytics Layer
- Produces CampaignMetricsDB (aggregated)
- Produces ChannelMetricsDB (per-channel)
- Produces ROITrackerDB (cost/revenue)
- Produces ABTestResultDB (test results)

---

## RISK MITIGATION

| Risk | Mitigation |
|------|-----------|
| Metric calculation errors | Comprehensive unit tests + validation |
| Performance issues | Denormalized tables + indexes |
| Attribution inaccuracy | Multiple models + comparison |
| A/B test false positives | Statistical rigor + confidence intervals |
| Report generation lag | Async processing + caching |

---

## DELIVERABLES

### Code
- ~1,400 lines of production code
- 7 new database tables
- 8+ service classes
- 20+ test cases
- Full API implementation

### Documentation
- PHASE_C_IMPLEMENTATION_COMPLETE.md
- PHASE_C_QUICK_START.md
- Analytics API guide
- Report templates guide
- A/B testing best practices

### Ready For
- Executive dashboards
- Data-driven decision making
- Campaign optimization
- ROI tracking
- Automated reporting

---

## NEXT AFTER PHASE C

**Phase D: AI-Powered Optimization** (estimated 3-4 days)
- ML-based channel selection
- Dynamic template optimization
- Send time prediction
- Lead scoring improvements
- Anomaly detection

---

**Status**: Ready to implement ✅  
**Dependencies**: Phase A ✅ + Phase B ✅  
**Start Date**: Now  
**Target Completion**: 2-3 days
