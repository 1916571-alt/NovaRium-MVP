import requests
import time
import hashlib
import random
from agent_swarm.behaviors import BehaviorStrategy, get_behavior_by_name

class HeuristicAgent:
    """
    Refactored Agent complying with SOLID Principles.
    - SRP: Handles Session/Networking only. Decisions delegated to Strategy.
    - OCP: New behaviors added via BehaviorStrategy classes.
    - DIP: Depends on BehaviorStrategy abstraction.
    """
    
    def __init__(self, agent_id: str, behavior: BehaviorStrategy):
        self.agent_id = agent_id
        if isinstance(behavior, str):
            # Backward compatibility / Factory usage
            self.behavior = get_behavior_by_name(behavior)
        else:
            self.behavior = behavior # Dependency Injection
            
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
            # 1. Visit Home
            res = self.session.get(f"{self.base_url}/?uid={self.agent_id}", timeout=5)
            if res.status_code != 200:
                return {"success": False, "error": "Server error"}
            
            time.sleep(random.uniform(0.3, 1.5))
            
            # 2. Get Variant
            variant = self._get_variant()
            
            # 3. Click Decision (Delegated to Strategy)
            clicked = False
            if self.behavior.should_click(variant):
                clicked = True
                self.session.post(
                    f"{self.base_url}/click",
                    data={"uid": self.agent_id, "element": f"banner_{variant}"},
                    timeout=5
                )
                time.sleep(random.uniform(0.5, 2.0))
            
            # 4. Purchase Decision (Delegated to Strategy)
            purchased = False
            if clicked and self.behavior.should_purchase():
                purchased = True
                self.session.post(
                    f"{self.base_url}/order",
                    data={"uid": self.agent_id, "amount": random.randint(15000, 50000)},
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

