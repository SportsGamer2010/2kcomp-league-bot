#!/usr/bin/env python3
"""Test script to check teams data structure."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.config import settings

async def test_teams_data():
    try:
        print('🔗 Testing teams data structure...')
        
        session = await create_http_session()
        http_client = HTTPClient(session)
        print('✅ HTTP client created')
        
        print('📊 Fetching first event...')
        events = []
        try:
            async for event in http_client.paginate(settings.SPORTSPRESS_BASE + "/events", per_page=1):
                events.append(event)
                break
        except Exception as e:
            print(f'Pagination error (expected): {e}')
        
        if events:
            event = events[0]
            print(f'Event ID: {event.get("id", "N/A")}')
            print(f'Teams data: {event.get("teams", "N/A")}')
            print(f'Teams type: {type(event.get("teams"))}')
            
            if event.get("teams"):
                teams = event["teams"]
                print(f'Teams length: {len(teams) if isinstance(teams, list) else "Not a list"}')
                if isinstance(teams, list):
                    for i, team in enumerate(teams):
                        print(f'  Team {i}: {team} (type: {type(team)})')
        else:
            print('❌ No events returned from API')
        
        await session.close()
        print('✅ Test completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_teams_data())
