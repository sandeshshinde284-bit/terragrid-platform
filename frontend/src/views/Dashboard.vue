<template>
  <div class="dashboard">
    <Header />

    <div class="content-grid" :class="{ 'detail-open': selectedIncidentData }">
      <!-- Left: Incidents Panel -->
      <aside class="incidents-panel glass-panel">
        <div class="incidents-header">
          <div class="header-title-row">
            <h3>
              🌍 {{ $t('dashboard.activeIncidents') }}
              <span v-if="isLoading" class="loading-indicator">⟳ Updating…</span>
            </h3>
            <span class="live-badge" :class="{ connected: isConnected }">
              {{ isConnected ? '🟢 Live Updates' : '🔴 Offline' }}
            </span>
          </div>
          <div class="sort-controls">
            <select v-model="sortBy" class="sort-dropdown">
              <option value="threat">↓ Threat Score</option>
              <option value="area">↓ Affected Area</option>
              <option value="population">↓ Population</option>
              <option value="time">↓ Detection Time</option>
            </select>
          </div>
        </div>
        <div class="incident-list" :class="{ 'is-loading': isLoading }">
          <IncidentCard 
            v-for="incident in sortedAndPaginatedIncidents"
            :key="incident.id"
            :incident="incident"
            @expand="expandIncident"
          />
        </div>

        <!-- Pagination Controls -->
        <div class="pagination-controls">
          <button 
            class="pagination-btn prev-btn"
            @click="previousPage"
            :disabled="currentPage === 1"
          >
            ← Previous
          </button>
          <span class="page-info">
            Page {{ currentPage }} / {{ totalPages }}
          </span>
          <button 
            class="pagination-btn next-btn"
            @click="nextPage"
            :disabled="currentPage >= totalPages"
          >
            Next →
          </button>
        </div>
      </aside>

      <!-- Center: Map -->
      <main class="map-section glass-panel">
        <div class="map-container">
          <div v-if="appStore.viewMode === '2d'" class="map-view">
            <MapComponent />
          </div>
          <div v-else class="map-view three-d-view">
            <div class="three-d-placeholder">
              <h2>🌐 {{ $t('map.title') }}</h2>
              <p>California disaster map in 3D perspective</p>
              <p class="terrain-icon">🏔️</p>
              <p class="coming-soon">3D view coming in STEP 2</p>
            </div>
          </div>
        </div>
      </main>

      <!-- Right: Detail Panel (Slides Out) -->
      <transition name="slide-right">
        <aside v-if="selectedIncidentData" class="detail-panel glass-panel">
          <div class="detail-header">
            <div class="header-top">
              <span class="incident-type-icon">{{ getIncidentIcon(selectedIncidentData.type) }}</span>
              <h3>{{ formatIncidentType(selectedIncidentData.type) }}</h3>
            </div>
            <button class="close-btn" @click="closeDetail">✕</button>
          </div>

          <div class="detail-content">
            <div class="detail-item">
              <label>{{ $t('incidents.location') }}</label>
              <div class="location-value">📍 {{ selectedIncidentData.location }}</div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.status') }}</label>
              <div class="status-badge" :class="selectedIncidentData.status">
                {{ selectedIncidentData.status.toUpperCase() }}
              </div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.threatScore') }}</label>
              <div class="threat-score">{{ getThreatScore(selectedIncidentData) }}/100</div>
            </div>

            <div class="divider"></div>

            <div class="detail-item">
              <label>{{ $t('incidents.detectionTime') }}</label>
              <div class="value">{{ formatDate(selectedIncidentData.detectionTime) }}</div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.affectedArea') }}</label>
              <div class="metric-value">{{ selectedIncidentData.affectedArea.toFixed(1) }} km²</div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.population') }}</label>
              <div class="metric-value">{{ selectedIncidentData.affectedPopulation.toLocaleString() }}</div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.trend') }}</label>
              <div class="trend-value">+{{ selectedIncidentData.trend.toFixed(1) }} km²/h</div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.forecast') }}</label>
              <div class="forecast-value">+{{ selectedIncidentData.forecast6h.toFixed(1) }} km²</div>
            </div>

            <div class="divider"></div>

            <div class="summary-section">
              <label>{{ $t('common.details') }}</label>
              <p>
                {{ formatIncidentType(selectedIncidentData.type) }} activity near
                {{ selectedIncidentData.location }} is currently
                {{ selectedIncidentData.status }} and remains under active monitoring.
              </p>
            </div>
          </div>
        </aside>
      </transition>

      <!-- Mobile Modal Overlay (Mobile <480px only) -->
      <transition name="fade">
        <div v-if="selectedIncidentData" class="mobile-detail-overlay" @click="closeDetail"></div>
      </transition>

      <!-- Mobile Detail Modal (Mobile <480px only) -->
      <transition name="slide-up">
        <div v-if="selectedIncidentData" class="mobile-detail-modal glass-panel">
          <div class="detail-header">
            <div class="header-top">
              <span class="incident-type-icon">{{ getIncidentIcon(selectedIncidentData.type) }}</span>
              <h3>{{ formatIncidentType(selectedIncidentData.type) }}</h3>
            </div>
            <button class="close-btn" @click="closeDetail">✕</button>
          </div>

          <div class="detail-content">
            <div class="detail-item">
              <label>{{ $t('incidents.location') }}</label>
              <div class="location-value">📍 {{ selectedIncidentData.location }}</div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.status') }}</label>
              <div class="status-badge" :class="selectedIncidentData.status">
                {{ selectedIncidentData.status.toUpperCase() }}
              </div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.threatScore') }}</label>
              <div class="threat-score">{{ getThreatScore(selectedIncidentData) }}/100</div>
            </div>

            <div class="divider"></div>

            <div class="detail-item">
              <label>{{ $t('incidents.detectionTime') }}</label>
              <div class="value">{{ formatDate(selectedIncidentData.detectionTime) }}</div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.affectedArea') }}</label>
              <div class="metric-value">{{ selectedIncidentData.affectedArea.toFixed(1) }} km²</div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.population') }}</label>
              <div class="metric-value">{{ selectedIncidentData.affectedPopulation.toLocaleString() }}</div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.trend') }}</label>
              <div class="trend-value">+{{ selectedIncidentData.trend.toFixed(1) }} km²/h</div>
            </div>

            <div class="detail-item">
              <label>{{ $t('incidents.forecast') }}</label>
              <div class="forecast-value">+{{ selectedIncidentData.forecast6h.toFixed(1) }} km²</div>
            </div>

            <div class="divider"></div>

            <div class="summary-section">
              <label>{{ $t('common.details') }}</label>
              <p>
                {{ formatIncidentType(selectedIncidentData.type) }} activity near
                {{ selectedIncidentData.location }} is currently
                {{ selectedIncidentData.status }} and remains under active monitoring.
              </p>
            </div>
          </div>
        </div>
      </transition>

      <!-- Right: AI Insights (Hidden when detail open) -->
      <aside v-if="!selectedIncidentData" class="insights-panel glass-panel">
        <h3>🤖 {{ $t('dashboard.aiInsights') }}</h3>
        <div v-if="alertsStore.criticalInsights.length" class="insights-list">
          <div v-for="insight in alertsStore.criticalInsights" :key="insight.id" class="insight-item">
            <div class="action">{{ insight.action }}</div>
            <div class="meta">{{ insight.estimatedAffected.toLocaleString() }} people</div>
          </div>
        </div>
        <p v-else class="no-insights">{{ $t('alerts.noAlerts') }}</p>
      </aside>
    </div>

    <!-- Bottom: Metrics -->
    <footer class="metrics-section glass-panel">
      <div class="metric">
        <span class="label">{{ $t('dashboard.totalAffectedArea') }}</span>
        <span class="value">{{ eventsStore.totalAffectedArea.toFixed(1) }} km²</span>
      </div>
      <div class="metric">
        <span class="label">{{ $t('dashboard.totalPopulation') }}</span>
        <span class="value">{{ eventsStore.totalAffectedPopulation.toLocaleString() }}</span>
      </div>
      <div class="metric">
        <span class="label">{{ $t('dashboard.activeIncidentsCount') }}</span>
        <span class="value">{{ eventsStore.allIncidents.length }}</span>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import Header from '@/components/organisms/Header.vue'
