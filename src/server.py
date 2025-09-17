#!/usr/bin/env python3
import os
import requests
import time
import threading
from typing import Dict, List, Optional, Any
from fastmcp import FastMCP

mcp = FastMCP("Sleeper Fantasy Football MCP Server")

# Sleeper API base URL
SLEEPER_BASE_URL = "https://api.sleeper.app/v1"

class SleeperAPI:
    """Client for interacting with the Sleeper Fantasy Football API"""
    
    def __init__(self):
        self.base_url = SLEEPER_BASE_URL
        self.session = requests.Session()
        # Add a small delay to respect rate limits
        self.session.headers.update({
            'User-Agent': 'Sleeper-MCP-Server/1.0'
        })
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user information by username with retry logic"""
        for attempt in range(3):
            try:
                response = self.session.get(f"{self.base_url}/user/{username}", timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                print(f"Error fetching user {username} (attempt {attempt + 1}): {e}")
                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                else:
                    return None
        return None
    
    def get_user_leagues(self, user_id: str, season: str = "2024") -> List[Dict]:
        """Get all leagues for a user in a specific season"""
        try:
            response = self.session.get(f"{self.base_url}/user/{user_id}/leagues/nfl/{season}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching leagues for user {user_id}: {e}")
            return []
    
    def get_league_rosters(self, league_id: str) -> List[Dict]:
        """Get all rosters in a league"""
        try:
            response = self.session.get(f"{self.base_url}/league/{league_id}/rosters")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching rosters for league {league_id}: {e}")
            return []
    
    def get_league_users(self, league_id: str) -> List[Dict]:
        """Get all users in a league"""
        try:
            response = self.session.get(f"{self.base_url}/league/{league_id}/users")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching users for league {league_id}: {e}")
            return []
    
    def get_league_matchups(self, league_id: str, week: int) -> List[Dict]:
        """Get matchups for a specific week in a league"""
        try:
            response = self.session.get(f"{self.base_url}/league/{league_id}/matchups/{week}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching matchups for league {league_id}, week {week}: {e}")
            return []
    
    def get_nfl_state(self) -> Optional[Dict]:
        """Get current NFL state including current week"""
        try:
            response = self.session.get(f"{self.base_url}/state/nfl")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching NFL state: {e}")
            return None
    
    def get_players(self) -> Dict:
        """Get all NFL players"""
        try:
            response = self.session.get(f"{self.base_url}/players/nfl")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching players: {e}")
            return {}

# Initialize Sleeper API client
sleeper_api = SleeperAPI()

@mcp.tool(description="Get current NFL season state including current week")
def get_nfl_state() -> Dict:
    """Get the current NFL state including season, week, and season type"""
    state = sleeper_api.get_nfl_state()
    if state:
        return {
            "season": state.get("season"),
            "week": state.get("week"),
            "season_type": state.get("season_type"),
            "display_week": state.get("display_week"),
            "leg": state.get("leg")
        }
    return {"error": "Unable to fetch NFL state"}

@mcp.tool(description="Get user information by Sleeper username")
def get_user_info(username: str) -> Dict:
    """Get user information from Sleeper by username"""
    user = sleeper_api.get_user_by_username(username)
    if user:
        return {
            "user_id": user.get("user_id"),
            "username": user.get("username"),
            "display_name": user.get("display_name"),
            "avatar": user.get("avatar")
        }
    return {"error": f"User '{username}' not found"}

@mcp.tool(description="Get all leagues for a user in the current season")
def get_user_leagues(username: str, season: str = "2024") -> List[Dict]:
    """Get all leagues for a user in a specific season"""
    user = sleeper_api.get_user_by_username(username)
    if not user:
        return [{"error": f"User '{username}' not found"}]
    
    leagues = sleeper_api.get_user_leagues(user["user_id"], season)
    return [
        {
            "league_id": league.get("league_id"),
            "name": league.get("name"),
            "season": league.get("season"),
            "status": league.get("status"),
            "settings": {
                "total_rosters": league.get("total_rosters"),
                "roster_positions": league.get("roster_positions"),
                "scoring_settings": league.get("scoring_settings")
            }
        }
        for league in leagues
    ]

@mcp.tool(description="Get user's lineup for the current week in a specific league")
def get_user_lineup(username: str, league_id: str) -> Dict:
    """Get a user's lineup for the current week in a specific league"""
    # Get current NFL state
    nfl_state = sleeper_api.get_nfl_state()
    if not nfl_state:
        return {"error": "Unable to fetch current NFL state"}
    
    current_week = nfl_state.get("week")
    if not current_week:
        return {"error": "Unable to determine current week"}
    
    # Get user info
    user = sleeper_api.get_user_by_username(username)
    if not user:
        return {"error": f"User '{username}' not found"}
    
    # Get league rosters
    rosters = sleeper_api.get_league_rosters(league_id)
    if not rosters:
        return {"error": f"Unable to fetch rosters for league {league_id}"}
    
    # Find user's roster
    user_roster = None
    for roster in rosters:
        if roster.get("owner_id") == user["user_id"]:
            user_roster = roster
            break
    
    if not user_roster:
        return {"error": f"User '{username}' not found in league {league_id}"}
    
    # Get league users for display names
    league_users = sleeper_api.get_league_users(league_id)
    user_map = {u["user_id"]: u for u in league_users}
    
    # Get current week matchups
    matchups = sleeper_api.get_league_matchups(league_id, current_week)
    if not matchups:
        return {"error": f"Unable to fetch matchups for week {current_week}"}
    
    # Find user's matchup
    user_matchup = None
    for matchup in matchups:
        if matchup.get("roster_id") == user_roster["roster_id"]:
            user_matchup = matchup
            break
    
    if not user_matchup:
        return {"error": f"No matchup found for user in week {current_week}"}
    
    # Get opponent info
    opponent_roster_id = user_matchup.get("matchup_id")
    opponent_roster = None
    opponent_user = None
    
    for roster in rosters:
        if roster.get("roster_id") == opponent_roster_id:
            opponent_roster = roster
            opponent_user = user_map.get(roster.get("owner_id"))
            break
    
    # Get players data
    players = sleeper_api.get_players()
    
    # Format lineup
    lineup = {
        "user": {
            "username": username,
            "display_name": user.get("display_name", username)
        },
        "week": current_week,
        "season": nfl_state.get("season"),
        "roster_id": user_roster["roster_id"],
        "starters": [],
        "bench": [],
        "opponent": {
            "roster_id": opponent_roster_id,
            "username": opponent_user.get("username") if opponent_user else "Unknown",
            "display_name": opponent_user.get("display_name") if opponent_user else "Unknown"
        } if opponent_roster else None
    }
    
    # Process starters
    starters = user_roster.get("starters", [])
    for player_id in starters:
        if player_id and player_id in players:
            player = players[player_id]
            lineup["starters"].append({
                "player_id": player_id,
                "name": player.get("full_name"),
                "position": player.get("position"),
                "team": player.get("team")
            })
    
    # Process bench players
    bench = user_roster.get("reserve", []) + user_roster.get("taxi", [])
    for player_id in bench:
        if player_id and player_id in players:
            player = players[player_id]
            lineup["bench"].append({
                "player_id": player_id,
                "name": player.get("full_name"),
                "position": player.get("position"),
                "team": player.get("team")
            })
    
    return lineup

