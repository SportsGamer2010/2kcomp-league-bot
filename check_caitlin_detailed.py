#!/usr/bin/env python3
"""Check CaitlinClark-'s detailed scoring records."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.config import settings

async def check_caitlin_detailed():
    try:
        print('🔗 Checking CaitlinClark- detailed records...')
        
        session = await create_http_session()
        http_client = HTTPClient(session)
        print('✅ HTTP client created')
        
        player_id = 2867  # CaitlinClark-
        print(f'📊 Checking player ID {player_id} (CaitlinClark-)...')
        
        # Get player info
        try:
            player_data = await http_client.get_json(f"{settings.SPORTSPRESS_BASE}/players/{player_id}")
            player_name = player_data.get("title", {}).get("rendered", "Unknown")
            print(f'Player: {player_name}')
        except Exception as e:
            print(f'Error getting player info: {e}')
            return
        
        # Get all events for this player
        print('📊 Fetching all events for this player...')
        try:
            events_data = await http_client.get_json(f"{settings.SPORTSPRESS_BASE}/players/{player_id}/events")
            print(f'Found {len(events_data)} events for {player_name}')
            
            # Check each event for scoring
            scoring_games = []
            for event in events_data:
                try:
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
                                        if pts and int(pts) > 0:  # Any scoring game
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
                                            
                                            scoring_games.append({
                                                'points': int(pts),
                                                'date': date,
                                                'game': game_info,
                                                'event_id': event_id,
                                                'team_id': team_id
                                            })
                except Exception as e:
                    continue
            
            if scoring_games:
                print(f'\n🏀 All scoring games for {player_name}:')
                scoring_games.sort(key=lambda x: x['points'], reverse=True)
                
                # Show top 10 scoring games
                for i, game in enumerate(scoring_games[:10]):
                    print(f'  {i+1}. {game["points"]} points - {game["game"]} ({game["date"]})')
                
                # Check for 63+ point games
                high_scores = [game for game in scoring_games if game['points'] >= 63]
                if high_scores:
                    print(f'\n✅ CONFIRMED: {player_name} has {len(high_scores)} games with 63+ points!')
                    for game in high_scores:
                        print(f'  🏆 {game["points"]} points - {game["game"]} ({game["date"]})')
                else:
                    max_points = max(game['points'] for game in scoring_games)
                    print(f'\n❌ No 63+ point games found. Highest: {max_points} points')
                    
                    # Show if there are any games close to 63
                    close_games = [game for game in scoring_games if game['points'] >= 60]
                    if close_games:
                        print(f'\n🎯 Games with 60+ points:')
                        for game in close_games:
                            print(f'  {game["points"]} points - {game["game"]} ({game["date"]})')
            else:
                print(f'\n❌ No scoring games found for {player_name}')
                
        except Exception as e:
            print(f'Error fetching player events: {e}')
        
        await session.close()
        print('✅ Check completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_caitlin_detailed())
