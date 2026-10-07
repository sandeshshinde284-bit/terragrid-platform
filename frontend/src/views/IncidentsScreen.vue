<template>
  <div class="incidents-screen">
    <Header />

    <div class="incidents-container">
      <!-- Filters & Search -->
      <div class="controls-panel glass-panel">
        <div class="search-bar">
          <input 
            v-model="searchQuery"
            type="text" 
            :placeholder="$t('incidents.search')"
            class="search-input"
          />
          <span class="search-icon">🔍</span>
        </div>

        <div class="filters">
          <div class="filter-group">
            <select v-model="filterType" class="filter-select">
              <option value="">{{ $t('incidents.filterByType') }} - All</option>
              <option value="fire">🔥 Wildfire / Fire</option>
              <option value="flood">💧 Flood</option>
              <option value="earthquake">🌍 Earthquake / Seismic</option>
              <option value="storm">🌀 Storm / Cyclone / Typhoon</option>
              <option value="weather">🌤️ Weather Advisory</option>
              <option value="landslide">⛰️ Landslide</option>
            </select>
          </div>

          <div class="filter-group">
            <select v-model="filterStatus" class="filter-select">
              <option value="">{{ $t('incidents.filterByStatus') }} - All</option>
              <option value="active">{{ $t('common.active') }}</option>
              <option value="monitoring">{{ $t('common.monitoring') }}</option>
              <option value="resolved">{{ $t('common.resolved') }}</option>
            </select>
          </div>

          <div class="filter-group">
            <select v-model="filterSeverity" class="filter-select">
              <option value="">{{ $t('incidents.filterBySeverity') }} - All</option>
              <option value="critical">{{ $t('common.critical') }}</option>
              <option value="high">{{ $t('common.high') }}</option>
              <option value="medium">{{ $t('common.medium') }}</option>
              <option value="low">{{ $t('common.low') }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Incidents Table -->
      <div class="incidents-table-wrapper glass-panel">
        <table class="incidents-table">
          <thead>
            <tr>
              <th>Hazard Type</th>
              <th>{{ $t('incidents.location') }}</th>
              <th>Country</th>
              <th>{{ $t('incidents.status') }}</th>
              <th>{{ $t('incidents.threatScore') }}</th>
              <th>{{ $t('incidents.affectedArea') }}</th>
              <th>{{ $t('incidents.population') }}</th>
              <th>{{ $t('incidents.trend') }}</th>
              <th>{{ $t('incidents.detectionTime') }}</th>
              <th>Recommended Action</th>
              <th>Analysis</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="incident in filteredIncidents" :key="incident.id" class="incident-row" :class="{ expanded: expandedIncidentId === incident.id }" @click="toggleExpanded(incident.id)">
              <td class="type-cell">
                <span class="type-icon">{{ getIcon(incident.type, incident.location) }}</span>
                <span class="type-name">{{ formatType(incident.type, incident.location) }}</span>
              </td>
              <td class="location-cell">
                <span class="location-text">{{ cleanLocation(incident.location) }}</span>
              </td>
              <td class="country-cell">
                <span class="country-name">{{ resolveCountry(incident.location, incident.countryCode).name }}</span>
              </td>
              <td class="status-cell">
                <span class="status-badge" :class="incident.status">{{ incident.status.toUpperCase() }}</span>
              </td>
              <td class="threat-cell">{{ incident.threatScore }}/100</td>
              <td class="area-cell">{{ incident.affectedArea.toFixed(1) }} km²</td>
              <td class="population-cell">{{ (incident.affectedPopulation / 1000).toFixed(0) }}K</td>
              <td class="trend-cell">+{{ incident.trend.toFixed(1) }} km²/h</td>
              <td class="time-cell">{{ formatDate(incident.detectionTime) }}</td>
              <td class="action-cell">
                <span class="action-badge">{{ getRecommendedAction(incident) }}</span>
              </td>
              <td class="view-cell">
                <button class="view-btn" @click="viewIncident(incident.id)">
                  View Details
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="filteredIncidents.length === 0" class="no-results">
          <p>{{ $t('alerts.noAlerts') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Header from '@/components/organisms/Header.vue'
import { useEventsStore } from '@/stores'
import type { IncidentLevel1 } from '@/types'

const router = useRouter()
const eventsStore = useEventsStore()
const searchQuery = ref('')
const filterType = ref('')
const filterStatus = ref('')
const filterSeverity = ref('')
const selectedIncidentData = ref<IncidentLevel1 | null>(null)
const expandedIncidentId = ref<string | null>(null)

const iconMap: Record<string, string> = {
  flood: '💧',
  earthquake: '🌍',
  seismic: '🌍',
  fire: '🔥',
  wildfire: '🔥',
  hurricane: '🌀',
  storm: '🌀',
  cyclone: '🌀',
  typhoon: '🌀',
  volcano: '🌋',
  landslide: '⛰️',
  drought: '🌾',
  snow_ice: '❄️',
  cold_wave: '❄️',
  heat_wave: '🌡️',
  temperature_extreme: '🌡️',
  tsunami: '🌊',
}

const getIcon = (type: string, location?: string): string => {
  const loc = (location || '').toLowerCase()
  const t = (type || '').toLowerCase()

  if (loc.includes('typhoon') || loc.includes('hurricane') || loc.includes('cyclone')) return '🌀'
  if (loc.includes('tornado')) return '🌪️'
  if (loc.includes('fire')) return '🔥'
  if (loc.includes('flood')) return '💧'
  if (loc.includes('quake') || loc.includes('seismic')) return '🌍'

  const icons: Record<string, string> = {
    fire: '🔥',
    wildfire: '🔥',
    flood: '💧',
    earthquake: '🌍',
    seismic: '🌍',
    storm: '⛈️',
    winter_storm: '❄️',
    dust_storm: '🌪️',
    volcano: '🌋',
    landslide: '⛰️',
    drought: '🌾',
    heat_wave: '🌡️',
    cold_wave: '❄️',
    snow_ice: '❄️',
    tsunami: '🌊',
    weather: '🌤️',
    other: '🌤️'
  }

  return icons[t] || '🌤️'
}

const formatType = (type: string, location?: string): string => {
  const loc = (location || '').toLowerCase()
  const t = (type || '').toLowerCase()

  // 1. High-fidelity meteorological specific classification
  if (loc.includes('super typhoon')) return 'Super Typhoon'
  if (loc.includes('typhoon')) return 'Typhoon'
  if (loc.includes('hurricane')) return 'Hurricane'
  if (loc.includes('cyclone')) return 'Cyclone'
  if (loc.includes('tornado')) return 'Tornado'

  // 2. OpenWeather atmospheric advisories
  if (t === 'other' || t === 'weather') {
    return 'Weather Advisory'
  }

  // 3. Standard clean mappings
  const map: Record<string, string> = {
    fire: 'Wildfire',
    wildfire: 'Wildfire',
    flood: 'Flood',
    earthquake: 'Earthquake',
    seismic: 'Seismic Event',
    storm: 'Storm System',
    winter_storm: 'Winter Storm',
    dust_storm: 'Dust Storm',
    volcano: 'Volcano',
    drought: 'Drought',
    landslide: 'Landslide',
    heat_wave: 'Heat Wave',
    cold_wave: 'Cold Wave',
    snow_ice: 'Snow & Ice',
    tsunami: 'Tsunami'
  }

  if (map[t]) return map[t]
  return t ? t.charAt(0).toUpperCase() + t.slice(1) : 'Weather Advisory'
}

const filteredIncidents = computed(() => {
  return eventsStore.allIncidents.filter((incident) => {
    // 1. Search Query: location, type, country, and formatted hazard name
    const q = searchQuery.value.trim().toLowerCase()
    let matchSearch = true
    if (q) {
      const loc = (incident.location || '').toLowerCase()
      const rawType = (incident.type || '').toLowerCase()
      const fmtType = formatType(incident.type, incident.location).toLowerCase()
      const country = (incident.countryCode || '').toLowerCase()
      matchSearch = loc.includes(q) || rawType.includes(q) || fmtType.includes(q) || country.includes(q)
    }

    // 2. Type Filter: Normalize categories!
    let matchType = true
    if (filterType.value) {
      const selected = filterType.value.toLowerCase()
      const incType = (incident.type || '').toLowerCase()
      const loc = (incident.location || '').toLowerCase()
      
      if (selected === 'fire') {
        matchType = incType.includes('fire') || loc.includes('fire')
      } else if (selected === 'flood') {
        matchType = incType.includes('flood') || loc.includes('flood')
      } else if (selected === 'earthquake') {
        matchType = incType.includes('earthquake') || incType.includes('seismic') || loc.includes('quake')
      } else if (selected === 'storm') {
        matchType = incType.includes('storm') || incType.includes('cyclone') || incType.includes('typhoon') || incType.includes('hurricane') || loc.includes('storm') || loc.includes('typhoon') || loc.includes('hurricane')
      } else if (selected === 'weather') {
        matchType = incType.includes('weather') || incType === 'other'
      } else if (selected === 'landslide') {
        matchType = incType.includes('landslide')
      } else {
        matchType = incType === selected
      }
    }

    // 3. Status Filter: Treat 'detected' and 'active' uniformly or match
    let matchStatus = true
    if (filterStatus.value) {
      const selected = filterStatus.value.toLowerCase()
      const incStatus = (incident.status || '').toLowerCase()
      if (selected === 'active') {
        matchStatus = incStatus === 'active' || incStatus === 'detected'
      } else {
        matchStatus = incStatus === selected
      }
    }

    // 4. Severity Filter: Calibrate against both severity string and 0-100 threat score!
    let matchSeverity = true
    if (filterSeverity.value) {
      const selected = filterSeverity.value.toLowerCase()
      const incSeverity = (incident.severity || '').toLowerCase()
      const threat = incident.threatScore ?? 50

      if (selected === 'critical') {
        matchSeverity = incSeverity === 'critical' || threat >= 80
      } else if (selected === 'high') {
        matchSeverity = incSeverity === 'high' || (threat >= 65 && threat < 80)
      } else if (selected === 'medium') {
        matchSeverity = incSeverity === 'medium' || (threat >= 45 && threat < 65)
      } else if (selected === 'low') {
        matchSeverity = incSeverity === 'low' || threat < 45
      }
    }

    return matchSearch && matchType && matchStatus && matchSeverity
  })
})

const totalArea = computed(() => 
  filteredIncidents.value.reduce((sum, i) => sum + i.affectedArea, 0)
)

const totalPopulation = computed(() =>
  filteredIncidents.value.reduce((sum, i) => sum + i.affectedPopulation, 0)
)

const avgThreat = computed(() => {
  if (filteredIncidents.value.length === 0) return 0
  const sum = filteredIncidents.value.reduce((sum, i) => sum + i.threatScore, 0)
  return sum / filteredIncidents.value.length
})

const formatDate = (date: Date) =>
  date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

const getTrendDirection = (trend: number): string => {
  return trend > 12 ? 'accelerating' : trend > 5 ? 'stable' : 'decelerating'
}

const getRecommendedAction = (incident: IncidentLevel1): string => {
  const threat = incident.threatScore ?? 50
  const pop = incident.affectedPopulation || 0
  
  if (threat >= 80) {
    return `🚨 MANDATORY EVACUATION (${(pop / 1000).toFixed(0)}K at risk)`
  } else if (threat >= 65) {
    return `⚠️ PREPARE SHELTERS & DEPLOY FIRST RESPONDERS`
  } else if (threat >= 50) {
    return `🛡️ ACTIVATE PERIMETER MONITORING`
  } else {
    return `📡 SENSOR SURVEILLANCE ACTIVE`
  }
}

const viewIncident = (id: string) => {
  router.push(`/incident/${id}`)
}

const toggleExpanded = (id: string) => {
  expandedIncidentId.value = expandedIncidentId.value === id ? null : id
}

// Native browser internationalization for country names
const regionNames = new Intl.DisplayNames(['en'], { type: 'region' })

const getCountryFlag = (code?: string): string => {
  if (!code) return '🌍'
  const trimmed = code.trim().toUpperCase()
  if (/^[A-Z]{2}$/.test(trimmed)) {
    return String.fromCodePoint(
      127397 + trimmed.charCodeAt(0),
      127397 + trimmed.charCodeAt(1)
    )
  }
  return '🌍'
}

const getCountryName = (code?: string): string => {
  if (!code) return ''
  const trimmed = code.trim().toUpperCase()
  if (/^[A-Z]{2}$/.test(trimmed)) {
    try {
      return regionNames.of(trimmed) || trimmed
    } catch {
      return trimmed
    }
  }
  return trimmed
}

/**
 * Leaves location intact or trims trailing 2-letter country code so location stays clean
 * e.g. "Dale, AL, US" -> "Dale, AL"
 *      "Port Fourchon, Louisiana, US" -> "Port Fourchon, Louisiana"
 *      "Karachi, PK" -> "Karachi"
 */
const cleanLocation = (location: string): string => {
  if (!location) return 'Unknown Sector'
  return location.replace(/,\s*[A-Za-z]{2}$/, '').trim()
}

/**
 * Resolves full country name and flag emoji for dedicated Country column
 */
const resolveCountry = (location: string, countryCode?: string): { name: string; flag: string } => {
  let code = countryCode ? countryCode.trim().toUpperCase() : ''
  
  // If backend passed the default 'UN' (Unknown/United Nations) or it's empty, 
  // attempt to extract the real country code from the location string (e.g. "Dale, AL, US" -> "US")
  if ((!code || code === 'UN') && location) {
    const match = location.trim().match(/,\s*([A-Za-z]{2})$/)
    if (match && match[1]) {
      code = match[1].toUpperCase()
    }
  }
  
  const name = getCountryName(code) || 'Global Sector'
  const flag = getCountryFlag(code)
  return { name, flag }
}

onMounted(async () => {
  if (eventsStore.allIncidents.length === 0) {
    try {
      const host = window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin
      const res = await fetch(`${host}/api/v1/incidents?limit=50`)
      if (res.ok) {
        const raw = await res.json()
        if (raw && raw.length > 0) {
          eventsStore.setIncidents(raw.map((e: any, idx: number) => ({
            id: e.id || `inc-${idx}`,
            type: e.event_type || 'fire',
            location: e.location_name || 'Unknown',
            countryCode: e.countryCode || 'UN',
            severity: e.severity || 'medium',
            status: e.status || 'active',
            threatScore: e.impact?.risk_score ?? 50,
            detectionTime: new Date(e.event_timestamp || Date.now()),
            affectedArea: e.impact?.affected_area_km2 ?? 150,
            affectedPopulation: e.impact?.affected_population ?? 50000,
            trend: e.impact?.trend_km2_per_hour ?? 5.2,
            forecast6h: e.impact?.forecast_6h_km2 ?? 31.2,
            coordinates: [e.latitude, e.longitude] as [number, number],
          })))
        }
      }
    } catch (err) {
      console.warn('Failed to hydrate incidents in IncidentsScreen:', err)
    }
  }
})
</script>

<style scoped>
.incidents-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.incidents-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.controls-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
}

.search-bar {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 36px;
  border: 2px solid var(--accent-cyan);
  border-radius: 6px;
  background: rgba(30, 144, 255, 0.05);
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: #808a92;
}

.search-input:focus {
  border-color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.1);
  box-shadow: 0 0 12px rgba(30, 144, 255, 0.3);
  outline: none;
}

.search-icon {
  position: absolute;
  left: 10px;
  font-size: 16px;
}

.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  width: 100%;
}

