"""
Test suite for Agent Behavior Strategies.

Tests verify:
1. Correct probability ranges based on industry benchmarks
2. Relative lift calculations for variant effects
3. AOV distribution by persona
4. Strategy pattern interface compliance
"""
import pytest
import sys
import os

# Add agent_swarm to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from agent_swarm.behaviors import (
    BehaviorStrategy,
    ImpulsiveBehavior,
    CalculatorBehavior,
    BrowserBehavior,
    MissionBehavior,
    CautiousBehavior,
    get_behavior_by_name,
    get_all_behaviors
)


class TestImpulsiveBehavior:
    """Test suite for ImpulsiveBehavior strategy."""

    def test_name_property(self):
        """Behavior should have correct name identifier."""
        behavior = ImpulsiveBehavior()
        assert behavior.name == "impulsive"

    def test_base_ctr_realistic(self):
        """Base CTR should be around 4.5% (industry benchmark)."""
        behavior = ImpulsiveBehavior()
        assert 0.03 <= behavior.base_ctr <= 0.06  # 3-6%

    def test_variant_b_applies_relative_lift(self):
        """Variant B should apply ~22% relative lift to CTR."""
        behavior = ImpulsiveBehavior()

        # Run trials
        clicks_a = sum(behavior.should_click('A') for _ in range(2000))
        clicks_b = sum(behavior.should_click('B') for _ in range(2000))

        # B should have higher clicks due to relative lift
        assert clicks_b > clicks_a

        # Expected: A ~4.5% (90), B ~5.5% (110) of 2000
        assert 60 < clicks_a < 130  # ~4.5% ± variance
        assert 80 < clicks_b < 150  # ~5.5% ± variance

    def test_purchase_rate_with_variant(self):
        """Purchase rate should differ by variant."""
        behavior = ImpulsiveBehavior()

        purchases_a = sum(behavior.should_purchase('A') for _ in range(1000))
        purchases_b = sum(behavior.should_purchase('B') for _ in range(1000))

        # B should have slightly higher purchase rate (+10% lift)
        # Base 12%, B ~13.2%
        assert 80 < purchases_a < 160  # ~12%
        assert 90 < purchases_b < 180  # ~13.2%

    def test_aov_range(self):
        """AOV should be in higher range for impulsive buyers."""
        behavior = ImpulsiveBehavior()
        min_val, max_val = behavior.aov_range
        assert min_val == 25000
        assert max_val == 65000

    def test_get_order_value_in_range(self):
        """Generated order values should be within AOV range."""
        behavior = ImpulsiveBehavior()
        min_val, max_val = behavior.aov_range

        for _ in range(100):
            value = behavior.get_order_value()
            assert min_val <= value <= max_val
            assert value % 100 == 0  # Rounded to nearest 100


class TestCalculatorBehavior:
    """Test suite for CalculatorBehavior strategy."""

    def test_name_property(self):
        behavior = CalculatorBehavior()
        assert behavior.name == "calculator"

    def test_base_ctr_moderate(self):
        """Calculator CTR should be around 2.5%."""
        behavior = CalculatorBehavior()
        assert 0.02 <= behavior.base_ctr <= 0.035

    def test_variant_b_moderate_lift(self):
        """Calculator users respond to discounts (+18% lift)."""
        behavior = CalculatorBehavior()

        clicks_a = sum(behavior.should_click('A') for _ in range(2000))
        clicks_b = sum(behavior.should_click('B') for _ in range(2000))

        # B should have more clicks
        assert clicks_b > clicks_a

        # A ~2.5% (50), B ~2.95% (59) of 2000
        assert 30 < clicks_a < 80
        assert 40 < clicks_b < 100

    def test_high_cvr_after_click(self):
        """If they click, high intent to purchase (~18%)."""
        behavior = CalculatorBehavior()
        purchases = sum(behavior.should_purchase('A') for _ in range(1000))
        assert 130 < purchases < 230  # ~18%

    def test_aov_value_conscious(self):
        """AOV should skew slightly lower (value-conscious)."""
        behavior = CalculatorBehavior()
        assert behavior.aov_mean_shift < 0.5