import IncidentCard from '@/components/molecules/IncidentCard.vue'
import MapComponent from '@/components/organisms/MapComponent.vue'
import { useAppStore } from '@/stores'
import { useEventsStore } from '@/stores'
import { useAlertsStore } from '@/stores'
import { useMockMode } from '@/composables/useMockMode'
import { useWebSocket } from '@/composables/useWebSocket'
import type { IncidentLevel1 } from '@/types'

const appStore = useAppStore()
const eventsStore = useEventsStore()
const alertsStore = useAlertsStore()
const { isMockMode, fetchWithMockMode } = useMockMode()
const { isConnected } = useWebSocket()

const isLoading = ref(false)
const apiError = ref<string | null>(null)
const sortBy = ref<'threat' | 'area' | 'population' | 'time'>('threat')
const currentPage = ref(1)
const cardsPerPage = ref(5) // 5-10 cards per page on mobile

const selectedIncidentData = computed<IncidentLevel1 | null>(
  () =>
    eventsStore.allIncidents.find(
      (incident) => incident.id === appStore.selectedIncident || incident.id === appStore.expandedIncident,
    ) ?? null,
)

const sortedAndPaginatedIncidents = computed(() => {
  let incidents = [...eventsStore.allIncidents]
  
  // Apply sorting
  switch (sortBy.value) {
    case 'area':
      incidents.sort((a, b) => (b.affectedArea || 0) - (a.affectedArea || 0))
      break
    case 'population':
      incidents.sort((a, b) => (b.affectedPopulation || 0) - (a.affectedPopulation || 0))
      break
    case 'time':
      incidents.sort((a, b) => new Date(b.detectionTime).getTime() - new Date(a.detectionTime).getTime())
      break
    case 'threat':
    default:
      // Already sorted by threatScore in backend, but ensure here too
      incidents.sort((a, b) => (b.threatScore || 0) - (a.threatScore || 0))
  }
  
  // Apply pagination (only on mobile, desktop shows all)
  const startIndex = (currentPage.value - 1) * cardsPerPage.value
  const endIndex = startIndex + cardsPerPage.value
  return incidents.slice(startIndex, endIndex)
})

const hasMoreIncidents = computed(() => {
  return currentPage.value * cardsPerPage.value < eventsStore.allIncidents.length
})

