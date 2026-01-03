"""Verify that EventSearcher is a singleton by checking instance IDs."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import settings
from services.agent_factory import AgentFactory


async def main():
    """Demonstrate that EventSearcher is a singleton."""
    print("=" * 60)
    print("EventSearcher Singleton Verification")
    print("=" * 60)
    print()

    # Create AgentFactory (simulates startup)
    print("1. Creating AgentFactory (simulates application startup)...")
    factory = AgentFactory(settings)
    print(f"   ✓ AgentFactory created at: {hex(id(factory))}")
    print(f"   ✓ EventSearcher created at: {hex(id(factory.event_searcher))}")
    print()

    # Simulate multiple requests creating dependencies
    print("2. Simulating 5 user requests (create_dependencies called 5 times)...")
    print()

    searcher_ids = set()
    deps_ids = set()

    for i in range(1, 6):
        # This is what happens on every request
        deps = factory.create_dependencies()

        searcher_id = id(deps.event_searcher)
        deps_id = id(deps)

        searcher_ids.add(searcher_id)
        deps_ids.add(deps_id)

        print(f"   Request #{i}:")
        print(f"      - AgentDependencies ID: {hex(deps_id)} {'(NEW)' if len(deps_ids) == i else '(DUPLICATE!)'}")
        print(f"      - EventSearcher ID:     {hex(searcher_id)} {'(SAME!)' if searcher_id in searcher_ids else '(NEW!)'}")
        print()

    # Results
    print("3. Results:")
    print(f"   - Unique AgentDependencies instances: {len(deps_ids)} ✓ (should be 5)")
    print(f"   - Unique EventSearcher instances:     {len(searcher_ids)} ✓ (should be 1)")
    print()

    if len(searcher_ids) == 1:
        print("✅ SUCCESS: EventSearcher is a singleton!")
        print(f"   All requests share EventSearcher at {hex(list(searcher_ids)[0])}")
    else:
        print("❌ FAILURE: EventSearcher is NOT a singleton!")
        print(f"   Found {len(searcher_ids)} different instances")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
