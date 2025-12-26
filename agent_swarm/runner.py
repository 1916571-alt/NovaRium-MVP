"""
Agent Swarm Runner
Orchestrates multiple agents to simulate realistic user traffic.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from agent_swarm.agent import HeuristicAgent
from agent_swarm.behaviors import get_behavior_by_name

def run_agent_swarm(config, progress_callback=None, run_id=None, weight=1.0):
    """
    Runs a swarm of agents with specified distribution.

    Args:
        config: Dict with trait counts, e.g. {"impulsive": 20, "calculator": 25, ...}
        progress_callback: Optional function to report progress (current, total, message)
        run_id: Optional unique identifier for this experiment run
        weight: Statistical weight for hybrid simulation (default 1.0)

    Returns:
        Dict with results summary
    """
    # Generate unique run_id if not provided
    if not run_id:
        run_id = f"run_{int(time.time() * 1000)}"

    # Generate agent list
    agents = []
    agent_id_counter = int(time.time() * 1000)  # Unique ID base

    for trait, count in config.items():
        for i in range(count):
            agent_id = f"agent_{trait}_{agent_id_counter + i}"
            # Use Factory to get Behavior Object
            behavior = get_behavior_by_name(trait)
            agents.append(HeuristicAgent(agent_id, behavior, run_id, weight))
    
    total = len(agents)
    results = {
        "total": total,
        "success": 0,
        "failed": 0,
        "clicked": 0,
        "bounced": 0,
        "purchased": 0,
        "by_trait": {}
    }
    
    # Run agents concurrently
    with ThreadPoolExecutor(max_workers=50) as executor:
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
                if result.get("bounced"):
                    results["bounced"] += 1
                if result.get("purchased"):
                    results["purchased"] += 1

                # Track by trait
                trait = result["trait"]
                if trait not in results["by_trait"]:
                    results["by_trait"][trait] = {"total": 0, "clicked": 0, "bounced": 0, "purchased": 0}
                results["by_trait"][trait]["total"] += 1
                if result.get("clicked"):
                    results["by_trait"][trait]["clicked"] += 1
                if result.get("bounced"):
                    results["by_trait"][trait]["bounced"] += 1
                if result.get("purchased"):
                    results["by_trait"][trait]["purchased"] += 1
            else:
                results["failed"] += 1
            
            # Progress callback
            if progress_callback:
                progress_callback(completed, total, f"{agent.behavior.name} 에이전트 완료")

    results["run_id"] = run_id
    results["weight"] = weight
    results["effective_total"] = int(total * weight)
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
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run Agent Swarm Simulation")
    parser.add_argument("--count", type=int, default=100, help="Total number of agents")
    parser.add_argument("--weights", type=str, default="40,10,20,20,10", help="Weights (Window, Mission, Rational, Impulsive, Cautious)")
    parser.add_argument("--turbo", action="store_true", help="Run without delays")
    parser.add_argument("--run-id", type=str, default=None, help="Unique run identifier for experiment isolation")
    parser.add_argument("--weight", type=float, default=1.0, help="Statistical weight for hybrid simulation")

    args = parser.parse_args()
    
    if args.turbo:
        import os
        os.environ["AGENT_TURBO"] = "1"
    
    # Map weights to trait names (matching app.py UI order)
    traits = ["window", "mission", "rational", "impulsive", "cautious"]
    weight_vals = [int(w) for w in args.weights.split(",")]
    
    if len(weight_vals) != 5:
        raise ValueError("Expected 5 comma-separated weights")
    
    # Calculate counts per trait
    total_weight = sum(weight_vals)
    config = {}
    for trait, weight in zip(traits, weight_vals):
        config[trait] = int((weight / total_weight) * args.count)

    # Adjust rounding discrepancy
    current_total = sum(config.values())
    if current_total < args.count:
        config["window"] += (args.count - current_total)

    def progress(current, total, msg):
        print(f"[{current}/{total}] {msg}")
        sys.stdout.flush()

    effective = int(args.count * args.weight)
    print(f"Starting Swarm: Total={args.count}, Effective={effective} (x{args.weight}), Traits={config}, Run ID={args.run_id or 'auto-generated'}")
    results = run_agent_swarm(config, progress, args.run_id, args.weight)
    
    print("\n=== Results ===")
    print(f"Total: {results['total']}")
    print(f"Success: {results['success']}")
    print(f"Clicked: {results['clicked']} ({results['clicked']/results['total']*100:.1f}%)")
    print(f"Purchased: {results['purchased']} ({results['purchased']/results['total']*100:.1f}%)")
    for trait, stats in results.get('by_trait', {}).items():
        ctr = stats['clicked'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"  {trait}: CTR={ctr:.1f}%")
