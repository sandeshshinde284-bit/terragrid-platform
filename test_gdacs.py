import httpx
import json

# Test different GDACS endpoints
endpoints = [
    'https://www.gdacs.org/api/v1/events.json',
    'https://api.gdacs.org/v1/events',
    'https://www.gdacs.org/rss.xml',
    'https://www.gdacs.org/api/v3/events',
    'https://www.gdacs.org/api/v1/crises',
]

for url in endpoints:
    try:
        response = httpx.get(url, timeout=5)
        print(f'URL: {url}')
        print(f'Status: {response.status_code}')
        print(f'Content-Type: {response.headers.get("content-type", "unknown")}')
        print(f'Length: {len(response.text)} bytes')
        
        if response.status_code == 200:
            if 'json' in response.headers.get('content-type', '').lower():
                try:
                    data = response.json()
                    print(f'JSON Valid: Yes')
                    print(f'Keys: {list(data.keys())[:5]}')
                except:
                    print(f'JSON Valid: No')
            print(f'First 300 chars: {response.text[:300]}')
        print('-' * 80)
        print()
        
    except Exception as e:
        print(f'URL: {url}')
        print(f'Error: {str(e)}')
        print('-' * 80)
        print()
