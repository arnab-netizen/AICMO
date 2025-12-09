"""Tests for Analytics & Attribution Engine.

Stage A: Analytics engine tests
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import tempfile
import os

from aicmo.domain.intake import ClientIntake
from aicmo.analytics.domain import (
    AttributionModel,
    ChannelType,
    MetricType,
    TouchPoint,
    ConversionEvent,
    ChannelPerformance,
    AttributionReport,
    MMMAnalysis,
    PerformanceDashboard,
    CampaignAnalysis,
)
from aicmo.analytics.service import (
    calculate_attribution,
    generate_mmm_analysis,
    generate_performance_dashboard,
    analyze_campaign,
)
from aicmo.learning.event_types import EventType


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_intake():
    """Sample client intake for testing."""
    return ClientIntake(
        brand_name="AnalyticsTestCo",
        industry="E-commerce",
        product_service="Online retail platform",
        primary_goal="Maximize ROAS",
        target_audiences=["Online shoppers", "Deal seekers"]
    )


@pytest.fixture
def sample_conversion():
    """Sample conversion event for testing."""
    return ConversionEvent(
        conversion_id="conv-1",
        customer_id="cust-1",
        conversion_type="purchase",
        conversion_value=150.0,
        timestamp=datetime.now(),
        touchpoints=[
            TouchPoint(
                touchpoint_id="tp-1",
                customer_id="cust-1",
                channel=ChannelType.PAID_SEARCH,
                timestamp=datetime.now() - timedelta(days=1)
            ),
            TouchPoint(
                touchpoint_id="tp-2",
                customer_id="cust-1",
                channel=ChannelType.PAID_SOCIAL,
                timestamp=datetime.now() - timedelta(hours=2)
            )
        ],
        primary_channel=ChannelType.PAID_SOCIAL
    )


# ═══════════════════════════════════════════════════════════════════════
# Domain Model Tests
# ═══════════════════════════════════════════════════════════════════════


class TestTouchPointDomain:
    """Test TouchPoint domain model."""
    
    def test_touchpoint_creation(self):
        """Test creating a touchpoint."""
        touchpoint = TouchPoint(
            touchpoint_id="tp-123",
            customer_id="cust-456",
            channel=ChannelType.PAID_SEARCH,
            campaign_name="Spring Sale",
            timestamp=datetime.now(),
            interaction_type="click",
            attributed_value=50.0
        )
        
        assert touchpoint.channel == ChannelType.PAID_SEARCH
        assert touchpoint.attributed_value == 50.0


class TestConversionEventDomain:
    """Test ConversionEvent domain model."""
    
    def test_conversion_creation(self, sample_conversion):
        """Test creating a conversion event."""
        assert sample_conversion.conversion_value == 150.0
        assert len(sample_conversion.touchpoints) == 2
        assert sample_conversion.primary_channel == ChannelType.PAID_SOCIAL


class TestChannelPerformanceDomain:
    """Test ChannelPerformance domain model."""
    
    def test_channel_performance_creation(self):
        """Test creating channel performance."""
        performance = ChannelPerformance(
            channel=ChannelType.PAID_SEARCH,
            brand_name="TestBrand",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            impressions=100000,
            clicks=5000,
            conversions=250,
            cost=10000.0,
            revenue=50000.0,
            ctr=5.0,
            roas=5.0
        )
        
        assert performance.channel == ChannelType.PAID_SEARCH
        assert performance.roas == 5.0


# ═══════════════════════════════════════════════════════════════════════
# Service Function Tests
# ═══════════════════════════════════════════════════════════════════════


class TestAttributionCalculation:
    """Test attribution calculation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_calculate_attribution_returns_report(self, temp_db, sample_intake, sample_conversion):
        """Test that calculate_attribution returns a report."""
        report = calculate_attribution(
            sample_intake,
            conversions=[sample_conversion],
            model=AttributionModel.LINEAR
        )
        
        assert isinstance(report, AttributionReport)
        assert report.brand_name == sample_intake.brand_name
        assert report.attribution_model == AttributionModel.LINEAR
    
    def test_report_has_channel_performance(self, temp_db, sample_intake, sample_conversion):
        """Test that report includes channel performance."""
        report = calculate_attribution(sample_intake, [sample_conversion])
        
        assert len(report.channel_performance) > 0
        assert report.total_conversions > 0
        assert report.overall_roas >= 0
    
    def test_attribution_logs_event(self, temp_db, sample_intake, sample_conversion):
        """Test that attribution calculation logs learning event."""
        with patch('aicmo.analytics.service.log_event') as mock_log:
            calculate_attribution(sample_intake, [sample_conversion])
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.ANALYTICS_REPORT_GENERATED.value


