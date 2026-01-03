# Event Discovery & Route Planning Agent

An intelligent multi-user AI agent that helps you discover popular events in any city and plan your visits. Built with **FastAPI**, **pydantic-ai**, **Redis**, Perplexity AI for event search, and Mapbox for geocoding.

## ✨ Features

### Core Capabilities
- 🎭 **Event Discovery**: Find popular events using Perplexity AI's real-time search
- 🗺️ **City Center Geocoding**: Get precise city coordinates as reference points
- 📍 **Proximity-Based Geocoding**: Accurate venue location with bounding box constraints
- 🔗 **Google Maps Integration**: Direct links to event locations
- 🔄 **Retry Logic**: Automatic retry with exponential backoff for API timeouts

### Multi-User System
- 🌐 **FastAPI REST API**: Production-ready HTTP endpoints
- 📊 **Redis Session Management**: Distributed session storage with 24-hour TTL
- 🔄 **Real-time Streaming**: Server-Sent Events (SSE) for live responses
- ⏱️ **Status Updates**: Periodic acknowledgments every 3 seconds during long operations
- 👥 **Concurrent Users**: Support for multiple simultaneous sessions
- 💬 **Interactive Chat**: CLI client with streaming support

## 🚀 Quick Start

```bash
# 1. Setup environment
make setup              # Copy .env.example to .env

# 2. Edit .env and add your API keys:
#    - GEMINI_API_KEY (from Google AI Studio)
#    - PERPLEXITY_API_KEY (from Perplexity)
#    - MAPBOX_ACCESS_TOKEN (from Mapbox)

# 3. Install dependencies
uv venv --python 3.13
source .venv/bin/activate
uv pip install -r requirements.txt

# 4. Start Redis (required for session management)
docker run -d --name redis -p 6379:6379 redis:7
# OR: make redis-start

# 5. Start FastAPI server (Terminal 1)
make api-dev
# Server will start at http://localhost:8000

# 6. Start interactive chat (Terminal 2)
make chat
```

## 💬 Example Conversation

Once you run `make chat`, here's how to interact with the agent:

```
You: Hi, I want to explore events in a city

Agent: Hello! I'd be happy to help you discover events. Which city and country
       would you like to explore?

You: Limassol, Cyprus

Agent: [Gets city center coordinates: 34.6851, 33.0328]
       [Searches for events in Limassol for November 2025]

       Here are the top events in Limassol, Cyprus for November 2025:

       1. Limassol Wine Festival
          Date: November 5-7, 2025
          Venue: Limassol Municipal Gardens
          Description: Annual celebration of Cypriot wines with tastings...

       2. Limassol Marathon
          Date: November 13, 2025
          Venue: Molos Promenade
          Description: International marathon event along the coastal road...

       3. Contemporary Art Exhibition
          Date: November 15-30, 2025
          Venue: Rialto Theatre
          Description: Modern art showcase featuring local and international artists...

       [... more events ...]

       Which events would you like to visit? Please select by number (e.g., 1, 3, 5).

You: 1, 3

Agent: [Geocodes only events #1 and #3]

       Great! Here are your selected events with locations:

       📍 Google Maps Links:

       1. Limassol Wine Festival - Limassol Municipal Gardens
          https://www.google.com/maps?q=34.6851,33.0320

       3. Contemporary Art Exhibition - Rialto Theatre
          https://www.google.com/maps?q=34.6734,33.0424

       Click these links to view locations in Google Maps and plan your visit!
```

## 🏗️ Project Structure

