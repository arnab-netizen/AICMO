"""
Dashboard Data Layer for AICMO CAM Analytics

Provides data aggregation and formatting for analytics dashboards.

Supported Dashboards:
- Campaign Dashboard: Overall campaign health and KPIs
- Channel Dashboard: Per-channel performance comparison
- ROI Dashboard: Cost, revenue, and ROI metrics
- A/B Test Dashboard: Active and completed test results
- Trend Dashboard: Metrics over time
- Lead Dashboard: Lead quality and status breakdown
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from aicmo.cam.db_models import (
    CampaignDB, LeadDB, OutreachAttemptDB,
    CampaignMetricsDB, ChannelMetricsDB, LeadAttributionDB,
    ABTestConfigDB, ABTestResultDB, ROITrackerDB, AnalyticsEventDB
)
from aicmo.cam.domain import MetricsPeriod, Channel, AttemptStatus

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Provides aggregated data for various analytics dashboards.
    
    Responsibilities:
    - Fetch and aggregate metrics from database
    - Format data for dashboard consumption
    - Calculate derived metrics on-demand
    - Cache frequently requested data
    """
    
    def __init__(self, db: Session):
        """Initialize dashboard service with database session."""
        self.db = db
    
    def get_campaign_dashboard(
        self,
        campaign_id: int,
        period: MetricsPeriod = MetricsPeriod.DAILY
    ) -> Dict[str, Any]:
        """
        Get campaign-level dashboard with overall health metrics.
        
        Includes:
        - Lead metrics (total, qualified, engaged, converted)
        - Outreach metrics (sent, opened, clicked, replied)
        - Engagement and conversion rates
        - Revenue and ROI
        - Recent trend
        
        Args:
            campaign_id: Campaign ID
            period: Aggregation period
        
        Returns:
            Dashboard data dictionary
        """
        campaign = self.db.query(CampaignDB).filter_by(id=campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Get latest metrics
        metrics = self.db.query(CampaignMetricsDB).filter(
            and_(
                CampaignMetricsDB.campaign_id == campaign_id,
                CampaignMetricsDB.period == period.value
            )
        ).order_by(desc(CampaignMetricsDB.date)).first()
        
        if not metrics:
            metrics = self._get_default_metrics()
        
        # Calculate trend (7-day comparison)
        old_metrics = self.db.query(CampaignMetricsDB).filter(
            and_(
                CampaignMetricsDB.campaign_id == campaign_id,
                CampaignMetricsDB.period == period.value,
                CampaignMetricsDB.date < (date.today() - timedelta(days=7))
            )
        ).order_by(desc(CampaignMetricsDB.date)).first()
        
        trend = self._calculate_trend(metrics, old_metrics)
        
        return {
            'campaign_id': campaign_id,
            'campaign_name': campaign.name,
            'status': campaign.status,
            'metrics': {
                'total_leads': metrics.total_leads,
                'qualified_leads': metrics.qualified_leads,
                'engaged_leads': metrics.engaged_leads,
                'converted_leads': metrics.converted_leads,
                'sent_count': metrics.sent_count,
                'opened_count': metrics.opened_count,
                'clicked_count': metrics.clicked_count,
                'replied_count': metrics.replied_count,
                'engagement_rate': round(metrics.engagement_rate * 100, 2),
                'conversion_rate': round(metrics.conversion_rate * 100, 2),
                'average_response_time_hours': round(metrics.average_response_time or 0, 1),
                'total_cost': round(metrics.total_cost, 2),
                'roi_percent': round(metrics.roi_percent or 0, 2)
            },
            'trend': trend,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def get_channel_dashboard(
        self,
        campaign_id: int,
        period: MetricsPeriod = MetricsPeriod.DAILY
    ) -> Dict[str, Any]:
        """
        Get per-channel performance comparison dashboard.
        
        Includes:
        - Delivery rate by channel
        - Reply rate by channel
        - Click-through rate by channel
        - Efficiency score by channel
        - Cost per metric by channel
        
        Args:
            campaign_id: Campaign ID
            period: Aggregation period
        
        Returns:
            Dashboard data with channel breakdown
        """
        # Get channel metrics
        channel_metrics = self.db.query(ChannelMetricsDB).filter(
            and_(
                ChannelMetricsDB.campaign_id == campaign_id,
                ChannelMetricsDB.date == date.today()
            )
        ).all()
        
        channels_data = []
        for cm in channel_metrics:
            channels_data.append({
                'channel': cm.channel,
                'sent_count': cm.sent_count,
                'delivery_rate': round(cm.delivery_rate * 100, 2),
                'bounce_rate': round(cm.bounce_rate * 100, 2),
                'opened_count': cm.opened_count,
                'clicked_count': cm.clicked_count,
                'replied_count': cm.replied_count,
                'reply_rate': round(cm.reply_rate * 100, 2),
                'click_through_rate': round(cm.click_through_rate * 100, 2),
                'cost_per_send': round(cm.cost_per_send or 0, 3),
                'cost_per_engagement': round(cm.cost_per_engagement or 0, 3),
                'efficiency_score': round(cm.efficiency_score, 1)
            })
        
        # Rank channels by efficiency
        ranked_channels = sorted(
            channels_data,
            key=lambda x: x['efficiency_score'],
            reverse=True
        )
        
        return {
            'campaign_id': campaign_id,
            'period': period.value,
            'channels': ranked_channels,
            'best_channel': ranked_channels[0]['channel'] if ranked_channels else None,
            'total_sent': sum(c['sent_count'] for c in channels_data),
            'total_delivered': sum(c['sent_count'] - int(c['bounce_rate'] / 100 * c['sent_count']) for c in channels_data),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def get_roi_dashboard(
        self,
        campaign_id: int
    ) -> Dict[str, Any]:
        """
        Get ROI and revenue dashboard.
        
        Includes:
        - Total acquisition cost
        - Total deal value
        - ROI percent
        - Payback period
        - Cost efficiency metrics
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            ROI dashboard data
        """
        # Get ROI records
        roi_records = self.db.query(ROITrackerDB).filter_by(
            campaign_id=campaign_id
        ).all()
        
        if not roi_records:
            return {
                'campaign_id': campaign_id,
                'total_cost': 0.0,
                'total_revenue': 0.0,
                'roi_percent': 0.0,
                'deals_closed': 0,
                'payback_period_days': None,
                'cost_per_deal': 0.0,
                'average_deal_value': 0.0,
                'last_updated': datetime.utcnow().isoformat()
            }
        
        total_cost = sum(r.acquisition_cost for r in roi_records)
        total_revenue = sum(r.deal_value or 0 for r in roi_records if r.deal_closed)
        deals_closed = len([r for r in roi_records if r.deal_closed])
        
        roi_percent = ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0
        cost_per_deal = total_cost / deals_closed if deals_closed > 0 else 0
        avg_deal_value = total_revenue / deals_closed if deals_closed > 0 else 0
        
        # Calculate payback period
        closed_sorted = sorted(
            [r for r in roi_records if r.deal_closed and r.deal_date],
            key=lambda r: r.deal_date
        )
        payback_days = None
        if closed_sorted and roi_records:
            cumulative = 0
            first_spend = min(r.spend_date for r in roi_records)
            for record in closed_sorted:
                cumulative += record.deal_value - record.acquisition_cost
                if cumulative >= 0:
                    payback_days = (record.deal_date - first_spend).days
                    break
        
        return {
            'campaign_id': campaign_id,
            'total_cost': round(total_cost, 2),
            'total_revenue': round(total_revenue, 2),
            'roi_percent': round(roi_percent, 2),
            'deals_closed': deals_closed,
            'cost_per_deal': round(cost_per_deal, 2),
            'average_deal_value': round(avg_deal_value, 2),
            'payback_period_days': payback_days,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def get_abtest_dashboard(
        self,
        campaign_id: int,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get A/B test dashboard with active and past tests.
        
        Includes:
        - Active tests and progress
        - Completed tests and results
        - Statistical significance
        - Recommended actions
        
        Args:
            campaign_id: Campaign ID
            status: Filter by status (RUNNING, COMPLETED, etc.)
        
        Returns:
            A/B test dashboard data
        """
        # Get test configs
        query = self.db.query(ABTestConfigDB).filter_by(campaign_id=campaign_id)
        if status:
            query = query.filter_by(status=status)
        
        tests = query.all()
        
        tests_data = []
        for test in tests:
            # Get results if available
            result = self.db.query(ABTestResultDB).filter_by(
                test_config_id=test.id
            ).first()
            
            test_data = {
                'test_config_id': test.id,
                'test_name': test.test_name,
                'test_type': test.test_type,
                'status': test.status,
                'hypothesis': test.hypothesis,
                'control_variant': test.control_variant,
                'treatment_variant': test.treatment_variant,
                'total_sample_size': test.total_sample_size,
                'confidence_level': test.confidence_level,
                'start_date': test.start_date.isoformat() if test.start_date else None,
                'end_date': test.end_date.isoformat() if test.end_date else None
            }
            
            if result:
                test_data.update({
                    'control_metric_value': result.control_metric_value,
                    'treatment_metric_value': result.treatment_metric_value,
                    'p_value': round(result.p_value, 4) if result.p_value else None,
                    'is_significant': result.statistical_significance,
                    'winner': result.winner,
                    'effect_size': round(result.effect_size, 4) if result.effect_size else None,
                    'recommendation': result.recommendation
                })
            
            tests_data.append(test_data)
        
        # Count tests by status
        running = len([t for t in tests if t.status == 'RUNNING'])
        completed = len([t for t in tests if t.status == 'COMPLETED'])
        
        return {
            'campaign_id': campaign_id,
            'tests': tests_data,
            'running_count': running,
            'completed_count': completed,
            'total_tests': len(tests),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def get_trend_dashboard(
        self,
        campaign_id: int,
        days: int = 30,
        period: MetricsPeriod = MetricsPeriod.DAILY
    ) -> Dict[str, Any]:
        """
        Get time-series trend data for metrics.
        
        Includes:
        - Engagement rate trend
        - Conversion rate trend
        - Reply rate trend
        - ROI trend
        
        Args:
            campaign_id: Campaign ID
            days: Number of days to include
            period: Aggregation period
        
        Returns:
            Trend dashboard data
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get historical metrics
        metrics = self.db.query(CampaignMetricsDB).filter(
            and_(
                CampaignMetricsDB.campaign_id == campaign_id,
                CampaignMetricsDB.period == period.value,
                CampaignMetricsDB.date >= start_date,
                CampaignMetricsDB.date <= end_date
            )
        ).order_by(CampaignMetricsDB.date).all()
        
        trend_data = {
            'dates': [m.date.isoformat() for m in metrics],
            'engagement_rates': [round(m.engagement_rate * 100, 2) for m in metrics],
            'conversion_rates': [round(m.conversion_rate * 100, 2) for m in metrics],
            'total_leads': [m.total_leads for m in metrics],
            'converted_leads': [m.converted_leads for m in metrics],
            'roi_percents': [round(m.roi_percent or 0, 2) for m in metrics]
        }
        
        return {
            'campaign_id': campaign_id,
            'period': period.value,
            'days': days,
            'trend_data': trend_data,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def get_lead_dashboard(
        self,
        campaign_id: int
    ) -> Dict[str, Any]:
        """
        Get lead quality and status breakdown dashboard.
        
        Includes:
        - Lead count by grade (A, B, C)
        - Lead count by status
        - Lead source breakdown
        - Recent additions
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            Lead dashboard data
        """
        # Get lead breakdown by grade
        leads = self.db.query(LeadDB).filter_by(campaign_id=campaign_id).all()
        
        by_grade = {}
        by_status = {}
        by_source = {}
        
        for lead in leads:
            # Count by grade
            grade = lead.grade or 'UNGRADED'
            by_grade[grade] = by_grade.get(grade, 0) + 1
            
            # Count by status
            status = lead.status or 'UNKNOWN'
            by_status[status] = by_status.get(status, 0) + 1
            
            # Count by source
            source = lead.source.value if lead.source else 'UNKNOWN'
            by_source[source] = by_source.get(source, 0) + 1
        
        return {
            'campaign_id': campaign_id,
            'total_leads': len(leads),
            'by_grade': by_grade,
            'by_status': by_status,
            'by_source': by_source,
            'high_quality_rate': round(
                (by_grade.get('A', 0) + by_grade.get('B', 0)) / len(leads) * 100,
                2
            ) if leads else 0,
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def _get_default_metrics(self) -> Dict:
        """Get default metrics object when no data exists."""
        class DefaultMetrics:
            total_leads = 0
            qualified_leads = 0
            engaged_leads = 0
            converted_leads = 0
            sent_count = 0
            opened_count = 0
            clicked_count = 0
            replied_count = 0
            engagement_rate = 0.0
            conversion_rate = 0.0
            average_response_time = None
            total_cost = 0.0
            roi_percent = None
        
        return DefaultMetrics()
    
    def _calculate_trend(self, current: Any, previous: Any) -> Dict[str, float]:
        """Calculate percent change trend."""
        if not previous:
            return {}
        
        return {
            'engagement_rate_change': self._percent_change(
                current.engagement_rate, previous.engagement_rate
            ),
            'conversion_rate_change': self._percent_change(
                current.conversion_rate, previous.conversion_rate
            ),
            'lead_growth': self._percent_change(
                current.total_leads, previous.total_leads
            )
        }
    
    def _percent_change(self, current: float, previous: float) -> float:
        """Calculate percent change between two values."""
        if not previous or previous == 0:
            return 0.0
        return round(((current - previous) / previous) * 100, 2)