class TestBrowserBehavior:
    """Test suite for BrowserBehavior (window shoppers)."""

    def test_name_property(self):
        behavior = BrowserBehavior()
        assert behavior.name == "browser"

    def test_high_click_rate(self):
        """Browsers click a lot (~6.5%)."""
        behavior = BrowserBehavior()
        clicks = sum(behavior.should_click('A') for _ in range(2000))

        # ~6.5% of 2000 = 130
        assert 100 < clicks < 170

    def test_minimal_variant_effect(self):
        """Browsers aren't influenced much by design (+2%)."""
        behavior = BrowserBehavior()
        assert behavior.variant_b_ctr_lift <= 0.05  # Max 5%

    def test_very_low_purchase_rate(self):
        """Browsers rarely buy (~2%)."""
        behavior = BrowserBehavior()
        purchases = sum(behavior.should_purchase('A') for _ in range(1000))

        # ~2% of 1000 = 20
        assert 5 < purchases < 45

    def test_low_aov(self):
        """When they do buy, it's cheap items."""
        behavior = BrowserBehavior()
        min_val, max_val = behavior.aov_range
        assert max_val <= 30000


class TestMissionBehavior:
    """Test suite for MissionBehavior (goal-oriented)."""

    def test_name_property(self):
        behavior = MissionBehavior()
        assert behavior.name == "mission"

    def test_low_click_rate(self):
        """Mission users ignore distractions (~1.2%)."""
        behavior = MissionBehavior()
        clicks = sum(behavior.should_click('A') for _ in range(2000))

        # ~1.2% of 2000 = 24
        assert 10 < clicks < 50

    def test_high_conversion_when_clicked(self):
        """If they click, they're likely to buy (~32%)."""
        behavior = MissionBehavior()
        purchases = sum(behavior.should_purchase('A') for _ in range(1000))

        # ~32% of 1000 = 320
        assert 270 < purchases < 380

    def test_high_aov(self):
        """Mission buyers make larger planned purchases."""
        behavior = MissionBehavior()
        min_val, max_val = behavior.aov_range
        assert min_val >= 25000
        assert max_val >= 60000


class TestCautiousBehavior:
    """Test suite for CautiousBehavior (hesitant users)."""

    def test_name_property(self):
        behavior = CautiousBehavior()
        assert behavior.name == "cautious"

    def test_very_low_click_rate(self):
        """Cautious users rarely engage (~0.8%)."""
        behavior = CautiousBehavior()
        clicks = sum(behavior.should_click('A') for _ in range(2000))

        # ~0.8% of 2000 = 16
        assert 5 < clicks < 35

    def test_no_variant_effect(self):
        """Cautious users distrust marketing, no variant effect."""
        behavior = CautiousBehavior()
        assert behavior.variant_b_ctr_lift == 0.0
        assert behavior.variant_b_cvr_lift == 0.0

    def test_low_purchase_rate(self):
        """Even if they click, low purchase (~6%)."""
        behavior = CautiousBehavior()
        purchases = sum(behavior.should_purchase('A') for _ in range(1000))

        # ~6% of 1000 = 60
        assert 30 < purchases < 100

    def test_low_aov_risk_averse(self):
        """Cautious buyers make small, safe purchases."""
        behavior = CautiousBehavior()
        assert behavior.aov_mean_shift < 0.5  # Skews low


class TestBehaviorFactory:
    """Test suite for get_behavior_by_name factory function."""

    def test_factory_returns_correct_instances(self):
        """Factory should return proper strategy instances."""
        assert isinstance(get_behavior_by_name("impulsive"), ImpulsiveBehavior)
        assert isinstance(get_behavior_by_name("calculator"), CalculatorBehavior)
        assert isinstance(get_behavior_by_name("browser"), BrowserBehavior)
        assert isinstance(get_behavior_by_name("mission"), MissionBehavior)
        assert isinstance(get_behavior_by_name("cautious"), CautiousBehavior)

    def test_factory_aliases(self):
        """Factory should handle UI aliases."""
        assert isinstance(get_behavior_by_name("rational"), CalculatorBehavior)
        assert isinstance(get_behavior_by_name("window"), BrowserBehavior)

    def test_factory_case_insensitive(self):
        """Factory should handle uppercase/mixed case."""
        assert isinstance(get_behavior_by_name("IMPULSIVE"), ImpulsiveBehavior)
        assert isinstance(get_behavior_by_name("CaLcUlAtOr"), CalculatorBehavior)

    def test_factory_default_fallback(self):
        """Unknown behavior should default to BrowserBehavior."""
        unknown = get_behavior_by_name("nonexistent_behavior")
        assert isinstance(unknown, BrowserBehavior)


