#!/usr/bin/env python3
"""
Interactive console chat with the event discovery and route planning agent.

This script provides a conversational interface where users can:
1. Specify a country and city
2. Discover popular events in that location
3. Plan routes between event locations

Prerequisites:
- Environment variables configured in .env file
- GOOGLE_API_KEY must be set
- PERPLEXITY_API_KEY must be set
- MAPBOX_ACCESS_TOKEN must be set

Usage:
    python scripts/chat.py
    or
    make chat
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

# Import agent and utilities
from src.agent.agent import mapbox_agent
from src.utils.event_handler import EventProcessor
from src.utils.stderr_filter import apply_stderr_filter

print(f"Loaded vars: {load_dotenv()}")

for key in ["LANGFUSE_HOST", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]:
    if key in os.environ:
        os.environ[key] = os.environ[key].strip('"').strip("'")

apply_stderr_filter()


def check_langfuse_health():
    """Verify Langfuse connection and configuration."""
    try:
        langfuse_public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
        langfuse_secret_key = os.environ.get("LANGFUSE_SECRET_KEY")

        if not langfuse_public_key or not langfuse_secret_key:
            return False

        langfuse_host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

        print("📊 Langfuse observability enabled:")
        print(f"   Host: {langfuse_host}")
        print(f"   Public Key: {langfuse_public_key[:8]}...")

        from langfuse import Langfuse

        langfuse_client = Langfuse(
            public_key=langfuse_public_key,
            secret_key=langfuse_secret_key,
            host=langfuse_host,
        )

        if langfuse_client:
            print("   ✅ Langfuse client initialized")
            print("   📈 All conversations will be tracked")
            return True
        else:
            return False

    except ImportError:
        print("⚠️  Langfuse package not installed (observability disabled)")
        print(
            "   Install with: uv pip install langfuse openinference-instrumentation-google-adk"
        )
        return False
    except Exception as e:
        print(f"⚠️  Langfuse initialization failed: {e}")
        print("   Continuing without observability tracking")
        return False


# Check and enable Langfuse instrumentation
langfuse_available = check_langfuse_health()

if langfuse_available:
    try:
        from openinference.instrumentation.google_adk import GoogleADKInstrumentor

        GoogleADKInstrumentor().instrument()
        print("   ✅ GoogleADKInstrumentor enabled")
        print()
    except ImportError:
        print("   ⚠️  openinference-instrumentation-google-adk not installed")
        print(
            "   Install with: uv pip install openinference-instrumentation-google-adk"
        )
        print()
    except Exception as e:
        print(f"   ⚠️  Instrumentation failed: {e}")
        print()


async def main():
    """Run interactive console chat."""

    print("=" * 70)
    print("🗺️  Event Discovery & Route Planning Assistant")
    print("=" * 70)
    print()

    # Check required environment variables
    required_vars = {
        "GOOGLE_API_KEY": "Google API Key (for AI agent)",
        "PERPLEXITY_API_KEY": "Perplexity API Key (for event search)",
        "MAPBOX_ACCESS_TOKEN": "Mapbox Access Token (for geocoding & routing)",
    }

    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  - {var}: {description}")

    if missing_vars:
        print("❌ ERROR: Missing required environment variables:")
        print()
        for var in missing_vars:
            print(var)
        print()
        print("Please set these in your .env file")
        return

    print("✓ All environment variables configured")
    print()

    # Initialize runner
    print("🚀 Initializing agent...")
    runner = InMemoryRunner(agent=mapbox_agent, app_name="EventRouteApp")
    print(f"✓ Agent initialized: {mapbox_agent.name}")
    print(f"✓ Available tools: {len(mapbox_agent.tools)} tools")
    print()

    # Create session
    print("📝 Creating session...")
    session = await runner.session_service.create_session(
        app_name="EventRouteApp", user_id="console_user"
    )
    print(f"✓ Session created: {session.id}")
    print()

    # Display help
    print("=" * 70)
    print("💬 Chat Instructions")
    print("=" * 70)
    print()
    print("The agent will help you discover events and plan routes.")
    print()
    print("Example conversation flow:")
    print("  1. Agent: 'Which country and city would you like to explore?'")
    print("  2. You: 'Paris, France'")
    print("  3. Agent will search for events and help plan routes")
    print()
    print("Commands:")
    print("  - Type 'quit', 'exit', or 'q' to end the chat")
    print("  - Press Ctrl+C to interrupt")
    print()
    print("=" * 70)
    print()

    # Start chat loop
    try:
        while True:
            # Get user input
            print("You: ", end="", flush=True)
            user_input = input().strip()

            # Check for exit commands
            if user_input.lower() in ["quit", "exit", "q"]:
                print()
                print("👋 Goodbye! Thanks for using the Event Route Assistant!")
                break

            # Skip empty input
            if not user_input:
                continue

            print()

            # Create message
            message = Content(parts=[Part(text=user_input)], role="user")

            # Process with event handler
            processor = EventProcessor(verbose=True)

            print("🤖 Assistant: ", end="", flush=True)
            print()

            try:
                async for event in runner.run_async(
                    user_id="console_user", session_id=session.id, new_message=message
                ):
                    processor.process_event(event)

                # Get and display response
                response_text = processor.get_response()
                print()
                print(f"🤖 {response_text}")
                print()

            except Exception as e:
                print()
                print(f"❌ Error processing message: {e}")
                import traceback

                traceback.print_exc()
                print()

    except KeyboardInterrupt:
        print()
        print()
        print("⚠️  Chat interrupted by user")
        print("👋 Goodbye!")
    except Exception as e:
        print()
        print(f"❌ Chat error: {e}")
        import traceback

        traceback.print_exc()

    print()
    print("=" * 70)


if __name__ == "__main__":
    print()
    print("🚀 Starting Event Discovery & Route Planning Chat")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