class TestMMMAnalysis:
    """Test MMM analysis generation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_generate_mmm_returns_analysis(self, temp_db, sample_intake):
        """Test that generate_mmm_analysis returns analysis."""
        analysis = generate_mmm_analysis(sample_intake, historical_data_days=90)
        
        assert isinstance(analysis, MMMAnalysis)
        assert analysis.brand_name == sample_intake.brand_name
        assert len(analysis.channel_contributions) > 0
    
    def test_mmm_has_optimization_recommendations(self, temp_db, sample_intake):
        """Test that MMM includes optimization recommendations."""
        analysis = generate_mmm_analysis(sample_intake)
        
        assert len(analysis.recommended_budget_allocation) > 0
        assert len(analysis.predicted_roi_by_channel) > 0
        assert 0 <= analysis.model_r_squared <= 1
    
    def test_mmm_logs_event(self, temp_db, sample_intake):
        """Test that MMM analysis logs learning event."""
        with patch('aicmo.analytics.service.log_event') as mock_log:
            generate_mmm_analysis(sample_intake)
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.ANALYTICS_REPORT_GENERATED.value


class TestPerformanceDashboard:
    """Test performance dashboard generation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_generate_dashboard_returns_dashboard(self, temp_db, sample_intake):
        """Test that generate_performance_dashboard returns dashboard."""
        dashboard = generate_performance_dashboard(sample_intake, period_days=7)
        
        assert isinstance(dashboard, PerformanceDashboard)
        assert dashboard.brand_name == sample_intake.brand_name
        assert len(dashboard.current_metrics) > 0
    
    def test_dashboard_has_comparisons(self, temp_db, sample_intake):
        """Test that dashboard includes period comparisons."""
        dashboard = generate_performance_dashboard(sample_intake)
        
        assert len(dashboard.previous_period_metrics) > 0
        assert len(dashboard.percent_changes) > 0
    
    def test_dashboard_logs_event(self, temp_db, sample_intake):
        """Test that dashboard generation logs learning event."""
        with patch('aicmo.analytics.service.log_event') as mock_log:
            generate_performance_dashboard(sample_intake)
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.ANALYTICS_REPORT_GENERATED.value


class TestCampaignAnalysis:
    """Test campaign analysis."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_analyze_campaign_returns_analysis(self, temp_db, sample_intake):
        """Test that analyze_campaign returns analysis."""
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()
        
        analysis = analyze_campaign(
            sample_intake,
            campaign_id="camp-123",
            campaign_name="Holiday Sale",
            start_date=start,
            end_date=end
        )
        
        assert isinstance(analysis, CampaignAnalysis)
        assert analysis.brand_name == sample_intake.brand_name
        assert analysis.campaign_name == "Holiday Sale"
    
    def test_campaign_has_performance_metrics(self, temp_db, sample_intake):
        """Test that campaign analysis includes performance metrics."""
        start = datetime.now() - timedelta(days=30)
        end = datetime.now()
        
        analysis = analyze_campaign(
            sample_intake,
            campaign_id="camp-123",
            campaign_name="Test Campaign",
            start_date=start,
            end_date=end
        )
        
        assert analysis.total_spend > 0
        assert analysis.roas > 0
        assert len(analysis.optimization_recommendations) > 0
    
    def test_campaign_analysis_logs_event(self, temp_db, sample_intake):
        """Test that campaign analysis logs learning event."""
        with patch('aicmo.analytics.service.log_event') as mock_log:
            start = datetime.now() - timedelta(days=30)
            end = datetime.now()
            
            analyze_campaign(
                sample_intake,
                campaign_id="camp-123",
                campaign_name="Test",
                start_date=start,
                end_date=end
            )
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.ANALYTICS_REPORT_GENERATED.value


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════


class TestAnalyticsEngineIntegration:
    """Test analytics engine integration."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_analytics_workflow(self, temp_db):
        """Test complete analytics workflow."""
        # Create intake
        intake = ClientIntake(
            brand_name="WorkflowTest",
            industry="SaaS",
            product_service="Project management software",
            primary_goal="Optimize marketing spend",
            target_audiences=["Project managers", "Teams"]
        )
        
        # Create sample conversion
        conversion = ConversionEvent(
            conversion_id="conv-1",
            customer_id="cust-1",
            conversion_type="subscription",
            conversion_value=99.0,
            timestamp=datetime.now(),
            touchpoints=[]
        )
        
        # Calculate attribution
        attribution = calculate_attribution(intake, [conversion])
        assert attribution.total_conversions > 0
        
        # Generate MMM analysis
        mmm = generate_mmm_analysis(intake)
        assert len(mmm.channel_contributions) > 0
        
        # Generate dashboard
        dashboard = generate_performance_dashboard(intake)
        assert len(dashboard.current_metrics) > 0
        
        # Analyze campaign
        campaign = analyze_campaign(
            intake,
            campaign_id="camp-1",
            campaign_name="Q4 Push",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        assert campaign.roas > 0
