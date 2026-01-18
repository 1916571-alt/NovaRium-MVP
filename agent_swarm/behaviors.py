"""
Agent Behavior Strategies for A/B Test Simulation.

Implements the Strategy Pattern for different user personas.
All probability values are based on e-commerce industry benchmarks:
- Banner CTR: 0.5% ~ 5%
- Purchase CVR (after click): 5% ~ 30%
- Overall CVR: 1% ~ 4%
"""
from abc import ABC, abstractmethod
import random
from typing import Tuple


class BehaviorStrategy(ABC):
    """
    Abstract Base Class for Agent Behaviors (Strategy Pattern).
    Enables Open/Closed Principle: Add new behaviors without modifying Agent class.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Behavior name identifier."""
        pass

    @property
    def base_ctr(self) -> float:
        """Base click-through rate (0.0 ~ 1.0)."""
        return 0.02  # 2% default

    @property
    def variant_b_ctr_lift(self) -> float:
        """Relative CTR lift for variant B (e.g., 0.15 = +15%)."""
        return 0.0  # No effect by default

    @property
    def base_cvr(self) -> float:
        """Base conversion rate after click (0.0 ~ 1.0)."""
        return 0.10  # 10% default

    @property
    def variant_b_cvr_lift(self) -> float:
        """Relative CVR lift for variant B."""
        return 0.0  # No effect by default

    @property
    def aov_range(self) -> Tuple[int, int]:
        """Average Order Value range (min, max) in KRW."""
        return (20000, 40000)  # Default 20K ~ 40K

    @property
    def aov_mean_shift(self) -> float:
        """
        Shift towards mean or extremes.
        0.5 = uniform, < 0.5 = skew low, > 0.5 = skew high
        """
        return 0.5

    def should_click(self, variant: str) -> bool:
        """
        Decide whether to click the banner based on variant.
        Uses relative lift calculation for realism.
        """
        ctr = self.base_ctr
        if variant == 'B':
            # Apply relative lift (e.g., 2% * 1.15 = 2.3%)
            ctr = ctr * (1 + self.variant_b_ctr_lift)
        return random.random() < ctr

    def should_purchase(self, variant: str = 'A') -> bool:
        """
        Decide whether to purchase after clicking.
        Variant can also affect purchase decision.
        """
        cvr = self.base_cvr
        if variant == 'B':
            cvr = cvr * (1 + self.variant_b_cvr_lift)
        return random.random() < cvr

    def get_order_value(self) -> int:
        """
        Generate order value based on persona's spending pattern.
        Uses triangular distribution for more realistic spread.
        """
        min_val, max_val = self.aov_range
        # Triangular distribution with persona-based mode
        mode = min_val + (max_val - min_val) * self.aov_mean_shift
        value = random.triangular(min_val, max_val, mode)
        return int(round(value, -2))  # Round to nearest 100


class ImpulsiveBehavior(BehaviorStrategy):
    """
    Reacts immediately to urgent cues (red banners, limited time offers).
    - High CTR (responds to visual stimuli)
    - Strong variant B effect (urgency messaging works)
    - Moderate CVR (sometimes regrets and abandons)
    - High AOV (impulsive expensive purchases)
    """
    name = "impulsive"

    @property
    def base_ctr(self) -> float:
        return 0.045  # 4.5% - High engagement

    @property
    def variant_b_ctr_lift(self) -> float:
        return 0.22  # +22% relative lift for urgent design

    @property
    def base_cvr(self) -> float:
        return 0.12  # 12% after click

    @property
    def variant_b_cvr_lift(self) -> float:
        return 0.10  # +10% CVR lift (urgency pushes to buy)

    @property
    def aov_range(self) -> Tuple[int, int]:
        return (25000, 65000)  # Higher spending

    @property
    def aov_mean_shift(self) -> float:
        return 0.6  # Skews toward higher values


class CalculatorBehavior(BehaviorStrategy):
    """
    Carefully evaluates discounts and prices before deciding.
    - Moderate CTR (needs to see value proposition)
    - Moderate variant B effect (responds to visible discounts)
    - High CVR (if they click, they've done the math)
    - Medium AOV (calculated, value-conscious purchases)
    """
    name = "calculator"

    @property
    def base_ctr(self) -> float:
        return 0.025  # 2.5%

    @property
    def variant_b_ctr_lift(self) -> float:
        return 0.18  # +18% for discount visibility

    @property
    def base_cvr(self) -> float:
        return 0.18  # 18% - High intent when clicking

    @property
    def variant_b_cvr_lift(self) -> float:
        return 0.08  # +8% (discount seals the deal)

    @property
    def aov_range(self) -> Tuple[int, int]:
        return (18000, 42000)

    @property
    def aov_mean_shift(self) -> float:
        return 0.45  # Slightly value-conscious