const totalPages = computed(() => {
  return Math.ceil(eventsStore.allIncidents.length / cardsPerPage.value) || 1
})

const loadMoreIncidents = () => {
  currentPage.value += 1
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value += 1
  }
}

const previousPage = () => {
  if (currentPage.value > 1) {
    currentPage.value -= 1
  }
}

const expandIncident = (id: string) => {
  appStore.setSelectedIncident(id)
  appStore.setExpandedIncident(id)
}

const closeDetail = () => {
  appStore.setSelectedIncident(null)
  appStore.setExpandedIncident(null)
}

const formatDate = (date: Date) =>
  date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

const formatIncidentType = (type: IncidentLevel1['type']) =>
  type.charAt(0).toUpperCase() + type.slice(1)

const getIncidentIcon = (type: IncidentLevel1['type']) => {
  const icons: Record<string, string> = {
    fire: '🔥',
    flood: '💧',
    landslide: '🏔️',
    earthquake: '📍',
  }
  return icons[type] || '⚠️'
}

const getThreatScore = (incident: IncidentLevel1 | null): number => {
  if (!incident) return 0
  if (incident.threatScore) return incident.threatScore
  // Map severity to threat score
  const severityMap: Record<string, number> = {
    low: 25,
    medium: 50,
    high: 75,
  }
  return severityMap[incident.severity] || 75
}

/**
 * California bounding box (matches MapComponent.vue MAP_BOUNDS, with padding)
 * Live global feeds need filtering so only geographically relevant events
 * are shown on this California-focused map/list.
 */
const CA_BOUNDS = { minLat: 30, maxLat: 44, minLon: -127, maxLon: -112 }
const MAX_INCIDENTS_DISPLAYED = 20

/**
 * Fetch incidents from backend API
 */
const fetchIncidents = async () => {
  try {
    isLoading.value = true
    apiError.value = null
    
    console.log(`📡 Fetching incidents (Mode: ${isMockMode.value ? '🧪 MOCK' : '🌐 LIVE'})`)
    
    const response = await fetchWithMockMode('http://localhost:8000/api/v1/ingest/all')
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }
    
    const result = await response.json()
    const events = result.data?.events ?? []
    console.log('✅ Incidents loaded:', events.length, 'events (raw, before filtering)')
    
    // Transform backend response to store format
    if (Array.isArray(events) && events.length > 0) {
      const mapped = events.map((event: any, index: number) => {
        const impact = event.impact || {}
        const severity = (event.severity || 'medium').toLowerCase()
        return {
          id: event.data?.nasa_id || event.data?.gdacs_id || `event-${index}-${Date.now()}`,
          type: event.event_type || 'fire',
          location: event.location_name || 'Unknown',
          severity: (severity === 'critical' ? 'high' : severity) as 'low' | 'medium' | 'high',
          status: event.status === 'detected' || event.status === 'active' ? 'active' : (event.status || 'active'),
          threatScore: impact.risk_score ?? undefined,
          detectionTime: new Date(event.event_timestamp || Date.now()),
          affectedArea: impact.affected_area_km2 ?? 150,
          affectedPopulation: impact.affected_population ?? 50000,
          trend: impact.trend_km2_per_hour ?? 5.2,
          forecast6h: impact.forecast_6h_km2 ?? 31.2,
          coordinates: [event.latitude, event.longitude] as [number, number],
        }
      })

      // This dashboard's map is scoped to California — filter out events
      // that fall outside those bounds so live (global) feeds don't clutter it.
      const inCalifornia = mapped.filter(
        (incident) =>
          incident.coordinates[0] >= CA_BOUNDS.minLat &&
          incident.coordinates[0] <= CA_BOUNDS.maxLat &&
          incident.coordinates[1] >= CA_BOUNDS.minLon &&
          incident.coordinates[1] <= CA_BOUNDS.maxLon,
      )

      // Prefer in-region events; fall back to the highest-threat global
      // events if nothing is currently happening in California.
      const pool = inCalifornia.length > 0 ? inCalifornia : mapped
      const incidents = pool
        .slice()
        .sort((a, b) => (b.threatScore ?? 0) - (a.threatScore ?? 0))
        .slice(0, MAX_INCIDENTS_DISPLAYED)

      console.log(
        `📍 Showing ${incidents.length} incident(s) after CA filter + cap (of ${mapped.length} total)`,
      )

      eventsStore.setIncidents(incidents)
    } else {
      // Fallback to mock data if no events
      console.warn('⚠️ No events from API, using mock data')
      eventsStore.initMockData()
    }
  } catch (error) {
    console.error('❌ Failed to fetch incidents:', error)
    apiError.value = error instanceof Error ? error.message : 'Failed to fetch data'
    // Fallback to mock data on error
    eventsStore.initMockData()
  } finally {
    isLoading.value = false
  }
}

/**
 * Load alerts from store (can be extended to fetch from backend)
 */
const loadAlerts = () => {
  if (alertsStore.criticalInsights.length === 0) {
    alertsStore.initMockInsights()
  }
}

onMounted(() => {
  // Fetch from backend API instead of using mock store data directly
  fetchIncidents()
  loadAlerts()
})

// Watch for mock mode changes and refetch
watch(isMockMode, () => {
  console.log(`🔄 Mock mode changed to: ${isMockMode.value ? '🧪 MOCK' : '🌐 LIVE'}`)
  currentPage.value = 1  // Reset pagination
  fetchIncidents()
})

