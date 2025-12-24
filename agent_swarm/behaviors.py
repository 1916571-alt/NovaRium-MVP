from abc import ABC, abstractmethod
import random

class BehaviorStrategy(ABC):
    """
    Abstract Base Class for Agent Behaviors (Strategy Pattern).
    Enables Open/Closed Principle: Add new behaviors without modifying Agent class.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def should_click(self, variant: str) -> bool:
        """
        Decide whether to click the banner based on variant (A/B).
        """
        pass

    @abstractmethod
    def should_purchase(self) -> bool:
        """
        Decide whether to purchase after clicking.
        """
        pass

class ImpulsiveBehavior(BehaviorStrategy):
    """Reacts immediately to urgent cues (red banners, limited time)."""
    name = "impulsive"

    def should_click(self, variant: str) -> bool:
        base_prob = 0.30
        if variant == 'B':  # Assuming B is Red/Urgent
            base_prob += 0.25 # Huge boost
        return random.random() < base_prob

    def should_purchase(self) -> bool:
        return random.random() < 0.25

class CalculatorBehavior(BehaviorStrategy):
    """Carefully evaluates discounts and prices."""
    name = "calculator"

    def should_click(self, variant: str) -> bool:
        base_prob = 0.20
        if variant == 'B': # Discount visible
            base_prob += 0.10
        return random.random() < base_prob

    def should_purchase(self) -> bool:
        return random.random() < 0.20

class BrowserBehavior(BehaviorStrategy):
    """Window shopping: High clicks, very low purchase."""
    name = "browser"

    def should_click(self, variant: str) -> bool:
        return random.random() < 0.50 # High click rate

    def should_purchase(self) -> bool:
        return random.random() < 0.02 # Very low conversion

class MissionBehavior(BehaviorStrategy):
    """Goal-oriented: Low click (unless relevant), high purchase if clicked."""
    name = "mission"

    def should_click(self, variant: str) -> bool:
        return random.random() < 0.15

    def should_purchase(self) -> bool:
        return random.random() < 0.40 # High conversion

class CautiousBehavior(BehaviorStrategy):
    """Hesitates, reads reviews, low engagement."""
    name = "cautious"

    def should_click(self, variant: str) -> bool:
        return random.random() < 0.08

    def should_purchase(self) -> bool:
        return random.random() < 0.10

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
