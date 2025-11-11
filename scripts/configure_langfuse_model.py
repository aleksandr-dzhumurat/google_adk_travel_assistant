#!/usr/bin/env python3
import os

import requests
from dotenv import load_dotenv

print(f"Loaded vars: {load_dotenv()}")

langfuse_vars = ["LANGFUSE_HOST", "LANGFUSE_BASE_URL", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
for key in langfuse_vars:
    if key in os.environ:
        os.environ[key] = os.environ[key].strip('"').strip("'")

LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

MODEL_CONFIG = {
    "modelName": "gemini-2.0-flash",
    "matchPattern": "(?i)^(gemini-2\\.0-flash)$",
    "startDate": "2025-01-01T00:00:00.000Z",
    "unit": "TOKENS",
    "inputPrice": 0.0000001,
    "outputPrice": 0.0000004,
    "totalPrice": None,
    "tokenizerId": "openai",
}


def check_credentials():
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        print("❌ ERROR: Langfuse credentials not found!")
        print()
        print("Please add the following to your .env file:")
        print("  LANGFUSE_PUBLIC_KEY=your_public_key_here")
        print("  LANGFUSE_SECRET_KEY=your_secret_key_here")
        print("  LANGFUSE_HOST=https://cloud.langfuse.com  # Optional")
        print()
        print("Get your keys from: https://cloud.langfuse.com/")
        return False
    return True


def check_existing_models():
    print("🔍 Checking existing model definitions...")
    try:
        response = requests.get(
            f"{LANGFUSE_HOST}/api/public/models",
            auth=(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY),
            timeout=10,
        )

        if response.status_code == 200:
            models = response.json()
            model_count = len(models.get("data", []))
            print(f"✅ Found {model_count} model definition(s)")

            # Check for Gemini models
            gemini_models = [
                m
                for m in models.get("data", [])
                if "gemini" in m.get("modelName", "").lower()
            ]

            if gemini_models:
                print("\n📊 Existing Gemini models:")
                for model in gemini_models:
                    print(f"   - {model.get('modelName')}")
                    print(f"     Pattern: {model.get('matchPattern')}")

                    input_price = (model.get("inputPrice") or 0) * 1_000_000
                    output_price = (model.get("outputPrice") or 0) * 1_000_000

                    if input_price > 0 or output_price > 0:
                        print(f"     Input: ${input_price:.2f}/1M tokens")
                        print(f"     Output: ${output_price:.2f}/1M tokens")
                    else:
                        print("     Pricing: Not configured")

            return models
        else:
            print(f"❌ Failed to fetch models: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return None


def create_model_definition():
    print("\n📝 Creating model definition for gemini-2.0-flash-exp...")
    print(
        f"   Input price: ${MODEL_CONFIG['inputPrice'] * 1_000_000:.2f} per 1M tokens"
    )
    print(
        f"   Output price: ${MODEL_CONFIG['outputPrice'] * 1_000_000:.2f} per 1M tokens"
    )

    try:
        response = requests.post(
            f"{LANGFUSE_HOST}/api/public/models",
            auth=(LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY),
            json=MODEL_CONFIG,
            timeout=10,
        )

        if response.status_code == 200:
            print("✅ Model definition created successfully!")
            model_data = response.json()
            print(f"   Model ID: {model_data.get('id', 'N/A')}")
            return True
        else:
            print(f"❌ Failed to create model: {response.status_code}")
            print(f"   Response: {response.text}")
            if response.status_code == 409:
                print("\n⚠️  Note: Model already exists!")
                print("   This is normal if you've run this script before.")
                print("   The existing model definition will continue to work.")
                return True
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False


def main():
    print("=" * 70)
    print("🚀 Langfuse Model Configuration")
    print("=" * 70)
    print()
    print("This script configures cost tracking for your event discovery agent.")
    print()

    if not check_credentials():
        return

    print(f"Langfuse Host: {LANGFUSE_HOST}")
    print(f"Public Key: {LANGFUSE_PUBLIC_KEY[:8]}...")
    print()

    existing_models = check_existing_models()

    if existing_models is None:
        print("\n❌ Could not connect to Langfuse API")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify LANGFUSE_HOST is correct")
        print("3. Ensure API keys are valid")
        return

    print()
    success = create_model_definition()

    print("\n" + "=" * 70)
    if success:
        print("✅ Configuration completed successfully!")
        print("=" * 70)
        print("\n📊 Next steps:")
        print("1. Verify in Langfuse UI: https://cloud.langfuse.com/")
        print("   Navigate to: Settings > Models")
        print("2. Run your agent with: make chat")
        print("3. View traces in Langfuse to see cost tracking")
        print("\n💡 Tip: Set LANGFUSE_TRACING_ENABLED=true in .env to enable tracing")
    else:
        print("⚠️  Configuration incomplete")
        print("=" * 70)
        print("\nTroubleshooting:")
        print("1. Verify credentials: https://cloud.langfuse.com/project/settings")
        print("2. Check API access permissions")
        print("3. Try deleting existing model if present")

    print()


if __name__ == "__main__":
    main()