// Reset pagination when sort order changes
watch(sortBy, () => {
  currentPage.value = 1
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  padding: 16px;
  gap: 16px;
}

.content-grid {
  display: grid;
  grid-template-columns: 320px 1fr 300px;
  gap: 16px;
  flex: 1;
  min-height: 0;
  transition: grid-template-columns 300ms ease;
}

.content-grid.detail-open {
  grid-template-columns: 250px 1fr 320px;
}

.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  padding: 16px;
  overflow: hidden;
}

/* Incidents Panel */
.incidents-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.incidents-panel h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading-indicator {
  font-size: 11px;
  font-weight: 500;
  color: var(--accent-cyan);
  animation: spin-pulse 1s linear infinite;
}

@keyframes spin-pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.incident-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding-right: 4px;
  transition: opacity 0.2s ease;
}

.incident-list.is-loading {
  opacity: 0.5;
  pointer-events: none;
}

.incident-list::-webkit-scrollbar {
  width: 6px;
}

.incident-list::-webkit-scrollbar-track {
  background: transparent;
}

.incident-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 999px;
}

.incident-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Map Section */
.map-section {
  padding: 0;
  overflow: hidden;
}

.map-container,
.map-view {
  width: 100%;
  height: 100%;
}

.three-d-view {
  display: flex;
}

.three-d-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  text-align: center;
  padding: 32px;
}

.three-d-placeholder h2 {
  font-size: 24px;
  margin: 0;
  color: var(--text-primary);
}

.three-d-placeholder p {
  margin: 8px 0;
  font-size: 14px;
}

.terrain-icon {
  font-size: 40px !important;
  margin-top: 20px !important;
}

.coming-soon {
  margin-top: 20px !important;
}

/* Detail Panel (Right Slide) */
.detail-panel {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0;
  overflow: hidden;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  gap: 12px;
  flex-shrink: 0;
}

.header-top {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.incident-type-icon {
  font-size: 24px;
}

.detail-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-content::-webkit-scrollbar {
  width: 0;
}

.detail-content::-webkit-scrollbar-track {
  background: transparent;
}

.detail-content::-webkit-scrollbar-thumb {
  background: transparent;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.detail-item label {
  color: var(--text-secondary);
  font-weight: 500;
  text-transform: uppercase;
  font-size: 10px;
  letter-spacing: 0.1em;
}

.detail-item .value {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 14px;
}

.location-value {
  font-size: 14px;
  color: var(--accent-cyan);
  font-weight: 600;
}

.threat-score {
  color: #ff6b6b;
  font-size: 20px;
  font-weight: 700;
}

.metric-value {
  color: var(--accent-cyan);
  font-size: 14px;
  font-weight: 600;
}

.trend-value {
  color: #fbbf24;
  font-weight: 700;
  font-size: 14px;
}

.forecast-value {
  color: #10b981;
  font-weight: 700;
  font-size: 14px;
}

.divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 8px 0;
}

.summary-section {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-section label {
  color: var(--text-secondary);
  font-weight: 500;
  text-transform: uppercase;
  font-size: 10px;
  letter-spacing: 0.1em;
}

.summary-section p {
  margin: 0;
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.5;
  font-weight: 400;
}

.status-badge {
  display: inline-flex;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  width: fit-content;
}

.status-badge.active {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.status-badge.monitoring {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.status-badge.resolved {
  background: rgba(107, 114, 128, 0.2);
  color: #6b7280;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 20px;
  transition: all 200ms ease;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  flex-shrink: 0;
}

.close-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.1);
}

/* Insights Panel */
.insights-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.insights-panel h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
}

.insights-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.insight-item {
  background: var(--critical-surface);
  border: 1px solid var(--critical-border);
  border-radius: 8px;
  padding: 8px;
  font-size: 12px;
}

.action {
  font-weight: 600;
  color: var(--critical);
  margin-bottom: 4px;
}

.meta {
  color: var(--text-secondary);
}

.no-insights {
  color: var(--text-secondary);
  font-size: 12px;
  margin: 0;
}

/* Metrics Footer */
.metrics-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  height: 80px;
}

.metric {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}

.label {
  font-size: 12px;
  color: #b0b9c1;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.value {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
}

/* Slide Right Animation */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 300ms ease;
}

.slide-right-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

/* Slide Up Animation */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 300ms ease;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* Fade Animation */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 300ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Mobile Detail Modal (Hidden on desktop) */
.mobile-detail-overlay {
  display: none;
}

.mobile-detail-modal {
  display: none;
}

/* ===== SORT CONTROLS & HEADER ===== */
.incidents-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.live-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(255, 59, 48, 0.15);
  color: #ff3b30;
  border: 1px solid rgba(255, 59, 48, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.3s ease;
}

.live-badge.connected {
  background: rgba(52, 199, 89, 0.15);
  color: #34c759;
  border: 1px solid rgba(52, 199, 89, 0.3);
}

.incidents-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-controls {
  display: flex;
  gap: 8px;
}

.sort-dropdown {
  background: rgba(20, 30, 48, 0.5);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(30, 144, 255, 0.2);
  color: var(--accent-cyan);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 200ms ease;
}

