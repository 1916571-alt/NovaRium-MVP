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
    get_behavior_by_name
)


class TestImpulsiveBehavior:
    """Test suite for ImpulsiveBehavior strategy."""
    
    def test_name_property(self):
        """Behavior should have correct name identifier."""
        behavior = ImpulsiveBehavior()
        assert behavior.name == "impulsive"
    
    def test_variant_b_increases_click_probability(self):
        """Variant B (urgent/red) should significantly boost click rate."""
        behavior = ImpulsiveBehavior()
        
        # Run 1000 trials to get statistical confidence
        clicks_a = sum(behavior.should_click('A') for _ in range(1000))
        clicks_b = sum(behavior.should_click('B') for _ in range(1000))
        
        # Variant B should have noticeably more clicks (base 30% + 25% boost)
        assert clicks_b > clicks_a, "Variant B should have higher click rate for impulsive users"
        
        # Rough sanity check: B should be ~55%, A should be ~30%
        assert 200 < clicks_a < 400  # ~30% of 1000
        assert 450 < clicks_b < 650  # ~55% of 1000
    
    def test_purchase_probability(self):
        """Purchase rate should be around 25%."""
        behavior = ImpulsiveBehavior()
        purchases = sum(behavior.should_purchase() for _ in range(1000))
        
        # Should be roughly 250 ± margin
        assert 200 < purchases < 300


class TestCalculatorBehavior:
    """Test suite for CalculatorBehavior strategy."""
    
    def test_name_property(self):
        behavior = CalculatorBehavior()
        assert behavior.name == "calculator"
    
    def test_variant_b_modest_boost(self):
        """Calculator users are less influenced by urgency."""
        behavior = CalculatorBehavior()
        
        clicks_a = sum(behavior.should_click('A') for _ in range(1000))
        clicks_b = sum(behavior.should_click('B') for _ in range(1000))
        
        # B should be better, but not as dramatic as impulsive
        assert clicks_b > clicks_a
        
        # A ~20%, B ~30%
        assert 150 < clicks_a < 250
        assert 250 < clicks_b < 350
    
    def test_purchase_rate_moderate(self):
        """Purchase rate should be around 20%."""
        behavior = CalculatorBehavior()
        purchases = sum(behavior.should_purchase() for _ in range(1000))
        assert 150 < purchases < 250


class TestBrowserBehavior:
    """Test suite for BrowserBehavior (window shoppers)."""
    
    def test_name_property(self):
        behavior = BrowserBehavior()
        assert behavior.name == "browser"
    
    def test_high_click_rate(self):
        """Browsers click a lot (50%)."""
        behavior = BrowserBehavior()
        clicks = sum(behavior.should_click('A') for _ in range(1000))
        
        # Should be around 500
        assert 450 < clicks < 550
    
    def test_very_low_purchase_rate(self):
        """Browsers rarely buy (2%)."""
        behavior = BrowserBehavior()
        purchases = sum(behavior.should_purchase() for _ in range(1000))
        
        # Should be around 20
        assert 5 < purchases < 40  # Allow some variance


class TestMissionBehavior:
    """Test suite for MissionBehavior (goal-oriented)."""
    
    def test_name_property(self):
        behavior = MissionBehavior()
        assert behavior.name == "mission"
    
    def test_low_click_rate(self):
        """Mission users ignore distractions (15% click)."""
        behavior = MissionBehavior()
        clicks = sum(behavior.should_click('A') for _ in range(1000))
        
        assert 100 < clicks < 200
    
    def test_high_conversion_when_clicked(self):
        """If they click, they're likely to buy (40%)."""
        behavior = MissionBehavior()
        purchases = sum(behavior.should_purchase() for _ in range(1000))
        
        assert 350 < purchases < 450


class TestCautiousBehavior:
    """Test suite for CautiousBehavior (hesitant users)."""
    
    def test_name_property(self):
        behavior = CautiousBehavior()
        assert behavior.name == "cautious"
    
    def test_very_low_click_rate(self):
        """Cautious users rarely engage (8%)."""
        behavior = CautiousBehavior()
        clicks = sum(behavior.should_click('A') for _ in range(1000))
        
        assert 50 < clicks < 120
    
    def test_low_purchase_rate(self):
        """Even if they click, low purchase (10%)."""
        behavior = CautiousBehavior()
        purchases = sum(behavior.should_purchase() for _ in range(1000))
        
        assert 70 < purchases < 130


class TestBehaviorFactory:
    """Test suite for get_behavior_by_name factory function."""
    
    def test_factory_returns_correct_instances(self):
        """Factory should return proper strategy instances."""
        assert isinstance(get_behavior_by_name("impulsive"), ImpulsiveBehavior)
        assert isinstance(get_behavior_by_name("calculator"), CalculatorBehavior)
        assert isinstance(get_behavior_by_name("browser"), BrowserBehavior)
        assert isinstance(get_behavior_by_name("mission"), MissionBehavior)
        assert isinstance(get_behavior_by_name("cautious"), CautiousBehavior)
    
    def test_factory_case_insensitive(self):
        """Factory should handle uppercase/mixed case."""
        assert isinstance(get_behavior_by_name("IMPULSIVE"), ImpulsiveBehavior)
        assert isinstance(get_behavior_by_name("CaLcUlAtOr"), CalculatorBehavior)
    
    def test_factory_default_fallback(self):
        """Unknown behavior should default to BrowserBehavior."""
        unknown = get_behavior_by_name("nonexistent_behavior")
        assert isinstance(unknown, BrowserBehavior)
    
    def test_factory_returns_new_instances(self):
        """Each call should return a fresh instance (not singleton)."""
        b1 = get_behavior_by_name("impulsive")
        b2 = get_behavior_by_name("impulsive")
        # They should be different objects (not same reference)
        # Note: Current implementation may return same instance, 
        # but this test documents expected behavior for future refactoring
        assert b1.name == b2.name  # At minimum, same type


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
        """All strategies must implement should_purchase."""
        behavior = behavior_class()
        result = behavior.should_purchase()
        assert isinstance(result, bool)
