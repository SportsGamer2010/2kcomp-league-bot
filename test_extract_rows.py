#!/usr/bin/env python3
"""Test script to check if _extract_rows_from_event is working."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.sportspress import fetch_events, _extract_rows_from_event
from core.config import settings

async def test_extract_rows():
    try:
        print('🔗 Testing _extract_rows_from_event function...')
        
        session = await create_http_session()
        http_client = HTTPClient(session)
        print('✅ HTTP client created')
        
        print('📊 Fetching events...')
        events = []
        try:
            async for event in http_client.paginate(settings.SPORTSPRESS_BASE + "/events", per_page=5):
                events.append(event)
                if len(events) >= 5:  # Limit to first 5 events
                    break
        except Exception as e:
            print(f'Pagination error (expected): {e}')
        print(f'Events returned: {len(events)}')
        
        if events:
            print('📈 Testing _extract_rows_from_event on first event...')
            event = events[0]
            print(f'  Event ID: {event.get("id", "N/A")}')
            print(f'  Event title: {event.get("title", {}).get("rendered", "N/A")}')
            
            # Test the extraction function
            rows = _extract_rows_from_event(event)
            print(f'  Rows extracted: {len(rows)}')
            
            if rows:
                print('  Sample rows:')
                for i, row in enumerate(rows[:3]):  # Show first 3 rows
                    print(f'    Row {i+1}: {row.name} - {row.points} pts, {row.rebounds} reb, {row.assists} ast')
            else:
                print('  ❌ No rows extracted')
                print('  Event keys:', list(event.keys()))
                if 'performance' in event:
                    print('  Performance data exists:', bool(event['performance']))
        else:
            print('❌ No events returned from API')
        
        await session.close()
        print('✅ Test completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_extract_rows())