.sort-dropdown:hover {
  border-color: var(--accent-cyan);
  background: rgba(20, 30, 48, 0.7);
}

.sort-dropdown option {
  background: #0f172a;
  color: #ffffff;
}

/* ===== PAGINATION CONTROLS ===== */
.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(30, 144, 255, 0.2);
}

.page-info {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-cyan);
  white-space: nowrap;
}

.pagination-btn {
  flex: 1;
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(30, 144, 255, 0.15), rgba(14, 165, 233, 0.15));
  border: 1px solid rgba(30, 144, 255, 0.3);
  border-radius: 6px;
  color: var(--accent-cyan);
  font-weight: 600;
  font-size: 11px;
  cursor: pointer;
  transition: all 150ms ease;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.pagination-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(30, 144, 255, 0.25), rgba(14, 165, 233, 0.25));
  border-color: var(--accent-cyan);
  box-shadow: 0 0 12px rgba(30, 144, 255, 0.25);
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.load-more-btn {
  width: 100%;
  padding: 12px;
  margin-top: 8px;
  background: linear-gradient(135deg, rgba(30, 144, 255, 0.2), rgba(14, 165, 233, 0.2));
  border: 1.5px solid var(--accent-cyan);
  border-radius: 8px;
  color: var(--accent-cyan);
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  transition: all 200ms ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.load-more-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(30, 144, 255, 0.3), rgba(14, 165, 233, 0.3));
  box-shadow: 0 0 16px rgba(30, 144, 255, 0.3);
  transform: translateY(-2px);
}

.load-more-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ===== RESPONSIVE DESIGN ===== */

/* Desktop XL (1600px+) */
@media (min-width: 1600px) {
  .content-grid {
    grid-template-columns: 340px 1fr 320px;
  }

  .incidents-panel h3 {
    font-size: 16px;
  }

  .card-body {
    gap: 6px;
  }

  .value {
    font-size: 20px;
  }

  .metrics-section {
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
  }
}

/* Desktop Large (1200px - 1599px) */
@media (max-width: 1599px) and (min-width: 1200px) {
  .content-grid {
    grid-template-columns: 300px 1fr 280px;
  }

  .content-grid.detail-open {
    grid-template-columns: 280px 1fr 300px;
  }

  .metrics-section {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Laptop/Tablet (1024px - 1199px) */
@media (max-width: 1199px) {
  .dashboard {
    padding: 12px;
    gap: 12px;
  }

  .content-grid {
    grid-template-columns: 270px 1fr 300px;
    gap: 12px;
  }

  .content-grid.detail-open {
    grid-template-columns: 250px 1fr 320px;
  }

  .glass-panel {
    padding: 12px;
  }

  .incidents-panel h3 {
    font-size: 13px;
  }

  .incident-list {
    gap: 6px;
  }

  .detail-panel {
    width: 320px;
    max-height: calc(100vh - 200px);
    overflow-y: auto;
  }

  /* Commented out to prevent overriding IncidentCard's internal responsive styles:
  .incident-card {
    min-height: 120px;
    padding: 10px;
    gap: 8px;
  }
  */

  .card-header {
    gap: 4px;
    padding-bottom: 6px;
  }

  .icon {
    font-size: 20px;
  }

  .card-body {
    gap: 3px;
  }

  .label {
    font-size: 8px;
  }

  .value {
    font-size: 12px;
  }

  .action-btn {
    font-size: 11px;
    padding: 6px 10px;
  }

  .three-d-placeholder {
    padding: 20px;
  }

  .three-d-placeholder h2 {
    font-size: 18px;
  }

  .three-d-placeholder p {
    font-size: 12px;
  }

  .metrics-section {
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    height: auto;
    min-height: 70px;
  }

  .metric {
    gap: 2px;
  }

  .label {
    font-size: 11px;
  }

  .value {
    font-size: 16px;
  }

  .insights-panel {
    width: 300px;
  }

  .insights-panel h3 {
    font-size: 13px;
    margin: 0 0 8px 0;
  }

  .insight-item {
    padding: 8px;
    font-size: 12px;
    line-height: 1.4;
  }

  .action {
    margin-bottom: 3px;
    font-weight: 600;
  }

  .meta {
    font-size: 11px;
    color: var(--text-secondary);
  }

  .detail-item {
    padding: 8px 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .detail-item label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-secondary);
    letter-spacing: 0.5px;
  }

  .detail-item .value,
  .detail-item .location-value,
  .detail-item .status-badge,
  .detail-item .threat-score,
  .detail-item .metric-value,
  .detail-item .trend-value,
  .detail-item .forecast-value {
    font-size: 13px;
    font-weight: 600;
    color: var(--accent-cyan);
  }

  .summary-section {
    padding: 8px 0;
  }

  .summary-section p {
    font-size: 12px;
    line-height: 1.5;
    color: var(--text-primary);
  }
}

/* iPad/Landscape (768px - 1023px) */
@media (max-width: 1023px) {
  .dashboard {
    padding: 10px;
    gap: 10px;
  }

  .content-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
  }

  .content-grid.detail-open {
    grid-template-columns: 1fr;
  }

  .incidents-panel,
  .map-section,
  .detail-panel,
  .insights-panel {
    min-height: 300px;
  }

  .detail-panel {
    width: 100%;
    position: static;
    border-radius: 8px;
  }

  .glass-panel {
    padding: 12px;
    border-radius: 10px;
  }

  .incidents-panel h3 {
    font-size: 13px;
  }

  .incident-list {
    gap: 10px;
  }

  /* Commented out to prevent overriding IncidentCard's internal responsive styles:
  .incident-card {
    min-height: 150px;
    padding: 12px;
    gap: 10px;
  }
  */

  .card-header {
    gap: 6px;
    padding-bottom: 8px;
  }

  .header-top {
    gap: 10px;
  }

  .header-top h3 {
    font-size: 12px;
    line-height: 1.2;
  }

  .icon {
    font-size: 20px;
  }

  .location {
    font-size: 11px;
  }

  .card-body {
    gap: 4px;
  }

  .metric-row {
    line-height: 1.3;
  }

  .label {
    font-size: 9px;
  }

  .value {
    font-size: 13px;
  }

  .action-btn {
    font-size: 11px;
    padding: 7px 11px;
  }
}

