#!/usr/bin/env python3
"""
Entry point script for the Lodgify MCP Server.
This provides a flexible way to start the server with different configurations.
"""

import argparse
import asyncio
import os
import sys

import httpx

from lodgify_server import LodgifyConfig, test_lodgify_api_connection

API_KEY_MASK_LENGTH = 4


async def run_test_api_connection() -> bool:
    api_key = os.getenv("LODGIFY_API_KEY")
    if not api_key:
        print("❌ Error: LODGIFY_API_KEY not found", file=sys.stderr)
        print("   Please set the LODGIFY_API_KEY environment variable", file=sys.stderr)
        return False

    config = LodgifyConfig(api_key=api_key)
    async with httpx.AsyncClient(
        base_url=config.base_url,
        headers={
            "X-ApiKey": config.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=config.timeout,
    ) as client:
        return await test_lodgify_api_connection(client)


def test_api_connection() -> bool:
    return asyncio.run(run_test_api_connection())


def run_mcp_server() -> None:
    """Run the MCP server."""
    try:
        # Ensure we have an API key for server mode
        api_key = os.getenv("LODGIFY_API_KEY")
        if not api_key:
            print(
                "❌ Error: LODGIFY_API_KEY is required for server mode", file=sys.stderr
            )
            sys.exit(1)

        from lodgify_server import mcp

        print("🚀 Starting Lodgify MCP Server...", file=sys.stderr)
        print(
            "📡 Server is ready to accept MCP protocol messages via stdin/stdout",
            file=sys.stderr,
        )
        print(
            "🔗 Connect this server to an MCP client like Claude Desktop",
            file=sys.stderr,
        )

        # Set up proper signal handling for graceful shutdown
        import signal

        def signal_handler(signum: int, frame: object) -> None:
            print(
                f"\n🛑 Received signal {signum}, shutting down gracefully...",
                file=sys.stderr,
            )
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run the server
        mcp.run()

    except KeyboardInterrupt:
        print("\n🛑 Server interrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Server error: {e}", file=sys.stderr)
        sys.exit(1)


def show_info() -> None:
    """Show information about the MCP server."""
    print("🏨 Lodgify MCP Server", file=sys.stderr)
    print("=" * 40, file=sys.stderr)
    print(
        "📋 This is a Model Context Protocol (MCP) server for the Lodgify API.",
        file=sys.stderr,
    )
    print(
        "🏨 It provides tools and resources for managing vacation rental properties.",
        file=sys.stderr,
    )

    api_key = os.getenv("LODGIFY_API_KEY")
    if api_key:
        masked_key = (
            api_key[:API_KEY_MASK_LENGTH] + "*" * (len(api_key) - API_KEY_MASK_LENGTH)
            if len(api_key) > API_KEY_MASK_LENGTH
            else "*" * len(api_key)
        )
        print(f"🔑 API key configured: Yes ({masked_key})", file=sys.stderr)
    else:
        print("🔑 API key configured: ❌ No", file=sys.stderr)

    print(
        "\n📖 To use this server, connect it to an MCP client like Claude Desktop.",
        file=sys.stderr,
    )
    print("🔌 The server communicates via JSON-RPC over stdin/stdout.", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Lodgify MCP Server - A Model Context Protocol server for vacation rental management"
    )
    parser.add_argument(
        "--mode",
        choices=["test", "server", "info"],
        default="server",
        help="Operation mode: test API connection, run MCP server, or show info",
    )
    parser.add_argument(
        "--api-key",
        help="Lodgify API key (can also be set via LODGIFY_API_KEY env var)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Set environment variables
    if args.api_key:
        os.environ["LODGIFY_API_KEY"] = args.api_key

    if args.debug:
        os.environ["PYTHONPATH"] = "/app"
        print("Debug mode enabled", file=sys.stderr)
        print(f"API key set: {'Yes' if args.api_key else 'No'}", file=sys.stderr)
        print(f"Mode: {args.mode}", file=sys.stderr)

    # Validate API key for modes that need it
    if args.mode in ["server", "test"] and not args.api_key:
        api_key = os.getenv("LODGIFY_API_KEY")
        if not api_key:
            print("❌ Error: API key is required for this mode", file=sys.stderr)
            print(
                "   Use --api-key or set LODGIFY_API_KEY environment variable",
                file=sys.stderr,
            )
            sys.exit(1)

    if args.mode == "test":
        success = test_api_connection()
        sys.exit(0 if success else 1)
    elif args.mode == "info":
        show_info()
    elif args.mode == "server":
        run_mcp_server()