@mcp.tool(description="Get a user's current week lineup across all their leagues")
def get_user_weekly_lineup(username: str) -> Dict:
    """Get a user's lineup for the current week across all their leagues"""
    # Get current NFL state
    nfl_state = sleeper_api.get_nfl_state()
    if not nfl_state:
        return {"error": "Unable to fetch current NFL state"}
    
    current_week = nfl_state.get("week")
    current_season = nfl_state.get("season")
    
    # Get user info
    user = sleeper_api.get_user_by_username(username)
    if not user:
        return {"error": f"User '{username}' not found"}
    
    # Get user's leagues
    leagues = sleeper_api.get_user_leagues(user["user_id"], str(current_season))
    if not leagues:
        return {"error": f"No leagues found for user '{username}' in season {current_season}"}
    
    result = {
        "user": {
            "username": username,
            "display_name": user.get("display_name", username)
        },
        "week": current_week,
        "season": current_season,
        "leagues": []
    }
    
    # Get lineup for each league
    for league in leagues:
        league_id = league["league_id"]
        lineup = get_user_lineup(username, league_id)
        
        if "error" not in lineup:
            result["leagues"].append({
                "league_id": league_id,
                "league_name": league["name"],
                "lineup": lineup
            })
        else:
            result["leagues"].append({
                "league_id": league_id,
                "league_name": league["name"],
                "error": lineup["error"]
            })
    
    return result

@mcp.tool(description="Get information about the MCP server including name, version, environment, and Python version")
def get_server_info() -> dict:
    return {
        "server_name": "Sleeper Fantasy Football MCP Server",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "python_version": os.sys.version.split()[0],
        "description": "MCP server for interacting with Sleeper Fantasy Football API"
    }

# Add health check tool for monitoring
@mcp.tool(description="Health check endpoint for monitoring server status")
def health_check() -> dict:
    """Health check for Render and monitoring"""
    return {
        "status": "healthy",
        "server": "Sleeper Fantasy Football MCP Server",
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "version": "1.0.0",
        "endpoints": {
            "mcp": "/mcp",
            "health": "use health_check tool"
        }
    }

def keep_alive():
    """Keep the server alive by making periodic requests"""
    while True:
        try:
            # Make a simple request to keep the server warm
            requests.get(f"http://localhost:{os.environ.get('PORT', 8000)}/mcp", timeout=5)
            print("Keep-alive ping sent")
        except:
            pass  # Ignore errors, just keep trying
        time.sleep(300)  # Ping every 5 minutes

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"Starting FastMCP server on {host}:{port}")
    
    # Start keep-alive thread in production
    if os.environ.get("ENVIRONMENT") == "production":
        keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
        keep_alive_thread.start()
        print("Keep-alive thread started")
    
    mcp.run(
        transport="http",
        host=host,
        port=port,
        stateless_http=True
    )
