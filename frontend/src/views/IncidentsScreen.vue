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
              <option value="fire">🔥 Fire</option>
              <option value="flood">💧 Flood</option>
              <option value="earthquake">🌍 Earthquake</option>
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
              <td class="location-cell">{{ incident.location }}</td>
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

        <!-- Stats Footer - moved inside wrapper -->
        <div class="stats-footer glass-panel">
          <div class="stat">
            <span class="label">{{ $t('incidents.viewing') }}</span>
            <span class="value">{{ filteredIncidents.length }}</span>
          </div>
          <div class="stat">
            <span class="label">Total {{ $t('incidents.affectedArea') }}</span>
            <span class="value">{{ totalArea.toFixed(1) }} km²</span>
          </div>
          <div class="stat">
            <span class="label">Total {{ $t('incidents.population') }}</span>
            <span class="value">{{ totalPopulation.toLocaleString() }}</span>
          </div>
          <div class="stat">
            <span class="label">Avg {{ $t('incidents.threatScore') }}</span>
            <span class="value">{{ avgThreat.toFixed(0) }}/100</span>
          </div>
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
    const matchSearch = 
      incident.location.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      incident.type.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const matchType = !filterType.value || incident.type === filterType.value
    const matchStatus = !filterStatus.value || incident.status === filterStatus.value
    const matchSeverity = !filterSeverity.value || incident.severity === filterSeverity.value

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
  width: 25%;
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
  max-width: 200px;
}

.action-badge {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid #ef4444;
  color: #fca5a5;
  padding: 6px 10px;
  border-radius: 4px;
  display: inline-block;
  font-weight: 600;
  white-space: nowrap;
}

.no-results {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}

.stats-footer {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  padding: 16px;
  margin-top: 16px;
  border-top: 1px solid rgba(30, 144, 255, 0.2);
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat .label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-weight: 600;
}

.stat .value {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent-cyan);
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
  .controls-panel {
    padding: 12px;
  }

  .filters {
    flex-direction: column;
  }

  .filter-select {
    width: 100%;
  }

  .incidents-table-wrapper {
    overflow-x: auto;
  }

  .detail-panel {
    width: 280px;
    right: 8px;
  }

  .stats-footer {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .incidents-screen {
    padding: 8px;
    gap: 8px;
  }

  .incidents-container {
    gap: 8px;
  }

  .controls-panel {
    padding: 10px;
    gap: 8px;
  }

  .filters {
    grid-template-columns: 1fr;
  }

  .filter-select {
    width: 100%;
  }

  .search-input {
    font-size: 13px;
  }

  /* Mobile: Transform table into collapsible cards */
  .incidents-table-wrapper {
    padding: 0;
    background: transparent;
  }

  .incidents-table {
    display: block;
    font-size: 11px;
  }

  .incidents-table thead {
    display: none;
  }

  .incidents-table tbody {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  /* Each row becomes a card */
  .incident-row {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0;
    padding: 0;
    border: 1px solid rgba(30, 144, 255, 0.25);
    border-radius: 8px;
    background: rgba(20, 50, 120, 0.5);
    overflow: hidden;
    transition: all 0.2s ease;
  }

  .incident-row:hover {
    background: rgba(20, 50, 120, 0.6);
    border-color: rgba(30, 144, 255, 0.4);
  }

  .incident-row.expanded {
    background: rgba(20, 50, 120, 0.7);
    border-color: rgba(30, 144, 255, 0.5);
  }

  /* Hide all cells by default */
  .incident-row td {
    display: none;
  }

  /* Show first cell (icon) as header */
  .detail-cell {
    display: block !important;
    grid-column: 1;
    padding: 12px;
    font-size: 20px;
    border: none;
    background: transparent;
    position: relative;
    cursor: pointer;
  }

  /* Add expand arrow icon */
  .detail-cell::after {
    content: '▶';
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 14px;
    color: #67e8f9;
    transition: transform 0.2s ease;
  }

  /* Rotate arrow when expanded */
  .incident-row.expanded .detail-cell::after {
    transform: translateY(-50%) rotate(90deg);
  }

  /* Show location as header text */
  .location-cell {
    display: block !important;
    grid-column: 1;
    padding: 12px 0 0 0;
    font-weight: 600;
    border: none;
    background: transparent;
    cursor: pointer;
    font-size: 13px;
    color: #ffffff;
    position: relative;
    top: -48px;
    left: 50px;
    width: calc(100% - 90px);
  }

  /* Show status as header badge */
  .status-cell {
    display: block !important;
    grid-column: 1;
    padding: 0;
    border: none;
    background: transparent;
    cursor: pointer;
    position: relative;
    top: -48px;
    text-align: right;
    padding-right: 50px;
  }

  /* Create clickable header area */
  .detail-cell,
  .location-cell,
  .status-cell {
    cursor: pointer;
    user-select: none;
  }

  /* Header row structure */
  .detail-cell::before {
    content: '';
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 14px;
    color: #67e8f9;
  }

  /* Show expanded details when row is active */
  .incident-row.expanded .threat-cell,
  .incident-row.expanded .area-cell,
  .incident-row.expanded .population-cell,
  .incident-row.expanded .trend-cell,
  .incident-row.expanded .time-cell,
  .incident-row.expanded .action-cell,
  .incident-row.expanded .view-cell {
    display: grid !important;
    grid-template-columns: 70px 1fr;
    gap: 8px;
    padding: 12px;
    border-bottom: 1px solid rgba(30, 144, 255, 0.1);
    border-top: 1px solid rgba(30, 144, 255, 0.1);
    align-items: center;
  }

  .threat-cell::before {
    content: 'Threat';
    font-weight: 600;
    color: #a0aec0;
    font-size: 9px;
    text-transform: uppercase;
  }

  .area-cell::before {
    content: 'Area';
    font-weight: 600;
    color: #a0aec0;
    font-size: 9px;
    text-transform: uppercase;
  }

  .population-cell::before {
    content: 'Population';
    font-weight: 600;
    color: #a0aec0;
    font-size: 9px;
    text-transform: uppercase;
  }

  .trend-cell::before {
    content: 'Trend';
    font-weight: 600;
    color: #a0aec0;
    font-size: 9px;
    text-transform: uppercase;
  }

  .time-cell::before {
    content: 'Time';
    font-weight: 600;
    color: #a0aec0;
    font-size: 9px;
    text-transform: uppercase;
  }

  .action-cell::before {
    content: 'Action';
    font-weight: 600;
    color: #a0aec0;
    font-size: 9px;
    text-transform: uppercase;
  }

  .view-cell {
    display: block !important;
    padding: 0 12px 12px 12px !important;
    border: none !important;
    background: transparent !important;
  }

  .view-btn {
    width: 100%;
    padding: 8px 12px;
    font-size: 11px;
    background: rgba(30, 144, 255, 0.15);
    border: 1px solid #0ea5e9;
    color: #67e8f9;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .view-btn:hover {
    background: rgba(30, 144, 255, 0.25);
    color: #ffffff;
  }

  .status-badge {
    display: inline-block;
    padding: 6px 10px;
    font-size: 10px;
    border-radius: 4px;
  }

  .action-badge {
    display: block;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
    padding: 8px 10px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 10px;
    white-space: normal;
  }

  .stats-footer {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    padding: 12px;
    margin-top: 12px;
    border-top: 1px solid rgba(30, 144, 255, 0.2);
  }

  .stat .label {
    font-size: 10px;
  }

  .stat .value {
    font-size: 16px;
  }
}
</style>