.filter-group {
  display: flex;
  width: 100%;
}

.filter-select {
  width: 100%;
  padding: 8px 12px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  background: transparent;
  color: #ffffff;
  font-size: 12px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.filter-select:hover {
  border-color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.1);
}

.filter-select:focus {
  border-color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.15);
  outline: none;
}

.filter-select option {
  background: var(--bg-panel);
  color: #ffffff;
}

.incidents-table thead {
  position: sticky;
  top: 0;
  /* Use a much more solid background so scrolling text doesn't bleed through the blur */
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(12px);
  z-index: 10; /* CRITICAL: Keeps header strictly above the scrolling table rows */
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); /* Adds a subtle drop shadow to separate header from scrolling content */
}

/* Ensure the wrapper doesn't clip the sticky header shadow */
.incidents-table-wrapper {
  flex: 1;
  overflow: auto;
  padding: 16px;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative; /* Helps context for sticky children */
}

.incidents-table th {
  padding: 14px 10px;
  text-align: left;
  font-weight: 700;
  border-bottom: 2px solid var(--accent-cyan);
  color: #ffffff;
  white-space: nowrap;
  text-transform: uppercase;
  font-size: 12px;
  letter-spacing: 0.5px;
}

/* Specific Column Widths */
.incidents-table th:nth-child(1),
.incidents-table td:nth-child(1) {
  min-width: 130px;
  text-align: left;
}

