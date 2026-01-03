"""Verify that settings load correctly from .env file."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.settings import settings


def main():
    """Verify settings loaded correctly."""
    print("=" * 70)
    print("Settings Verification")
    print("=" * 70)
    print()

    # Required settings
    print("✓ REQUIRED Settings (from .env):")
    print(f"  - Gemini API Key:      {settings.gemini_api_key[:20]}... (length: {len(settings.gemini_api_key)})")
    print(f"  - Perplexity API Key:  {settings.perplexity_api_key[:20]}... (length: {len(settings.perplexity_api_key)})")
    print(f"  - Mapbox Access Token: {settings.mapbox_access_token[:20]}... (length: {len(settings.mapbox_access_token)})")
    print()

    # Optional settings from .env
    print("✓ OPTIONAL Settings (from .env if provided):")
    print(f"  - Agent Name:          {settings.agent_name}")
    print(f"  - Agent Debug:         {settings.agent_debug}")
    print()

    # Langfuse (if configured)
    if settings.langfuse_public_key:
        print(f"  - Langfuse Enabled:    Yes")
        print(f"    Public Key:          {settings.langfuse_public_key[:20]}...")
    else:
        print(f"  - Langfuse Enabled:    No (not configured)")
    print()

    # BrightData (if configured)
    if settings.brightdata_token:
        print(f"  - BrightData Token:    {settings.brightdata_token[:20]}... (configured)")
    else:
        print(f"  - BrightData Token:    Not configured")
    print()

    # Settings with defaults
    print("✓ DEFAULT Settings (using built-in defaults):")
    print(f"  - Redis URL:           {settings.redis_url}")
    print(f"  - API Host:            {settings.api_host}")
    print(f"  - API Port:            {settings.api_port}")
    print(f"  - Session TTL Hours:   {settings.session_ttl_hours}")
    print(f"  - Max Sessions:        {settings.max_sessions}")
    print(f"  - Gemini Model:        {settings.gemini_model}")
    print(f"  - Log Level:           {settings.log_level}")
    print()

    print("=" * 70)
    print("✅ All settings loaded successfully!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        print()
        print("Make sure you have a .env file with required variables:")
        print("  - GEMINI_API_KEY")
        print("  - PERPLEXITY_API_KEY")
        print("  - MAPBOX_ACCESS_TOKEN")
        sys.exit(1)