class TestGetAllBehaviors:
    """Test suite for get_all_behaviors utility function."""

    def test_returns_all_five_behaviors(self):
        """Should return all 5 behavior types."""
        behaviors = get_all_behaviors()
        assert len(behaviors) == 5
        assert "impulsive" in behaviors
        assert "calculator" in behaviors
        assert "browser" in behaviors
        assert "mission" in behaviors
        assert "cautious" in behaviors

    def test_all_are_behavior_instances(self):
        """All values should be BehaviorStrategy instances."""
        behaviors = get_all_behaviors()
        for name, behavior in behaviors.items():
            assert isinstance(behavior, BehaviorStrategy)


class TestBehaviorStrategyInterface:
    """Test that all behaviors implement the Strategy interface correctly."""

    @pytest.mark.parametrize("behavior_class", [
        ImpulsiveBehavior,
        CalculatorBehavior,
        BrowserBehavior,
        MissionBehavior,
        CautiousBehavior
    ])
    def test_all_behaviors_have_name(self, behavior_class):
        """All strategies must have a name property."""
        behavior = behavior_class()
        assert hasattr(behavior, 'name')
        assert isinstance(behavior.name, str)
        assert len(behavior.name) > 0

    @pytest.mark.parametrize("behavior_class", [
        ImpulsiveBehavior,
        CalculatorBehavior,
        BrowserBehavior,
        MissionBehavior,
        CautiousBehavior
    ])
    def test_all_behaviors_have_base_metrics(self, behavior_class):
        """All strategies must have base CTR and CVR."""
        behavior = behavior_class()
        assert 0 < behavior.base_ctr < 1
        assert 0 < behavior.base_cvr < 1

    @pytest.mark.parametrize("behavior_class", [
        ImpulsiveBehavior,
        CalculatorBehavior,
        BrowserBehavior,
        MissionBehavior,
        CautiousBehavior
    ])
    def test_all_behaviors_implement_should_click(self, behavior_class):
        """All strategies must implement should_click."""
        behavior = behavior_class()
        result_a = behavior.should_click('A')
        result_b = behavior.should_click('B')

        assert isinstance(result_a, bool)
        assert isinstance(result_b, bool)

    @pytest.mark.parametrize("behavior_class", [
        ImpulsiveBehavior,
        CalculatorBehavior,
        BrowserBehavior,
        MissionBehavior,
        CautiousBehavior
    ])
    def test_all_behaviors_implement_should_purchase(self, behavior_class):
        """All strategies must implement should_purchase with variant."""
        behavior = behavior_class()
        result_a = behavior.should_purchase('A')
        result_b = behavior.should_purchase('B')
        assert isinstance(result_a, bool)
        assert isinstance(result_b, bool)

    @pytest.mark.parametrize("behavior_class", [
        ImpulsiveBehavior,
        CalculatorBehavior,
        BrowserBehavior,
        MissionBehavior,
        CautiousBehavior
    ])
    def test_all_behaviors_implement_get_order_value(self, behavior_class):
        """All strategies must implement get_order_value."""
        behavior = behavior_class()
        value = behavior.get_order_value()
        assert isinstance(value, int)
        assert value > 0

    @pytest.mark.parametrize("behavior_class", [
        ImpulsiveBehavior,
        CalculatorBehavior,
        BrowserBehavior,
        MissionBehavior,
        CautiousBehavior
    ])
    def test_all_behaviors_have_aov_range(self, behavior_class):
        """All strategies must have valid AOV range."""
        behavior = behavior_class()
        min_val, max_val = behavior.aov_range
        assert min_val > 0
        assert max_val > min_val


class TestRelativeLiftCalculation:
    """Test that relative lift is calculated correctly."""

    def test_relative_lift_formula(self):
        """Verify relative lift formula: base * (1 + lift)."""
        behavior = ImpulsiveBehavior()

        # CTR: 4.5% * (1 + 0.22) = 5.49%
        expected_ctr_b = behavior.base_ctr * (1 + behavior.variant_b_ctr_lift)
        assert abs(expected_ctr_b - 0.0549) < 0.001

        # CVR: 12% * (1 + 0.10) = 13.2%
        expected_cvr_b = behavior.base_cvr * (1 + behavior.variant_b_cvr_lift)
        assert abs(expected_cvr_b - 0.132) < 0.001

    def test_no_lift_for_variant_a(self):
        """Variant A should use base rates without lift."""
        behavior = ImpulsiveBehavior()

        # Run many trials with variant A
        clicks = sum(behavior.should_click('A') for _ in range(10000))
        expected = behavior.base_ctr * 10000

        # Should be within 20% of expected
        assert abs(clicks - expected) / expected < 0.2
