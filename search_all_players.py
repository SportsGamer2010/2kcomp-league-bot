#!/usr/bin/env python3
"""Search all players for CaitlinClark or similar names."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.config import settings

async def search_all_players():
    try:
        print('🔗 Searching all players for CaitlinClark...')
        
        session = await create_http_session()
        http_client = HTTPClient(session)
        print('✅ HTTP client created')
        
        # Search through all players
        print('📊 Fetching all players...')
        all_players = []
        page = 1
        
        while True:
            try:
                players_data = await http_client.get_json(f"{settings.SPORTSPRESS_BASE}/players?per_page=100&page={page}")
                if not players_data:
                    break
                all_players.extend(players_data)
                print(f'Fetched page {page}: {len(players_data)} players')
                page += 1
                if len(players_data) < 100:  # Last page
                    break
            except Exception as e:
                print(f'Error fetching page {page}: {e}')
                break
        
        print(f'Total players found: {len(all_players)}')
        
        # Search for CaitlinClark or similar names
        caitlin_matches = []
        for player in all_players:
            player_name = player.get("title", {}).get("rendered", "").lower()
            if "caitlin" in player_name or "clark" in player_name:
                caitlin_matches.append(player)
        
        if caitlin_matches:
            print(f'\n✅ Found {len(caitlin_matches)} potential matches:')
            for player in caitlin_matches:
                name = player.get("title", {}).get("rendered", "Unknown")
                player_id = player.get("id", "Unknown")
                print(f'  - {name} (ID: {player_id})')
        else:
            print('\n❌ No players found with "caitlin" or "clark" in their name')
            
        # Also search for any player with 63+ points in any game
        print('\n🔍 Searching for any player with 63+ point games...')
        high_scorers = []
        
        # Check recent events for high scoring games
        events = []
        try:
            async for event in http_client.paginate(settings.SPORTSPRESS_BASE + "/events", per_page=50):
                events.append(event)
                if len(events) >= 200:  # Limit to avoid too many API calls
                    break
        except Exception as e:
            print(f'Error fetching events: {e}')
        
        print(f'Checking {len(events)} events for high scoring games...')
        
        for event in events:
            try:
                performance = event.get("performance", {})
                if performance:
                    for team_id, team_performance in performance.items():
                        if team_id == "0":  # Skip header
                            continue
                        if isinstance(team_performance, dict):
                            for player_id, player_stats in team_performance.items():
                                if player_id == "0":  # Skip header
                                    continue
                                pts = player_stats.get("pts", 0)
                                if pts and int(pts) >= 63:  # 63+ points
                                    # Get player name
                                    try:
                                        player_data = await http_client.get_json(f"{settings.SPORTSPRESS_BASE}/players/{player_id}")
                                        player_name = player_data.get("title", {}).get("rendered", f"Player {player_id}")
                                    except:
                                        player_name = f"Player {player_id}"
                                    
                                    date = event.get("date", "Unknown")
                                    teams = event.get("teams", [])
                                    team_names = []
                                    for t_id in teams:
                                        try:
                                            team_data = await http_client.get_json(f"{settings.SPORTSPRESS_BASE}/teams/{t_id}")
                                            team_name = team_data.get("title", {}).get("rendered", f"Team {t_id}")
                                            team_names.append(team_name)
                                        except:
                                            team_names.append(f"Team {t_id}")
                                    
                                    game_info = f"{team_names[0]} vs {team_names[1]}" if len(team_names) >= 2 else "Unknown vs Unknown"
                                    
                                    high_scorers.append({
                                        'player_name': player_name,
                                        'player_id': player_id,
                                        'points': int(pts),
                                        'date': date,
                                        'game': game_info,
                                        'event_id': event.get("id")
                                    })
            except Exception as e:
                continue
        
        if high_scorers:
            print(f'\n🏆 Found {len(high_scorers)} games with 63+ points:')
            high_scorers.sort(key=lambda x: x['points'], reverse=True)
            for game in high_scorers:
                print(f'  {game["player_name"]} - {game["points"]} points ({game["game"]} - {game["date"]})')
        else:
            print('\n❌ No games found with 63+ points')
        
        await session.close()
        print('✅ Search completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(search_all_players())