```
google_adk_travel_assistant/
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
├── Makefile                  # Build commands
├── README.md                 # This file
├── scripts/
│   ├── test_chat.py         # 💬 Interactive CLI chat client with streaming
│   ├── test_agent.py        # 🧪 Tests for geocoding tools
│   └── test_setup.py        # ✅ Environment verification
└── src/
    ├── api/                 # 🌐 FastAPI application
    │   ├── app.py           # FastAPI app with lifespan management
    │   ├── dependencies.py  # Dependency injection
    │   └── routes/
    │       ├── sessions.py  # Session CRUD endpoints
    │       ├── messages.py  # Message/chat endpoints
    │       └── health.py    # Health check & metrics
    ├── services/            # 🔧 Business logic layer
    │   ├── session_store.py     # Redis session persistence
    │   ├── session_manager.py   # Session management with streaming
    │   └── agent_factory.py     # Agent creation & configuration
    ├── models/              # 📋 Pydantic models
    │   ├── requests.py      # Request models (CreateSession, SendMessage)
    │   └── responses.py     # Response models (SessionResponse, etc.)
    ├── config/              # ⚙️  Configuration
    │   └── settings.py      # Pydantic settings from environment
    ├── agent/               # 🤖 Agent implementation
    │   ├── pydantic_agent.py # pydantic-ai agent with tools
    │   ├── geo_tools.py     # 🗺️  Mapbox geocoding tools
    │   └── perplexity.py    # 🔍 Event search via Perplexity AI
    └── utils/
        └── stderr_filter.py  # 🔇 Warning suppression
```

## 🔧 Setup

### 1. Environment Variables

Copy `.env.example` to `.env`:

```bash
make setup
```

Then edit `.env` and add your API keys:

```bash
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key_here        # Google AI API Key (for agent)
PERPLEXITY_API_KEY=your_perplexity_api_key_here
MAPBOX_ACCESS_TOKEN=your_mapbox_token_here

# Redis Configuration
REDIS_URL=redis://localhost:6379
SESSION_TTL_HOURS=24

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
GEMINI_MODEL=gemini-2.0-flash-exp
MAX_SESSIONS=100
MAX_MESSAGES_PER_SESSION=50

# Optional - Langfuse Observability
LANGFUSE_PUBLIC_KEY=your_public_key_here
LANGFUSE_SECRET_KEY=your_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 2. Get API Keys

**Google API Key:**
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click "Create API Key"
3. Copy and add to `.env`

**Perplexity API Key:**
1. Go to [Perplexity AI](https://www.perplexity.ai/)
2. Sign up and navigate to [API Settings](https://www.perplexity.ai/settings/api)
3. Generate an API key
4. Copy and add to `.env`

**Mapbox Access Token:**
1. Go to [Mapbox Account](https://account.mapbox.com/)
2. Sign up or log in
3. Navigate to "Access tokens"
4. Copy your default public token
5. Paste in `.env`

### 3. Install Dependencies

```bash
# Create virtual environment
uv venv --python 3.13

# Activate it
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -r requirements.txt
```

### 4. Start Redis Server

Redis is required for distributed session management:

```bash
# Using Docker (recommended)
docker run -d --name redis -p 6379:6379 redis:7

# OR using Makefile
make redis-start

# Verify Redis is running
docker ps | grep redis
```

**Alternative**: Install Redis locally
- macOS: `brew install redis && brew services start redis`
- Ubuntu: `sudo apt install redis-server`
- Windows: Use Docker or WSL2

## 🎯 How It Works

The agent follows an intelligent 6-step workflow:

```
1. 📍 Clarify Location
   ↓ Ask user for city and country

2. 🗺️  Get City Center
   ↓ Find city center coordinates using Mapbox

3. 🔍 Search Events
   ↓ Discover events using Perplexity AI (current month)

4. 📋 Present Events
   ↓ Show numbered list with details

5. ✅ User Selection
   ↓ User picks events to visit

6. 🔗 Geocode & Generate Links
   ↓ Geocode selected venues
   ↓ Create Google Maps links
