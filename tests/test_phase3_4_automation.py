"""
Phase 3 & 4: Follow-up engine and decision engine tests.
"""

import pytest
from aicmo.cam.services.decision_engine import CampaignMetricsSnapshot, DecisionEngine


class TestCampaignMetrics:
    """Tests for campaign metrics calculation."""
    
    def test_metrics_snapshot_creation(self):
        """Test metrics snapshot can be created."""
        metrics = CampaignMetricsSnapshot(
            campaign_id=1,
            campaign_name="Test Campaign",
            sent_count=100,
            delivered_count=98,
            reply_count=10,
            positive_count=8,
            negative_count=1,
            unsub_count=1,
            bounce_count=2,
            ooo_count=1,
        )
        assert metrics.campaign_id == 1
        assert metrics.sent_count == 100
    
    def test_reply_rate_calculation(self):
        """Test reply rate calculation."""
        metrics = CampaignMetricsSnapshot(
            campaign_id=1,
            campaign_name="Test",
            sent_count=100,
            delivered_count=100,
            reply_count=20,
            positive_count=10,
            negative_count=5,
            unsub_count=2,
            bounce_count=3,
            ooo_count=1,
        )
        
        assert metrics.reply_rate == 20.0
    
    def test_positive_rate_calculation(self):
        """Test positive rate calculation."""
        metrics = CampaignMetricsSnapshot(
            campaign_id=1,
            campaign_name="Test",
            sent_count=100,
            delivered_count=100,
            reply_count=20,
            positive_count=15,
            negative_count=5,
            unsub_count=0,
            bounce_count=0,
            ooo_count=0,
        )
        
        assert metrics.positive_rate == 15.0
    
    def test_bounce_rate_calculation(self):
        """Test bounce rate calculation."""
        metrics = CampaignMetricsSnapshot(
            campaign_id=1,
            campaign_name="Test",
            sent_count=100,
            delivered_count=97,
            reply_count=10,
            positive_count=8,
            negative_count=2,
            unsub_count=0,
            bounce_count=3,
            ooo_count=0,
        )
        
        assert metrics.bounce_rate == 3.0
    
    def test_reply_rate_with_zero_sends(self):
        """Test reply rate with no sends (avoid division by zero)."""
        metrics = CampaignMetricsSnapshot(
            campaign_id=1,
            campaign_name="Test",
            sent_count=0,
            delivered_count=0,
            reply_count=0,
            positive_count=0,
            negative_count=0,
            unsub_count=0,
            bounce_count=0,
            ooo_count=0,
        )
        
        assert metrics.reply_rate == 0.0
        assert metrics.positive_rate == 0.0
        assert metrics.bounce_rate == 0.0
    
    def test_metrics_string_representation(self):
        """Test metrics can be pretty-printed."""
        metrics = CampaignMetricsSnapshot(
            campaign_id=1,
            campaign_name="Test Campaign",
            sent_count=100,
            delivered_count=98,
            reply_count=10,
            positive_count=8,
            negative_count=1,
            unsub_count=1,
            bounce_count=2,
            ooo_count=0,
        )
        
        str_repr = str(metrics)
        assert "Test Campaign" in str_repr
        assert "Sent: 100" in str_repr
        assert "Replies: 10" in str_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
