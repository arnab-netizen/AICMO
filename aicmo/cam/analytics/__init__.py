"""
Analytics module for AICMO CAM system.

Provides metrics calculation, A/B testing, dashboards, and reporting.
"""

from aicmo.cam.analytics.metrics_calculator import MetricsCalculator
from aicmo.cam.analytics.ab_testing import ABTestRunner, StatisticalCalculator, HypothesisValidator
from aicmo.cam.analytics.dashboard import DashboardService
from aicmo.cam.analytics.reporting import ReportGenerator

__all__ = [
    'MetricsCalculator',
    'ABTestRunner',
    'StatisticalCalculator',
    'HypothesisValidator',
    'DashboardService',
    'ReportGenerator',
]
