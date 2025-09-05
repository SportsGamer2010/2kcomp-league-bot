#!/usr/bin/env python3
"""Test script to check records computation with limited events."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.sportspress import fetch_events, _extract_rows_from_event
from core.records import RecordsData, RecordCandidate, _try_update_max, SingleGameRecord
from core.config import settings

async def test_records_limited():
    try:
        print('🔗 Testing records computation with limited events...')
        
        session = await create_http_session()
        http_client = HTTPClient(session)
        print('✅ HTTP client created')
        
        print('📊 Fetching limited events...')
        events = []
        try:
            async for event in http_client.paginate(settings.SPORTSPRESS_BASE + "/events", per_page=10):
                events.append(event)
                if len(events) >= 10:  # Limit to first 10 events
                    break
        except Exception as e:
            print(f'Pagination error (expected): {e}')
        print(f'Events fetched: {len(events)}')
        
        # Manually compute records
        records = RecordsData()
        total_rows = 0
        
        for event in events:
            try:
                player_rows = _extract_rows_from_event(event)
                total_rows += len(player_rows)
                
                for row in player_rows:
                    # Check points record
                    records.points = _try_update_max(
                        records.points,
                        RecordCandidate(
                            stat="points",
                            value=row.points,
                            holder=row.name,
                            game=row.game,
                            date=row.date,
                        ),
                    )
                    
                    # Check rebounds record
                    records.rebounds = _try_update_max(
                        records.rebounds,
                        RecordCandidate(
                            stat="rebounds",
                            value=row.rebounds,
                            holder=row.name,
                            game=row.game,
                            date=row.date,
                        ),
                    )
                    
                    # Check assists record
                    records.assists = _try_update_max(
                        records.assists,
                        RecordCandidate(
                            stat="assists",
                            value=row.assists,
                            holder=row.name,
                            game=row.game,
                            date=row.date,
                        ),
                    )
                    
            except Exception as e:
                print(f'Error processing event {event.get("id", "unknown")}: {e}')
        
        print(f'Total player rows processed: {total_rows}')
        print('📈 Records found:')
        for attr in ['points', 'rebounds', 'assists', 'steals', 'blocks']:
            record = getattr(records, attr, None)
            if record:
                print(f'  {attr}: {record.holder} - {record.value} (Game: {record.game})')
            else:
                print(f'  {attr}: No record')
        
        await session.close()
        print('✅ Test completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_records_limited())
