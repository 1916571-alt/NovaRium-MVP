"""
Quick test simulation script
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set turbo mode
os.environ['AGENT_TURBO'] = '1'

from agent_swarm.agent import HeuristicAgent
from agent_swarm.behaviors import get_behavior_by_name
import time

def test_simulation():
    print("="*60)
    print("테스트 시뮬레이션 시작")
    print("="*60)

    run_id = f"test_run_{int(time.time() * 1000)}"
    print(f"\n[RUN ID] {run_id}")

    # Create 10 agents with mixed behaviors
    agents = []
    traits = {
        "window": 4,
        "mission": 1,
        "rational": 2,
        "impulsive": 2,
        "cautious": 1
    }

    agent_id_counter = int(time.time() * 1000)

    for trait, count in traits.items():
        for i in range(count):
            agent_id = f"agent_{trait}_{agent_id_counter + i}"
            behavior = get_behavior_by_name(trait)
            agents.append(HeuristicAgent(agent_id, behavior, run_id))

    print(f"\n[AGENTS] Total {len(agents)} agents created")
    print(f"   - Window: {traits['window']}명")
    print(f"   - Mission: {traits['mission']}명")
    print(f"   - Rational: {traits['rational']}명")
    print(f"   - Impulsive: {traits['impulsive']}명")
    print(f"   - Cautious: {traits['cautious']}명")

    # Run agents
    print(f"\n[RUNNING] Simulation started...")
    results = {
        "total": len(agents),
        "success": 0,
        "clicked": 0,
        "purchased": 0,
        "by_variant": {"A": 0, "B": 0}
    }

    for i, agent in enumerate(agents):
        result = agent.run_session()
        if result.get("success"):
            results["success"] += 1
            results["by_variant"][result["variant"]] += 1
            if result.get("clicked"):
                results["clicked"] += 1
            if result.get("purchased"):
                results["purchased"] += 1

        print(f"   [{i+1}/{len(agents)}] {agent.agent_id} - Variant {result.get('variant', '?')}, Clicked: {result.get('clicked', False)}, Purchased: {result.get('purchased', False)}")

    # Print results
    print(f"\n" + "="*60)
    print("테스트 결과")
    print("="*60)
    print(f"[SUCCESS] {results['success']}/{results['total']}")
    print(f"[CLICKS] {results['clicked']} ({results['clicked']/results['total']*100:.1f}%)")
    print(f"[PURCHASES] {results['purchased']} ({results['purchased']/results['total']*100:.1f}%)")
    print(f"\n[DISTRIBUTION]")
    print(f"   - Group A: {results['by_variant']['A']}명")
    print(f"   - Group B: {results['by_variant']['B']}명")

    # Check database
    print(f"\n" + "="*60)
    print("데이터베이스 확인")
    print("="*60)

    import duckdb
    con = duckdb.connect('novarium_local.db')

    # Count assignments for this run
    count = con.execute(f"SELECT COUNT(*) FROM assignments WHERE run_id = '{run_id}'").fetchone()[0]
    print(f"[DB] Assignments saved: {count}")

    # Count events for this run
    events = con.execute(f"SELECT COUNT(*) FROM events WHERE run_id = '{run_id}'").fetchone()[0]
    print(f"[DB] Events saved: {events}")

    # Show variant distribution from DB
    variants = con.execute(f"""
        SELECT variant, COUNT(*) as cnt
        FROM assignments
        WHERE run_id = '{run_id}'
        GROUP BY variant
        ORDER BY variant
    """).fetchall()

    print(f"\n[DB DISTRIBUTION]")
    for variant, cnt in variants:
        print(f"   - Variant {variant}: {cnt}명")

    con.close()

    print(f"\n[COMPLETE] Test finished! Run ID: {run_id}")
    return run_id

if __name__ == "__main__":
    test_simulation()