.type-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.type-name {
  font-size: 12px;
  font-weight: 700;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.incidents-table th:nth-child(2),
.incidents-table td:nth-child(2) {
  width: 20%;
  min-width: 140px;
}

/* Column 3: Country */
.incidents-table th:nth-child(3),
.incidents-table td:nth-child(3) {
  min-width: 150px;
}

/* Column 10: Recommended Action */
.incidents-table th:nth-child(10),
.incidents-table td:nth-child(10) {
  min-width: 240px;
  width: 280px;
}

/* Column 11: Analysis (View Button) */
.incidents-table th:nth-child(11),
.incidents-table td:nth-child(11) {
  min-width: 140px;
  width: 140px;
  text-align: center;
  white-space: nowrap;
}

.country-cell {
  white-space: nowrap;
}

.country-flag {
  font-size: 16px;
  margin-right: 6px;
}

.country-name {
  color: #cbd5e1;
  font-weight: 500;
  font-size: 13px;
}

.incidents-table td {
  padding: 12px 10px;
  border-bottom: 1px solid rgba(30, 64, 175, 0.2);
  color: #ffffff;
  font-weight: 500;
  vertical-align: middle;
}

.location-cell {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 0;
}

.incident-row:hover {
  background: rgba(30, 144, 255, 0.15);
  transition: all 200ms ease;
}

/* Collapsible card styles */
.incident-header {
  padding: 0 !important;
  border-bottom: none !important;
  cursor: pointer;
}

.incident-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 10px;
  width: 100%;
}

