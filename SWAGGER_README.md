# 🚀 TerraGrid APIs - Swagger UI Documentation

## Quick Start

### Option 1: **Open Swagger UI in Browser** (Recommended)

1. Double-click: `swagger-ui.html`
2. Browser opens with interactive API documentation
3. Test endpoints directly from the UI

---

### Option 2: **Use Online Swagger Editor**

1. Go to: https://editor.swagger.io/
2. Menu → File → Import URL
3. Paste: `https://raw.githubusercontent.com/your-repo/terragrid-platform/main/API_SWAGGER.yaml`
4. Click Import

---

### Option 3: **Use VS Code Extension**

1. Install: "Swagger Viewer" extension
2. Open: `API_SWAGGER.yaml`
3. Right-click → "Swagger Viewer"

---

## 📋 **APIs Documented**

### 1️⃣ **NASA EONET** (No Auth Required)
- **Purpose:** Real-time wildfire, flood, volcano detection
- **Endpoint:** `https://eonet.gsfc.nasa.gov/api/v3/events`
- **Test:** Get events with `limit=5`

### 2️⃣ **USGS Earthquake** (No Auth Required)
- **Purpose:** Seismic data with magnitude, location, depth
- **Endpoint:** `https://earthquake.usgs.gov/fdsnws/event/1/query`
- **Test:** Get earthquakes near Delhi coordinates

### 3️⃣ **NOAA Weather** (Requires Token)
- **Purpose:** Temperature, wind speed, humidity, precipitation
- **Endpoint:** `https://www.ncdc.noaa.gov/cdo-web/api/v2`
- **Token:** `TDwVaQPGqxIlxikIfxyKqeUecrnTCOcx`
- **Test:** Get Delhi weather stations

---

## 🧪 **Testing in Swagger UI**

### Step 1: Select API Section
Click on any API section (NASA EONET, USGS, NOAA)

### Step 2: Click "Try it out"
Button appears on the right

### Step 3: Fill Parameters
- For NASA: Set `limit=5`
- For USGS: Set `limit=10`, `format=geojson`
- For NOAA: Set `token=TDwVaQPGqxIlxikIfxyKqeUecrnTCOcx`, `datasetid=GHCND`

### Step 4: Click "Execute"
API returns real data!

---

## 📊 **Expected Responses**

### NASA EONET
```json
{
  "events": [
    {
      "id": "EONET_1234",
      "title": "Hurricane Nolo",
      "geometries": [{
        "type": "Point",
        "coordinates": [77.1025, 28.7041]
      }]
    }
  ]
}
```

### USGS Earthquake
```json
{
  "type": "FeatureCollection",
  "features": [{
    "properties": {
      "mag": 3.5,
      "place": "38 km WNW of Four Mile Road, Alaska",
      "title": "M 3.5 - Four Mile Road, Alaska"
    },
    "geometry": {
      "coordinates": [77.1025, 28.7041, 10.0]
    }
  }]
}
```

### NOAA Weather
```json
{
  "metadata": {
    "resultset": {
      "count": 13
    }
  },
  "results": [
    {
      "name": "DELHI SADAR, IN",
      "id": "GHCND:IN022021600",
      "latitude": 28.63,
      "longitude": 77.25
    }
  ]
}
```

---

## ⚙️ **Configuration**

### `.env` Variables
```bash
NASA_EONET_URL=https://eonet.gsfc.nasa.gov/api/v3
USGS_EARTHQUAKE_URL=https://earthquake.usgs.gov/fdsnws/event/1
NOAA_API_KEY=TDwVaQPGqxIlxikIfxyKqeUecrnTCOcx
NOAA_API_BASE_URL=https://www.ncdc.noaa.gov/cdo-web/api/v2
```

---

## 🔗 **File References**

| File | Purpose |
|------|---------|
| `API_SWAGGER.yaml` | OpenAPI 3.0 specification |
| `swagger-ui.html` | Interactive documentation viewer |
| `.env` | API keys and endpoints |

---

## 💡 **Tips**

1. **No CORS Issues:** Swagger UI handles API calls directly (not through browser)
2. **Save Requests:** Use "Try it out" to save test requests
3. **Export Responses:** Copy-paste JSON from responses
4. **Share Link:** Send `swagger-ui.html` to team for documentation

---

## 🚀 **Next Steps**

After testing these 3 APIs:
1. Add Google Maps API to Swagger
2. Add Twilio SMS endpoints
3. Add SendGrid Email endpoints
4. Add Gemini API endpoints
5. Add Overpass/OpenStreetMap endpoints

---

## 📞 **Support**

If APIs return errors in Swagger:
1. Check `.env` file has correct tokens
2. Verify internet connection
3. Check API rate limits (NOAA: 5 req/sec)
4. Check timestamp/date formats

---

**Created:** September 25, 2026  
**Status:** ✅ Ready to test APIs interactively