/* Mobile Large (480px - 767px) */
@media (max-width: 767px) {
  .dashboard {
    padding: 8px;
    gap: 8px;
    height: auto;
    min-height: 100vh;
  }

  .content-grid {
    grid-template-columns: 1fr;
    gap: 10px;
    min-height: auto;
    flex: none;
  }

  .glass-panel {
    padding: 12px;
    border-radius: 8px;
  }

  /* Incidents Panel - Scrollable */
  .incidents-panel {
    max-height: 35vh;
    min-height: auto;
    order: 1;
  }

  .incidents-panel h3 {
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 8px;
  }

  .incident-list {
    gap: 10px;
    overflow-y: auto;
    max-height: calc(35vh - 40px);
  }

  /* Commented out to prevent overriding IncidentCard's internal responsive styles:
  .incident-card {
    min-height: auto;
    padding: 12px;
    gap: 8px;
    word-wrap: break-word;
  }
  */

  .card-header {
    gap: 8px;
    padding-bottom: 8px;
    flex-wrap: wrap;
  }

  .header-top {
    gap: 8px;
    flex: 1 1 100%;
  }

  .header-top h3 {
    font-size: 13px;
    line-height: 1.3;
    margin: 0;
  }

  .icon {
    font-size: 20px;
    flex-shrink: 0;
  }

  .location {
    font-size: 11px;
    color: var(--accent-cyan);
    flex: 1 1 100%;
  }

  .card-body {
    gap: 6px;
    width: 100%;
  }

  .metric-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .metric-row:last-child {
    border-bottom: none;
  }

  .label {
    font-size: 9px;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }

  .value {
    font-size: 13px;
    font-weight: 700;
    color: var(--accent-cyan);
    text-align: right;
  }

  .action-btn {
    font-size: 11px;
    padding: 8px 12px;
    margin-top: 8px;
    width: 100%;
  }

  /* Map Section */
  .map-section {
    min-height: 35vh;
    order: 2;
  }

  .map-container {
    height: 100%;
  }

  /* Detail Panel */
  .detail-panel {
    width: 100%;
    position: static;
    order: 3;
    max-height: auto;
  }

  .detail-header {
    padding: 12px;
    gap: 8px;
  }

  .detail-header h3 {
    font-size: 15px;
    margin: 0;
  }

  .detail-content {
    padding: 12px;
    gap: 10px;
  }

  .detail-item {
    padding: 8px 0;
    gap: 4px;
  }

  .detail-item label {
    font-size: 9px;
    font-weight: 600;
  }

  .detail-item .value,
  .detail-item .location-value,
  .detail-item .threat-score,
  .detail-item .metric-value,
  .detail-item .trend-value,
  .detail-item .forecast-value {
    font-size: 14px;
    font-weight: 700;
  }

  .summary-section {
    padding: 10px 0;
  }

  .summary-section p {
    font-size: 12px;
    line-height: 1.5;
  }

  /* Insights Panel */
  .insights-panel {
    min-height: auto;
    order: 4;
    max-height: 30vh;
    overflow-y: auto;
  }

  .insights-panel h3 {
    font-size: 13px;
    margin: 0 0 8px 0;
    font-weight: 600;
  }

  .insight-item {
    padding: 8px;
    font-size: 12px;
    line-height: 1.4;
  }

  .action {
    margin-bottom: 4px;
    font-weight: 600;
  }

  .meta {
    font-size: 11px;
    color: var(--text-secondary);
  }

  /* Metrics Section */
  .metrics-section {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    height: auto;
    padding: 12px;
    order: 5;
  }

  .metric {
    padding: 10px;
    gap: 4px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 6px;
  }

  .metric .label {
    font-size: 10px;
  }

  .metric .value {
    font-size: 15px;
  }

  .three-d-placeholder {
    padding: 16px;
  }

  .three-d-placeholder h2 {
    font-size: 18px;
    margin-bottom: 12px;
  }

  .three-d-placeholder p {
    font-size: 12px;
    margin: 6px 0;
  }

  .terrain-icon {
    font-size: 36px;
    margin-top: 12px;
  }

  /* Mobile Detail Modal - Show on mobile */
  .detail-panel {
    display: none;
  }

  .mobile-detail-overlay {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    z-index: 999;
  }

  .mobile-detail-modal {
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 90vw;
    max-width: 500px;
    max-height: 80vh;
    background: linear-gradient(180deg, var(--header-bg-start), var(--header-bg-end));
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 0;
    gap: 0;
    z-index: 1000;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    overflow: hidden;
  }

  .mobile-detail-modal .detail-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.2);
    gap: 8px;
    flex-shrink: 0;
  }

  .mobile-detail-modal .detail-header .header-top {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
    min-width: 0;
  }

  .mobile-detail-modal .detail-header h3 {
    font-size: 16px;
    font-weight: 700;
    margin: 0;
    color: #ffffff;
    word-break: break-word;
  }

  .mobile-detail-modal .close-btn {
    background: rgba(30, 144, 255, 0.15);
    border: 1px solid var(--accent-cyan);
    color: var(--accent-cyan);
    width: 32px;
    height: 32px;
    border-radius: 6px;
    font-size: 18px;
    cursor: pointer;
    transition: all 0.2s ease;
    flex-shrink: 0;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .mobile-detail-modal .close-btn:active {
    background: rgba(30, 144, 255, 0.25);
  }

  .mobile-detail-modal .detail-content {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    gap: 12px;
    display: flex;
    flex-direction: column;
  }

  .mobile-detail-modal .detail-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .mobile-detail-modal .detail-item label {
    font-size: 9px;
    font-weight: 700;
    color: var(--text-secondary);
    letter-spacing: 0.3px;
    text-transform: uppercase;
  }

  .mobile-detail-modal .detail-item .value,
  .mobile-detail-modal .detail-item .location-value,
  .mobile-detail-modal .detail-item .threat-score,
  .mobile-detail-modal .detail-item .metric-value,
  .mobile-detail-modal .detail-item .trend-value,
  .mobile-detail-modal .detail-item .forecast-value {
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
  }

  .mobile-detail-modal .divider {
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
    margin: 4px 0;
  }

  .mobile-detail-modal .summary-section {
    padding-top: 8px;
  }

  .mobile-detail-modal .summary-section label {
    font-size: 9px;
    font-weight: 700;
    color: var(--text-secondary);
    letter-spacing: 0.3px;
    text-transform: uppercase;
    display: block;
    margin-bottom: 8px;
  }

  .mobile-detail-modal .summary-section p {
    font-size: 13px;
    line-height: 1.6;
    color: var(--text-secondary);
    margin: 0;
  }
}

