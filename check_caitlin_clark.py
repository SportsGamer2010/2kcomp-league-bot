#!/usr/bin/env python3
"""Check CaitlinClark's scoring records."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.config import settings

async def check_caitlin_clark():
    try:
        print('🔗 Checking CaitlinClark player records...')
        
        session = await create_http_session()
        http_client = HTTPClient(session)
        print('✅ HTTP client created')
        
        # Search for CaitlinClark player
        print('📊 Searching for CaitlinClark player...')
        try:
            # Try to find player by name
            players_data = await http_client.get_json(settings.SPORTSPRESS_BASE + '/players?per_page=100')
            
            caitlin_player = None
            for player in players_data:
                player_name = player.get("title", {}).get("rendered", "").lower()
                if "caitlin" in player_name and "clark" in player_name:
                    caitlin_player = player
                    break
            
            if caitlin_player:
                player_id = caitlin_player.get("id")
                player_name = caitlin_player.get("title", {}).get("rendered", "Unknown")
                print(f'✅ Found player: {player_name} (ID: {player_id})')
                
                # Get player's events/games
                print('📊 Fetching player events...')
                try:
                    events_data = await http_client.get_json(f"{settings.SPORTSPRESS_BASE}/players/{player_id}/events")
                    print(f'Found {len(events_data)} events for {player_name}')
                    
                    # Check each event for high scoring games
                    high_scores = []
                    for event in events_data:
                        # Get event details
                        event_id = event.get("id")
                        event_data = await http_client.get_json(f"{settings.SPORTSPRESS_BASE}/events/{event_id}")
                        
                        # Check performance data
                        performance = event_data.get("performance", {})
                        if performance:
                            for team_id, team_performance in performance.items():
                                if team_id == "0":  # Skip header
                                    continue
                                if isinstance(team_performance, dict):
                                    for player_id_key, player_stats in team_performance.items():
                                        if player_id_key == "0":  # Skip header
                                            continue
                                        if str(player_id_key) == str(player_id):
                                            pts = player_stats.get("pts", 0)
                                            if pts and int(pts) >= 50:  # High scoring games
                                                date = event_data.get("date", "Unknown")
                                                teams = event_data.get("teams", [])
                                                team_names = []
                                                for t_id in teams:
                                                    try:
                                                        team_data = await http_client.get_json(f"{settings.SPORTSPRESS_BASE}/teams/{t_id}")
                                                        team_name = team_data.get("title", {}).get("rendered", f"Team {t_id}")
                                                        team_names.append(team_name)
                                                    except:
                                                        team_names.append(f"Team {t_id}")
                                                
                                                game_info = f"{team_names[0]} vs {team_names[1]}" if len(team_names) >= 2 else "Unknown vs Unknown"
                                                high_scores.append({
                                                    'points': int(pts),
                                                    'date': date,
                                                    'game': game_info,
                                                    'event_id': event_id
                                                })
                    
                    if high_scores:
                        print(f'\n🏆 High scoring games for {player_name}:')
                        high_scores.sort(key=lambda x: x['points'], reverse=True)
                        for game in high_scores:
                            print(f'  {game["points"]} points - {game["game"]} ({game["date"]})')
                            
                        # Check if 63 points exists
                        max_points = max(game['points'] for game in high_scores)
                        if max_points >= 63:
                            print(f'\n✅ CONFIRMED: {player_name} scored {max_points} points in a single game!')
                        else:
                            print(f'\n❌ No 63+ point games found. Highest: {max_points} points')
                    else:
                        print(f'\n❌ No high scoring games found for {player_name}')
                        
                except Exception as e:
                    print(f'Error fetching player events: {e}')
            else:
                print('❌ CaitlinClark player not found')
                print('Available players (first 10):')
                for i, player in enumerate(players_data[:10]):
                    name = player.get("title", {}).get("rendered", "Unknown")
                    print(f'  {i+1}. {name}')
                    
        except Exception as e:
            print(f'Error searching players: {e}')
        
        await session.close()
        print('✅ Check completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_caitlin_clark())
