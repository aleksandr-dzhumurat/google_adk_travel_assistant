# Event Discovery & Route Planning Agent

An intelligent AI agent that helps you discover popular events in any city and plan your visits. Built with Google ADK, Perplexity AI for event search, and Mapbox for geocoding.

## ✨ Features

- 🎭 **Event Discovery**: Find popular events using Perplexity AI's real-time search
- 🗺️ **City Center Geocoding**: Get precise city coordinates as reference points
- 📍 **Proximity-Based Geocoding**: Accurate venue location with bounding box constraints
- 🔗 **Google Maps Integration**: Direct links to event locations
- 🔄 **Retry Logic**: Automatic retry with exponential backoff for API timeouts
- 💬 **Interactive Chat**: Conversational interface for event exploration

## 🚀 Quick Start

```bash
# 1. Setup environment
make setup              # Copy .env.example to .env

# 2. Edit .env and add your API keys:
#    - GOOGLE_API_KEY (from Google AI Studio)
#    - PERPLEXITY_API_KEY (from Perplexity)
#    - MAPBOX_ACCESS_TOKEN (from Mapbox)

# 3. Install dependencies
uv venv --python 3.13
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt

# 4. Start interactive chat
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
agentic_map/
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── requirements.txt          # Python dependencies
├── Makefile                  # Build commands
├── README.md                 # This file
├── scripts/
│   ├── chat.py              # 💬 Console chat interface (main entry point)
│   ├── test_agent.py        # 🧪 Tests for geocoding tools
│   └── test_setup.py        # ✅ Environment verification
└── src/
    ├── agent/
    │   ├── agent.py         # 🤖 Agent definition with tools & workflow
    │   ├── geo_tools.py     # 🗺️  Mapbox geocoding tools
    │   └── perplexity.py    # 🔍 Event search via Perplexity AI
    └── utils/
        ├── event_handler.py  # 📦 Event processing utilities
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
# Google AI API Key (for agent)
GOOGLE_API_KEY=your_google_api_key_here

# Perplexity API Key (for event search)
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Mapbox Access Token (for geocoding)
MAPBOX_ACCESS_TOKEN=your_mapbox_token_here

# Optional
AGENT_NAME=event_route_agent
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
make chat              # Start interactive chat with the agent
make test-agent        # Test geocoding tools
make test-setup        # Verify environment configuration
make run-perplexity    # Test Perplexity event search directly
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

### Architecture

- **Framework**: Google ADK (Agent Development Kit)
- **Event Search**: Perplexity AI Sonar model
- **Geocoding**: Mapbox Geocoding API
- **Runner**: InMemoryRunner (no external servers needed)
- **Tools**: Python functions wrapped with `FunctionTool()`

## 🐛 Troubleshooting

### Common Errors

**Error: "GOOGLE_API_KEY must be set"**
```bash
# Solution: Create .env file and add your key
make setup
# Edit .env and add GOOGLE_API_KEY=your_key_here
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

**Agent returns wrong country for venue:**
```
This is now fixed with bounding box constraints.
The agent only searches within ~50km of city center.
```

**API timeout errors:**
```
The agent automatically retries with exponential backoff.
If it still fails after 3 attempts, try again later.
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

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Perplexity AI API](https://docs.perplexity.ai/)
- [Mapbox Geocoding API](https://docs.mapbox.com/api/search/geocoding/)
- [Google AI Studio](https://aistudio.google.com/)
- [Langfuse Observability](https://langfuse.com/docs) - Optional cost tracking

## 🤝 Contributing

This is a personal project, but feel free to fork and adapt for your needs!

## 📄 License

MIT

---

**Made with ❤️ using Google ADK, Perplexity AI, and Mapbox**