class BrowserBehavior(BehaviorStrategy):
    """
    Window shopping behavior: Clicks everything, rarely buys.
    - Very high CTR (curious, clicks everything)
    - No variant effect (not influenced by design)
    - Very low CVR (just browsing)
    - Low AOV when they do buy
    """
    name = "browser"

    @property
    def base_ctr(self) -> float:
        return 0.065  # 6.5% - Clicks a lot

    @property
    def variant_b_ctr_lift(self) -> float:
        return 0.02  # Minimal effect (+2%)

    @property
    def base_cvr(self) -> float:
        return 0.02  # 2% - Rarely converts

    @property
    def variant_b_cvr_lift(self) -> float:
        return 0.0  # No effect

    @property
    def aov_range(self) -> Tuple[int, int]:
        return (12000, 28000)  # Low spending

    @property
    def aov_mean_shift(self) -> float:
        return 0.35  # Skews low


class MissionBehavior(BehaviorStrategy):
    """
    Goal-oriented: Knows what they want, goes straight for it.
    - Low CTR (ignores distractions, focused on goal)
    - Minimal variant effect (not easily swayed)
    - Very high CVR (came with purchase intent)
    - High AOV (planned, often larger purchases)
    """
    name = "mission"

    @property
    def base_ctr(self) -> float:
        return 0.012  # 1.2% - Focused, ignores banners

    @property
    def variant_b_ctr_lift(self) -> float:
        return 0.05  # +5% minimal effect

    @property
    def base_cvr(self) -> float:
        return 0.32  # 32% - High intent

    @property
    def variant_b_cvr_lift(self) -> float:
        return 0.03  # +3% minimal

    @property
    def aov_range(self) -> Tuple[int, int]:
        return (28000, 72000)  # Planned larger purchases

    @property
    def aov_mean_shift(self) -> float:
        return 0.55  # Slightly higher


class CautiousBehavior(BehaviorStrategy):
    """
    Hesitant: Reads reviews, compares options, slow to decide.
    - Very low CTR (suspicious of promotions)
    - No variant effect (distrusts marketing)
    - Low CVR (even after clicking, needs more convincing)
    - Low AOV (risk-averse, small purchases first)
    """
    name = "cautious"

    @property
    def base_ctr(self) -> float:
        return 0.008  # 0.8% - Very hesitant

    @property
    def variant_b_ctr_lift(self) -> float:
        return 0.0  # No effect (distrusts marketing)

    @property
    def base_cvr(self) -> float:
        return 0.06  # 6%

    @property
    def variant_b_cvr_lift(self) -> float:
        return 0.0  # No effect

    @property
    def aov_range(self) -> Tuple[int, int]:
        return (12000, 30000)  # Small, safe purchases

    @property
    def aov_mean_shift(self) -> float:
        return 0.3  # Strongly skews low


# =============================================================================
# Behavior Statistics Summary (for documentation)
# =============================================================================
"""
| Persona    | Base CTR | B Lift | Base CVR | B Lift | AOV Range    |
|------------|----------|--------|----------|--------|--------------|
| Impulsive  | 4.5%     | +22%   | 12%      | +10%   | 25K ~ 65K    |
| Calculator | 2.5%     | +18%   | 18%      | +8%    | 18K ~ 42K    |
| Browser    | 6.5%     | +2%    | 2%       | 0%     | 12K ~ 28K    |
| Mission    | 1.2%     | +5%    | 32%      | +3%    | 28K ~ 72K    |
| Cautious   | 0.8%     | 0%     | 6%       | 0%     | 12K ~ 30K    |

Expected overall metrics (with equal persona distribution):
- Weighted CTR: ~3.1%
- Weighted CVR (after click): ~14%
- Overall Conversion: ~0.43%
"""


def get_behavior_by_name(name: str) -> BehaviorStrategy:
    """Factory method to get strategy by name."""
    strategies = {
        "impulsive": ImpulsiveBehavior(),
        "calculator": CalculatorBehavior(),
        "rational": CalculatorBehavior(),  # Alias for UI consistency
        "browser": BrowserBehavior(),
        "window": BrowserBehavior(),  # Alias for UI consistency
        "mission": MissionBehavior(),
        "cautious": CautiousBehavior()
    }
    return strategies.get(name.lower(), BrowserBehavior())  # Default


def get_all_behaviors() -> dict:
    """Get all behavior instances for analysis."""
    return {
        "impulsive": ImpulsiveBehavior(),
        "calculator": CalculatorBehavior(),
        "browser": BrowserBehavior(),
        "mission": MissionBehavior(),
        "cautious": CautiousBehavior()
    }
