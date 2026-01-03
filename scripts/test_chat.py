"""Interactive chat client for testing FastAPI multi-user system."""
import json
import sys
import uuid
from pathlib import Path

import requests

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
USER_ID = str(uuid.uuid4())  # Generate unique user ID for this session


def create_session(user_id: str) -> str:
    """Create a new session for the user."""
    url = f"{API_BASE_URL}/sessions"
    payload = {"user_id": user_id}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        session_id = data["session_id"]
        print(f"✓ Session created: {session_id}")
        return session_id
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create session: {e}")
        sys.exit(1)


def get_session_info(session_id: str) -> dict:
    """Get session information."""
    url = f"{API_BASE_URL}/sessions/{session_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def send_message_stream(session_id: str, message: str) -> tuple[str, int]:
    """Send a message and stream agent response.

    Returns:
        tuple of (full_response, message_count)
    """
    url = f"{API_BASE_URL}/sessions/{session_id}/messages/stream"
    payload = {"message": message}

    try:
        response = requests.post(url, json=payload, stream=True, timeout=120)
        response.raise_for_status()

        full_response = ""
        message_count = 0
        got_done_signal = False

        # Process Server-Sent Events
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix

                    if data_str == '[DONE]':
                        got_done_signal = True
                        break

                    try:
                        data = json.loads(data_str)
                        chunk_type = data.get('type')
                        content = data.get('content', '')

                        if chunk_type == 'status':
                            print(f"\n💭 {content}", flush=True)
                            print("🤖 ", end='', flush=True)  # Continue agent prefix
                        elif chunk_type == 'text':
                            print(content, end='', flush=True)
                            full_response += content
                        elif chunk_type == 'done':
                            message_count = data.get('message_count', 0)
                        elif chunk_type == 'error':
                            print(f"\n❌ Error: {content}")
                            return None, 0
                    except json.JSONDecodeError:
                        pass

        if not got_done_signal and not full_response:
            print("\n⚠️  Stream ended without completion signal")
            return None, 0

        return full_response, message_count
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timeout after 120s")
        return None, 0
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Failed to send message: {e}")
        return None, 0


def send_message(session_id: str, message: str) -> dict:
    """Send a message and get agent response (non-streaming fallback)."""
    url = f"{API_BASE_URL}/sessions/{session_id}/messages"
    payload = {"message": message}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send message: {e}")
        return None


def check_health() -> bool:
    """Check if the API server is running."""
    url = f"{API_BASE_URL}/health"

    try:
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False


def main():
    """Run interactive chat session."""
    print("=" * 70)
    print("FastAPI Multi-User Chat Client")
    print("=" * 70)
    print()

    # Check server health
    print("Checking server status...")
    if not check_health():
        print("❌ API server is not running!")
        print()
        print("Please start the server first:")
        print("  make api-dev")
        print("  # or")
        print("  uvicorn src.api.app:app --reload")
        sys.exit(1)
    print("✓ API server is running")
    print()

    # Create or reuse session
    print(f"User ID: {USER_ID}")
    session_id = create_session(USER_ID)
    print()

    print("=" * 70)
    print("Chat Session Started")
    print("=" * 70)
    print("Type your messages below. Commands:")
    print("  'quit' or 'exit' - End session")
    print("  'info' - Show session info")
    print("  'clear' - Clear screen")
    print()

    # Interactive chat loop
    message_count = 0
    while True:
        try:
            # Get user input
            user_input = input("\n🧑 You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in ['quit', 'exit']:
                print("\n👋 Ending chat session...")
                break

            if user_input.lower() == 'info':
                info = get_session_info(session_id)
                if info:
                    print(f"\n📊 Session Info:")
                    print(f"  Session ID: {info['session_id']}")
                    print(f"  User ID: {info['user_id']}")
                    print(f"  Messages: {info['message_count']}")
                    print(f"  Created: {info['created_at']}")
                continue

            if user_input.lower() == 'clear':
                print("\033[2J\033[H")  # Clear screen
                continue

            # Send message to agent (streaming with exhaustive tool execution)
            print("\n🤖 Agent: ", end="", flush=True)
            response, msg_count = send_message_stream(session_id, user_input)

            if response:
                message_count = msg_count
                print()  # New line after streaming response
            else:
                print("(Failed to get response)")

        except KeyboardInterrupt:
            print("\n\n👋 Chat interrupted. Exiting...")
            break
        except EOFError:
            print("\n\n👋 End of input. Exiting...")
            break

    print()
    print("=" * 70)
    print(f"Session ended. Total messages: {message_count}")
    print("=" * 70)


if __name__ == "__main__":
    main()