/* Mobile Small (320px - 479px) */
@media (max-width: 479px) {
  .dashboard {
    padding: 6px;
    gap: 6px;
    height: auto;
    min-height: 100vh;
  }

  .content-grid {
    grid-template-columns: 1fr;
    gap: 8px;
    min-height: auto;
    flex: none;
  }

  .glass-panel {
    padding: 10px;
    border-radius: 6px;
  }

  /* Incidents Panel - Compact & Scrollable */
  .incidents-panel {
      max-height: 50vh;
    min-height: auto;
    order: 1;
    padding: 10px;
  }

  .incidents-panel h3 {
    font-size: 12px;
    font-weight: 600;
    margin: 0 0 8px 0;
  }

  .incidents-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .sort-dropdown {
    font-size: 10px;
    padding: 4px 8px;
    width: 100%;
  }

  .incident-list {
    gap: 8px;
    overflow-y: auto;
    padding-right: 2px;
    display: flex;
    flex-direction: column;
  }

  .load-more-btn {
    font-size: 10px;
    padding: 10px;
  }

  /* Commented out to prevent overriding IncidentCard's internal responsive styles:
  .incident-card {
    min-height: auto;
    padding: 8px;
    gap: 6px;
    border-radius: 6px;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }
  */

  .card-header {
    gap: 6px;
    padding-bottom: 6px;
    align-items: flex-start;
  }

  .header-top {
    gap: 6px;
    flex-wrap: wrap;
    align-items: flex-start;
    width: 100%;
  }

  .header-top h3 {
    font-size: 12px;
    line-height: 1.3;
    margin: 0;
    flex: 1 1 auto;
    min-width: 0;
    word-break: break-word;
  }

  .icon {
    font-size: 18px;
    flex-shrink: 0;
    line-height: 1;
    margin-top: 2px;
  }

  .location {
    font-size: 10px;
    color: var(--accent-cyan);
    font-weight: 600;
    flex: 1 1 100%;
  }

  .card-body {
    gap: 6px;
    width: 100%;
  }

  .metric-row {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 4px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .metric-row:last-child {
    border-bottom: none;
  }

  .label {
    font-size: 8px;
    font-weight: 700;
    color: var(--text-secondary);
    letter-spacing: 0.3px;
    text-transform: uppercase;
  }

  .value {
    font-size: 11px;
    font-weight: 700;
    color: var(--accent-cyan);
  }

  .value.trend-up {
    color: #10b981;
  }

  .action-btn {
    font-size: 10px;
    padding: 6px 10px;
    margin-top: 6px;
    width: 100%;
    border-radius: 4px;
  }

  /* Map Section */
  .map-section {
    min-height: 30vh;
    order: 2;
    padding: 0;
  }

  .map-container {
    height: 100%;
    border-radius: 6px;
    overflow: hidden;
  }

  .three-d-placeholder {
    padding: 12px;
  }

  .three-d-placeholder h2 {
    font-size: 14px;
    margin: 0 0 8px 0;
  }

  .three-d-placeholder p {
    font-size: 10px;
    margin: 4px 0;
  }

  .terrain-icon {
    font-size: 32px;
    margin-top: 8px;
  }

  .coming-soon {
    margin-top: 8px;
    font-size: 10px;
  }

  /* Detail Panel */
  .detail-panel {
    width: 100%;
    position: static;
    order: 3;
    max-height: auto;
    padding: 0;
  }

  .detail-header {
    padding: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .detail-header h3 {
    font-size: 13px;
    margin: 0;
    flex: 1;
  }

  .close-btn {
    width: 24px;
    height: 24px;
    font-size: 16px;
  }

  .detail-content {
    padding: 10px;
    gap: 8px;
    max-height: 40vh;
    overflow-y: auto;
  }

  .detail-item {
    padding: 6px 0;
    gap: 2px;
  }

  .detail-item label {
    font-size: 8px;
    font-weight: 600;
    letter-spacing: 0.2px;
  }

  .detail-item .value,
  .detail-item .location-value,
  .detail-item .threat-score,
  .detail-item .metric-value,
  .detail-item .trend-value,
  .detail-item .forecast-value {
    font-size: 12px;
    font-weight: 700;
  }

  .divider {
    margin: 4px 0;
  }

  .summary-section {
    padding: 8px 0;
  }

  .summary-section label {
    font-size: 8px;
    font-weight: 600;
  }

  .summary-section p {
    font-size: 11px;
    line-height: 1.4;
    margin: 0;
  }

  /* Insights Panel */
  .insights-panel {
    min-height: auto;
    order: 4;
    max-height: 25vh;
    overflow-y: auto;
    padding: 10px;
  }

  .insights-panel h3 {
    font-size: 12px;
    margin: 0 0 6px 0;
    font-weight: 600;
  }

  .insights-list {
    gap: 6px;
  }

  .insight-item {
    padding: 6px;
    font-size: 10px;
    line-height: 1.3;
    border-radius: 4px;
  }

  .action {
    font-weight: 600;
    margin-bottom: 2px;
    font-size: 11px;
  }

  .meta {
    font-size: 9px;
    color: var(--text-secondary);
  }

  .no-insights {
    font-size: 11px;
  }

  /* Metrics Section */
  .metrics-section {
    grid-template-columns: 1fr;
    gap: 6px;
    height: auto;
    padding: 10px;
    order: 5;
  }

  .metric {
    padding: 8px;
    gap: 2px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.03);
  }

  .metric .label {
    font-size: 8px;
    font-weight: 700;
  }

  .metric .value {
    font-size: 13px;
    font-weight: 700;
  }

  /* Mobile Detail Modal - Show on mobile */
  .detail-panel {
    display: none;
  }

  .mobile-detail-overlay {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    z-index: 999;
  }

  .mobile-detail-modal {
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 90vw;
    max-width: 450px;
    max-height: 75vh;
    background: linear-gradient(180deg, var(--header-bg-start), var(--header-bg-end));
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    padding: 0;
    gap: 0;
    z-index: 1000;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    overflow: hidden;
  }

  .mobile-detail-modal .detail-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.2);
    gap: 8px;
    flex-shrink: 0;
  }

  .mobile-detail-modal .detail-header .header-top {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
  }

  .mobile-detail-modal .detail-header h3 {
    font-size: 14px;
    font-weight: 700;
    margin: 0;
    color: #ffffff;
    word-break: break-word;
    line-height: 1.3;
  }

  .mobile-detail-modal .detail-header .incident-type-icon {
    font-size: 20px;
    flex-shrink: 0;
  }

  .mobile-detail-modal .close-btn {
    background: rgba(30, 144, 255, 0.15);
    border: 1px solid var(--accent-cyan);
    color: var(--accent-cyan);
    width: 28px;
    height: 28px;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.2s ease;
    flex-shrink: 0;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .mobile-detail-modal .close-btn:active {
    background: rgba(30, 144, 255, 0.25);
  }

  .mobile-detail-modal .detail-content {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    gap: 10px;
    display: flex;
    flex-direction: column;
  }

  .mobile-detail-modal .detail-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .mobile-detail-modal .detail-item label {
    font-size: 8px;
    font-weight: 700;
    color: var(--text-secondary);
    letter-spacing: 0.2px;
    text-transform: uppercase;
  }

  .mobile-detail-modal .detail-item .value,
  .mobile-detail-modal .detail-item .location-value,
  .mobile-detail-modal .detail-item .threat-score,
  .mobile-detail-modal .detail-item .metric-value,
  .mobile-detail-modal .detail-item .trend-value,
  .mobile-detail-modal .detail-item .forecast-value {
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
  }

  .mobile-detail-modal .status-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    background: rgba(255, 255, 255, 0.1);
  }

  .mobile-detail-modal .divider {
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
    margin: 2px 0;
  }

  .mobile-detail-modal .summary-section {
    padding-top: 6px;
  }

  .mobile-detail-modal .summary-section label {
    font-size: 8px;
    font-weight: 700;
    color: var(--text-secondary);
    letter-spacing: 0.2px;
    text-transform: uppercase;
    display: block;
    margin-bottom: 6px;
  }

  .mobile-detail-modal .summary-section p {
    font-size: 12px;
    line-height: 1.5;
    color: var(--text-secondary);
    margin: 0;
  }
}
</style>