.incident-summary .icon-cell {
  font-size: 24px;
  width: auto;
  text-align: center;
  flex-shrink: 0;
}

.summary-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.summary-content strong {
  color: #ffffff;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.expand-icon {
  color: var(--accent-cyan);
  font-size: 12px;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.incident-row.expanded .expand-icon {
  transform: rotate(180deg);
}

.detail-row {
  background: transparent !important;
  display: contents;
}

.detail-content {
  padding: 16px 10px !important;
  border-bottom: 1px solid rgba(30, 64, 175, 0.2);
  background: rgba(10, 30, 80, 0.4);
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-label {
  font-size: 10px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 13px;
  color: #ffffff;
  font-weight: 600;
}

.icon-cell {
  font-size: 20px;
  width: 45px;
  text-align: center;
}

.status-badge {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 4px;
  font-weight: 700;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.status-badge.active {
  background: linear-gradient(135deg, #10b981, #059669);
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.status-badge.monitoring {
  background: linear-gradient(135deg, #3b82f6, #1e40af);
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.status-badge.resolved {
  background: linear-gradient(135deg, #8b7355, #6b6b6b);
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.3);
}

.threat-score {
  font-weight: 700;
  color: #ffffff;
}

.trend {
  color: #10b981;
  font-weight: 600;
}

.detection-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.view-btn {
  padding: 8px 14px;
  background: linear-gradient(135deg, #1e40af, #0ea5e9);
  border: 2px solid var(--accent-cyan);
  color: #ffffff;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  box-shadow: 0 2px 8px rgba(30, 144, 255, 0.4);
}

.view-btn:hover {
  background: linear-gradient(135deg, #1e3a8a, #0284c7);
  box-shadow: 0 4px 16px rgba(30, 144, 255, 0.6);
  transform: translateY(-2px);
}

.action-cell {
  font-size: 11px;
  min-width: 240px;
  max-width: 320px;
  vertical-align: middle;
}

.action-badge {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid #ef4444;
  color: #fca5a5;
  padding: 6px 12px;
  border-radius: 6px;
  display: block;
  font-weight: 600;
  white-space: normal;
  word-break: normal;
  line-height: 1.4;
  text-align: left;
}

.view-cell {
  min-width: 140px;
  text-align: center;
  white-space: nowrap;
  vertical-align: middle;
}

.no-results {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}

.detail-panel {
  position: fixed;
  right: 16px;
  top: 76px;
  bottom: 16px;
  width: 350px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  z-index: 50;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 16px;
}

.modal-box {
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.2), rgba(14, 165, 233, 0.1));
  border: 2px solid var(--accent-cyan);
  border-radius: 12px;
  padding: 24px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 24px rgba(30, 144, 255, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 16px;
  border-bottom: 2px solid var(--accent-cyan);
  margin-bottom: 16px;
}

.modal-header h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--accent-cyan);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.modal-time {
  font-size: 11px;
  color: #b0b9c1;
  font-weight: 500;
}

.modal-close-btn {
  background: none;
  border: none;
  color: var(--accent-cyan);
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.modal-close-btn:hover {
  background: rgba(30, 144, 255, 0.15);
  transform: scale(1.1);
}

.modal-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 16px;
}

.modal-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.modal-label {
  font-size: 12px;
  color: #b0b9c1;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  min-width: 100px;
}

.modal-value {
  font-size: 14px;
  color: #ffffff;
  font-weight: 600;
  text-align: right;
}

.modal-status-group {
  display: flex;
  gap: 8px;
  align-items: center;
}

.modal-status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.modal-status-badge.active {
  background: rgba(16, 185, 129, 0.3);
  color: #10b981;
}

.modal-status-badge.monitoring {
  background: rgba(59, 130, 246, 0.3);
  color: #3b82f6;
}

.modal-status-badge.resolved {
  background: rgba(107, 114, 128, 0.3);
  color: #6b7280;
}

.modal-trend {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.modal-trend.accelerating {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.modal-trend.stable {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.modal-trend.decelerating {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.modal-threat {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent-cyan);
}

.modal-action-box {
  background: rgba(239, 68, 68, 0.1);
  border: 2px solid #ef4444;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.modal-action-label {
  font-size: 11px;
  color: #ef4444;
  font-weight: 700;
  text-transform: uppercase;
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}

.modal-action-text {
  font-size: 13px;
  color: #ffffff;
  font-weight: 600;
  line-height: 1.4;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 2px solid var(--accent-cyan);
}

.modal-btn-close {
  width: 100%;
  padding: 10px 14px;
  background: linear-gradient(135deg, #1e40af, #0ea5e9);
  border: 2px solid var(--accent-cyan);
  color: #ffffff;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(30, 144, 255, 0.4);
}

.modal-btn-close:hover {
  background: linear-gradient(135deg, #1e3a8a, #0284c7);
  box-shadow: 0 4px 16px rgba(30, 144, 255, 0.6);
  transform: translateY(-2px);
}

.modal-btn-details {
  flex: 1;
  padding: 10px 14px;
  background: linear-gradient(135deg, #0ea5e9, #00d9ff);
  border: 2px solid #00d9ff;
  color: #000;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.5);
}

.modal-btn-details:hover {
  background: linear-gradient(135deg, #38bdf8, #06b6d4);
  border-color: #06b6d4;
  box-shadow: 0 4px 16px rgba(14, 165, 233, 0.7);
  transform: translateY(-2px);
}

.status {
  font-weight: 600;
}

.status.active {
  color: #22c55e;
}

.status.monitoring {
  color: #3b82f6;
}

.status.resolved {
  color: #6b7280;
}

.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 300ms ease;
}

.slide-right-enter-from {
  transform: translateX(100%);
}

.slide-right-leave-to {
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 300ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 1024px) {
  .incidents-table-wrapper {
    padding: 12px;
  }

  .incidents-table {
    font-size: 12px;
  }

  .incidents-table th,
  .incidents-table td {
    padding: 8px 4px;
  }

  .detail-panel {
    width: 300px;
  }
}

@media (max-width: 768px) {
  .incidents-screen {
    padding: 10px;
    height: auto;
    min-height: 100vh;
    overflow-y: auto;
  }

  .controls-panel {
    padding: 12px;
  }

  .filters {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .filter-select {
    width: 100%;
  }

  .search-input {
    font-size: 13px;
  }

  /* Mobile: Clean Incident Cards Layout (Replaces Table) */
  .incidents-table-wrapper {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    box-shadow: none !important;
  }

  .incidents-table {
    display: block;
    width: 100%;
  }

  .incidents-table thead {
    display: none;
  }

  .incidents-table tbody {
    display: flex;
    flex-direction: column;
    gap: 12px;
    width: 100%;
  }

  /* Each table row becomes a sleek, high-tech Mobile Card */
  .incident-row {
    display: grid !important;
    grid-template-columns: 1fr auto !important;
    grid-template-areas: 
      "header status"
      "location location" !important;
    row-gap: 6px !important;
    column-gap: 8px !important;
    padding: 14px 16px !important;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(30, 41, 59, 0.65)) !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.45) !important;
    backdrop-filter: blur(16px) !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
    user-select: none !important;
    position: relative !important;
  }

  .incident-row:hover {
    border-color: #38bdf8 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(14, 165, 233, 0.2) !important;
  }

  .incident-row.expanded {
    border-color: #38bdf8 !important;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.85)) !important;
    box-shadow: 0 10px 32px rgba(14, 165, 233, 0.25) !important;
  }

  /* 1. Header Area: Hazard Type on Left with chevron */
  .incident-row .type-cell {
    grid-area: header !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    min-width: unset !important;
  }

  .incident-row .type-icon {
    font-size: 20px !important;
  }

  .incident-row .type-name {
    font-size: 13px !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
  }

  /* 2. Status & Threat Badges on Right */
  .incident-row .status-cell {
    grid-area: status !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
    position: static !important;
  }

  .incident-row .status-badge {
    padding: 3px 8px !important;
    font-size: 9px !important;
    font-weight: 800 !important;
    border-radius: 4px !important;
    letter-spacing: 0.5px !important;
  }

  /* Expand chevron */
  .incident-row .status-cell::after {
    content: '▾';
    font-size: 16px;
    color: #38bdf8;
    transition: transform 0.25s ease;
    margin-left: 2px;
  }

  .incident-row.expanded .status-cell::after {
    transform: rotate(180deg);
  }

  /* 3. Location Row */
  .incident-row .location-cell {
    grid-area: location !important;
    display: block !important;
    padding: 2px 0 4px 0 !important;
    border: none !important;
    background: transparent !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    color: #38bdf8 !important;
    line-height: 1.4 !important;
    position: static !important;
    width: 100% !important;
    white-space: normal !important;
    max-width: unset !important;
  }

  /* 4. HIDDEN IN COLLAPSED STATE */
  .incident-row .threat-cell,
  .incident-row .area-cell,
  .incident-row .population-cell,
  .incident-row .trend-cell,
  .incident-row .time-cell,
  .incident-row .action-cell,
  .incident-row .view-cell {
    display: none !important;
  }

  /* 5. EXPANDED BODY: Compact 2x2 Grid + Action + Button */
  .incident-row.expanded {
    grid-template-columns: 1fr 1fr !important;
    grid-template-areas: 
      "header status"
      "location location" !important;
  }

  .incident-row.expanded .threat-cell,
  .incident-row.expanded .action-cell,
  .incident-row.expanded .view-cell {
    grid-column: 1 / -1 !important;
  }

  .incident-row.expanded .area-cell,
  .incident-row.expanded .trend-cell {
    grid-column: 1 !important;
  }

  .incident-row.expanded .population-cell,
  .incident-row.expanded .time-cell {
    grid-column: 2 !important;
  }

  .incident-row.expanded .threat-cell {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    margin-top: 6px !important;
    border: 1px solid rgba(245, 158, 11, 0.25) !important;
    background: rgba(245, 158, 11, 0.08) !important;
    color: #fbbf24 !important;
    border-radius: 8px !important;
    padding: 7px 12px !important;
    font-size: 13px !important;
    font-weight: 800 !important;
  }

  .incident-row.expanded .threat-cell::before { content: 'THREAT SCORE'; font-size: 10px; font-weight: 700; color: #94a3b8; }

  /* 2x2 Metric Tiles */
  .incident-row.expanded .area-cell,
  .incident-row.expanded .population-cell,
  .incident-row.expanded .trend-cell,
  .incident-row.expanded .time-cell {
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    background: rgba(30, 41, 59, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 8px !important;
    padding: 8px 10px !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    color: #f1f5f9 !important;
    gap: 3px !important;
  }

  .incident-row.expanded .area-cell::before { content: 'AFFECTED AREA'; font-size: 9px; font-weight: 700; color: #94a3b8; }
  .incident-row.expanded .population-cell::before { content: 'POPULATION AT RISK'; font-size: 9px; font-weight: 700; color: #94a3b8; }
  .incident-row.expanded .trend-cell::before { content: 'SPREAD RATE'; font-size: 9px; font-weight: 700; color: #94a3b8; }
  .incident-row.expanded .time-cell::before { content: 'DETECTED'; font-size: 9px; font-weight: 700; color: #94a3b8; }

  .incident-row.expanded .action-cell {
    display: block !important;
    width: 100% !important;
    max-width: 100% !important;
    min-width: 100% !important;
    padding: 6px 0 !important;
    margin: 4px 0 !important;
    border: none !important;
    box-sizing: border-box !important;
    overflow: visible !important;
  }

  .incident-row.expanded .action-badge {
    display: block !important;
    width: 100% !important;
    max-width: 100% !important;
    box-sizing: border-box !important;
    text-align: center !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    padding: 10px 12px !important;
    border-radius: 6px !important;
    background: rgba(239, 68, 68, 0.12) !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
    color: #fca5a5 !important;
    white-space: normal !important;
    word-break: break-word !important;
    line-height: 1.4 !important;
  }

  .incident-row.expanded .view-cell {
    display: block !important;
    width: 100% !important;
    padding: 6px 0 0 0 !important;
    margin-top: 6px !important;
    border: none !important;
    background: transparent !important;
    box-sizing: border-box !important;
  }

  .incident-row.expanded .view-btn {
    width: 100% !important;
    padding: 12px 16px !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    text-align: center !important;
    border-radius: 8px !important;
    background: linear-gradient(135deg, #0ea5e9, #2563eb) !important;
    border: 1px solid #38bdf8 !important;
    color: #ffffff !important;
    cursor: pointer !important;
    box-shadow: 0 4px 16px rgba(14, 165, 233, 0.35) !important;
  }

  .incident-row.expanded .view-btn:hover {
    background: linear-gradient(135deg, #38bdf8, #1d4ed8) !important;
    box-shadow: 0 0 24px rgba(56, 189, 248, 0.5) !important;
  }

  /* Hide redundant bottom stats footer on mobile to keep view uncluttered */
  .stats-footer {
    display: none !important;
  }

  .detail-panel {
    width: 280px;
    right: 8px;
  }
}
</style>
