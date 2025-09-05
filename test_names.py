#!/usr/bin/env python3
"""Test script to check player and team names from API."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.config import settings

async def test_player_team_names():
    try:
        print('🔗 Testing player and team name fetching...')
        
        session = await create_http_session()
        http_client = HTTPClient(session)
        print('✅ HTTP client created')
        
        # Test fetching a specific player
        print('📊 Testing player API...')
        try:
            player_data = await http_client.get_json(settings.SPORTSPRESS_BASE + '/players/3968')
            player_name = player_data.get("title", {}).get("rendered", "N/A")
            print(f'Player 3968 name: {player_name}')
        except Exception as e:
            print(f'Player API error: {e}')
        
        # Test fetching a specific team
        print('📊 Testing team API...')
        try:
            team_data = await http_client.get_json(settings.SPORTSPRESS_BASE + '/teams/3958')
            team_name = team_data.get("title", {}).get("rendered", "N/A")
            print(f'Team 3958 name: {team_name}')
        except Exception as e:
            print(f'Team API error: {e}')
        
        # Test fetching all players to see structure
        print('📊 Testing players list...')
        try:
            players_data = await http_client.get_json(settings.SPORTSPRESS_BASE + '/players?per_page=5')
            if isinstance(players_data, list) and players_data:
                print(f'First player: {players_data[0].get("title", {}).get("rendered", "N/A")}')
                print(f'Player ID: {players_data[0].get("id", "N/A")}')
        except Exception as e:
            print(f'Players list error: {e}')
        
        await session.close()
        print('✅ Test completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_player_team_names())
