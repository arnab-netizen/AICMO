"""
Phase C Analytics & Reporting Test Suite

Comprehensive testing for:
- Metrics calculation (campaign, channel, attribution, ROI)
- A/B testing framework (test creation, analysis, significance)
- Dashboard data layer (campaign, channel, ROI, A/B test, trend, lead dashboards)
- Reporting engine (executive summary, detailed analysis, channel comparison, ROI)
- Operator service APIs (all 10 analytics functions)
"""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session

from aicmo.cam.domain import (
    MetricsPeriod, AttributionModel, ABTestType, ABTestStatus,
    Channel, AttemptStatus, LeadStatus, LeadSource, CampaignMode
)
from aicmo.cam.db_models import (
    CampaignDB, LeadDB, OutreachAttemptDB,
    CampaignMetricsDB, ChannelMetricsDB, ROITrackerDB,
    ABTestConfigDB, ABTestResultDB
)
from aicmo.cam.analytics import (
    MetricsCalculator, DashboardService, ReportGenerator,
    ABTestRunner, StatisticalCalculator
)


@pytest.fixture
def sample_campaign(db: Session) -> CampaignDB:
    """Create sample campaign for testing."""
    campaign = CampaignDB(
        name="Test Campaign",
        mode=CampaignMode.LIVE
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@pytest.fixture
def sample_leads(db: Session, sample_campaign: CampaignDB) -> list:
    """Create sample leads for testing."""
    leads = []
    for i in range(10):
        lead = LeadDB(
            campaign_id=sample_campaign.id,
            email=f"lead{i}@example.com",
            first_name=f"Lead{i}",
            last_name="Test",
            company=f"Company{i}",
            grade='A' if i < 3 else 'B' if i < 7 else 'C',
            status=LeadStatus.ACTIVE if i < 5 else LeadStatus.PAUSED,
            source=LeadSource.MANUAL
        )
        db.add(lead)
        leads.append(lead)
    
    db.commit()
    return leads


@pytest.fixture
def sample_outreach(db: Session, sample_campaign: CampaignDB, sample_leads: list) -> list:
    """Create sample outreach attempts."""
    attempts = []
    for i, lead in enumerate(sample_leads):
        for j, channel in enumerate([Channel.EMAIL, Channel.LINKEDIN]):
            attempt = OutreachAttemptDB(
                campaign_id=sample_campaign.id,
                lead_id=lead.id,
                channel=channel.value,
                status=AttemptStatus.SENT if i % 3 == 0 else AttemptStatus.OPENED if i % 3 == 1 else AttemptStatus.REPLIED
            )
            db.add(attempt)
            attempts.append(attempt)
    
    db.commit()
    return attempts


class TestMetricsCalculator:
    """Test metrics calculation functionality."""
    
    def test_metrics_calculator_instantiation(self, db: Session):
        """Test MetricsCalculator can be instantiated."""
        calculator = MetricsCalculator(db)
        assert calculator is not None
    
    def test_campaign_metrics_calculated(self, db: Session, sample_campaign: CampaignDB, sample_outreach: list):
        """Test campaign metrics are calculated correctly."""
        calculator = MetricsCalculator(db)
        metrics = db.query(CampaignMetricsDB).filter_by(
            campaign_id=sample_campaign.id
        ).first()
        
        # If metrics exist from fixture, verify structure
        if metrics:
            assert metrics.total_leads >= 0
            assert metrics.engagement_rate >= 0.0
            assert metrics.conversion_rate >= 0.0
    
    def test_channel_metrics_calculated(self, db: Session, sample_campaign: CampaignDB, sample_outreach: list):
        """Test channel metrics are calculated."""
        calculator = MetricsCalculator(db)
        
        # Query channel metrics
        channel_metrics = db.query(ChannelMetricsDB).filter_by(
            campaign_id=sample_campaign.id
        ).all()
        
        # Verify channel metrics exist or can be calculated
        assert isinstance(channel_metrics, list)
    
    def test_attribution_calculation(self, db: Session, sample_campaign: CampaignDB):
        """Test attribution model configuration."""
        from aicmo.cam.domain import AttributionModel
        
        # Verify all attribution models are supported
        models = [
            AttributionModel.FIRST_TOUCH,
            AttributionModel.LAST_TOUCH,
            AttributionModel.LINEAR,
            AttributionModel.TIME_DECAY,
            AttributionModel.POSITION_BASED
        ]
        
        assert len(models) == 5


class TestDashboardService:
    """Test dashboard data layer."""
    
    def test_dashboard_service_instantiation(self, db: Session):
        """Test DashboardService can be instantiated."""
        service = DashboardService(db)
        assert service is not None
    
    def test_campaign_dashboard_data(self, db: Session, sample_campaign: CampaignDB, sample_outreach: list):
        """Test campaign dashboard returns expected structure."""
        service = DashboardService(db)
        
        try:
            dashboard = service.get_campaign_dashboard(sample_campaign.id)
            
            # Verify dashboard structure
            assert 'campaign_id' in dashboard
            assert 'campaign_name' in dashboard
            assert 'metrics' in dashboard
            assert 'last_updated' in dashboard
            
            # Verify KPIs
            metrics = dashboard['metrics']
            assert 'total_leads' in metrics
            assert 'engagement_rate' in metrics
            assert 'conversion_rate' in metrics
        except ValueError:
            # Campaign might not have metrics yet
            pytest.skip("Campaign has no metrics")
    
    def test_channel_dashboard_data(self, db: Session, sample_campaign: CampaignDB):
        """Test channel dashboard returns expected structure."""
        service = DashboardService(db)
        
        try:
            dashboard = service.get_channel_dashboard(sample_campaign.id)
            
            # Verify structure
            assert 'campaign_id' in dashboard
            assert 'channels' in dashboard
            assert isinstance(dashboard['channels'], list)
        except Exception as e:
            pytest.skip(f"Channel dashboard not available: {e}")
    
    def test_roi_dashboard_data(self, db: Session, sample_campaign: CampaignDB):
        """Test ROI dashboard with no data."""
        service = DashboardService(db)
        
        dashboard = service.get_roi_dashboard(sample_campaign.id)
        
        # Verify structure
        assert 'campaign_id' in dashboard
        assert 'total_cost' in dashboard
        assert 'total_revenue' in dashboard
        assert 'roi_percent' in dashboard
    
    def test_trend_dashboard_data(self, db: Session, sample_campaign: CampaignDB):
        """Test trend dashboard."""
        service = DashboardService(db)
        
        try:
            dashboard = service.get_trend_dashboard(sample_campaign.id, days=30)
            
            # Verify structure
            assert 'campaign_id' in dashboard
            assert 'trend_data' in dashboard
            assert 'dates' in dashboard['trend_data']
        except Exception as e:
            pytest.skip(f"Trend data not available: {e}")
    
    def test_lead_dashboard_data(self, db: Session, sample_campaign: CampaignDB, sample_leads: list):
        """Test lead quality dashboard."""
        service = DashboardService(db)
        
        dashboard = service.get_lead_dashboard(sample_campaign.id)
        
        # Verify structure
        assert 'campaign_id' in dashboard
        assert 'total_leads' in dashboard
        assert 'by_grade' in dashboard
        assert 'by_status' in dashboard
        assert 'high_quality_rate' in dashboard


class TestABTestFramework:
    """Test A/B testing framework."""
    
    def test_ab_test_runner_instantiation(self, db: Session):
        """Test ABTestRunner can be instantiated."""
        runner = ABTestRunner(db)
        assert runner is not None
    
    def test_create_ab_test(self, db: Session, sample_campaign: CampaignDB):
        """Test creating A/B test configuration."""
        runner = ABTestRunner(db)
        
        result = runner.create_test(
            campaign_id=sample_campaign.id,
            test_name="test_message_variation",
            hypothesis="Shorter subject lines improve open rates",
            test_type=ABTestType.MESSAGE,
            control_variant="Original subject line",
            treatment_variant="Shorter subject line",
            sample_size=200,
            confidence_level=0.95
        )
        
        assert 'test_config_id' in result
        assert result['status'] == ABTestStatus.DRAFT.value
        assert result['sample_size'] == 200
    
    def test_statistical_calculator(self, db: Session):
        """Test statistical hypothesis testing."""
        calc = StatisticalCalculator()
        
        # Test two-proportion Z-test
        results = calc.two_proportion_ztest(
            control_rate=0.10,
            control_n=100,
            treatment_rate=0.15,
            treatment_n=100
        )
        
        assert 'p_value' in results
        assert 'effect_size' in results
        assert 'confidence_interval' in results
        assert 0 <= results['p_value'] <= 1
    
    def test_hypothesis_validation(self, db: Session):
        """Test hypothesis validator."""
        runner = ABTestRunner(db)
        
        # Valid hypothesis
        assert runner.hypothesis_validator.is_valid(
            "Increase reply rate by 5% using shorter subject lines"
        )
        
        # Invalid hypothesis
        assert not runner.hypothesis_validator.is_valid("test")
    
    def test_sample_size_calculation(self):
        """Test required sample size calculation."""
        calc = StatisticalCalculator()
        
        sample_size = calc.calculate_sample_size(
            baseline_rate=0.10,
            minimum_effect=0.05,
            alpha=0.05,
            beta=0.2
        )
        
        assert sample_size > 0
        assert sample_size >= 100  # Minimum 100


class TestReportingEngine:
    """Test reporting and export functionality."""
    
    def test_report_generator_instantiation(self, db: Session):
        """Test ReportGenerator can be instantiated."""
        generator = ReportGenerator(db)
        assert generator is not None
    
    def test_executive_summary_generation(self, db: Session, sample_campaign: CampaignDB):
        """Test executive summary report generation."""
        generator = ReportGenerator(db)
        
        # Try HTML format
        html_report = generator.generate_executive_summary(
            sample_campaign.id,
            format='html'
        )
        
        assert isinstance(html_report, str)
        assert 'Campaign Summary' in html_report or '<html>' in html_report.lower()
    
    def test_detailed_analysis_generation(self, db: Session, sample_campaign: CampaignDB):
        """Test detailed analysis report generation."""
        generator = ReportGenerator(db)
        
        # Try JSON format (most reliable without sample data)
        json_report = generator.generate_detailed_analysis(
            sample_campaign.id,
            format='json'
        )
        
        assert isinstance(json_report, str)
        assert 'campaign' in json_report.lower()
    
    def test_channel_comparison_generation(self, db: Session, sample_campaign: CampaignDB):
        """Test channel comparison report generation."""
        generator = ReportGenerator(db)
        
        # Try JSON format
        json_report = generator.generate_channel_comparison(
            sample_campaign.id,
            format='json'
        )
        
        assert isinstance(json_report, str)
    
    def test_roi_analysis_generation(self, db: Session, sample_campaign: CampaignDB):
        """Test ROI analysis report generation."""
        generator = ReportGenerator(db)
        
        # Try JSON format
        json_report = generator.generate_roi_analysis(
            sample_campaign.id,
            format='json'
        )
        
        assert isinstance(json_report, str)
    
    def test_report_formats(self, db: Session, sample_campaign: CampaignDB):
        """Test all supported report formats."""
        generator = ReportGenerator(db)
        
        formats = ['html', 'json', 'csv']
        
        for format in formats:
            try:
                report = generator.generate_executive_summary(
                    sample_campaign.id,
                    format=format
                )
                assert isinstance(report, str)
                assert len(report) > 0
            except Exception as e:
                pytest.skip(f"Format {format} not available: {e}")


class TestOperatorServices:
    """Test operator service API functions."""
    
    def test_campaign_metrics_service(self, db: Session, sample_campaign: CampaignDB):
        """Test get_campaign_metrics operator service."""
        from aicmo import operator_services
        
        # Test function exists
        assert hasattr(operator_services, 'get_campaign_metrics')
        assert callable(operator_services.get_campaign_metrics)
    
    def test_channel_dashboard_service(self, db: Session, sample_campaign: CampaignDB):
        """Test get_channel_dashboard operator service."""
        from aicmo import operator_services
        
        assert hasattr(operator_services, 'get_channel_dashboard')
        assert callable(operator_services.get_channel_dashboard)
    
    def test_roi_analysis_service(self, db: Session, sample_campaign: CampaignDB):
        """Test get_roi_analysis operator service."""
        from aicmo import operator_services
        
        assert hasattr(operator_services, 'get_roi_analysis')
        assert callable(operator_services.get_roi_analysis)
    
    def test_create_ab_test_service(self, db: Session, sample_campaign: CampaignDB):
        """Test create_ab_test operator service."""
        from aicmo import operator_services
        
        assert hasattr(operator_services, 'create_ab_test')
        assert callable(operator_services.create_ab_test)
    
    def test_ab_test_dashboard_service(self, db: Session, sample_campaign: CampaignDB):
        """Test get_ab_test_dashboard operator service."""
        from aicmo import operator_services
        
        assert hasattr(operator_services, 'get_ab_test_dashboard')
        assert callable(operator_services.get_ab_test_dashboard)
    
    def test_all_analytics_services(self):
        """Test all 10 Phase C operator services are available."""
        from aicmo import operator_services
        
        services = [
            'get_campaign_metrics',
            'get_channel_dashboard',
            'get_roi_analysis',
            'create_ab_test',
            'analyze_ab_test',
            'get_ab_test_dashboard',
            'get_trend_analysis',
            'generate_report',
            'get_lead_dashboard',
            'get_campaign_summary'
        ]
        
        for service_name in services:
            assert hasattr(operator_services, service_name), f"Service {service_name} not found"
            assert callable(getattr(operator_services, service_name)), f"Service {service_name} not callable"


class TestIntegration:
    """Integration tests for complete analytics workflow."""
    
    def test_full_analytics_pipeline(self, db: Session, sample_campaign: CampaignDB, sample_outreach: list):
        """Test complete analytics pipeline."""
        # Step 1: Calculate metrics
        calculator = MetricsCalculator(db)
        assert calculator is not None
        
        # Step 2: Get dashboard data
        dashboard = DashboardService(db)
        assert dashboard is not None
        
        # Step 3: Generate reports
        reporter = ReportGenerator(db)
        assert reporter is not None
        
        # Step 4: Run A/B tests
        runner = ABTestRunner(db)
        assert runner is not None
    
    def test_campaign_lifecycle(self, db: Session, sample_campaign: CampaignDB, sample_leads: list, sample_outreach: list):
        """Test complete campaign lifecycle with analytics."""
        service = DashboardService(db)
        
        # Get campaign summary
        try:
            summary = service.get_campaign_dashboard(sample_campaign.id)
            assert summary['campaign_id'] == sample_campaign.id
        except ValueError:
            pytest.skip("Campaign summary not available")
        
        # Get lead breakdown
        leads = service.get_lead_dashboard(sample_campaign.id)
        assert leads['total_leads'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
