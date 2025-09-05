#!/usr/bin/env python3
"""Test event URL structure for SportsPress."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.config import settings

async def test_event_urls():
    try:
        print('🔗 Testing event URL structure...')
        
        session = await create_http_session()
        http_client = HTTPClient(session)
        print('✅ HTTP client created')
        
        # Get a sample event to understand URL structure
        print('📊 Fetching sample event...')
        try:
            events = []
            async for event in http_client.paginate(settings.SPORTSPRESS_BASE + "/events", per_page=1):
                events.append(event)
                break
            
            if events:
                event = events[0]
                event_id = event.get("id")
                event_slug = event.get("slug", "")
                event_link = event.get("link", "")
                
                print(f'Event ID: {event_id}')
                print(f'Event Slug: {event_slug}')
                print(f'Event Link: {event_link}')
                
                # Try to construct URL
                base_url = "https://2kcompleague.com"
                
                # Common SportsPress URL patterns
                possible_urls = [
                    f"{base_url}/event/{event_slug}/",
                    f"{base_url}/events/{event_slug}/",
                    f"{base_url}/event/{event_id}/",
                    f"{base_url}/events/{event_id}/",
                    f"{base_url}/match/{event_slug}/",
                    f"{base_url}/matches/{event_slug}/",
                    f"{base_url}/game/{event_slug}/",
                    f"{base_url}/games/{event_slug}/",
                ]
                
                print(f'\n🔗 Possible URL patterns:')
                for url in possible_urls:
                    print(f'  - {url}')
                
                # Check if we can get more info from the event
                print(f'\n📊 Event details:')
                print(f'  Date: {event.get("date", "N/A")}')
                print(f'  Status: {event.get("status", "N/A")}')
                print(f'  Teams: {event.get("teams", "N/A")}')
                
        except Exception as e:
            print(f'Error fetching events: {e}')
        
        await session.close()
        print('✅ Test completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_event_urls())
