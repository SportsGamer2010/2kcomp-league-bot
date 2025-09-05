#!/usr/bin/env python3
"""Test script to check records with name resolution."""

import asyncio
from core.http import HTTPClient, create_http_session
from core.records import compute_single_game_records, resolve_record_names
from core.config import settings

async def test_records_with_names():
    try:
        print('🔗 Testing records with name resolution...')
        
        session = await create_http_session()
        http_client = HTTPClient(session)
        print('✅ HTTP client created')
        
        print('📊 Computing single-game records...')
        records_data = await compute_single_game_records(http_client)
        print(f'Records data type: {type(records_data)}')
        
        # Check if we have any records
        if records_data:
            print('📈 Records found (before name resolution):')
            for attr in ['points', 'rebounds', 'assists', 'steals', 'blocks']:
                record = getattr(records_data, attr, None)
                if record:
                    print(f'  {attr}: {record.holder} - {record.value} (Game: {record.game})')
                else:
                    print(f'  {attr}: No record')
            
            print('\n🔄 Resolving names...')
            records_data = await resolve_record_names(http_client, records_data)
            
            print('📈 Records found (after name resolution):')
            for attr in ['points', 'rebounds', 'assists', 'steals', 'blocks']:
                record = getattr(records_data, attr, None)
                if record:
                    print(f'  {attr}: {record.holder} - {record.value} (Game: {record.game})')
                else:
                    print(f'  {attr}: No record')
        else:
            print('❌ No records data returned')
        
        await session.close()
        print('✅ Test completed')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_records_with_names())
