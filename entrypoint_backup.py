#!/usr/bin/env python3
"""
Entry point script for the Lodgify MCP Server Docker container.
This provides a flexible way to start the server with different configurations.
"""

import argparse
import os
import sys

# HTTP status code constants
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_SERVER_ERROR = 500
API_KEY_MASK_LENGTH = 8

def test_api_connection():  # noqa: PLR0911
    """Test the Lodgify API connection."""
    print("Testing Lodgify API connection...", file=sys.stderr)
    try:
        import httpx
        api_key = os.getenv("LODGIFY_API_KEY")
        if not api_key:
            print("❌ Error: LODGIFY_API_KEY not found", file=sys.stderr)
            print("   Please set the LODGIFY_API_KEY environment variable", file=sys.stderr)
            return False

        if api_key.lower() in ['test', 'test123', 'dummy', 'fake']:
            print(f"⚠️  Warning: Using test API key '{api_key}' - this will fail", file=sys.stderr)

        headers = {
            "X-ApiKey": api_key,
            "Content-Type": "application/json"
        }

        print(f"🔑 Using API key: {api_key[:API_KEY_MASK_LENGTH]}{'*' * (len(api_key) - API_KEY_MASK_LENGTH)}", file=sys.stderr)

        response = httpx.get(
            "https://api.lodgify.com/v2/properties?limit=1",
            headers=headers,
            timeout=10
        )

        if response.status_code == HTTP_OK:
            print("✅ Lodgify API connection successful", file=sys.stderr)
            data = response.json()
            if isinstance(data, dict) and 'items' in data:
                count = len(data['items'])
                print(f"   Found {count} properties in account", file=sys.stderr)
            return True
        elif response.status_code == HTTP_UNAUTHORIZED:
            print("❌ API connection failed: Invalid API key")
            print("   Please check your LODGIFY_API_KEY is correct")
            return False
        elif response.status_code == HTTP_FORBIDDEN:
            print("❌ API connection failed: Access forbidden")
            print("   Please check your API key permissions")
            return False
        elif response.status_code >= HTTP_SERVER_ERROR:
            print(f"❌ API connection failed: Server error ({response.status_code})")
            print("   Lodgify API appears to be having issues")
            return False
        else:
            print(f"❌ API connection failed with status {response.status_code}")
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and 'message' in error_data:
                    print(f"   Error: {error_data['message']}")
            except Exception:
                print(f"   Response: {response.text[:200]}...")
            return False
    except httpx.TimeoutException:
        print("❌ API connection error: Request timed out")
        print("   Please check your internet connection")
        return False
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def run_mcp_server():
    """Run the MCP server."""
    try:
        # Ensure we have an API key for server mode
        api_key = os.getenv("LODGIFY_API_KEY")
        if not api_key:
            print("❌ Error: LODGIFY_API_KEY is required for server mode", file=sys.stderr)
            sys.exit(1)

        from lodgify_server import mcp
        print("🚀 Starting Lodgify MCP Server...")
        print("📡 Server is ready to accept MCP protocol messages via stdin/stdout")
        print("🔗 Connect this server to an MCP client like Claude Desktop")

        # Set up proper signal handling for graceful shutdown
        import signal

        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run the server
        mcp.run()

    except KeyboardInterrupt:
        print("\n🛑 Server interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Server error: {e}", file=sys.stderr)
        sys.exit(1)

def show_info():
    """Show information about the MCP server."""
    print("🏨 Lodgify MCP Server")
    print("=" * 40)
    print("📋 This is a Model Context Protocol (MCP) server for the Lodgify API.")
    print("🏨 It provides tools and resources for managing vacation rental properties.")

    api_key = os.getenv('LODGIFY_API_KEY')
    if api_key:
        masked_key = api_key[:API_KEY_MASK_LENGTH] + '*' * (len(api_key) - API_KEY_MASK_LENGTH) if len(api_key) > API_KEY_MASK_LENGTH else '*' * len(api_key)
        print(f"🔑 API key configured: Yes ({masked_key})")
    else:
        print("🔑 API key configured: ❌ No")

    print("\n📖 To use this server, connect it to an MCP client like Claude Desktop.")
    print("🔌 The server communicates via JSON-RPC over stdin/stdout.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Lodgify MCP Server - A Model Context Protocol server for vacation rental management"
    )
    parser.add_argument(
        "--mode",
        choices=["test", "server", "info"],
        default="server",
        help="Operation mode: test API connection, run MCP server, or show info"
    )
    parser.add_argument(
        "--api-key",
        help="Lodgify API key (can also be set via LODGIFY_API_KEY env var)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    args = parser.parse_args()

    # Set environment variables
    if args.api_key:
        os.environ["LODGIFY_API_KEY"] = args.api_key

    if args.debug:
        os.environ["PYTHONPATH"] = "/app"
        print("Debug mode enabled")
        print(f"API key set: {'Yes' if args.api_key else 'No'}")
        print(f"Mode: {args.mode}")

    # Validate API key for modes that need it
    if args.mode in ["server", "test"] and not args.api_key:
        api_key = os.getenv("LODGIFY_API_KEY")
        if not api_key:
            print("❌ Error: API key is required for this mode", file=sys.stderr)
            print("   Use --api-key or set LODGIFY_API_KEY environment variable", file=sys.stderr)
            sys.exit(1)

    if args.mode == "test":
        success = test_api_connection()
        sys.exit(0 if success else 1)
    elif args.mode == "info":
        show_info()
    elif args.mode == "server":
        run_mcp_server()
