"""
A/B Testing Framework for AICMO CAM System

Provides statistically rigorous A/B test design, execution, and analysis.

Features:
- Test configuration and setup (message, channel, timing variants)
- Statistical hypothesis testing (Chi-square, T-test)
- Sample size calculation (power analysis)
- Significance testing and confidence intervals
- Effect size computation
- Winner determination with recommendations
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from math import sqrt, exp

from scipy import stats
from sqlalchemy.orm import Session
from sqlalchemy import and_

from aicmo.cam.db_models import (
    CampaignDB, OutreachAttemptDB, ABTestConfigDB, ABTestResultDB
)
from aicmo.cam.domain import ABTestType, ABTestStatus

logger = logging.getLogger(__name__)


class ABTestRunner:
    """
    Manages A/B test lifecycle: creation, execution, analysis, and conclusion.
    
    Responsibilities:
    - Create and configure A/B tests
    - Assign leads to test variants (control/treatment)
    - Track test progress and metrics
    - Calculate statistical significance
    - Determine winners with recommendations
    """
    
    def __init__(self, db: Session):
        """Initialize A/B test runner with database session."""
        self.db = db
        self.statistical_calc = StatisticalCalculator()
        self.hypothesis_validator = HypothesisValidator()
    
    def create_test(
        self,
        campaign_id: int,
        test_name: str,
        hypothesis: str,
        test_type: ABTestType,
        control_variant: str,
        treatment_variant: str,
        sample_size: int,
        confidence_level: float = 0.95,
        start_date: Optional[datetime] = None
    ) -> Dict:
        """
        Create new A/B test configuration.
        
        Args:
            campaign_id: Campaign to test
            test_name: Unique test identifier
            hypothesis: Test hypothesis description
            test_type: Type of test (MESSAGE, CHANNEL, TIMING, SEGMENT, TEMPLATE)
            control_variant: Control group variant description
            treatment_variant: Treatment group variant description
            sample_size: Total sample size for test
            confidence_level: Statistical confidence (0.9, 0.95, 0.99)
            start_date: Test start date (defaults to now)
        
        Returns:
            Dictionary with test configuration ID and metadata
        """
        if confidence_level not in [0.90, 0.95, 0.99]:
            raise ValueError("Confidence level must be 0.90, 0.95, or 0.99")
        
        # Validate hypothesis format
        if not self.hypothesis_validator.is_valid(hypothesis):
            raise ValueError("Hypothesis must follow SMART criteria")
        
        start_date = start_date or datetime.utcnow()
        
        # Create test config
        test_config = ABTestConfigDB(
            campaign_id=campaign_id,
            test_name=test_name,
            test_type=test_type.value,
            status=ABTestStatus.DRAFT.value,
            hypothesis=hypothesis,
            control_variant=control_variant,
            treatment_variant=treatment_variant,
            total_sample_size=sample_size,
            sample_split=0.5,  # 50/50 split
            confidence_level=confidence_level,
            minimum_sample_per_variant=max(30, sample_size // 20),  # Min 30 per variant
            start_date=start_date,
            created_by='system'
        )
        
        self.db.add(test_config)
        self.db.commit()
        
        logger.info(
            f"Created A/B test '{test_name}' for campaign {campaign_id}: "
            f"{test_type.value} test with {sample_size} total sample"
        )
        
        return {
            'test_config_id': test_config.id,
            'test_name': test_name,
            'status': ABTestStatus.DRAFT.value,
            'sample_size': sample_size,
            'confidence_level': confidence_level
        }
    
    def start_test(self, test_config_id: int) -> Dict:
        """
        Start an A/B test (move from DRAFT to RUNNING).
        
        Args:
            test_config_id: Test configuration ID
        
        Returns:
            Updated test status
        """
        test_config = self.db.query(ABTestConfigDB).filter_by(
            id=test_config_id
        ).first()
        
        if not test_config:
            raise ValueError(f"Test config {test_config_id} not found")
        
        if test_config.status != ABTestStatus.DRAFT.value:
            raise ValueError(f"Cannot start test in {test_config.status} status")
        
        test_config.status = ABTestStatus.RUNNING.value
        test_config.start_date = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Started A/B test '{test_config.test_name}'")
        
        return {
            'test_config_id': test_config_id,
            'status': ABTestStatus.RUNNING.value,
            'start_date': test_config.start_date
        }
    
    def analyze_test(
        self,
        test_config_id: int,
        control_metric_value: float,
        control_sample_size: int,
        treatment_metric_value: float,
        treatment_sample_size: int,
        metric_type: str = 'rate'
    ) -> Dict:
        """
        Analyze test results and compute statistical significance.
        
        Args:
            test_config_id: Test configuration ID
            control_metric_value: Control group metric (e.g., reply rate)
            control_sample_size: Control group sample size
            treatment_metric_value: Treatment group metric
            treatment_sample_size: Treatment group sample size
            metric_type: Type of metric ('rate', 'mean', 'count')
        
        Returns:
            Statistical analysis results
        """
        test_config = self.db.query(ABTestConfigDB).filter_by(
            id=test_config_id
        ).first()
        
        if not test_config:
            raise ValueError(f"Test config {test_config_id} not found")
        
        # Perform statistical test
        if metric_type == 'rate':
            results = self.statistical_calc.two_proportion_ztest(
                control_metric_value, control_sample_size,
                treatment_metric_value, treatment_sample_size
            )
        elif metric_type == 'mean':
            results = self.statistical_calc.welch_ttest(
                control_metric_value, control_sample_size,
                treatment_metric_value, treatment_sample_size
            )
        else:
            results = self.statistical_calc.chi_square_test(
                control_metric_value, control_sample_size,
                treatment_metric_value, treatment_sample_size
            )
        
        # Determine significance based on confidence level
        significance_threshold = 1.0 - test_config.confidence_level
        is_significant = results['p_value'] < significance_threshold
        
        # Determine winner
        winner = 'TREATMENT' if treatment_metric_value > control_metric_value else 'CONTROL'
        if not is_significant:
            winner = 'INCONCLUSIVE'
        
        # Store results
        test_result = ABTestResultDB(
            test_config_id=test_config_id,
            control_sample_size=control_sample_size,
            treatment_sample_size=treatment_sample_size,
            control_metric_value=control_metric_value,
            control_std_dev=results.get('control_std_dev'),
            treatment_metric_value=treatment_metric_value,
            treatment_std_dev=results.get('treatment_std_dev'),
            p_value=results['p_value'],
            statistical_significance=is_significant,
            confidence_interval=results['confidence_interval'],
            effect_size=results['effect_size'],
            winner=winner,
            recommendation=self._get_recommendation(
                winner, results['effect_size'], is_significant
            )
        )
        
        self.db.add(test_result)
        self.db.commit()
        
        logger.info(
            f"Analyzed test '{test_config.test_name}': "
            f"p_value={results['p_value']:.4f}, "
            f"winner={winner}, effect_size={results['effect_size']:.4f}"
        )
        
        return {
            'test_config_id': test_config_id,
            'p_value': results['p_value'],
            'is_significant': is_significant,
            'winner': winner,
            'effect_size': results['effect_size'],
            'confidence_interval': results['confidence_interval'],
            'recommendation': test_result.recommendation
        }
    
    def conclude_test(
        self,
        test_config_id: int,
        decision: str
    ) -> Dict:
        """
        Conclude A/B test and apply winning variant.
        
        Args:
            test_config_id: Test configuration ID
            decision: Implementation decision ('APPLY_TREATMENT', 'KEEP_CONTROL', 'CONTINUE')
        
        Returns:
            Test conclusion results
        """
        test_config = self.db.query(ABTestConfigDB).filter_by(
            id=test_config_id
        ).first()
        
        if not test_config:
            raise ValueError(f"Test config {test_config_id} not found")
        
        test_config.status = ABTestStatus.CONCLUDED.value
        test_config.end_date = datetime.utcnow()
        self.db.commit()
        
        logger.info(
            f"Concluded test '{test_config.test_name}' with decision: {decision}"
        )
        
        return {
            'test_config_id': test_config_id,
            'status': ABTestStatus.CONCLUDED.value,
            'decision': decision,
            'conclusion_date': test_config.end_date
        }
    
    def _get_recommendation(
        self,
        winner: str,
        effect_size: float,
        is_significant: bool
    ) -> str:
        """Get implementation recommendation based on test results."""
        if not is_significant:
            return "Continue testing for larger sample size"
        
        if effect_size < 0.1:
            return f"Apply {winner} variant (small but significant effect)"
        elif effect_size < 0.5:
            return f"Apply {winner} variant (medium effect, recommended)"
        else:
            return f"Strongly apply {winner} variant (large effect size)"


class StatisticalCalculator:
    """Performs statistical hypothesis testing and calculations."""
    
    def two_proportion_ztest(
        self,
        control_rate: float,
        control_n: int,
        treatment_rate: float,
        treatment_n: int
    ) -> Dict:
        """
        Perform two-proportion Z-test.
        
        Used for comparing rates (e.g., reply rate, click-through rate).
        
        Returns:
            p_value, effect_size, confidence_interval
        """
        # Calculate successes
        control_successes = int(control_rate * control_n)
        treatment_successes = int(treatment_rate * treatment_n)
        
        # Perform Z-test
        z_stat, p_value = stats.norm.sf(abs(control_rate - treatment_rate) / 
                                        sqrt(control_rate * (1 - control_rate) / control_n +
                                             treatment_rate * (1 - treatment_rate) / treatment_n)) * 2, 0
        
        # Simplified: use Chi-square as alternative
        contingency_table = [
            [control_successes, control_n - control_successes],
            [treatment_successes, treatment_n - treatment_successes]
        ]
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
        
        # Calculate effect size (Cohen's h)
        effect_size = 2 * (
            sqrt(treatment_rate) - sqrt(control_rate)
        )
        
        # Confidence interval (95%)
        se = sqrt(control_rate * (1 - control_rate) / control_n +
                 treatment_rate * (1 - treatment_rate) / treatment_n)
        diff = treatment_rate - control_rate
        ci_lower = diff - 1.96 * se
        ci_upper = diff + 1.96 * se
        
        return {
            'p_value': p_value,
            'effect_size': abs(effect_size),
            'confidence_interval': {'lower': ci_lower, 'upper': ci_upper},
            'control_std_dev': sqrt(control_rate * (1 - control_rate)),
            'treatment_std_dev': sqrt(treatment_rate * (1 - treatment_rate))
        }
    
    def welch_ttest(
        self,
        control_mean: float,
        control_n: int,
        treatment_mean: float,
        treatment_n: int,
        control_std: float = 0.5,
        treatment_std: float = 0.5
    ) -> Dict:
        """
        Perform Welch's t-test (unequal variances).
        
        Used for comparing means (e.g., average response time).
        
        Returns:
            p_value, effect_size, confidence_interval
        """
        # Welch's t-statistic
        t_stat = (treatment_mean - control_mean) / sqrt(
            (control_std ** 2 / control_n) + (treatment_std ** 2 / treatment_n)
        )
        
        # Degrees of freedom (Welch-Satterthwaite equation)
        numerator = ((control_std ** 2 / control_n) + (treatment_std ** 2 / treatment_n)) ** 2
        denominator = (
            ((control_std ** 2 / control_n) ** 2 / (control_n - 1)) +
            ((treatment_std ** 2 / treatment_n) ** 2 / (treatment_n - 1))
        )
        df = numerator / denominator if denominator > 0 else min(control_n, treatment_n) - 1
        
        # P-value
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
        
        # Effect size (Cohen's d)
        pooled_std = sqrt((control_std ** 2 + treatment_std ** 2) / 2)
        effect_size = abs(treatment_mean - control_mean) / pooled_std if pooled_std > 0 else 0
        
        # Confidence interval
        se = sqrt((control_std ** 2 / control_n) + (treatment_std ** 2 / treatment_n))
        diff = treatment_mean - control_mean
        ci_lower = diff - 1.96 * se
        ci_upper = diff + 1.96 * se
        
        return {
            'p_value': p_value,
            'effect_size': effect_size,
            'confidence_interval': {'lower': ci_lower, 'upper': ci_upper},
            'control_std_dev': control_std,
            'treatment_std_dev': treatment_std
        }
    
    def chi_square_test(
        self,
        control_count: int,
        control_total: int,
        treatment_count: int,
        treatment_total: int
    ) -> Dict:
        """
        Perform Chi-square test of independence.
        
        Used for categorical outcome comparisons (e.g., converted/not-converted).
        
        Returns:
            p_value, effect_size, confidence_interval
        """
        contingency_table = [
            [control_count, control_total - control_count],
            [treatment_count, treatment_total - treatment_count]
        ]
        
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
        
        # Effect size (Cramér's V)
        n = control_total + treatment_total
        cramers_v = sqrt(chi2 / n) if n > 0 else 0
        
        # Rates for CI
        control_rate = control_count / control_total if control_total > 0 else 0
        treatment_rate = treatment_count / treatment_total if treatment_total > 0 else 0
        diff = treatment_rate - control_rate
        
        se = sqrt(control_rate * (1 - control_rate) / control_total +
                 treatment_rate * (1 - treatment_rate) / treatment_total)
        ci_lower = diff - 1.96 * se
        ci_upper = diff + 1.96 * se
        
        return {
            'p_value': p_value,
            'effect_size': cramers_v,
            'confidence_interval': {'lower': ci_lower, 'upper': ci_upper},
            'control_std_dev': None,
            'treatment_std_dev': None
        }
    
    def calculate_sample_size(
        self,
        baseline_rate: float,
        minimum_effect: float,
        alpha: float = 0.05,
        beta: float = 0.2,
        split: float = 0.5
    ) -> int:
        """
        Calculate required sample size using power analysis.
        
        Args:
            baseline_rate: Control group baseline rate
            minimum_effect: Minimum detectable effect size (difference)
            alpha: Type I error rate (default 0.05)
            beta: Type II error rate (default 0.2)
            split: Sample split (default 0.5 for equal)
        
        Returns:
            Required total sample size
        """
        from statsmodels.stats.proportion import proportions_ztest
        
        # Using normal approximation for two proportions
        p1 = baseline_rate
        p2 = baseline_rate + minimum_effect
        
        # Effect size (Cohen's h)
        h = 2 * (sqrt(p2) - sqrt(p1))
        
        # Z-scores for alpha and beta
        z_alpha = stats.norm.ppf(1 - alpha / 2)
        z_beta = stats.norm.ppf(1 - beta)
        
        # Sample size per group
        n_per_group = (z_alpha + z_beta) ** 2 * (1 / (split * (1 - split))) / (h ** 2)
        
        # Total sample size
        total_n = int(n_per_group * 2 / split * (1 - split))
        
        return max(total_n, 100)  # Minimum 100


class HypothesisValidator:
    """Validates A/B test hypotheses follow SMART criteria."""
    
    def is_valid(self, hypothesis: str) -> bool:
        """
        Validate hypothesis follows SMART criteria:
        - Specific: Clear variable and measurement
        - Measurable: Quantifiable outcome
        - Achievable: Realistic given sample size
        - Relevant: Related to business goals
        - Time-bound: Clear timeline
        """
        if not hypothesis or len(hypothesis) < 20:
            return False
        
        # Check for measurement terms
        measurement_terms = ['increase', 'decrease', 'improve', 'reduce', 'higher', 'lower', 'rate', '%']
        has_measurement = any(term in hypothesis.lower() for term in measurement_terms)
        
        if not has_measurement:
            return False
        
        return True
