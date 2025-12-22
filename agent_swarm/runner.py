"""
Agent Swarm Runner
Orchestrates multiple agents to simulate realistic user traffic.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from agent_swarm.agent import HeuristicAgent

def run_agent_swarm(config, progress_callback=None):
    """
    Runs a swarm of agents with specified distribution.
    
    Args:
        config: Dict with trait counts, e.g. {"impulsive": 20, "calculator": 25, ...}
        progress_callback: Optional function to report progress (current, total, message)
    
    Returns:
        Dict with results summary
    """
    # Generate agent list
    agents = []
    agent_id_counter = int(time.time() * 1000)  # Unique ID base
    
    for trait, count in config.items():
        for i in range(count):
            agent_id = f"agent_{trait}_{agent_id_counter + i}"
            agents.append(HeuristicAgent(agent_id, trait))
    
    total = len(agents)
    results = {
        "total": total,
        "success": 0,
        "failed": 0,
        "clicked": 0,
        "purchased": 0,
        "by_trait": {}
    }
    
    # Run agents concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(agent.run_session): agent for agent in agents}
        
        completed = 0
        for future in as_completed(futures):
            agent = futures[future]
            result = future.result()
            
            completed += 1
            
            # Update results
            if result.get("success"):
                results["success"] += 1
                if result.get("clicked"):
                    results["clicked"] += 1
                if result.get("purchased"):
                    results["purchased"] += 1
                
                # Track by trait
                trait = result["trait"]
                if trait not in results["by_trait"]:
                    results["by_trait"][trait] = {"total": 0, "clicked": 0, "purchased": 0}
                results["by_trait"][trait]["total"] += 1
                if result.get("clicked"):
                    results["by_trait"][trait]["clicked"] += 1
                if result.get("purchased"):
                    results["by_trait"][trait]["purchased"] += 1
            else:
                results["failed"] += 1
            
            # Progress callback
            if progress_callback:
                progress_callback(completed, total, f"{agent.trait} 에이전트 완료")
    
    return results


def get_default_config():
    """Returns the default agent distribution"""
    return {
        "impulsive": 20,
        "calculator": 25,
        "browser": 25,
        "mission": 20,
        "cautious": 10
    }


if __name__ == "__main__":
    # Test run
    config = get_default_config()
    
    def progress(current, total, msg):
        print(f"[{current}/{total}] {msg}")
    
    results = run_agent_swarm(config, progress)
    print("\n=== Results ===")
    print(f"Total: {results['total']}")
    print(f"Success: {results['success']}")
    print(f"Clicked: {results['clicked']} ({results['clicked']/results['total']*100:.1f}%)")
    print(f"Purchased: {results['purchased']} ({results['purchased']/results['total']*100:.1f}%)")
    print("\nBy Trait:")
    for trait, stats in results['by_trait'].items():
        ctr = stats['clicked'] / stats['total'] * 100 if stats['total'] > 0 else 0
        cvr = stats['purchased'] / stats['clicked'] * 100 if stats['clicked'] > 0 else 0
        print(f"  {trait}: CTR={ctr:.1f}% CVR={cvr:.1f}%")
