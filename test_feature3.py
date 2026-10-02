import httpx
import json

print("=" * 80)
print("FEATURE 3 POLLING TEST")
print("=" * 80)

# Test polling history
print("\n1. POLLING HISTORY (last 3 attempts):")
print("-" * 80)
try:
    response = httpx.get('http://localhost:8000/api/v1/polling/history?limit=3', timeout=5)
    data = response.json()
    if 'data' in data and 'history' in data['data']:
        for i, entry in enumerate(data['data']['history'], 1):
            print(f'\nAttempt #{i}:')
            print(f'  Time: {entry["timestamp"]}')
            print(f'  Total Events: {entry["total_events"]}')
            for source, info in entry['sources'].items():
                print(f'  {source}: {info["count"]} events')
except Exception as e:
    print(f'Error: {e}')

# Test get incidents endpoint
print("\n" + "=" * 80)
print("2. LATEST POLLED INCIDENTS (first 5):")
print("-" * 80)
try:
    response = httpx.get('http://localhost:8000/api/v1/polling/incidents', timeout=5)
    data = response.json()
    if 'data' in data:
        print(f'Total in cache: {data["data"]["count"]}')
        print(f'Last refresh: {data["data"]["last_refresh"]}')
        if 'incidents' in data['data'] and data['data']['incidents']:
            for i, incident in enumerate(data['data']['incidents'][:5], 1):
                print(f'\n{i}. {incident.get("location_name", "Unknown")}')
                print(f'   Type: {incident.get("event_type")}')
                print(f'   Severity: {incident.get("severity")}')
                print(f'   Source: {incident.get("source")}')
except Exception as e:
    print(f'Error: {e}')

# Test manual refresh
print("\n" + "=" * 80)
print("3. TRIGGERING MANUAL REFRESH:")
print("-" * 80)
try:
    response = httpx.post('http://localhost:8000/api/v1/polling/refresh?use_mock=false', timeout=30)
    data = response.json()
    print(f'Status: {data["status"]}')
    print(f'Message: {data["message"]}')
    if 'data' in data:
        sources = data['data'].get('sources', {})
        print(f'Events fetched:')
        total = 0
        for source, info in sources.items():
            count = info.get('count', 0)
            total += count
            print(f'  {source}: {count}')
        print(f'TOTAL: {total}')
except Exception as e:
    print(f'Error: {e}')

print("\n" + "=" * 80)
print("FEATURE 3 TEST COMPLETE")
print("=" * 80)
