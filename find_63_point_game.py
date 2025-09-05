#!/usr/bin/env python3
"""Find any 63+ point games in the system."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.config import settings

async def find_63_point_game():
    try:
        print('🔗 Searching for 63+ point games...')
        
        session = await create_http_session()
        http_client = HTTPClient(session)
        print('✅ HTTP client created')
        
        # Search through more events
        print('📊 Fetching events to find 63+ point games...')
        events_checked = 0
        high_scorers = []
        
        try:
            async for event in http_client.paginate(settings.SPORTSPRESS_BASE + "/events", per_page=50):
                events_checked += 1
                if events_checked % 50 == 0:
                    print(f'Checked {events_checked} events...')
                
                # Check performance data
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
                
                # Limit to avoid too many API calls
                if events_checked >= 500:
                    break
                    
        except Exception as e:
            print(f'Error during pagination: {e}')
        
        print(f'\n📊 Checked {events_checked} events total')
        
        if high_scorers:
            print(f'\n🏆 Found {len(high_scorers)} games with 63+ points:')
            high_scorers.sort(key=lambda x: x['points'], reverse=True)
            for game in high_scorers:
                print(f'  {game["player_name"]} - {game["points"]} points ({game["game"]} - {game["date"]})')
                
            # Check specifically for CaitlinClark-
            caitlin_games = [game for game in high_scorers if "caitlin" in game["player_name"].lower()]
            if caitlin_games:
                print(f'\n✅ CaitlinClark- 63+ point games:')
                for game in caitlin_games:
                    print(f'  🏆 {game["points"]} points - {game["game"]} ({game["date"]})')
        else:
            print('\n❌ No games found with 63+ points in the checked events')
            
            # Let's also check what the current highest score is
            print('\n🔍 Checking current highest scores...')
            all_scores = []
            events_checked = 0
            
            try:
                async for event in http_client.paginate(settings.SPORTSPRESS_BASE + "/events", per_page=50):
                    events_checked += 1
                    performance = event.get("performance", {})
                    if performance:
                        for team_id, team_performance in performance.items():
                            if team_id == "0":
                                continue
                            if isinstance(team_performance, dict):
                                for player_id, player_stats in team_performance.items():
                                    if player_id == "0":
                                        continue
                                    pts = player_stats.get("pts", 0)
                                    if pts and int(pts) > 0:
                                        all_scores.append(int(pts))
                    
                    if events_checked >= 200:  # Limit for performance
                        break
                        
            except Exception as e:
                print(f'Error checking scores: {e}')
            
            if all_scores:
                all_scores.sort(reverse=True)
                print(f'Top 10 highest scores found:')
                for i, score in enumerate(all_scores[:10]):
                    print(f'  {i+1}. {score} points')
        
        await session.close()
        print('✅ Search completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(find_63_point_game())
