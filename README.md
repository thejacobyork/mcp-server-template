# Sleeper Fantasy Football MCP Server

A [FastMCP](https://github.com/jlowin/fastmcp) server that integrates with the Sleeper Fantasy Football API, allowing users to check their weekly lineups and league information through Poke.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/InteractionCo/mcp-server-template)

## Features

- **Current Week Lineup**: Get your starting lineup and bench players for the current NFL week
- **Multi-League Support**: View lineups across all your Sleeper leagues
- **Matchup Information**: See who you're playing against this week
- **Player Details**: Get player names, positions, and teams
- **NFL State**: Check current season, week, and season type

## Available Tools

### `get_user_weekly_lineup(username: str)`
Get a user's lineup for the current week across all their leagues. This is the main tool for checking who is playing.

### `get_user_lineup(username: str, league_id: str)`
Get a user's lineup for the current week in a specific league.

### `get_user_info(username: str)`
Get user information from Sleeper by username.

### `get_user_leagues(username: str, season: str)`
Get all leagues for a user in a specific season.

### `get_nfl_state()`
Get current NFL season state including current week.

## Local Development

### Setup

Fork the repo, then run:

```bash
git clone <your-repo-url>
cd mcp-server-template
conda create -n mcp-server python=3.13
conda activate mcp-server
pip install -r requirements.txt
```

### Test

```bash
python src/server.py
# then in another terminal run:
npx @modelcontextprotocol/inspector
```

Open http://localhost:3000 and connect to `http://localhost:8000/mcp` using "Streamable HTTP" transport (NOTE THE `/mcp`!).

## Deployment

### Option 1: One-Click Deploy
Click the "Deploy to Render" button above.

### Option 2: Manual Deployment
1. Fork this repository
2. Connect your GitHub account to Render
3. Create a new Web Service on Render
4. Connect your forked repository
5. Render will automatically detect the `render.yaml` configuration

Your server will be available at `https://your-service-name.onrender.com/mcp` (NOTE THE `/mcp`!)

## Poke Setup

You can connect your MCP server to Poke at [poke.com/settings/connections](https://poke.com/settings/connections).

### Usage Examples

Once connected to Poke, you can ask questions like:

- "Who is playing for me this week?" (using your Sleeper username)
- "Show me my lineup for this week"
- "What's my matchup this week?"
- "Who am I playing against?"

### Testing the Connection

To test the connection explicitly, ask Poke something like:
`Tell the subagent to use the "{connection name}" integration's "get_user_weekly_lineup" tool with username "your_sleeper_username"`

If you run into persistent issues of Poke not calling the right MCP (e.g. after you've renamed the connection), you may send `clearhistory` to Poke to delete all message history and start fresh.

## API Information

This server uses the [Sleeper Fantasy Football API](https://docs.sleeper.com/), which is:
- **Free to use** - No API key required
- **Read-only** - Safe for public use
- **Rate limited** - 1000 requests per minute per IP

## Requirements

- Python 3.13+
- requests library for HTTP calls
- FastMCP for MCP server functionality

## Customization

The server is built with a modular `SleeperAPI` class that can be extended with additional endpoints. To add more tools, decorate functions with `@mcp.tool`:

```python
@mcp.tool(description="Your tool description")
def your_new_tool(param: str) -> Dict:
    """Your tool implementation."""
    # Use sleeper_api methods to fetch data
    return {"result": "data"}
```