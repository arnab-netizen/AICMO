"""
Reporting & Export Engine for AICMO CAM Analytics

Generates comprehensive reports and exports in multiple formats.

Supported Formats:
- HTML: Interactive web-based reports
- CSV: Excel-compatible spreadsheets
- JSON: Machine-readable data export
- PDF: Printable documents (requires reportlab)

Report Types:
- Executive Summary: High-level KPIs and recommendations
- Detailed Analysis: Comprehensive metrics breakdown
- Trend Report: Historical metrics and forecasts
- Channel Comparison: Performance across channels
- Lead Quality Report: Lead grading and status
- ROI Analysis: Cost, revenue, and profitability
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from io import StringIO, BytesIO
import csv
import json
from pathlib import Path

from sqlalchemy.orm import Session

from aicmo.cam.db_models import (
    CampaignDB, LeadDB, OutreachAttemptDB,
    CampaignMetricsDB, ChannelMetricsDB, ROITrackerDB
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates comprehensive reports in multiple formats.
    
    Responsibilities:
    - Aggregate data from analytics tables
    - Format data for different output formats
    - Generate reports with professional styling
    - Support batch report generation
    """
    
    def __init__(self, db: Session):
        """Initialize report generator with database session."""
        self.db = db
    
    def generate_executive_summary(
        self,
        campaign_id: int,
        format: str = 'html'
    ) -> str:
        """
        Generate executive summary report.
        
        Includes:
        - Campaign overview
        - Key performance indicators (KPIs)
        - Top insights and recommendations
        - Risk assessment
        - Next steps
        
        Args:
            campaign_id: Campaign ID
            format: Output format ('html', 'csv', 'json', 'pdf')
        
        Returns:
            Report content as string
        """
        campaign = self.db.query(CampaignDB).filter_by(id=campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Get latest metrics
        metrics = self.db.query(CampaignMetricsDB).filter_by(
            campaign_id=campaign_id
        ).order_by(CampaignMetricsDB.date.desc()).first()
        
        # Get ROI data
        roi_records = self.db.query(ROITrackerDB).filter_by(
            campaign_id=campaign_id
        ).all()
        
        # Compile report data
        report_data = {
            'campaign_name': campaign.name,
            'campaign_status': getattr(campaign, 'status', 'UNKNOWN'),
            'created_at': campaign.created_at.isoformat(),
            'kpis': {
                'total_leads': metrics.total_leads if metrics else 0,
                'qualified_leads': metrics.qualified_leads if metrics else 0,
                'engagement_rate': round((metrics.engagement_rate * 100) if metrics else 0, 2),
                'conversion_rate': round((metrics.conversion_rate * 100) if metrics else 0, 2),
                'roi_percent': round((metrics.roi_percent or 0) if metrics else 0, 2),
                'total_cost': sum(r.acquisition_cost for r in roi_records),
                'total_revenue': sum(r.deal_value or 0 for r in roi_records if r.deal_closed)
            },
            'insights': self._generate_insights(metrics, roi_records),
            'recommendations': self._generate_recommendations(metrics),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        if format == 'html':
            return self._format_html_summary(report_data)
        elif format == 'json':
            return json.dumps(report_data, indent=2)
        elif format == 'csv':
            return self._format_csv_summary(report_data)
        else:
            return json.dumps(report_data)
    
    def generate_detailed_analysis(
        self,
        campaign_id: int,
        format: str = 'html'
    ) -> str:
        """
        Generate detailed analysis report with full metrics.
        
        Includes:
        - Campaign overview
        - Lead pipeline analysis
        - Outreach performance
        - Channel breakdown
        - Attribution analysis
        - ROI calculation
        
        Args:
            campaign_id: Campaign ID
            format: Output format
        
        Returns:
            Detailed report content
        """
        campaign = self.db.query(CampaignDB).filter_by(id=campaign_id).first()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        # Get all metrics
        metrics = self.db.query(CampaignMetricsDB).filter_by(
            campaign_id=campaign_id
        ).order_by(CampaignMetricsDB.date.desc()).all()
        
        # Get channel breakdown
        channel_metrics = self.db.query(ChannelMetricsDB).filter_by(
            campaign_id=campaign_id
        ).all()
        
        # Get lead breakdown
        leads = self.db.query(LeadDB).filter_by(campaign_id=campaign_id).all()
        
        report_data = {
            'campaign_name': campaign.name,
            'campaign_objective': getattr(campaign, 'objective', None) or "Not specified",
            'leads': {
                'total': len(leads),
                'by_grade': self._count_by_grade(leads),
                'by_status': self._count_by_status(leads),
                'by_source': self._count_by_source(leads)
            },
            'outreach': {
                'total_attempts': sum(m.sent_count for m in metrics),
                'opened': sum(m.opened_count for m in metrics),
                'clicked': sum(m.clicked_count for m in metrics),
                'replied': sum(m.replied_count for m in metrics),
                'metrics_history': [
                    {
                        'date': m.date.isoformat(),
                        'sent': m.sent_count,
                        'engagement_rate': round(m.engagement_rate * 100, 2),
                        'conversion_rate': round(m.conversion_rate * 100, 2)
                    }
                    for m in sorted(metrics, key=lambda x: x.date)
                ]
            },
            'channels': [
                {
                    'channel': cm.channel,
                    'sent': cm.sent_count,
                    'delivery_rate': round(cm.delivery_rate * 100, 2),
                    'reply_rate': round(cm.reply_rate * 100, 2),
                    'efficiency_score': round(cm.efficiency_score, 1)
                }
                for cm in channel_metrics
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
        
        if format == 'html':
            return self._format_html_detailed(report_data)
        elif format == 'json':
            return json.dumps(report_data, indent=2)
        else:
            return json.dumps(report_data)
    
    def generate_channel_comparison(
        self,
        campaign_id: int,
        format: str = 'html'
    ) -> str:
        """
        Generate channel performance comparison report.
        
        Includes:
        - Channel ranking by efficiency
        - Performance metrics by channel
        - Cost per metric by channel
        - Recommendations for channel optimization
        
        Args:
            campaign_id: Campaign ID
            format: Output format
        
        Returns:
            Channel comparison report
        """
        channel_metrics = self.db.query(ChannelMetricsDB).filter_by(
            campaign_id=campaign_id
        ).all()
        
        # Rank channels
        ranked = sorted(
            [
                {
                    'channel': cm.channel,
                    'sent': cm.sent_count,
                    'delivery_rate': round(cm.delivery_rate * 100, 2),
                    'reply_rate': round(cm.reply_rate * 100, 2),
                    'click_through_rate': round(cm.click_through_rate * 100, 2),
                    'cost_per_send': round(cm.cost_per_send or 0, 3),
                    'efficiency_score': round(cm.efficiency_score, 1)
                }
                for cm in channel_metrics
            ],
            key=lambda x: x['efficiency_score'],
            reverse=True
        )
        
        report_data = {
            'campaign_id': campaign_id,
            'channels': ranked,
            'best_channel': ranked[0]['channel'] if ranked else None,
            'recommendations': self._generate_channel_recommendations(ranked),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        if format == 'html':
            return self._format_html_channels(report_data)
        elif format == 'csv':
            return self._format_csv_channels(ranked)
        elif format == 'json':
            return json.dumps(report_data, indent=2)
        else:
            return json.dumps(report_data)
    
    def generate_roi_analysis(
        self,
        campaign_id: int,
        format: str = 'html'
    ) -> str:
        """
        Generate ROI and profitability analysis report.
        
        Includes:
        - Acquisition costs
        - Deal values and closure rates
        - ROI calculation
        - Payback period
        - Cost efficiency metrics
        
        Args:
            campaign_id: Campaign ID
            format: Output format
        
        Returns:
            ROI analysis report
        """
        roi_records = self.db.query(ROITrackerDB).filter_by(
            campaign_id=campaign_id
        ).all()
        
        if not roi_records:
            return json.dumps({
                'campaign_id': campaign_id,
                'message': 'No ROI data available',
                'generated_at': datetime.utcnow().isoformat()
            })
        
        total_cost = sum(r.acquisition_cost for r in roi_records)
        total_revenue = sum(r.deal_value or 0 for r in roi_records if r.deal_closed)
        deals_closed = len([r for r in roi_records if r.deal_closed])
        
        roi_percent = ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        report_data = {
            'campaign_id': campaign_id,
            'summary': {
                'total_cost': round(total_cost, 2),
                'total_revenue': round(total_revenue, 2),
                'roi_percent': round(roi_percent, 2),
                'profit': round(total_revenue - total_cost, 2),
                'deals_closed': deals_closed,
                'cost_per_deal': round(total_cost / deals_closed if deals_closed > 0 else 0, 2),
                'average_deal_value': round(total_revenue / deals_closed if deals_closed > 0 else 0, 2)
            },
            'details': [
                {
                    'lead_id': r.lead_id,
                    'acquisition_cost': round(r.acquisition_cost, 2),
                    'deal_value': round(r.deal_value or 0, 2),
                    'deal_closed': r.deal_closed,
                    'roi': round(((r.deal_value or 0) - r.acquisition_cost) / r.acquisition_cost * 100 if r.acquisition_cost > 0 else 0, 2)
                }
                for r in roi_records
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
        
        if format == 'html':
            return self._format_html_roi(report_data)
        elif format == 'csv':
            return self._format_csv_roi(report_data)
        elif format == 'json':
            return json.dumps(report_data, indent=2)
        else:
            return json.dumps(report_data)
    
    # ========================================================================
    # FORMATTING METHODS
    # ========================================================================
    
    def _format_html_summary(self, data: Dict) -> str:
        """Format executive summary as HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width">
            <title>Campaign Summary: {data['campaign_name']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
                .header {{ border-bottom: 3px solid #007bff; padding-bottom: 10px; margin-bottom: 20px; }}
                .kpi-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
                .kpi-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
                .kpi-value {{ font-size: 28px; font-weight: bold; color: #007bff; }}
                .kpi-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
                .insights {{ background: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0; }}
                .recommendations {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
                ul {{ margin: 10px 0; padding-left: 20px; }}
                li {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Campaign Summary Report</h1>
                <p><strong>Campaign:</strong> {data['campaign_name']}</p>
                <p><strong>Status:</strong> {data['campaign_status']}</p>
                <p><strong>Generated:</strong> {data['generated_at']}</p>
            </div>
            
            <h2>Key Performance Indicators</h2>
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-value">{data['kpis']['total_leads']}</div>
                    <div class="kpi-label">Total Leads</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{data['kpis']['qualified_leads']}</div>
                    <div class="kpi-label">Qualified Leads</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{data['kpis']['engagement_rate']}%</div>
                    <div class="kpi-label">Engagement Rate</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{data['kpis']['conversion_rate']}%</div>
                    <div class="kpi-label">Conversion Rate</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${data['kpis']['total_cost']:.2f}</div>
                    <div class="kpi-label">Total Cost</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">{data['kpis']['roi_percent']}%</div>
                    <div class="kpi-label">ROI</div>
                </div>
            </div>
            
            <div class="insights">
                <h3>Key Insights</h3>
                <ul>
                    {"".join(f"<li>{insight}</li>" for insight in data['insights'])}
                </ul>
            </div>
            
            <div class="recommendations">
                <h3>Recommendations</h3>
                <ul>
                    {"".join(f"<li>{rec}</li>" for rec in data['recommendations'])}
                </ul>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_html_detailed(self, data: Dict) -> str:
        """Format detailed analysis as HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Detailed Analysis: {data['campaign_name']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
                h2 {{ margin-top: 30px; color: #007bff; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; font-weight: bold; }}
                tr:hover {{ background-color: #f5f5f5; }}
            </style>
        </head>
        <body>
            <h1>Detailed Campaign Analysis</h1>
            <p><strong>Campaign:</strong> {data['campaign_name']}</p>
            <p><strong>Objective:</strong> {data['campaign_objective'] or 'N/A'}</p>
            <p><strong>Generated:</strong> {data['generated_at']}</p>
            
            <h2>Lead Breakdown</h2>
            <p>Total Leads: {data['leads']['total']}</p>
            <table>
                <tr><th>Grade</th><th>Count</th></tr>
                {"".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in data['leads']['by_grade'].items())}
            </table>
            
            <h2>Outreach Performance</h2>
            <p>Total Attempts: {data['outreach']['total_attempts']}</p>
            <table>
                <tr><th>Metric</th><th>Count</th></tr>
                <tr><td>Opened</td><td>{data['outreach']['opened']}</td></tr>
                <tr><td>Clicked</td><td>{data['outreach']['clicked']}</td></tr>
                <tr><td>Replied</td><td>{data['outreach']['replied']}</td></tr>
            </table>
            
            <h2>Channel Performance</h2>
            <table>
                <tr><th>Channel</th><th>Sent</th><th>Delivery Rate</th><th>Reply Rate</th><th>Efficiency</th></tr>
                {"".join(f"<tr><td>{c['channel']}</td><td>{c['sent']}</td><td>{c['delivery_rate']}%</td><td>{c['reply_rate']}%</td><td>{c['efficiency_score']}</td></tr>" for c in data['channels'])}
            </table>
        </body>
        </html>
        """
        return html
    
    def _format_html_channels(self, data: Dict) -> str:
        """Format channel comparison as HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Channel Comparison</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #007bff; color: white; }}
                .best {{ background-color: #d4edda; }}
            </style>
        </head>
        <body>
            <h1>Channel Performance Comparison</h1>
            <p><strong>Best Performing Channel:</strong> {data['best_channel']}</p>
            
            <table>
                <tr>
                    <th>Channel</th>
                    <th>Sent</th>
                    <th>Delivery Rate</th>
                    <th>Reply Rate</th>
                    <th>CTR</th>
                    <th>Cost/Send</th>
                    <th>Efficiency Score</th>
                </tr>
                {"".join(f"<tr class='best' if c['channel'] == data['best_channel'] else ''><td>{c['channel']}</td><td>{c['sent']}</td><td>{c['delivery_rate']}%</td><td>{c['reply_rate']}%</td><td>{c['click_through_rate']}%</td><td>${c['cost_per_send']}</td><td>{c['efficiency_score']}</td></tr>" for c in data['channels'])}
            </table>
            
            <h2>Recommendations</h2>
            <ul>
                {"".join(f"<li>{rec}</li>" for rec in data['recommendations'])}
            </ul>
        </body>
        </html>
        """
        return html
    
    def _format_html_roi(self, data: Dict) -> str:
        """Format ROI analysis as HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>ROI Analysis</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px 20px; }}
                .value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #007bff; color: white; }}
            </style>
        </head>
        <body>
            <h1>ROI Analysis Report</h1>
            
            <div class="summary">
                <div class="metric">
                    <div class="value">${data['summary']['total_cost']:.2f}</div>
                    <div>Total Cost</div>
                </div>
                <div class="metric">
                    <div class="value">${data['summary']['total_revenue']:.2f}</div>
                    <div>Total Revenue</div>
                </div>
                <div class="metric">
                    <div class="value">{data['summary']['roi_percent']}%</div>
                    <div>ROI</div>
                </div>
                <div class="metric">
                    <div class="value">${data['summary']['profit']:.2f}</div>
                    <div>Profit</div>
                </div>
            </div>
            
            <table>
                <tr><th>Lead ID</th><th>Acquisition Cost</th><th>Deal Value</th><th>Closed</th><th>ROI</th></tr>
                {"".join(f"<tr><td>{d['lead_id']}</td><td>${d['acquisition_cost']}</td><td>${d['deal_value']}</td><td>{'Yes' if d['deal_closed'] else 'No'}</td><td>{d['roi']}%</td></tr>" for d in data['details'][:50])}
            </table>
        </body>
        </html>
        """
        return html
    
    def _format_csv_summary(self, data: Dict) -> str:
        """Format executive summary as CSV."""
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Metric', 'Value'])
        for key, value in data['kpis'].items():
            writer.writerow([key, value])
        return output.getvalue()
    
    def _format_csv_channels(self, channels: List[Dict]) -> str:
        """Format channel data as CSV."""
        output = StringIO()
        if not channels:
            return output.getvalue()
        
        writer = csv.DictWriter(output, fieldnames=channels[0].keys())
        writer.writeheader()
        writer.writerows(channels)
        return output.getvalue()
    
    def _format_csv_roi(self, data: Dict) -> str:
        """Format ROI data as CSV."""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=['lead_id', 'acquisition_cost', 'deal_value', 'deal_closed', 'roi'])
        writer.writeheader()
        writer.writerows(data['details'])
        return output.getvalue()
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _generate_insights(self, metrics: Any, roi_records: List) -> List[str]:
        """Generate key insights from data."""
        insights = []
        
        if metrics:
            if metrics.engagement_rate > 0.3:
                insights.append(f"Excellent engagement rate of {metrics.engagement_rate*100:.1f}%")
            if metrics.conversion_rate > 0.1:
                insights.append(f"Strong conversion rate of {metrics.conversion_rate*100:.1f}%")
        
        if roi_records:
            total_cost = sum(r.acquisition_cost for r in roi_records)
            total_revenue = sum(r.deal_value or 0 for r in roi_records if r.deal_closed)
            if total_revenue > 0 and total_cost > 0:
                roi = ((total_revenue - total_cost) / total_cost) * 100
                if roi > 100:
                    insights.append(f"Outstanding ROI of {roi:.1f}%")
        
        if not insights:
            insights.append("Campaign metrics available for analysis")
        
        return insights
    
    def _generate_recommendations(self, metrics: Any) -> List[str]:
        """Generate recommendations based on metrics."""
        recs = []
        
        if metrics:
            if metrics.engagement_rate < 0.1:
                recs.append("Low engagement rate - consider reviewing message content")
            if metrics.conversion_rate < 0.05:
                recs.append("Low conversion rate - evaluate lead quality")
            if metrics.average_response_time and metrics.average_response_time > 48:
                recs.append("Long response times - may need faster follow-up")
        
        if not recs:
            recs.append("Continue current campaign strategy")
        
        return recs
    
    def _generate_channel_recommendations(self, channels: List[Dict]) -> List[str]:
        """Generate channel optimization recommendations."""
        recs = []
        
        if channels:
            best = channels[0]
            recs.append(f"Increase budget allocation to {best['channel']} (highest efficiency)")
            
            worst = channels[-1]
            if worst['efficiency_score'] < 50:
                recs.append(f"Review {worst['channel']} strategy or consider deprioritizing")
        
        return recs
    
    def _count_by_grade(self, leads: List) -> Dict[str, int]:
        """Count leads by grade."""
        counts = {}
        for lead in leads:
            grade = lead.grade or 'UNGRADED'
            counts[grade] = counts.get(grade, 0) + 1
        return counts
    
    def _count_by_status(self, leads: List) -> Dict[str, int]:
        """Count leads by status."""
        counts = {}
        for lead in leads:
            status = lead.status or 'UNKNOWN'
            counts[status] = counts.get(status, 0) + 1
        return counts
    
    def _count_by_source(self, leads: List) -> Dict[str, int]:
        """Count leads by source."""
        counts = {}
        for lead in leads:
            source = lead.source.value if lead.source else 'UNKNOWN'
            counts[source] = counts.get(source, 0) + 1
        return counts
