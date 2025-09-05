#!/usr/bin/env python3
"""Debug script to check team ID extraction."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.sportspress import _extract_rows_from_event
from core.config import settings

async def debug_team_ids():
    try:
        print('🔗 Debugging team ID extraction...')
        
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
            print(f'Teams: {event.get("teams", "N/A")}')
            
            # Test extraction
            rows = _extract_rows_from_event(event)
            print(f'Rows extracted: {len(rows)}')
            
            if rows:
                row = rows[0]
                print(f'First row:')
                print(f'  Name: {row.name}')
                print(f'  Player ID: {getattr(row, "player_id", "None")}')
                print(f'  Team ID: {getattr(row, "team_id", "None")}')
                print(f'  Opp Team ID: {getattr(row, "opp_team_id", "None")}')
                print(f'  Game: {row.game}')
        else:
            print('❌ No events returned from API')
        
        await session.close()
        print('✅ Test completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_team_ids())
