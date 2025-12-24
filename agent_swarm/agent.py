import requests
import time
import hashlib
import random
import os
from agent_swarm.behaviors import BehaviorStrategy, get_behavior_by_name

class HeuristicAgent:
    """
    Refactored Agent complying with SOLID Principles.
    - SRP: Handles Session/Networking only. Decisions delegated to Strategy.
    - OCP: New behaviors added via BehaviorStrategy classes.
    - DIP: Depends on BehaviorStrategy abstraction.
    """
    
    def __init__(self, agent_id: str, behavior: BehaviorStrategy, run_id: str = None, weight: float = 1.0):
        self.agent_id = agent_id
        if isinstance(behavior, str):
            # Backward compatibility / Factory usage
            self.behavior = get_behavior_by_name(behavior)
        else:
            self.behavior = behavior # Dependency Injection

        self.run_id = run_id
        self.weight = weight  # For hybrid simulation
        self.base_url = "http://localhost:8000"
        self.session = requests.Session()
    
    def _get_variant(self):
        """Calculate which variant (A/B) this agent sees (matches server logic)"""
        h_val = int(hashlib.md5(str(self.agent_id).encode()).hexdigest(), 16) % 100
        return 'B' if h_val >= 50 else 'A'
    
    def run_session(self):
        """
        Simulates a complete user session.
        """
        try:
            is_turbo = os.getenv("AGENT_TURBO") == "1"
            
            # 1. Visit Home
            params = {"uid": self.agent_id, "weight": self.weight}
            if self.run_id:
                params["run_id"] = self.run_id
            res = self.session.get(f"{self.base_url}/", params=params, timeout=5)
            if res.status_code != 200:
                return {"success": False, "error": "Server error"}
            
            if not is_turbo:
                time.sleep(random.uniform(0.3, 1.5))
            else:
                time.sleep(0.02) # Minimum delay
            
            # 2. Get Variant
            variant = self._get_variant()
            
            # 3. Click Decision (Delegated to Strategy)
            clicked = False
            if self.behavior.should_click(variant):
                clicked = True
                click_data = {"uid": self.agent_id, "element": f"banner_{variant}"}
                if self.run_id:
                    click_data["run_id"] = self.run_id
                self.session.post(
                    f"{self.base_url}/click",
                    data=click_data,
                    timeout=5
                )
                self.session.post(
                    f"{self.base_url}/click",
                    data=click_data,
                    timeout=5
                )
                if not is_turbo:
                    time.sleep(random.uniform(0.5, 2.0))
                else:
                    time.sleep(0.02) # Minimum delay to prevent starvation
            
            # 4. Purchase Decision (Delegated to Strategy)
            purchased = False
            if clicked and self.behavior.should_purchase():
                purchased = True
                order_data = {"uid": self.agent_id, "amount": random.randint(15000, 50000)}
                if self.run_id:
                    order_data["run_id"] = self.run_id
                self.session.post(
                    f"{self.base_url}/order",
                    data=order_data,
                    timeout=5
                )
            
            return {
                "success": True,
                "agent_id": self.agent_id,
                "trait": self.behavior.name,
                "variant": variant,
                "clicked": clicked,
                "purchased": purchased
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    # Test
    from agent_swarm.behaviors import ImpulsiveBehavior
    agent = HeuristicAgent("test_user_001", ImpulsiveBehavior())
    # Note: Requires server running to succeed
    print(f"Agent initialized with trait: {agent.behavior.name}")

