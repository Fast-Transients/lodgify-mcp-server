# Lodgify MCP Server

A Model Context Protocol (MCP) server for the Lodgify vacation rental API. It exposes tools for managing properties, bookings and calendar data.

## Quick start
Install dependencies with `uv` and run the server with `uvx`:

```bash
export LODGIFY_API_KEY=your_api_key
uvx lodgify-mcp-server
```

To run from source:

```bash
git clone https://github.com/fast-transients/lodgify-mcp-server.git
cd lodgify-mcp-server
uv sync
export LODGIFY_API_KEY=your_api_key
uv run python entrypoint.py
```

## Claude Desktop configuration
Add this block to your Claude Desktop configuration (see examples in the `examples/` folder):

```json
{
  "mcpServers": {
    "lodgify": {
      "command": "uvx",
      "args": ["lodgify-mcp-server"],
      "env": {
        "LODGIFY_API_KEY": "your_api_key"
      }
    }
  }
}
```

### Local Development Method

If you're developing locally or prefer to run from source:

**Windows:**

```json
{
  "mcpServers": {
    "lodgify": {
      "command": "uv",
      "args": ["run", "--directory", "C:\\path\\to\\lodgify-mcp-server", "python", "entrypoint.py"],
      "env": {
        "LODGIFY_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

**Mac/Linux:**

```json
{
  "mcpServers": {
    "lodgify": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/lodgify-mcp-server", "python", "entrypoint.py"],
      "env": {
        "LODGIFY_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Config File Locations

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

## Local Development
 & Usage

### Setup

Clone and set up the project locally:

```bash
git clone https://github.com/fast-transients/lodgify-mcp-server.git
cd lodgify-mcp-server
uv sync
```

### Command-Line Interface

The server is managed via the `entrypoint.py` script, which provides several modes of operation.

**1. Set your API Key**

First, set your Lodgify API key as an environment variable.

*Windows PowerShell:*
```powershell
$env:LODGIFY_API_KEY="your_api_key_here"
```

*Mac/Linux:*
```bash
export LODGIFY_API_KEY="your_api_key_here"
```

Alternatively, you can pass the key directly using the `--api-key` flag in the commands below.

**2. Run the Server (Default Mode)**

This starts the MCP server, ready to connect to a client like Claude Desktop.

```bash
# --mode server is the default and can be omitted
uv run python entrypoint.py --mode server
```

**3. Test the API Connection**

Verify that your `LODGIFY_API_KEY` is correct and can connect to the Lodgify API.

```bash
uv run python entrypoint.py --mode test
```

**4. Display Server Information**

Show information about the server and check if the API key is configured.

```bash
uv run python entrypoint.py --mode info
```

## Testing with MCP Inspector

Test your setup using the MCP Inspector:

**Windows PowerShell:**

```powershell
$env:LODGIFY_API_KEY="your_api_key_here"
uvx @modelcontextprotocol/inspector lodgify-mcp-server
```

## Installation Methods

### Coming Soon: mcp-get

```bash
npx @michaellatman/mcp-get@latest install lodgify
```

### Direct Installation (uvx)

**Windows PowerShell:**

```powershell
$env:LODGIFY_API_KEY="your_api_key_here"
uvx lodgify-mcp-server
```

**Mac/Linux:**

```bash
export LODGIFY_API_KEY="your_api_key_here"
uvx lodgify-mcp-server
```

## Available Tools

- **Properties**: `get_properties`, `get_property_by_id`
- **Bookings**: `get_bookings`, `get_booking_by_id`, `create_booking`, `update_booking_status`
- **Calendar**: `get_calendar`

## Troubleshooting
- Ensure the `LODGIFY_API_KEY` environment variable is set.
- Getting `spawn uvx ENOENT`? Install `uv` from [astral.sh/uv](https://astral.sh/uv/) and restart your shell.

## Security
After syncing dependencies, run `pip-audit` to check for known vulnerabilities. The `uv.lock` file pins `starlette` 0.47.0 to address upstream advisories.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and testing instructions.