```

### Geocoding Strategy

The agent uses a **three-layer constraint** approach for accurate geocoding:

1. **Enhanced Query**: Appends city and country to venue names
   ```
   "Louvre Museum" → "Louvre Museum, Paris, France"
   ```

2. **Bounding Box**: Restricts results to ~50km radius from city center
   ```
   Prevents: "Art Gallery" in Cyprus → Result from Australia ❌
   Ensures: "Art Gallery" in Cyprus → Result from Cyprus ✅
   ```

3. **Proximity Bias**: Ranks results closer to city center higher
   ```
   Uses Mapbox proximity parameter for optimal results
   ```

## 🛠️ Available Commands

```bash
# Multi-User System
make redis-start       # Start Redis in Docker
make redis-stop        # Stop Redis container
make api-dev           # Start FastAPI server with auto-reload
make chat              # Start interactive CLI chat client
make list-redis        # List all Redis sessions with message counts

# Testing & Development
make test-agent        # Test geocoding tools
make test-setup        # Verify environment configuration
make run-perplexity    # Test Perplexity event search directly

# Optional
make configure-langfuse # Configure Langfuse model pricing (optional)
make clean             # Remove Python cache files
make setup             # Copy .env.example to .env
```

## 📚 Usage Examples

### Interactive Chat

```bash
make chat
```

Then ask naturally:
- `"I want to explore events in Paris, France"`
- `"Show me what's happening in Tokyo this month"`
- `"Find events in New York"`
- `"What can I do in Barcelona?"`

### Monitoring Redis Sessions

```bash
# List all active sessions with message counts
make list-redis

# Example output:
# ======================================================================
# Redis Session Inspector
# ======================================================================
# Redis URL: redis://localhost:6379
#
# ✓ Connected to Redis
#
# Found 2 active session(s):
# ----------------------------------------------------------------------
#
# 📊 Session: 12345678-abcd-1234-abcd-123456789abc
#    User ID: user_alice
#    Total Messages: 12
#    ├─ User messages: 6
#    └─ Agent messages: 6
#    Created: 2025-01-03T10:30:00
#    Last Activity: 2025-01-03T11:45:00
#    TTL: 22.5 hours remaining
#
# ----------------------------------------------------------------------
# Total Sessions: 2
```

### Testing Individual Tools

```bash
# Test geocoding and city center tools
make test-agent

# Output:
# ✅ Test 1: Get City Center (Paris, France)
# ✅ Test 2: Geocoding (1600 Amphitheatre Parkway)
# ✅ Test 3: Reverse Geocoding

# Test Perplexity event search
make run-perplexity
```

## 🔍 Technical Details

### Architecture

**Multi-User System:**
- **Framework**: pydantic-ai with Google Gemini 2.0 Flash
- **API**: FastAPI with async endpoints and Server-Sent Events (SSE)
- **Session Management**: Redis with pickle serialization
- **Streaming**: Real-time response streaming with status updates

**Agent & Tools:**
- **Event Search**: Perplexity AI Sonar model
- **Geocoding**: Mapbox Geocoding API with proximity constraints
- **Tools**: 5 async tools decorated with `@event_agent.tool`
- **Tool Execution**: `end_strategy='exhaustive'` ensures ALL tools execute before streaming text

### Streaming & Status Updates

The system provides real-time feedback during long operations:

```python
# Agent configured for exhaustive tool execution
event_agent = Agent(
    model=GeminiModel("gemini-2.0-flash-exp"),
    deps_type=AgentDependencies,
    system_prompt=SYSTEM_PROMPT,
    retries=2,
    end_strategy='exhaustive',  # Execute ALL tool calls before returning
)
```

**Status Update Flow:**
1. Client sends message via `/sessions/{id}/messages/stream`
2. Server immediately acknowledges: `"Processing your request..."`
3. Agent executes tools (get_city_center, search_events)
4. During execution, status messages appear every 3 seconds:
   - "Still searching for information..."
   - "This is taking a bit longer than expected..."
5. Once tools complete, agent streams text response in real-time
6. Client receives `[DONE]` signal when complete

**Key Implementation:**
```python
# Background task runs agent stream
async with agent.run_stream(message, deps=deps, message_history=messages) as result:
    async for chunk in result.stream_text(delta=True):
        yield {"type": "text", "content": chunk}

