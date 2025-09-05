#!/usr/bin/env python3
"""Test script to check event data structure."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.sportspress import fetch_events
from core.config import settings

async def test_event_structure():
    try:
        print('🔗 Testing event data structure...')
        
        session = await create_http_session()
        http_client = HTTPClient(session)
        print('✅ HTTP client created')
        
        print('📊 Fetching events (limited to first 10)...')
        events = []
        try:
            async for event in http_client.paginate(settings.SPORTSPRESS_BASE + "/events", per_page=10):
                events.append(event)
                if len(events) >= 10:  # Limit to first 10 events
                    break
        except Exception as e:
            print(f'Pagination error (expected): {e}')
        print(f'Events returned: {len(events)}')
        
        if events:
            print('📈 Sample event structure:')
            event = events[0]
            print(f'  Event ID: {event.get("id", "N/A")}')
            print(f'  Event title: {event.get("title", {}).get("rendered", "N/A")}')
            print(f'  All keys: {list(event.keys())}')
            
            # Check for player data
            if 'players' in event:
                print(f'  Players data: {event["players"]}')
            if 'results' in event:
                print(f'  Results data: {event["results"]}')
            if 'performances' in event:
                print(f'  Performances data: {event["performances"]}')
                
            # Check for any data that might contain player stats
            for key in event.keys():
                if 'player' in key.lower() or 'stat' in key.lower() or 'performance' in key.lower():
                    print(f'  {key}: {event[key]}')
        else:
            print('❌ No events returned from API')
        
        await session.close()
        print('✅ Test completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_event_structure())
