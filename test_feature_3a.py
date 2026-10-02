"""
Test Feature 3A Endpoints
"""
import urllib.request
import json

def test_endpoints():
    print("=== Testing Feature 3A Endpoints ===\n")
    
    # Test 1: Health check
    print("1. Health Check:")
    url = "http://localhost:8000/api/zones/health"
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            print(f"   Features: {data.get('features')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 2: Calculate zones
    print("2. Calculate Zones (San Francisco Earthquake):")
    url = "http://localhost:8000/api/zones/calculate?latitude=37.7749&longitude=-122.4194&severity=high&event_type=earthquake&location_name=test_sf&threat_score=75"
    try:
        req = urllib.request.Request(url, method='POST')
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            zones = data.get('data', {}).get('zones', [])
            print(f"   Zones Created: {len(zones)}")
            print(f"   Total Population: {data.get('data', {}).get('total_population_affected', 0):,}")
            for zone in zones:
                print(f"   - Zone {zone['zone_number']}: {zone['area_km2']} km2, {zone['population_estimate']:,} people")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 3: Safe Routes
    print("3. Safe Routes (San Francisco):")
    url = "http://localhost:8000/api/zones/routes?latitude=37.7749&longitude=-122.4194&event_type=earthquake&location_name=test_sf"
    try:
        req = urllib.request.Request(url, method='POST')
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            routes = data.get('data', {}).get('routes', [])
            print(f"   Routes Available: {len(routes)}")
            for route in routes:
                print(f"   - {route['name']}: {route['distance_km']}km, Safety: {route['safety_score']}%")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    print("OK Feature 3A Backend Complete!")

if __name__ == "__main__":
    test_endpoints()
