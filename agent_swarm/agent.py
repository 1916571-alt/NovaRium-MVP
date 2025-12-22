import requests
import random
import time
import hashlib
from datetime import datetime

class HeuristicAgent:
    """
    Behavioral Agent that simulates real user actions based on personality traits.
    
    Traits:
    - impulsive: Reacts immediately to urgent cues (red banners, "Limited Time")
    - calculator: Carefully evaluates discounts and prices
    - browser: Clicks a lot but rarely purchases (window shopping)
    - mission: Goal-oriented, searches and buys quickly
    - cautious: Reads reviews, hesitates, low conversion
    """
    
    def __init__(self, agent_id, trait="impulsive"):
        self.agent_id = agent_id
        self.trait = trait
        self.base_url = "http://localhost:8000"
        self.session = requests.Session()
    
    def _get_variant(self):
        """Calculate which variant (A/B) this agent sees (matches server logic)"""
        h_val = int(hashlib.md5(str(self.agent_id).encode()).hexdigest(), 16) % 100
        return 'B' if h_val >= 50 else 'A'
    
    def _decide_to_click(self, variant):
        """Trait-based decision logic for clicking banner"""
        base_prob = 0.10
        
        if self.trait == "impulsive":
            # Loves urgency and red colors
            base_prob = 0.30
            if variant == 'B':  # Assuming B is red/urgent
                base_prob += 0.25  # Huge boost
        
        elif self.trait == "calculator":
            # Checks discount carefully, moderate click rate
            base_prob = 0.20
            if variant == 'B':
                base_prob += 0.10  # Slight boost if discount is visible
        
        elif self.trait == "browser":
            # Clicks everything but doesn't commit
            base_prob = 0.50  # High click rate
        
        elif self.trait == "mission":
            # Only clicks if it matches their goal (simulated as low random click)
            base_prob = 0.15
        
        elif self.trait == "cautious":
            # Hesitates, low click rate
            base_prob = 0.08
        
        return random.random() < base_prob
    
    def _decide_to_purchase(self):
        """Trait-based conversion probability"""
        if self.trait == "impulsive":
            return random.random() < 0.25  # High conversion
        elif self.trait == "calculator":
            return random.random() < 0.20  # Moderate
        elif self.trait == "browser":
            return random.random() < 0.02  # Very low (window shopping)
        elif self.trait == "mission":
            return random.random() < 0.40  # Very high (knows what they want)
        elif self.trait == "cautious":
            return random.random() < 0.10  # Low (needs time to think)
        return False
    
    def run_session(self):
        """
        Simulates a complete user session:
        1. Visit home page
        2. See variant (A or B)
        3. Decide to click based on trait
        4. Decide to purchase based on trait
        """
        try:
            # 1. Visit Home
            res = self.session.get(f"{self.base_url}/?uid={self.agent_id}", timeout=5)
            if res.status_code != 200:
                return {"success": False, "error": "Server error"}
            
            # Simulate reading time
            time.sleep(random.uniform(0.3, 1.5))
            
            # 2. Get Variant
            variant = self._get_variant()
            
            # 3. Click Decision
            clicked = False
            if self._decide_to_click(variant):
                clicked = True
                self.session.post(
                    f"{self.base_url}/click",
                    data={"uid": self.agent_id, "element": f"banner_{variant}"},
                    timeout=5
                )
                time.sleep(random.uniform(0.5, 2.0))
            
            # 4. Purchase Decision (only if clicked)
            purchased = False
            if clicked and self._decide_to_purchase():
                purchased = True
                self.session.post(
                    f"{self.base_url}/order",
                    data={"uid": self.agent_id, "amount": random.randint(15000, 50000)},
                    timeout=5
                )
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "trait": self.trait,
                "variant": variant,
                "clicked": clicked,
                "purchased": purchased
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Test
    agent = HeuristicAgent("test_user_001", "impulsive")
    result = agent.run_session()
    print(result)
