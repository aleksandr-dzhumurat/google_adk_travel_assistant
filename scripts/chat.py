#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part

from src.agent.agent import mapbox_agent
from src.utils.event_handler import EventProcessor
from src.utils.stderr_filter import apply_stderr_filter

load_dotenv()

langfuse_vars = ["LANGFUSE_HOST", "LANGFUSE_BASE_URL", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
for key in langfuse_vars:
    if key in os.environ:
        original = os.environ[key]
        cleaned = original.strip('"').strip("'")
        if original != cleaned:
            print(f"⚠️  Warning: Cleaned {key} (removed quotes)")
            print(f"   Before: {repr(original)}")
            print(f"   After: {repr(cleaned)}")
        os.environ[key] = cleaned

apply_stderr_filter()


def check_langfuse_health():
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
        print("   Install with: uv pip install langfuse openinference-instrumentation-google-adk")
        return False
    except Exception as e:
        print(f"⚠️  Langfuse initialization failed: {e}")
        print("   Continuing without observability tracking")
        return False


langfuse_available = check_langfuse_health()

if langfuse_available:
    try:
        timeout_ms = os.environ.get("OTEL_EXPORTER_OTLP_TIMEOUT", "10000")
        os.environ.setdefault("OTEL_EXPORTER_OTLP_TIMEOUT", timeout_ms)

        from openinference.instrumentation.google_adk import GoogleADKInstrumentor

        GoogleADKInstrumentor().instrument()
        print("   ✅ GoogleADKInstrumentor enabled")
        print(f"   ⏱️  Timeout: {int(timeout_ms)/1000:.1f} seconds")
        print()
    except ImportError:
        print("   ⚠️  openinference-instrumentation-google-adk not installed")
        print("   Install with: uv pip install openinference-instrumentation-google-adk")
        print()
    except Exception as e:
        print(f"   ⚠️  Instrumentation failed: {e}")
        print()


async def main():
    print("=" * 70)
    print("🗺️  Event Discovery & Route Planning Assistant")
    print("=" * 70)
    print()

    required_vars = {
        "GOOGLE_API_KEY": "Google API Key (for AI agent)",
        "PERPLEXITY_API_KEY": "Perplexity API Key (for event search)",
        "MAPBOX_ACCESS_TOKEN": "Mapbox Access Token (for geocoding & routing)"
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

    print("🚀 Initializing agent...")
    runner = InMemoryRunner(agent=mapbox_agent, app_name="EventRouteApp")
    print(f"✓ Agent initialized: {mapbox_agent.name}")
    print(f"✓ Available tools: {len(mapbox_agent.tools)} tools")
    print()

    print("📝 Creating session...")
    session = await runner.session_service.create_session(
        app_name="EventRouteApp",
        user_id="console_user"
    )
    print(f"✓ Session created: {session.id}")
    print()

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

    try:
        while True:
            print("You: ", end="", flush=True)
            user_input = input().strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print()
                print("👋 Goodbye! Thanks for using the Event Route Assistant!")
                break

            if not user_input:
                continue

            print()

            message = Content(
                parts=[Part(text=user_input)],
                role="user"
            )

            processor = EventProcessor(verbose=True)

            print("🤖 Assistant: ", end="", flush=True)
            print()

            try:
                async for event in runner.run_async(
                    user_id="console_user",
                    session_id=session.id,
                    new_message=message
                ):
                    processor.process_event(event)

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
