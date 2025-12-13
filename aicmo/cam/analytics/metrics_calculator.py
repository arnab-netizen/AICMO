"""
Metrics calculation engine for campaign analytics.

Handles aggregation of metrics at campaign and channel level, including:
- Campaign-level KPIs (engagement rate, conversion rate, ROI)
- Channel-level performance (delivery rate, reply rate, efficiency)
- Multi-touch attribution (first-touch, last-touch, linear, time-decay, position-based)
- ROI calculation and tracking
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, select

from aicmo.cam.domain import (
    MetricsPeriod, AttributionModel, CampaignMetrics, ChannelMetrics,
    LeadAttribution, ROICalculation
)
from aicmo.cam.db_models import (
    CampaignDB, LeadDB, OutreachAttemptDB, CampaignMetricsDB, ChannelMetricsDB,
    LeadAttributionDB, ROITrackerDB, AnalyticsEventDB
)
from aicmo.core.db import get_session

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Calculates campaign and channel-level metrics from raw outreach and event data.
    
    Supports multiple aggregation periods (daily, weekly, monthly) and attribution
    models for multi-touch attribution analysis.
    """
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize metrics calculator with optional database session."""
        self.session = session
    
    def _get_session(self) -> Session:
        """Get or create a database session."""
        if self.session:
            return self.session
        return get_session()
    
    # ========================================================================
    # CAMPAIGN METRICS CALCULATION
    # ========================================================================
    
    def calculate_campaign_metrics(
        self,
        campaign_id: int,
        period: MetricsPeriod = MetricsPeriod.DAILY,
        target_date: Optional[date] = None
    ) -> CampaignMetrics:
        """
        Calculate aggregated campaign metrics for a specific period.
        
        Args:
            campaign_id: Campaign ID
            period: Aggregation period (DAILY, WEEKLY, MONTHLY, etc.)
            target_date: Target date for aggregation (defaults to today)
        
        Returns:
            CampaignMetrics object with calculated KPIs
        
        Raises:
            ValueError: If campaign_id is invalid
        """
        session = self._get_session()
        target_date = target_date or date.today()
        
        try:
            # Get campaign
            campaign = session.query(CampaignDB).filter(
                CampaignDB.id == campaign_id
            ).first()
            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")
            
            # Get date range based on period
            start_date, end_date = self._get_period_range(target_date, period)
            
            # Aggregate lead counts
            total_leads = session.query(func.count(LeadDB.id)).filter(
                and_(
                    LeadDB.campaign_id == campaign_id,
                    LeadDB.created_at >= start_date,
                    LeadDB.created_at <= end_date
                )
            ).scalar() or 0
            
            # Count qualified leads (grade A or B)
            qualified_leads = session.query(func.count(LeadDB.id)).filter(
                and_(
                    LeadDB.campaign_id == campaign_id,
                    LeadDB.grade.in_(['A', 'B']),
                    LeadDB.created_at >= start_date,
                    LeadDB.created_at <= end_date
                )
            ).scalar() or 0
            
            # Count engaged leads (at least one open/click/reply)
            engaged_leads = session.query(func.count(LeadDB.id)).filter(
                and_(
                    LeadDB.campaign_id == campaign_id,
                    LeadDB.created_at >= start_date,
                    LeadDB.created_at <= end_date
                )
            ).distinct().scalar() or 0  # Simplified: would join with AnalyticsEventDB
            
            # Count converted leads (grade A or B after engagement)
            converted_leads = session.query(func.count(LeadDB.id)).filter(
                and_(
                    LeadDB.campaign_id == campaign_id,
                    LeadDB.grade == 'A',
                    LeadDB.created_at >= start_date,
                    LeadDB.created_at <= end_date
                )
            ).scalar() or 0
            
            # Aggregate outreach metrics
            outreach_stats = session.query(
                func.count(OutreachAttemptDB.id).label('sent_count'),
                func.sum(
                    func.cast(
                        OutreachAttemptDB.status.ilike('opened'),
                        type_=type(1)
                    )
                ).label('opened_count')
            ).filter(
                and_(
                    OutreachAttemptDB.campaign_id == campaign_id,
                    OutreachAttemptDB.created_at >= start_date,
                    OutreachAttemptDB.created_at <= end_date
                )
            ).first()
            
            sent_count = outreach_stats.sent_count or 0
            opened_count = outreach_stats.opened_count or 0
            
            # Count clicks and replies from analytics events
            clicked_count = session.query(func.count(AnalyticsEventDB.id)).filter(
                and_(
                    AnalyticsEventDB.campaign_id == campaign_id,
                    AnalyticsEventDB.event_type == 'CLICKED',
                    AnalyticsEventDB.event_timestamp >= start_date,
                    AnalyticsEventDB.event_timestamp <= end_date
                )
            ).scalar() or 0
            
            replied_count = session.query(func.count(AnalyticsEventDB.id)).filter(
                and_(
                    AnalyticsEventDB.campaign_id == campaign_id,
                    AnalyticsEventDB.event_type == 'REPLIED',
                    AnalyticsEventDB.event_timestamp >= start_date,
                    AnalyticsEventDB.event_timestamp <= end_date
                )
            ).scalar() or 0
            
            # Calculate rates
            engagement_rate = (opened_count / sent_count * 100) if sent_count > 0 else 0.0
            conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0.0
            
            # Calculate average response time
            response_times = session.query(
                func.avg(
                    func.extract('epoch',
                        AnalyticsEventDB.event_timestamp - OutreachAttemptDB.sent_at
                    ) / 3600  # Convert to hours
                )
            ).filter(
                and_(
                    AnalyticsEventDB.campaign_id == campaign_id,
                    AnalyticsEventDB.event_type == 'REPLIED',
                    AnalyticsEventDB.event_timestamp >= start_date,
                    AnalyticsEventDB.event_timestamp <= end_date
                )
            ).scalar()
            average_response_time = float(response_times) if response_times else None
            
            # Get cost and revenue data
            roi_data = session.query(
                func.sum(ROITrackerDB.acquisition_cost).label('total_cost'),
                func.sum(ROITrackerDB.deal_value).label('total_revenue')
            ).filter(
                and_(
                    ROITrackerDB.campaign_id == campaign_id,
                    ROITrackerDB.spend_date >= start_date,
                    ROITrackerDB.spend_date <= end_date
                )
            ).first()
            
            total_cost = float(roi_data.total_cost or 0)
            total_revenue = float(roi_data.total_revenue or 0) if roi_data.total_revenue else None
            roi_percent = (
                (total_revenue - total_cost) / total_cost * 100
                if total_cost > 0 and total_revenue else None
            )
            
            # Create metrics object
            metrics = CampaignMetrics(
                campaign_id=campaign_id,
                period=period.value,
                date=target_date,
                total_leads=total_leads,
                qualified_leads=qualified_leads,
                engaged_leads=engaged_leads,
                converted_leads=converted_leads,
                sent_count=sent_count,
                opened_count=opened_count,
                clicked_count=clicked_count,
                replied_count=replied_count,
                engagement_rate=engagement_rate,
                conversion_rate=conversion_rate,
                average_response_time=average_response_time,
                total_cost=total_cost,
                total_revenue=total_revenue,
                roi_percent=roi_percent
            )
            
            logger.info(
                f"Calculated campaign metrics for campaign {campaign_id}: "
                f"leads={total_leads}, engagement_rate={engagement_rate:.2f}%, "
                f"roi={roi_percent:.2f}%" if roi_percent else "N/A"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating campaign metrics: {str(e)}")
            raise
    
    # ========================================================================
    # CHANNEL METRICS CALCULATION
    # ========================================================================
    
    def calculate_channel_metrics(
        self,
        campaign_id: int,
        channel: str,
        target_date: Optional[date] = None
    ) -> ChannelMetrics:
        """
        Calculate per-channel performance metrics.
        
        Args:
            campaign_id: Campaign ID
            channel: Channel type (EMAIL, LINKEDIN, CONTACT_FORM)
            target_date: Target date for aggregation (defaults to today)
        
        Returns:
            ChannelMetrics object with channel-specific KPIs
        
        Raises:
            ValueError: If campaign_id or channel is invalid
        """
        session = self._get_session()
        target_date = target_date or date.today()
        
        try:
            # Get date range (daily)
            start_date = datetime.combine(target_date, datetime.min.time())
            end_date = datetime.combine(target_date, datetime.max.time())
            
            # Get outreach attempts for channel
            outreach_query = session.query(OutreachAttemptDB).filter(
                and_(
                    OutreachAttemptDB.campaign_id == campaign_id,
                    OutreachAttemptDB.channel == channel,
                    OutreachAttemptDB.created_at >= start_date,
                    OutreachAttemptDB.created_at <= end_date
                )
            )
            
            outreach_attempts = outreach_query.all()
            sent_count = len(outreach_attempts)
            
            if sent_count == 0:
                # Return empty metrics
                return ChannelMetrics(
                    campaign_id=campaign_id,
                    channel=channel,
                    date=target_date,
                    sent_count=0,
                    delivery_rate=0.0,
                    bounce_rate=0.0,
                    opened_count=0,
                    clicked_count=0,
                    replied_count=0,
                    reply_rate=0.0,
                    click_through_rate=0.0,
                    efficiency_score=0.0
                )
            
            # Count delivery/bounce
            successful = sum(1 for a in outreach_attempts if a.status != 'FAILED')
            delivery_rate = (successful / sent_count * 100) if sent_count > 0 else 0.0
            bounce_rate = ((sent_count - successful) / sent_count * 100) if sent_count > 0 else 0.0
            
            # Get events for this channel
            opened_count = session.query(func.count(AnalyticsEventDB.id)).filter(
                and_(
                    AnalyticsEventDB.campaign_id == campaign_id,
                    AnalyticsEventDB.channel == channel,
                    AnalyticsEventDB.event_type == 'OPENED',
                    AnalyticsEventDB.event_timestamp >= start_date,
                    AnalyticsEventDB.event_timestamp <= end_date
                )
            ).scalar() or 0
            
            clicked_count = session.query(func.count(AnalyticsEventDB.id)).filter(
                and_(
                    AnalyticsEventDB.campaign_id == campaign_id,
                    AnalyticsEventDB.channel == channel,
                    AnalyticsEventDB.event_type == 'CLICKED',
                    AnalyticsEventDB.event_timestamp >= start_date,
                    AnalyticsEventDB.event_timestamp <= end_date
                )
            ).scalar() or 0
            
            replied_count = session.query(func.count(AnalyticsEventDB.id)).filter(
                and_(
                    AnalyticsEventDB.campaign_id == campaign_id,
                    AnalyticsEventDB.channel == channel,
                    AnalyticsEventDB.event_type == 'REPLIED',
                    AnalyticsEventDB.event_timestamp >= start_date,
                    AnalyticsEventDB.event_timestamp <= end_date
                )
            ).scalar() or 0
            
            # Calculate rates
            reply_rate = (replied_count / successful * 100) if successful > 0 else 0.0
            click_through_rate = (clicked_count / successful * 100) if successful > 0 else 0.0
            
            # Calculate efficiency score (0-100)
            # Combines delivery, reply rate, and click-through rate
            efficiency_score = (delivery_rate * 0.3 + reply_rate * 0.5 + click_through_rate * 0.2)
            
            # Get cost data
            cost_data = session.query(
                func.sum(ROITrackerDB.acquisition_cost).label('total_cost')
            ).filter(
                and_(
                    ROITrackerDB.campaign_id == campaign_id,
                    ROITrackerDB.channel == channel,
                    ROITrackerDB.spend_date >= start_date,
                    ROITrackerDB.spend_date <= end_date
                )
            ).first()
            
            total_cost = float(cost_data.total_cost or 0)
            cost_per_send = (total_cost / sent_count) if sent_count > 0 else None
            cost_per_engagement = (total_cost / (opened_count + clicked_count + replied_count)) if (opened_count + clicked_count + replied_count) > 0 else None
            
            metrics = ChannelMetrics(
                campaign_id=campaign_id,
                channel=channel,
                date=target_date,
                sent_count=sent_count,
                delivery_rate=delivery_rate,
                bounce_rate=bounce_rate,
                opened_count=opened_count,
                clicked_count=clicked_count,
                replied_count=replied_count,
                reply_rate=reply_rate,
                click_through_rate=click_through_rate,
                cost_per_send=cost_per_send,
                cost_per_engagement=cost_per_engagement,
                efficiency_score=efficiency_score
            )
            
            logger.info(
                f"Calculated channel metrics for {channel} in campaign {campaign_id}: "
                f"sent={sent_count}, delivery_rate={delivery_rate:.2f}%, "
                f"reply_rate={reply_rate:.2f}%"
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating channel metrics: {str(e)}")
            raise
    
    # ========================================================================
    # MULTI-TOUCH ATTRIBUTION CALCULATION
    # ========================================================================
    
    def calculate_lead_attribution(
        self,
        lead_id: int,
        campaign_id: int,
        model: AttributionModel = AttributionModel.LAST_TOUCH
    ) -> LeadAttribution:
        """
        Calculate multi-touch attribution for a lead across all channels.
        
        Supports multiple attribution models:
        - FIRST_TOUCH: 100% credit to first channel
        - LAST_TOUCH: 100% credit to last channel
        - LINEAR: Equal credit across all channels
        - TIME_DECAY: More credit to recent touches
        - POSITION_BASED: 40% first, 40% last, 20% middle
        
        Args:
            lead_id: Lead ID
            campaign_id: Campaign ID
            model: Attribution model to use
        
        Returns:
            LeadAttribution object with attribution weights and sequence
        """
        session = self._get_session()
        
        try:
            # Get touch sequence for this lead
            touches = session.query(AnalyticsEventDB).filter(
                and_(
                    AnalyticsEventDB.lead_id == lead_id,
                    AnalyticsEventDB.campaign_id == campaign_id,
                    AnalyticsEventDB.event_type.in_(['OPENED', 'CLICKED', 'REPLIED'])
                )
            ).order_by(AnalyticsEventDB.event_timestamp).all()
            
            if not touches:
                # No engagement, return empty attribution
                return LeadAttribution(
                    lead_id=lead_id,
                    campaign_id=campaign_id,
                    attribution_model=model.value,
                    touch_sequence=[],
                    attribution_weights={}
                )
            
            # Build touch sequence
            touch_sequence = [
                {
                    'channel': t.channel,
                    'timestamp': t.event_timestamp.isoformat(),
                    'action': t.event_type
                }
                for t in touches
            ]
            
            # Calculate attribution weights based on model
            attribution_weights = self._calculate_attribution_weights(touches, model)
            
            # Get first and last touch info
            first_touch = touches[0] if touches else None
            last_touch = touches[-1] if touches else None
            
            attribution = LeadAttribution(
                lead_id=lead_id,
                campaign_id=campaign_id,
                attribution_model=model.value,
                first_touch_channel=first_touch.channel if first_touch else None,
                first_touch_date=first_touch.event_timestamp if first_touch else None,
                last_touch_channel=last_touch.channel if last_touch else None,
                last_touch_date=last_touch.event_timestamp if last_touch else None,
                attribution_weights=attribution_weights,
                touch_sequence=touch_sequence
            )
            
            logger.info(
                f"Calculated attribution for lead {lead_id} using {model.value} model: "
                f"touches={len(touches)}, first={first_touch.channel if first_touch else 'N/A'}"
            )
            
            return attribution
            
        except Exception as e:
            logger.error(f"Error calculating lead attribution: {str(e)}")
            raise
    
    def _calculate_attribution_weights(
        self,
        touches: List,
        model: AttributionModel
    ) -> Dict[str, float]:
        """
        Calculate attribution weights based on the selected model.
        
        Args:
            touches: List of AnalyticsEventDB objects (chronologically ordered)
            model: Attribution model to apply
        
        Returns:
            Dictionary mapping channel names to credit percentages (0-1)
        """
        if not touches:
            return {}
        
        num_touches = len(touches)
        channels = [t.channel for t in touches]
        weights = {}
        
        if model == AttributionModel.FIRST_TOUCH:
            # 100% credit to first channel
            first_channel = channels[0]
            weights[first_channel] = 1.0
            
        elif model == AttributionModel.LAST_TOUCH:
            # 100% credit to last channel
            last_channel = channels[-1]
            weights[last_channel] = 1.0
            
        elif model == AttributionModel.LINEAR:
            # Equal credit to all channels
            equal_weight = 1.0 / num_touches
            for channel in set(channels):
                weights[channel] = equal_weight * channels.count(channel)
            
        elif model == AttributionModel.TIME_DECAY:
            # More credit to recent touches (exponential decay)
            total_weight = sum(2 ** i for i in range(num_touches))
            for i, channel in enumerate(channels):
                touch_weight = (2 ** i) / total_weight
                weights[channel] = weights.get(channel, 0) + touch_weight
            
        elif model == AttributionModel.POSITION_BASED:
            # 40% first, 40% last, 20% middle touches
            if num_touches == 1:
                weights[channels[0]] = 1.0
            elif num_touches == 2:
                weights[channels[0]] = 0.5
                weights[channels[1]] = 0.5
            else:
                # First touch
                weights[channels[0]] = weights.get(channels[0], 0) + 0.4
                # Last touch
                weights[channels[-1]] = weights.get(channels[-1], 0) + 0.4
                # Middle touches (equal distribution of 20%)
                middle_touches = channels[1:-1]
                if middle_touches:
                    middle_weight = 0.2 / len(middle_touches)
                    for channel in set(middle_touches):
                        weights[channel] = weights.get(channel, 0) + (middle_weight * middle_touches.count(channel))
        
        # Normalize to ensure sum = 1.0
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        return weights
    
    # ========================================================================
    # ROI CALCULATION
    # ========================================================================
    
    def calculate_roi(
        self,
        campaign_id: int,
        period: MetricsPeriod = MetricsPeriod.MONTHLY,
        target_date: Optional[date] = None
    ) -> ROICalculation:
        """
        Calculate ROI for a campaign based on costs and revenue.
        
        Args:
            campaign_id: Campaign ID
            period: Aggregation period
            target_date: Target date for calculation
        
        Returns:
            ROICalculation object with cost/revenue/ROI breakdown
        """
        session = self._get_session()
        target_date = target_date or date.today()
        
        try:
            start_date, end_date = self._get_period_range(target_date, period)
            
            # Get total costs
            cost_data = session.query(
                func.sum(ROITrackerDB.acquisition_cost).label('total_cost'),
                func.count(ROITrackerDB.id).label('spend_count')
            ).filter(
                and_(
                    ROITrackerDB.campaign_id == campaign_id,
                    ROITrackerDB.spend_date >= start_date,
                    ROITrackerDB.spend_date <= end_date
                )
            ).first()
            
            total_cost = float(cost_data.total_cost or 0)
            spend_count = cost_data.spend_count or 0
            
            # Get total revenue from closed deals
            revenue_data = session.query(
                func.sum(ROITrackerDB.deal_value).label('total_revenue'),
                func.count(ROITrackerDB.id).label('deal_count')
            ).filter(
                and_(
                    ROITrackerDB.campaign_id == campaign_id,
                    ROITrackerDB.deal_closed == True,
                    ROITrackerDB.deal_date >= start_date,
                    ROITrackerDB.deal_date <= end_date
                )
            ).first()
            
            total_revenue = float(revenue_data.total_revenue or 0) if revenue_data.total_revenue else 0
            deal_count = revenue_data.deal_count or 0
            
            # Calculate metrics
            roi_percent = (
                ((total_revenue - total_cost) / total_cost * 100)
                if total_cost > 0 else None
            )
            
            cost_per_acquisition = (total_cost / spend_count) if spend_count > 0 else None
            average_deal_value = (total_revenue / deal_count) if deal_count > 0 else None
            
            # Calculate payback period
            payback_days = None
            if total_cost > 0 and total_revenue > total_cost:
                daily_revenue = total_revenue / (end_date - start_date).days
                payback_days = int(total_cost / daily_revenue) if daily_revenue > 0 else None
            
            roi = ROICalculation(
                campaign_id=campaign_id,
                period=period.value,
                date=target_date,
                total_cost=total_cost,
                total_revenue=total_revenue,
                roi_percent=roi_percent,
                cost_per_acquisition=cost_per_acquisition,
                average_deal_value=average_deal_value,
                payback_period_days=payback_days,
                deal_count=deal_count
            )
            
            logger.info(
                f"Calculated ROI for campaign {campaign_id}: "
                f"cost=${total_cost:.2f}, revenue=${total_revenue:.2f}, "
                f"roi={roi_percent:.2f}%" if roi_percent else "N/A"
            )
            
            return roi
            
        except Exception as e:
            logger.error(f"Error calculating ROI: {str(e)}")
            raise
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _get_period_range(
        self,
        target_date: date,
        period: MetricsPeriod
    ) -> Tuple[datetime, datetime]:
        """
        Get the start and end datetime for a given period and target date.
        
        Args:
            target_date: The target date
            period: The period type
        
        Returns:
            Tuple of (start_datetime, end_datetime)
        """
        if period == MetricsPeriod.DAILY:
            start = datetime.combine(target_date, datetime.min.time())
            end = datetime.combine(target_date, datetime.max.time())
        
        elif period == MetricsPeriod.WEEKLY:
            # Start of week (Monday)
            days_since_monday = target_date.weekday()
            week_start = target_date - timedelta(days=days_since_monday)
            week_end = week_start + timedelta(days=6)
            start = datetime.combine(week_start, datetime.min.time())
            end = datetime.combine(week_end, datetime.max.time())
        
        elif period == MetricsPeriod.MONTHLY:
            # Start of month
            month_start = target_date.replace(day=1)
            if target_date.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
            start = datetime.combine(month_start, datetime.min.time())
            end = datetime.combine(month_end, datetime.max.time())
        
        elif period == MetricsPeriod.QUARTERLY:
            # Start of quarter
            quarter = (target_date.month - 1) // 3
            quarter_start = target_date.replace(month=quarter * 3 + 1, day=1)
            quarter_end = quarter_start + timedelta(days=91)  # Approximate
            start = datetime.combine(quarter_start, datetime.min.time())
            end = datetime.combine(quarter_end, datetime.max.time())
        
        elif period == MetricsPeriod.YEARLY:
            # Start of year
            year_start = target_date.replace(month=1, day=1)
            year_end = target_date.replace(month=12, day=31)
            start = datetime.combine(year_start, datetime.min.time())
            end = datetime.combine(year_end, datetime.max.time())
        
        else:
            # Default to daily
            start = datetime.combine(target_date, datetime.min.time())
            end = datetime.combine(target_date, datetime.max.time())
        
        return start, end
    
    def save_campaign_metrics(
        self,
        metrics: CampaignMetrics,
        session: Optional[Session] = None
    ) -> CampaignMetricsDB:
        """Save calculated campaign metrics to database."""
        s = session or self._get_session()
        try:
            db_metrics = CampaignMetricsDB(
                campaign_id=metrics.campaign_id,
                period=metrics.period,
                date=metrics.date,
                total_leads=metrics.total_leads,
                qualified_leads=metrics.qualified_leads,
                engaged_leads=metrics.engaged_leads,
                converted_leads=metrics.converted_leads,
                sent_count=metrics.sent_count,
                opened_count=metrics.opened_count,
                clicked_count=metrics.clicked_count,
                replied_count=metrics.replied_count,
                engagement_rate=metrics.engagement_rate,
                conversion_rate=metrics.conversion_rate,
                average_response_time=metrics.average_response_time,
                total_cost=metrics.total_cost,
                total_revenue=metrics.total_revenue,
                roi_percent=metrics.roi_percent
            )
            s.add(db_metrics)
            s.commit()
            logger.info(f"Saved campaign metrics for campaign {metrics.campaign_id}")
            return db_metrics
        except Exception as e:
            logger.error(f"Error saving campaign metrics: {str(e)}")
            s.rollback()
            raise
    
    def save_channel_metrics(
        self,
        metrics: ChannelMetrics,
        session: Optional[Session] = None
    ) -> ChannelMetricsDB:
        """Save calculated channel metrics to database."""
        s = session or self._get_session()
        try:
            db_metrics = ChannelMetricsDB(
                campaign_id=metrics.campaign_id,
                channel=metrics.channel,
                date=metrics.date,
                sent_count=metrics.sent_count,
                delivery_rate=metrics.delivery_rate,
                bounce_rate=metrics.bounce_rate,
                opened_count=metrics.opened_count,
                clicked_count=metrics.clicked_count,
                replied_count=metrics.replied_count,
                reply_rate=metrics.reply_rate,
                click_through_rate=metrics.click_through_rate,
                cost_per_send=metrics.cost_per_send,
                cost_per_engagement=metrics.cost_per_engagement,
                efficiency_score=metrics.efficiency_score
            )
            s.add(db_metrics)
            s.commit()
            logger.info(f"Saved channel metrics for {metrics.channel} in campaign {metrics.campaign_id}")
            return db_metrics
        except Exception as e:
            logger.error(f"Error saving channel metrics: {str(e)}")
            s.rollback()
            raise
    
    def save_lead_attribution(
        self,
        attribution: LeadAttribution,
        session: Optional[Session] = None
    ) -> LeadAttributionDB:
        """Save calculated lead attribution to database."""
        s = session or self._get_session()
        try:
            db_attribution = LeadAttributionDB(
                lead_id=attribution.lead_id,
                campaign_id=attribution.campaign_id,
                attribution_model=attribution.attribution_model,
                first_touch_channel=attribution.first_touch_channel,
                first_touch_date=attribution.first_touch_date,
                last_touch_channel=attribution.last_touch_channel,
                last_touch_date=attribution.last_touch_date,
                attribution_weights=attribution.attribution_weights,
                touch_sequence=attribution.touch_sequence
            )
            s.add(db_attribution)
            s.commit()
            logger.info(f"Saved attribution for lead {attribution.lead_id}")
            return db_attribution
        except Exception as e:
            logger.error(f"Error saving lead attribution: {str(e)}")
            s.rollback()
            raise