# Status updates sent every 3 seconds during tool execution
if elapsed >= 3.0 and consecutive_timeouts >= 3:
    yield {"type": "status", "content": "Still working..."}
```

### Server-Sent Events (SSE)

**What is SSE?**

Server-Sent Events (SSE) is a web technology that enables servers to push real-time updates to clients over a single HTTP connection. Unlike traditional request-response, SSE keeps the connection open and sends data as it becomes available.

**Why SSE for this project?**

- ✅ **Real-time Streaming**: Agent responses appear word-by-word as they're generated
- ✅ **Status Updates**: Show "Still working..." messages during long tool executions
- ✅ **Single Connection**: No polling needed - efficient and low-latency
- ✅ **Built-in Reconnection**: Browsers automatically reconnect if connection drops
- ✅ **Simple Protocol**: Text-based format easier to debug than WebSockets

**How SSE Works Here:**

```python
# Server (FastAPI) - src/api/routes/messages.py
@router.post("/{session_id}/messages/stream")
async def send_message_stream(...):
    async def generate():
        # Send chunks as they arrive
        async for chunk in manager.send_message_stream(session_id, message):
            yield f"data: {json.dumps(chunk)}\n\n"  # ← SSE format
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

```python
# Client (scripts/test_chat.py)
response = requests.post(url, json=payload, stream=True)

for line in response.iter_lines():
    if line.startswith('data: '):
        data = json.loads(line[6:])  # Remove 'data: ' prefix

        if data['type'] == 'text':
            print(data['content'], end='', flush=True)  # Stream to console
        elif data['type'] == 'status':
            print(f"\n💭 {data['content']}")
```

**SSE Message Format:**

Each SSE message follows this format:
```
data: {"type": "status", "content": "Processing..."}

data: {"type": "text", "content": "Hello"}

data: {"type": "text", "content": " world"}

data: {"type": "done", "message_count": 12}

data: [DONE]

```

**SSE vs WebSockets:**

| Feature | SSE (This Project) | WebSockets |
|---------|-------------------|------------|
| Direction | Server → Client only | Bi-directional |
| Protocol | HTTP | Custom protocol |
| Complexity | Simple | More complex |
| Reconnection | Automatic | Manual |
| Use Case | Real-time updates | Chat, gaming |

SSE is perfect for this project because we only need server-to-client streaming (agent responses), not client-to-server streaming.

### Retry Logic

Perplexity API calls use exponential backoff to handle timeouts gracefully:

```python
@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=3,
    max_time=90
)
```

- **Max retries**: 3 attempts
- **Max time**: 90 seconds total
- **Wait pattern**: ~1s, ~2s, ~4s, ~8s
- **Handles**: Timeout and Connection errors

### Session Persistence

**Redis Storage:**
- **Key Prefix**: `session:{session_id}` (e.g., `session:user_alice`)
- Sessions stored with 24-hour TTL
- Message history serialized with pickle
- Automatic TTL refresh on each interaction
- Support for 100+ concurrent sessions

**Session Manager:**
- Per-process agent caching for performance
- Message history trimming (max 50 messages)
- Thread pool for running sync geo_tools in async context

**Monitoring:**
- Use `make list-redis` to inspect active sessions
- Shows message counts, TTL, and last activity
- Helpful for debugging and monitoring user interactions

## 🐛 Troubleshooting

### Common Errors

**Error: "GEMINI_API_KEY must be set"**
```bash
# Solution: Create .env file and add your key
make setup
# Edit .env and add GEMINI_API_KEY=your_key_here
```

**Error: "Connection refused" or "Redis connection failed"**
```bash
# Solution: Start Redis server
make redis-start
# OR
docker run -d --name redis -p 6379:6379 redis:7

# Verify Redis is running
docker ps | grep redis
```

