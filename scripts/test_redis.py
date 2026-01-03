"""Test script to list Redis sessions and their message counts."""
import asyncio
import os
import pickle
import sys
from pathlib import Path

import redis.asyncio as redis
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()


async def list_sessions():
    """List all Redis sessions with message counts."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    print("=" * 70)
    print("Redis Session Inspector")
    print("=" * 70)
    print(f"Redis URL: {redis_url}")
    print()

    # Connect to Redis
    client = redis.from_url(redis_url, decode_responses=False, encoding="utf-8")

    try:
        # Test connection
        await client.ping()
        print("✓ Connected to Redis")
        print()

        # Get all session keys
        keys = await client.keys("session:*")

        if not keys:
            print("No active sessions found.")
            print()
            print("Tip: Start a chat session with 'make chat' to create sessions.")
            return

        print(f"Found {len(keys)} active session(s):")
        print("-" * 70)

        # Process each session
        for key in sorted(keys):
            session_id = key.decode("utf-8").replace("session:", "")

            # Load session data
            data = await client.get(key)
            if not data:
                print(f"⚠️  {session_id}: (empty or expired)")
                continue

            try:
                session_data = pickle.loads(data)

                # Extract info
                messages = session_data.get("messages", [])
                metadata = session_data.get("metadata", {})
                updated_at = session_data.get("updated_at", "unknown")

                # Get TTL
                ttl = await client.ttl(key)
                ttl_hours = ttl / 3600 if ttl > 0 else 0

                # Count user vs agent messages
                user_messages = 0
                agent_messages = 0
                for msg in messages:
                    if hasattr(msg, 'kind'):
                        if msg.kind == 'request':
                            user_messages += 1
                        elif msg.kind == 'response':
                            agent_messages += 1

                # Print session info
                print(f"\n📊 Session: {session_id}")
                print(f"   User ID: {metadata.get('user_id', 'N/A')}")
                print(f"   Total Messages: {len(messages)}")
                print(f"   ├─ User messages: {user_messages}")
                print(f"   └─ Agent messages: {agent_messages}")
                print(f"   Created: {metadata.get('created_at', 'N/A')}")
                print(f"   Last Activity: {metadata.get('last_activity', updated_at)}")
                print(f"   TTL: {ttl_hours:.1f} hours remaining")

            except Exception as e:
                print(f"⚠️  {session_id}: Error loading session - {e}")

        print()
        print("-" * 70)
        print(f"Total Sessions: {len(keys)}")

    except redis.ConnectionError:
        print("❌ Failed to connect to Redis!")
        print()
        print("Make sure Redis is running:")
        print("  make redis-start")
        print("  # OR")
        print("  docker run -d --name redis -p 6379:6379 redis:7")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        await client.close()


async def clear_sessions():
    """Clear all sessions (with confirmation)."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    client = redis.from_url(redis_url, decode_responses=False, encoding="utf-8")

    try:
        keys = await client.keys("session:*")

        if not keys:
            print("No sessions to clear.")
            return

        print(f"Found {len(keys)} session(s).")
        confirm = input("Are you sure you want to delete ALL sessions? (yes/no): ")

        if confirm.lower() == 'yes':
            for key in keys:
                await client.delete(key)
            print(f"✓ Deleted {len(keys)} session(s)")
        else:
            print("Cancelled.")
    finally:
        await client.close()


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        print("⚠️  CLEAR MODE: This will delete all sessions!")
        asyncio.run(clear_sessions())
    else:
        asyncio.run(list_sessions())


if __name__ == "__main__":
    main()