**Error: "API server is not running!"**
```bash
# Solution: Start FastAPI server in a separate terminal
make api-dev
# OR
uvicorn src.api.app:app --reload

# Check server health
curl http://localhost:8000/api/v1/health
```

**Error: "PERPLEXITY_API_KEY must be set"**
```bash
# Solution: Add Perplexity API key to .env
# Edit .env and add PERPLEXITY_API_KEY=your_key_here
```

**Error: "MAPBOX_ACCESS_TOKEN not found"**
```bash
# Solution: Add Mapbox token to .env
# Edit .env and add MAPBOX_ACCESS_TOKEN=your_token_here
```

**Agent not calling tools / saying "I'll search..." but not executing:**
```
This was fixed by adding end_strategy='exhaustive' to the Agent configuration.
The agent now executes ALL tool calls before streaming text responses.
```

**Agent returns wrong country for venue:**
```
This is now fixed with bounding box constraints.
The agent only searches within ~50km of city center.
```

**Stream timeout or "(Failed to get response)":**
```
The streaming timeout is 120 seconds. If operations take longer:
1. Check Redis connection
2. Check Perplexity API status
3. Look at server logs: make api-dev will show detailed logs
```

## 📊 Optional: Langfuse Observability

[Langfuse](https://langfuse.com/) is an open-source LLM observability platform that helps you track costs, monitor performance, and debug your agent.

### Benefits

- 💰 **Cost Tracking**: Monitor token usage and API costs per conversation
- 📈 **Performance Analytics**: Track response times and success rates
- 🐛 **Debugging**: Replay conversations and inspect tool calls
- 📊 **Usage Insights**: Understand user patterns and popular queries

### Setup

1. **Create Langfuse account** (free):
   ```bash
   # Visit: https://cloud.langfuse.com/
   ```

2. **Get API keys**:
   - Go to Settings → API Keys
   - Create new key pair
   - Copy Public Key and Secret Key

3. **Add to `.env`**:
   ```bash
   LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
   LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

4. **Configure model pricing**:
   ```bash
   make configure-langfuse
   ```

5. **View traces**:
   - Run your agent: `make chat`
   - Open Langfuse dashboard
   - Navigate to "Traces" to see conversations
   - Check "Models" → "Usage" for cost analysis

### What Gets Tracked

- ✅ Every conversation and message
- ✅ Token counts (input/output)
- ✅ API costs (based on Gemini pricing)
- ✅ Response times
- ✅ Tool calls (geocoding, event search)
- ✅ Errors and exceptions

### Example Dashboard

After running a few conversations, you'll see:
- Total cost: $0.02
- Total tokens: 5,234
- Average response time: 2.3s
- Success rate: 98%
- Most used tools: `search_events`, `geocode_address_near`

## 📖 Resources

### Frameworks & APIs
- [pydantic-ai Documentation](https://github.com/pydantic/pydantic-ai) - Agent framework
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Web framework
- [Redis Documentation](https://redis.io/docs/) - Session storage
- [Perplexity AI API](https://docs.perplexity.ai/) - Event search
- [Mapbox Geocoding API](https://docs.mapbox.com/api/search/geocoding/) - Geocoding
- [Google AI Studio](https://aistudio.google.com/) - Get Gemini API key
- [Langfuse Observability](https://langfuse.com/docs) - Optional cost tracking

### Key Technologies
- **pydantic-ai**: Modern agent framework with tool decorators
- **FastAPI**: Async web framework with Server-Sent Events (SSE) for real-time streaming
- **Redis**: In-memory data store for distributed session management
- **Google Gemini 2.0 Flash**: Fast LLM for agent responses with streaming support

## 🤝 Contributing

This is a personal project, but feel free to fork and adapt for your needs!

## 📄 License

MIT

---

**Made with ❤️ using pydantic-ai, FastAPI, Redis, Google Gemini, Perplexity AI, and Mapbox**
