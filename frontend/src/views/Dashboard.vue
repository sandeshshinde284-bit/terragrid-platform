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

          <!-- Quick Search Bar -->
          <div class="sidebar-search-section">
            <div class="sidebar-search-box">
              <span class="search-icon">🔍</span>
              <input
                v-model="dashboardSearchQuery"
                type="text"
                placeholder="Search city, hazard, or country..."
                class="sidebar-search-input"
              />
              <button
                v-if="dashboardSearchQuery"
                class="search-clear-btn"
                @click="dashboardSearchQuery = ''"
                aria-label="Clear search"
              >✕</button>
            </div>
          </div>
          
          <!-- Country Filter Buttons -->
          <div class="country-filter-section">
            <div class="filter-label">Filter by Country:</div>
            <select v-model="selectedCountry" class="country-dropdown">
              <option :value="null">All Countries</option>
              <option v-for="country in availableCountries" :key="country" :value="country">
                {{ getCountryName(country) }}
              </option>
            </select>
          </div>

          <!-- Event Type & Sort Controls -->
          <div class="filter-controls">
            <select v-model="selectedEventType" class="event-type-dropdown">
              <option value="">All Event Types</option>
              <option value="earthquake">🔴 Earthquake</option>
              <option value="flood">🌊 Flood</option>
              <option value="storm">⚡ Storm</option>
              <option value="fire">🔥 Fire</option>
              <option value="volcano">🌋 Volcano</option>
              <option value="weather">🌤️ Weather</option>
            </select>
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
          <div class="map-view">
            <MapComponent :incidents="filteredIncidents" :selectedCountry="selectedCountry" />
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
            
            <!-- 1. OPERATIONAL ACTION PLAN -->
            <div class="ai-decision-plan">
              <div class="ai-plan-header">
                <span class="ai-pulse-dot"></span>
                <label class="ai-plan-title">⚡ Operational Action Plan</label>
                <span class="ai-engine-chip">Live Triage</span>
              </div>
              
              <!-- High-Tech Tactical Loading State with Dynamic Stepper & Shimmer Skeletons -->
              <div v-if="isLoadingInsights" class="ai-tactical-loading">
                <div class="loading-radar-header">
                  <div class="radar-ping-ring">
                    <span class="radar-dot"></span>
                  </div>
                  <div class="loading-telemetry-text">
                    <span class="loading-phase-tag">AI COGNITIVE PROCESSING ACTIVE</span>
                    <strong class="cycling-step-text">{{ currentLoadingPhaseText }}</strong>
                  </div>
                </div>

                <div class="tactical-progress-track">
                  <div class="tactical-scan-laser"></div>
                </div>

                <!-- Ghost Skeleton Micro-Cards -->
                <div class="skeleton-action-cards">
                  <div class="skeleton-tag shimmer"></div>
                  <div class="skeleton-card shimmer" v-for="n in 3" :key="n">
                    <div class="sk-num">0{{ n }}</div>
                    <div class="sk-lines">
                      <div class="sk-line full"></div>
                      <div class="sk-line half"></div>
                    </div>
                  </div>
                  <div class="skeleton-evac shimmer"></div>
                </div>
              </div>
              
              <div v-else-if="aiPlan" class="ai-plan-content">
                <div class="country-context-tag">{{ formatTacticalText(aiPlan.country_context) }}</div>
                
                <div class="tactical-group">
                  <span class="group-title">Immediate Action Items:</span>
                  <div class="tactical-action-cards">
                    <div v-for="(act, idx) in aiPlan.immediate_actions" :key="idx" class="tactical-action-card">
                      <span class="action-num">0{{ idx + 1 }}</span>
                      <span class="action-text">{{ formatTacticalText(act) }}</span>
                    </div>
                  </div>
                </div>

                <div class="tactical-group" v-if="aiPlan.evacuation_guidance">
                  <span class="group-title">🛣️ Evacuation Routing:</span>
                  <div class="evacuation-card">
                    <p class="evac-text">{{ formatTacticalText(aiPlan.evacuation_guidance) }}</p>
                  </div>
                </div>

                <div class="tactical-group" v-if="aiPlan.resource_allocation && aiPlan.resource_allocation.length">
                  <span class="group-title">🚒 Resource Deployment:</span>
                  <div class="resource-chip-grid">
                    <div v-for="(res, rIdx) in aiPlan.resource_allocation" :key="rIdx" class="resource-chip">
                      <strong class="res-label">{{ res.resource }}:</strong>
                      <span class="res-qty">{{ res.quantity }}</span>
                      <span class="res-status" :class="res.status ? res.status.toLowerCase() : ''">{{ res.status }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 2. INCIDENT PROFILE (Boxed & Padded) -->
            <div class="profile-card glass-subpanel">
              <div class="profile-item">
                <span class="card-section-label">{{ $t('incidents.location') }}</span>
                <div class="profile-location">📍 {{ selectedIncidentData.location }}</div>
              </div>

              <div class="profile-split-row">
                <div class="profile-item">
                  <span class="card-section-label">{{ $t('incidents.status') }}</span>
                  <div class="status-badge" :class="selectedIncidentData.status">
                    {{ selectedIncidentData.status.toUpperCase() }}
                  </div>
                </div>
                <div class="profile-item align-right">
                  <span class="card-section-label">{{ $t('incidents.threatScore') }}</span>
                  <div class="threat-score-pill tooltip-container">
                    <span class="threat-score-num">{{ getThreatScore(selectedIncidentData) }}</span>
                    <span class="threat-score-max">/100</span>

                    <!-- Floating Tactical Tooltip -->
                    <div class="tactical-tooltip">
                      <div class="tooltip-header">
                        <span class="tooltip-dot" :class="getSeverityClass(getThreatScore(selectedIncidentData))"></span>
                        <strong>THREAT LEVEL: {{ getThreatScore(selectedIncidentData) }}/100</strong>
                      </div>
                      <p class="tooltip-desc">{{ getThreatTooltipText(getThreatScore(selectedIncidentData)) }}</p>
                      <div class="tooltip-factors">
                        <div class="factor-row"><span>💨 Atmospheric Risk:</span> <strong>Active</strong></div>
                        <div class="factor-row"><span>👥 Population Density:</span> <strong>{{ selectedIncidentData.affectedPopulation ? selectedIncidentData.affectedPopulation.toLocaleString() : 'Estimating' }}</strong></div>
                        <div class="factor-row"><span>📈 Perimeter Growth:</span> <strong>+{{ selectedIncidentData.trend?.toFixed(1) || '0.0' }} km²/h</strong></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. COMPACT STATS GRID -->
            <div class="metadata-grid glass-subpanel">
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
            </div>

            <!-- 4. SITUATION BRIEFING (Boxed & Padded) -->
            <div class="summary-card glass-subpanel">
              <span class="card-section-label">SITUATION SUMMARY</span>
              <p class="summary-text">
                {{ aiPlan?.severity_assessment || `${formatIncidentType(selectedIncidentData.type, selectedIncidentData.location)} activity near ${selectedIncidentData.location} is currently ${selectedIncidentData.status} and remains under active monitoring.` }}
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
            <!-- 1. AI TACTICAL RESPONSE (Mobile) -->
            <!-- 1. OPERATIONAL ACTION PLAN -->
            <div class="ai-decision-plan">
              <div class="ai-plan-header">
                <span class="ai-pulse-dot"></span>
                <label class="ai-plan-title">⚡ Operational Action Plan</label>
                <span class="ai-engine-chip">Live Triage</span>
              </div>
              
              <!-- High-Tech Tactical Loading State with Dynamic Stepper & Shimmer Skeletons -->
              <div v-if="isLoadingInsights" class="ai-tactical-loading">
                <div class="loading-radar-header">
                  <div class="radar-ping-ring">
                    <span class="radar-dot"></span>
                  </div>
                  <div class="loading-telemetry-text">
                    <span class="loading-phase-tag">AI COGNITIVE PROCESSING ACTIVE</span>
                    <strong class="cycling-step-text">{{ currentLoadingPhaseText }}</strong>
                  </div>
                </div>

                <div class="tactical-progress-track">
                  <div class="tactical-scan-laser"></div>
                </div>

                <!-- Ghost Skeleton Micro-Cards -->
                <div class="skeleton-action-cards">
                  <div class="skeleton-tag shimmer"></div>
                  <div class="skeleton-card shimmer" v-for="n in 3" :key="n">
                    <div class="sk-num">0{{ n }}</div>
                    <div class="sk-lines">
                      <div class="sk-line full"></div>
                      <div class="sk-line half"></div>
                    </div>
                  </div>
                  <div class="skeleton-evac shimmer"></div>
                </div>
              </div>
              
              <div v-else-if="aiPlan" class="ai-plan-content">
                <div class="country-context-tag">{{ formatTacticalText(aiPlan.country_context) }}</div>
                
                <div class="tactical-group">
                  <span class="group-title">Immediate Action Items:</span>
                  <div class="tactical-action-cards">
                    <div v-for="(act, idx) in aiPlan.immediate_actions" :key="idx" class="tactical-action-card">
                      <span class="action-num">0{{ idx + 1 }}</span>
                      <span class="action-text">{{ formatTacticalText(act) }}</span>
                    </div>
                  </div>
                </div>

                <div class="tactical-group" v-if="aiPlan.evacuation_guidance">
                  <span class="group-title">🛣️ Evacuation Routing:</span>
                  <div class="evacuation-card">
                    <p class="evac-text">{{ formatTacticalText(aiPlan.evacuation_guidance) }}</p>
                  </div>
                </div>

                <div class="tactical-group" v-if="aiPlan.resource_allocation && aiPlan.resource_allocation.length">
                  <span class="group-title">🚒 Resource Deployment:</span>
                  <div class="resource-chip-grid">
                    <div v-for="(res, rIdx) in aiPlan.resource_allocation" :key="rIdx" class="resource-chip">
                      <strong class="res-label">{{ res.resource }}:</strong>
                      <span class="res-qty">{{ res.quantity }}</span>
                      <span class="res-status" :class="res.status ? res.status.toLowerCase() : ''">{{ res.status }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 2. INCIDENT PROFILE (Mobile) -->
            <div class="profile-card glass-subpanel">
              <div class="profile-item">
                <span class="card-section-label">{{ $t('incidents.location') }}</span>
                <div class="profile-location">📍 {{ selectedIncidentData.location }}</div>
              </div>

              <div class="profile-split-row">
                <div class="profile-item">
                  <span class="card-section-label">{{ $t('incidents.status') }}</span>
                  <div class="status-badge" :class="selectedIncidentData.status">
                    {{ selectedIncidentData.status.toUpperCase() }}
                  </div>
                </div>
                <div class="profile-item align-right">
                  <span class="card-section-label">{{ $t('incidents.threatScore') }}</span>
                  <div class="threat-score-pill tooltip-container">
                    <span class="threat-score-num">{{ getThreatScore(selectedIncidentData) }}</span>
                    <span class="threat-score-max">/100</span>

                    <!-- Floating Tactical Tooltip -->
                    <div class="tactical-tooltip">
                      <div class="tooltip-header">
                        <span class="tooltip-dot" :class="getSeverityClass(getThreatScore(selectedIncidentData))"></span>
                        <strong>THREAT LEVEL: {{ getThreatScore(selectedIncidentData) }}/100</strong>
                      </div>
                      <p class="tooltip-desc">{{ getThreatTooltipText(getThreatScore(selectedIncidentData)) }}</p>
                      <div class="tooltip-factors">
                        <div class="factor-row"><span>💨 Atmospheric Risk:</span> <strong>Active</strong></div>
                        <div class="factor-row"><span>👥 Population Density:</span> <strong>{{ selectedIncidentData.affectedPopulation ? selectedIncidentData.affectedPopulation.toLocaleString() : 'Estimating' }}</strong></div>
                        <div class="factor-row"><span>📈 Perimeter Growth:</span> <strong>+{{ selectedIncidentData.trend?.toFixed(1) || '0.0' }} km²/h</strong></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. COMPACT STATS GRID (Mobile) -->
            <div class="metadata-grid glass-subpanel">
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
            </div>

            <!-- 4. SITUATION BRIEFING (Mobile) -->
            <div class="summary-card glass-subpanel">
              <span class="card-section-label">{{ $t('common.details') }}</span>
              <p class="summary-text">
                {{ formatIncidentType(selectedIncidentData.type) }} activity near
                {{ selectedIncidentData.location }} is currently
                {{ selectedIncidentData.status }} and remains under active monitoring.
              </p>
            </div>
          </div>
        </div>
      </transition>

      <!-- Right: AI Insights (Default view when no incident is selected) -->
      <aside v-if="!selectedIncidentData" class="insights-panel glass-panel">
        <div class="insights-panel-header">
          <h3>🤖 {{ $t('dashboard.aiInsights') }}</h3>
          <span class="ai-live-badge">REAL-TIME</span>
        </div>

        <!-- Global Situation Assessment Summary -->
        <div class="ai-overview-card glass-subpanel">
          <div class="overview-title">GLOBAL SITUATION ASSESSMENT</div>
          <p class="overview-text">
            Autonomous threat detection is actively monitoring 
            <strong style="color: #38bdf8;">{{ filteredIncidents.length }} active hazards</strong>. 
            Prioritizing emergency response for high-severity clusters below.
          </p>
        </div>

        <div class="insights-subheading">CRITICAL PRIORITY ACTIONS:</div>

        <div v-if="liveCriticalInsights.length" class="insights-list">
          <div 
            v-for="insight in liveCriticalInsights" 
            :key="insight.id" 
            class="insight-item-interactive glass-subpanel"
            @click="expandIncident(insight.incidentId)"
            title="Click to open tactical response plan"
          >
            <div class="insight-top">
              <span class="insight-type-tag">{{ getIncidentIcon(insight.type) }} {{ insight.type.toUpperCase() }}</span>
              <span class="insight-score" :class="getSeverityClass(insight.threatScore)">
                {{ insight.threatScore }}/100
              </span>
            </div>
            <div class="insight-action">{{ insight.action }}</div>
            <div class="insight-meta">
              <span>👥 {{ insight.estimatedAffected.toLocaleString() }} at risk</span>
              <span class="insight-inspect">Inspect Plan →</span>
            </div>
          </div>
        </div>
        <p v-else class="no-insights">No critical priority threats detected.</p>
      </aside>
    </div>

    <!-- Bottom: Metrics & Live Operational Telemetry Bar -->
    <footer class="metrics-section glass-panel">
      <!-- Left: Macro Stats -->
      <div class="metrics-group">
        <div class="metric">
          <span class="label">{{ $t('dashboard.totalAffectedArea') }}</span>
          <span class="value">{{ totalAffectedArea.toFixed(1) }} km²</span>
        </div>
        <div class="metric">
          <span class="label">{{ $t('dashboard.totalPopulation') }}</span>
          <span class="value">{{ totalPopulation.toLocaleString() }}</span>
        </div>
        <div class="metric">
          <span class="label">{{ $t('dashboard.activeIncidentsCount') }}</span>
          <span class="value">{{ activeIncidentsCount }}</span>
        </div>
      </div>

      <!-- Right: Operational Emergency Telemetry -->
      <div class="operational-telemetry-hud">
        <!-- Option 1: Multi-Hazard Breakdown -->
        <div class="hazard-breakdown-group">
          <div class="hazard-pill" title="Active Wildfires">
            <span class="h-icon">🔥</span>
            <span class="h-name">Fires</span>
            <span class="h-count">{{ filteredHazardCounts.fire }}</span>
          </div>
          <div class="hazard-pill" title="Active Floods">
            <span class="h-icon">💧</span>
            <span class="h-name">Floods</span>
            <span class="h-count">{{ filteredHazardCounts.flood }}</span>
          </div>
          <div class="hazard-pill" title="Active Seismic / Earthquakes">
            <span class="h-icon">🌍</span>
            <span class="h-name">Seismic</span>
            <span class="h-count">{{ filteredHazardCounts.earthquake }}</span>
          </div>
          <div class="hazard-pill" title="Severe Storms">
            <span class="h-icon">🌀</span>
            <span class="h-name">Storms</span>
            <span class="h-count">{{ filteredHazardCounts.storm }}</span>
          </div>
        </div>

        <div class="telemetry-divider"></div>

        <!-- Option 2: Chronological Latest Signal -->
        <div v-if="latestIncident" class="latest-signal-pill" @click="expandIncident(latestIncident.id)" title="Click to inspect latest signal">
          <span class="pulse-beacon"></span>
          <span class="signal-tag">LATEST:</span>
          <span class="signal-location">{{ latestIncident.location }}</span>
          <span class="signal-time">{{ formatTimeAgo(latestIncident.detectionTime) }}</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Header from '@/components/organisms/Header.vue'
import IncidentCard from '@/components/molecules/IncidentCard.vue'
import MapComponent from '@/components/organisms/MapComponent.vue'
import { useAppStore } from '@/stores'
import { useEventsStore } from '@/stores'
import { useAlertsStore } from '@/stores'
import { useMockMode } from '@/composables/useMockMode'
import { useWebSocket } from '@/composables/useWebSocket'
import type { IncidentLevel1 } from '@/types'

const { t: $t } = useI18n()
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
const selectedCountry = ref<string | null>(null)
const selectedEventType = ref<string>('')
const dashboardSearchQuery = ref('')

const getThreatTooltipText = (score: number) => {
  if (score >= 80) return 'Severe hazard level. Imminent risk to civil population, primary transport arteries, and critical hospital infrastructure.'
  if (score >= 65) return 'Elevated hazard level. Rapid environmental expansion vector requiring shelter activation and first-responder mobilization.'
  if (score >= 50) return 'Moderate hazard level. Active environmental perimeter requiring continuous telemetry monitoring.'
  return 'Baseline hazard advisory. Minimal immediate risk to municipal boundaries.'
}

// Feature 6: Reactive AI Decision Support Plan
const aiPlan = ref<any | null>(null)
const isLoadingInsights = ref(false)

const loadingPhases = [
  '🛰️ Cross-referencing satellite perimeter with municipal boundary...',
  '💨 Ingesting real-time OpenWeather wind & atmospheric vectors...',
  '🏥 Evaluating hospital exposure & bridge choke-points...',
  '⚡ Synthesizing emergency operational action directives...'
]
const loadingPhaseIndex = ref(0)
const currentLoadingPhaseText = computed(() => loadingPhases[loadingPhaseIndex.value] || loadingPhases[0])
let loadingInterval: any = null

// Watch for incident selection to fetch Gemini AI Response Plan
watch(
  () => appStore.selectedIncident,
  async (newId) => {
    if (!newId) {
      aiPlan.value = null
      if (loadingInterval) clearInterval(loadingInterval)
      return
    }
    
    try {
      isLoadingInsights.value = true
      aiPlan.value = null
      loadingPhaseIndex.value = 0
      
      if (loadingInterval) clearInterval(loadingInterval)
      loadingInterval = setInterval(() => {
        loadingPhaseIndex.value = (loadingPhaseIndex.value + 1) % loadingPhases.length
      }, 850)
      
      const host = window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : window.location.origin
        
      const response = await fetch(`${host}/api/v1/incidents/${newId}/insights`)
      if (response.ok) {
        const data = await response.json()
        aiPlan.value = data.plan
      }
    } catch (err) {
      console.warn('Failed to fetch AI insights plan:', err)
    } finally {
      if (loadingInterval) clearInterval(loadingInterval)
      isLoadingInsights.value = false
    }
  }
)

// Stats for dashboard
const stats = ref({
  total: 0,
  by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
  by_type: {},
  by_country: {}
})

const selectedIncidentData = computed<IncidentLevel1 | null>(
  () =>
    eventsStore.allIncidents.find(
      (incident) => incident.id === appStore.selectedIncident || incident.id === appStore.expandedIncident,
    ) ?? null,
)

// Filtered and sorted incidents based on active country, event type, and sort criteria
const filteredIncidents = computed(() => {
  let incidents = [...eventsStore.allIncidents]
  
  // Apply quick search query across location, hazard type, country code, and country name
  if (dashboardSearchQuery.value.trim()) {
    const q = dashboardSearchQuery.value.trim().toLowerCase()
    incidents = incidents.filter(i => {
      const loc = (i.location || '').toLowerCase()
      const rawType = (i.type || '').toLowerCase()
      const fmtType = formatIncidentType(i.type, i.location).toLowerCase()
      const country = (i.countryCode || '').toLowerCase()
      const countryName = getCountryName(i.countryCode || '').toLowerCase()
      return loc.includes(q) || rawType.includes(q) || fmtType.includes(q) || country.includes(q) || countryName.includes(q)
    })
  }
  
  // Apply country filter
  if (selectedCountry.value) {
    incidents = incidents.filter(i => {
      return i.countryCode === selectedCountry.value
    })
  }
  
  // Apply event type filter
  if (selectedEventType.value) {
    incidents = incidents.filter(i => i.type === selectedEventType.value)
  }
  
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
      incidents.sort((a, b) => (b.threatScore || 0) - (a.threatScore || 0))
  }
  
  return incidents
})


// Bottom bar stats based on filtered list
const totalAffectedArea = computed(() =>
  filteredIncidents.value.reduce((sum, i) => sum + (i.affectedArea || 0), 0)
)
const totalPopulation = computed(() =>
  filteredIncidents.value.reduce((sum, i) => sum + (i.affectedPopulation || 0), 0)
)
const activeIncidentsCount = computed(() => filteredIncidents.value.length)

// Hazard breakdown dynamically computed from filtered list
const filteredHazardCounts = computed(() => {
  const counts = { fire: 0, flood: 0, earthquake: 0, storm: 0 }
  filteredIncidents.value.forEach((i) => {
    const t = (i.type || '').toLowerCase()
    if (t.includes('fire') || t.includes('wildfire')) counts.fire++
    else if (t.includes('flood')) counts.flood++
    else if (t.includes('earthquake') || t.includes('seismic')) counts.earthquake++
    else if (t.includes('storm') || t.includes('weather') || t.includes('cyclone') || t.includes('typhoon')) counts.storm++
  })
  return counts
})

// Chronologically latest disaster event from filtered list
const latestIncident = computed(() => {
  if (!filteredIncidents.value.length) return null
  const sorted = [...filteredIncidents.value].sort(
    (a, b) => new Date(b.detectionTime).getTime() - new Date(a.detectionTime).getTime()
  )
  return sorted[0]
})

// Relative time formatting for emergency telemetry
const formatTimeAgo = (date: Date | string) => {
  if (!date) return ''
  const d = new Date(date)
  const diffMinutes = Math.floor((Date.now() - d.getTime()) / 60000)
  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  const diffHours = Math.floor(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  return `${Math.floor(diffHours / 24)}d ago`
}

// Live dynamic critical insights derived from real PostgreSQL database events!
const liveCriticalInsights = computed(() => {
  const topIncidents = [...filteredIncidents.value]
    .sort((a, b) => (b.threatScore || 0) - (a.threatScore || 0))
    .slice(0, 3)

  return topIncidents.map(inc => {
    const type = (inc.type || 'Hazard').toLowerCase()
    let action = ''
    if (type.includes('fire')) action = `Deploy perimeter containment & thermal surveillance in ${inc.location}`
    else if (type.includes('flood')) action = `Establish water barriers & riverbank evacuation corridor in ${inc.location}`
    else if (type.includes('earthquake') || type.includes('seismic')) action = `Dispatch search & rescue units to epicenter in ${inc.location}`
    else if (type.includes('storm')) action = `Issue high-wind & storm surge shelter warnings for ${inc.location}`
    else action = `Initiate multi-agency rapid response mobilization in ${inc.location}`

    return {
      id: inc.id,
      incidentId: inc.id,
      type: inc.type || 'Hazard',
      location: inc.location,
      threatScore: inc.threatScore || 50,
      action,
      estimatedAffected: inc.affectedPopulation || 15000,
      severity: (inc.threatScore && inc.threatScore >= 80) ? 'critical' : 'high'
    }
  })
})

const sortedAndPaginatedIncidents = computed(() => {
  const startIndex = (currentPage.value - 1) * cardsPerPage.value
  const endIndex = startIndex + cardsPerPage.value
  return filteredIncidents.value.slice(startIndex, endIndex)
})

// Get incidents grouped by country
const groupedByCountry = computed(() => {
  const grouped: { [key: string]: any[] } = {}
  
  eventsStore.allIncidents.forEach(incident => {
    const country = incident.countryCode || 'UN'
    
    if (!grouped[country]) {
      grouped[country] = []
    }
    grouped[country].push(incident)
  })
  
  return grouped
})

// Available countries for filter
const availableCountries = computed(() => {
  const countries = new Set<string>()
  eventsStore.allIncidents.forEach(incident => {
    const country = incident.countryCode
    if (country && country !== 'UN') countries.add(country)
  })
  return Array.from(countries).sort()
})

// Get statistics
const statsComputed = computed(() => {
  const s = {
    total: eventsStore.allIncidents.length,
    by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
    by_type: {} as Record<string, number>,
    by_country: {} as Record<string, number>
  }
  
  eventsStore.allIncidents.forEach(incident => {
    // Count by severity
    const severity = incident.severity || 'low'
    s.by_severity[severity as keyof typeof s.by_severity]++
    
    // Count by type
    const type = incident.type || 'unknown'
    s.by_type[type] = (s.by_type[type] || 0) + 1
    
    // Count by country
    const country = incident.countryCode || 'UN'
    s.by_country[country] = (s.by_country[country] || 0) + 1
  })
  
  return s
})

// Country details with incident counts
const countryDetails = computed(() => {
  return Object.entries(groupedByCountry.value).map(([country, incidents]) => {
    const critical = incidents.filter(i => i.severity === 'critical').length
    const high = incidents.filter(i => i.severity === 'high').length
    const medium = incidents.filter(i => i.severity === 'medium').length
    
    return {
      code: country,
      name: getCountryName(country),
      flag: getCountryFlag(country),
      count: incidents.length,
      critical,
      high,
      medium,
      incidents: incidents.sort((a, b) => (b.threatScore || 0) - (a.threatScore || 0))
    }
  }).sort((a, b) => b.critical - a.critical || b.count - a.count)
})

// Dynamic pagination indicators based on the currently filtered list!
const hasMoreIncidents = computed(() => {
  return currentPage.value * cardsPerPage.value < filteredIncidents.value.length
})

const totalPages = computed(() => {
  return Math.ceil(filteredIncidents.value.length / cardsPerPage.value) || 1
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

const formatIncidentType = (type: string, location?: string): string => {
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

const getIncidentIcon = (type: string, location?: string): string => {
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

const getSeverityClass = (score?: number) => {
  const s = score ?? 50
  if (s >= 80) return 'critical'
  if (s >= 65) return 'high'
  return 'medium'
}

/**
 * Automatically converts shouting ALL-CAPS text blocks into clean, readable Sentence Case,
 * preserving critical emergency agency acronyms (FEMA, NOAA, USCG, JFO, etc.).
 */
const formatTacticalText = (text: string): string => {
  if (!text) return ''
  const upperCount = (text.match(/[A-Z]/g) || []).length
  const letterCount = (text.match(/[a-zA-Z]/g) || []).length
  if (letterCount > 20 && upperCount / letterCount > 0.55) {
    return text
      .toLowerCase()
      .replace(/(^\s*\w|[.!?]\s*\w)/g, c => c.toUpperCase())
      .replace(/\b(us|usa|fema|noaa|usgs|nasa|gdacs|jfo|eoc|lang|uscg|als|ems|ndrf|ch-47|i-10|i-49|us-90|dotd)\b/gi, m => m.toUpperCase())
  }
  return text
}

// Native browser internationalization for country names (supports all 249 countries dynamically without hardcoding)
const regionNames = new Intl.DisplayNames(['en'], { type: 'region' })

/**
 * Mathematically generates the Unicode flag emoji from a 2-letter ISO country code.
 * (e.g. "US" -> 🇺🇸, "IN" -> 🇮🇳, "JP" -> 🇯🇵, "NP" -> 🇳🇵)
 * Uses Unicode Regional Indicator Symbols (offset 127397) - zero hardcoding required!
 */
const getCountryFlag = (code: string): string => {
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

/**
 * Dynamically resolves country names using native browser Intl.DisplayNames.
 * Works for all ISO country codes worldwide with zero hardcoded dictionaries.
 */
const getCountryName = (code: string): string => {
  if (!code) return 'Unknown'
  const trimmed = code.trim()
  if (/^[A-Za-z]{2}$/.test(trimmed)) {
    try {
      return regionNames.of(trimmed.toUpperCase()) || trimmed
    } catch {
      return trimmed
    }
  }
  return trimmed
}

/**
 * 50 US State postal codes + territories.
 * Collapses states like "FL", "TX", "CA", "CO" into the canonical country "US".
 */
    const US_STATE_CODES = new Set([
        // 50 States
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',

        // Federal District & Territories
        'DC', 'PR', 'VI', 'GU', 'MP', 'AS',

        // Freely Associated States
        'FM', 'MH', 'PW',

        // Military Postal Regions
        'AA', 'AE', 'AP'
    ]);

/**
 * Resolves a reliable, canonical 2-letter ISO country code from location and source.
 * Prevents US state abbreviations (FL, TX) and marine zones (Mississippi Sound) from leaking into the country dropdown.
 */
const resolveCountryCode = (locationName: string, source: string, lat?: number, lon?: number): string => {
  const src = (source || '').toUpperCase()
  
  // 1. NOAA is unconditionally the United States
  if (src.includes('NOAA')) return 'US'
  
  if (!locationName) return 'UN'
  const locUpper = locationName.toUpperCase()
  
  // 2. Full country names & common US aliases
  if (locUpper.includes('UNITED STATES') || locUpper.includes('USA') || locUpper.endsWith(', US') || locUpper.endsWith(' US')) {
    return 'US'
  }
  if (locUpper.includes('INDIA')) return 'IN'
  if (locUpper.includes('CHINA')) return 'CN'
  if (locUpper.includes('NEPAL')) return 'NP'
  if (locUpper.includes('JAPAN')) return 'JP'
  if (locUpper.includes('CHILE')) return 'CL'
  if (locUpper.includes('PHILIPPINES')) return 'PH'
  if (locUpper.includes('INDONESIA')) return 'ID'
  if (locUpper.includes('CANADA')) return 'CA'
  if (locUpper.includes('AUSTRALIA')) return 'AU'
  if (locUpper.includes('MEXICO')) return 'MX'
  
  const locParts = locationName.split(',')
  const lastPart = locParts.length > 0 ? locParts[locParts.length - 1].trim().toUpperCase() : ''
  
  // 3. Special case: 'IN' (Indiana vs India). Lon ~ 60-100 is India, Lon < -50 is Indiana, US
  if (lastPart === 'IN') {
    return (lon !== undefined && lon > 50 && lon < 100) ? 'IN' : 'US'
  }
  
  // 4. US State code detection (e.g., "Apalachicola, FL" -> "US")
  if (US_STATE_CODES.has(lastPart)) {
    return 'US'
  }
  
  // 5. Genuine 2-letter ISO country code verification via Intl API
  if (/^[A-Z]{2}$/.test(lastPart)) {
    try {
      const name = regionNames.of(lastPart)
      if (name && name !== lastPart) {
        return lastPart
      }
    } catch {
      // Not a valid country code
    }
  }
  
  return 'UN'
}

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
    console.log('Incidents loaded:', events.length, 'events (raw, global)')
    
    // Transform backend response to store format
    if (Array.isArray(events) && events.length > 0) {
      const mapped = events.map((event: any, index: number) => {
        const impact = event.impact || {}
        const severity = (event.severity || 'medium').toLowerCase()
        const locationName = event.location_name || 'Unknown'
        const source = event.source || event.data?.source || 'unknown'
        
        // Canonical Country Code extraction (collapses US states and NOAA marine alerts into 'US')
        const countryCode = resolveCountryCode(locationName, source, event.latitude, event.longitude)

        return {
          id: event.data?.id || event.data?.nasa_id || event.data?.gdacs_id || event.id || `event-${index}-${Date.now()}`,
          type: event.event_type || 'fire',
          location: locationName,
          countryCode: countryCode,
          severity: (severity === 'critical' ? 'high' : severity) as 'low' | 'medium' | 'high',
          status: event.status === 'detected' || event.status === 'active' ? 'active' : (event.status || 'active'),
          threatScore: impact.risk_score ?? undefined,
          detectionTime: new Date(event.event_timestamp || Date.now()),
          affectedArea: impact.affected_area_km2 || 0,
          affectedPopulation: impact.affected_population || 0,
          trend: impact.trend_km2_per_hour || 0,
          forecast6h: impact.forecast_6h_km2 || 0,
          coordinates: [event.latitude, event.longitude] as [number, number],
        }
      })

      // Global Platform: Show all live disaster incidents worldwide sorted by threat score
      const incidents = mapped.sort((a, b) => (b.threatScore ?? 0) - (a.threatScore ?? 0))

      console.log(`📍 Loaded ${incidents.length} global incident(s) worldwide across all sources`)
      eventsStore.setIncidents(incidents)
    } else {
      // Live mode strictness: No mock fallbacks allowed
      console.warn('No events from API. (Mock fallback disabled for strict live testing)')
      
      // Look for failing sources to report in the banner
      const sources = result.data?.sources || {}
      const failedSources = Object.keys(sources).filter(k => sources[k].count === 0 || sources[k].status !== 'success')
      
      if (failedSources.length > 0) {
          apiError.value = `Live Mode: 0 events returned from ${failedSources.join(', ')}`
      } else {
          apiError.value = "Live Mode: Currently 0 active disaster events worldwide."
      }
      
      eventsStore.setIncidents([])
    }
  } catch (error) {
    console.error('Failed to fetch incidents:', error)
    apiError.value = error instanceof Error ? error.message : 'Failed to fetch data'
      //// Fallback to mock data on error
      //eventsStore.initMockData()
      // Strict live testing: No mock fallback on network error
    eventsStore.setIncidents([])
  } finally {
    isLoading.value = false
  }
}

/**
 * Load alerts from store (can be extended to fetch from backend)
 */
const loadAlerts = () => {
  if (alertsStore.criticalInsights.length === 0) {
    // COMMENTED OUT (Live Mode): Never show mock insights as fallback
    // alertsStore.initMockInsights()
  }
}

onMounted(async () => {
  isLoading.value = true
  apiError.value = null
  
  try {
    console.log('📥 Loading historical incidents from database (Feature 5)...')
    
    // Feature 5: Hydrate UI from database first so it survives restarts
    const host = window.location.hostname === 'localhost'
      ? 'http://localhost:8000'
      : window.location.origin
      
    const response = await fetch(`${host}/api/v1/incidents?limit=50`)
    
    if (response.ok) {
        const rawIncidents = await response.json()
        if (rawIncidents && rawIncidents.length > 0) {
            // Re-use the existing transformation logic from fetchIncidents
            const mapped = rawIncidents.map((event: any, index: number) => {
              const impact = event.impact || {}
              const severity = (event.severity || 'medium').toLowerCase()
              const locationName = event.location_name || 'Unknown'
              const source = event.source || event.data?.source || 'unknown'
              
              // Canonical Country Code extraction (collapses US states and NOAA marine alerts into 'US')
              const countryCode = resolveCountryCode(locationName, source, event.latitude, event.longitude)

              return {
                id: event.data?.id || event.data?.nasa_id || event.data?.gdacs_id || event.id || `event-${index}-${Date.now()}`,
                type: event.event_type || 'fire',
                location: locationName,
                countryCode: countryCode,
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
            eventsStore.setIncidents(mapped)
            console.log(`✅ Loaded ${mapped.length} historical incidents from DB`)
        } else {
            console.log('⚠️ Database is empty, waiting for polling/WebSockets to provide live data')
            // Optionally run a manual fetch if DB is completely empty on first boot
            await fetchIncidents()
        }
    } else {
        console.warn('Failed to load from database, falling back to REST ingestion')
        await fetchIncidents()
    }
  } catch (e: any) {
    console.error('❌ Database hydration failed:', e)
    apiError.value = e.message
    await fetchIncidents()
  } finally {
    isLoading.value = false
    loadAlerts()
    
    // Connect to WebSocket for live updates AFTER database hydration
    console.log('📡 Connecting to WebSocket for live updates...')
    // Note: useWebSocket internally uses onMounted so we don't need to call connect() here,
    // just instantiating it inside setup/onMounted is sufficient as Vue handles it.
  }
})

// Watch for mock mode changes and refetch
watch(isMockMode, () => {
  console.log(`🔄 Mock mode changed to: ${isMockMode.value ? '🧪 MOCK' : '🌐 LIVE'}`)
  currentPage.value = 1  // Reset pagination
  fetchIncidents()
})

// Reset pagination when sort order, country filter, or event type filter changes
watch([sortBy, selectedCountry, selectedEventType], () => {
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
  grid-template-columns: 320px 1fr 340px;
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
  min-width: 320px;
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
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
  overflow-y: auto;
  flex: 1;
}

.detail-item-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

/* Unified Glass Subpanel Styling for Right Panel */
.glass-subpanel {
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 14px;
}

.profile-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profile-item.align-right {
  align-items: flex-end;
}

.card-section-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: #94a3b8;
  letter-spacing: 0.8px;
}

.profile-location {
  font-size: 14px;
  font-weight: 700;
  color: #38bdf8;
  line-height: 1.4;
}

.profile-split-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.threat-score-pill {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
}

.threat-score-num {
  font-size: 18px;
  font-weight: 800;
  color: #ff6b6b;
}

.threat-score-max {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
}

.summary-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-text {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  color: #cbd5e1;
}

.metadata-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
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
  color: #38bdf8;
  font-weight: 600;
  word-break: break-word;
  overflow-wrap: break-word;
  line-height: 1.4;
  max-height: 2.8em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  padding-left: 10px;
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
  padding: 12px 10px 0 10px;
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

/* Insights Panel - Enterprise AI Situational Assessment */
.insights-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
}

.insights-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.insights-panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
}

.ai-live-badge {
  font-size: 10px;
  font-weight: 800;
  color: #10b981;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 2px 8px;
  border-radius: 999px;
  letter-spacing: 0.5px;
}

.ai-overview-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 10px;
  padding: 12px;
}

.overview-title {
  font-size: 10px;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.8px;
}

.overview-text {
  font-size: 12px;
  line-height: 1.5;
  color: #cbd5e1;
  margin: 0;
}

.insights-subheading {
  font-size: 10px;
  font-weight: 800;
  color: #94a3b8;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  margin-top: 4px;
}

.insights-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.insight-item-interactive {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  cursor: pointer;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.insight-item-interactive:hover {
  background: rgba(30, 41, 59, 0.8);
  border-color: #38bdf8;
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
}

.insight-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.insight-type-tag {
  font-size: 11px;
  font-weight: 800;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 4px;
}

.insight-score {
  font-size: 11px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 4px;
}

.insight-score.critical {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.insight-score.high {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.insight-score.medium {
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.insight-action {
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
  color: #f8fafc;
}

.insight-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}

.insight-inspect {
  color: #38bdf8;
  font-weight: 700;
}

.no-insights {
  color: var(--text-secondary);
  font-size: 12px;
  margin: 0;
}

/* Metrics Footer - Full-Width Command Center Bar */
.metrics-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  gap: 24px;
  min-height: 72px;
}

.metrics-group {
  display: flex;
  align-items: center;
  gap: 32px;
}

.metric {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
}

.label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.value {
  font-size: 18px;
  font-weight: 800;
  color: #ffffff;
}

/* Operational Emergency Telemetry HUD */
.operational-telemetry-hud {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(0, 0, 0, 0.35);
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.hazard-breakdown-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hazard-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.hazard-pill .h-icon {
  font-size: 13px;
}

.hazard-pill .h-name {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.3px;
}

.hazard-pill .h-count {
  font-weight: 800;
  color: #ffffff;
  font-family: monospace;
}

/* Hide hazard text name on mobile/tablets to preserve compact icon look */
@media (max-width: 1199px) {
  .hazard-pill .h-name {
    display: none;
  }
}

.telemetry-divider {
  width: 1px;
  height: 20px;
  background: rgba(255, 255, 255, 0.15);
}

.latest-signal-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 10px;
  border-radius: 6px;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  transition: all 0.2s ease;
}

.latest-signal-pill:hover {
  background: rgba(16, 185, 129, 0.15);
  border-color: #10b981;
}

.pulse-beacon {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 10px #10b981;
  animation: beaconPulse 2s infinite;
}

@keyframes beaconPulse {
  0% { transform: scale(0.9); opacity: 0.8; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.8; }
}

.signal-tag {
  font-size: 10px;
  font-weight: 800;
  color: #10b981;
  letter-spacing: 0.5px;
}

.signal-location {
  font-size: 12px;
  font-weight: 700;
  color: #38bdf8;
  max-width: 220px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.signal-time {
  font-size: 11px;
  color: #94a3b8;
  font-family: monospace;
}

/* AI Tactical Response - De-Congested & Airy Command Styling */
.ai-decision-plan {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ai-plan-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.ai-plan-title {
  color: #38bdf8 !important;
  font-weight: 800 !important;
  font-size: 13px !important;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.ai-engine-chip {
  font-size: 9px;
  font-weight: 800;
  color: #10b981;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 2px 7px;
  border-radius: 999px;
  letter-spacing: 0.5px;
}

.country-context-tag {
  display: block;
  font-size: 11px;
  font-weight: 700;
  color: #38bdf8;
  background: rgba(14, 165, 233, 0.12);
  padding: 8px 12px;
  border-radius: 6px;
  border-left: 3px solid #38bdf8;
  line-height: 1.4;
}

.tactical-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.group-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: #94a3b8;
  letter-spacing: 0.5px;
}

.tactical-action-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tactical-action-card {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 10px 12px;
  transition: all 0.2s ease;
}

.tactical-action-card:hover {
  background: rgba(30, 41, 59, 0.8);
  border-color: rgba(56, 189, 248, 0.3);
}

.action-num {
  color: #38bdf8;
  font-weight: 800;
  font-size: 11px;
  font-family: monospace;
  margin-top: 2px;
  flex-shrink: 0;
}

.action-text {
  font-size: 12px;
  line-height: 1.5;
  color: #f1f5f9 !important;
}

.evacuation-card {
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-left: 3px solid #f59e0b;
  border-radius: 6px;
  padding: 10px 14px;
}

.evac-text {
  font-size: 12px;
  line-height: 1.6;
  color: #f8fafc !important;
  margin: 0;
}

.resource-chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.resource-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  background: rgba(30, 41, 59, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 4px 10px;
  border-radius: 6px;
}

.res-label {
  color: #38bdf8;
}

.res-qty {
  color: #ffffff;
  font-weight: 700;
}

.res-status {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  color: #10b981;
  background: rgba(16, 185, 129, 0.15);
  padding: 1px 6px;
  border-radius: 4px;
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
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}

.header-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

/* ===== COUNTRY FILTER ===== */
.country-filter-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.filter-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-cyan);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.country-dropdown {
  background: rgba(20, 30, 48, 0.5);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(30, 144, 255, 0.2);
  color: var(--accent-cyan);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 150ms ease;
}

.country-dropdown:hover {
  border-color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.1);
}

.country-dropdown:focus {
  outline: none;
  border-color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.15);
  box-shadow: 0 0 8px rgba(30, 144, 255, 0.3);
}

.country-dropdown option {
  background: rgba(20, 30, 48, 1);
  color: var(--accent-cyan);
  font-weight: 600;
}

.filter-controls {
  display: flex;
  gap: 8px;
  width: 100%;
}

.event-type-dropdown {
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
  flex: 1;
  min-width: 140px;
}

.event-type-dropdown:hover {
  border-color: var(--accent-cyan);
  background: rgba(20, 30, 48, 0.7);
}

.event-type-dropdown:focus {
  outline: none;
  border-color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.15);
  box-shadow: 0 0 8px rgba(30, 144, 255, 0.3);
}

.event-type-dropdown option {
  background: #0f172a;
  color: #ffffff;
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
  flex: 1;
  min-width: 140px;
}

.sort-dropdown:hover {
  border-color: var(--accent-cyan);
  background: rgba(20, 30, 48, 0.7);
}

.sort-dropdown:focus {
  outline: none;
  border-color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.15);
  box-shadow: 0 0 8px rgba(30, 144, 255, 0.3);
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
    grid-template-columns: 300px 1fr 320px;
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
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
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

  /* Metrics Section on Mobile */
  .metrics-section {
    display: flex !important;
    flex-direction: column !important;
    gap: 12px !important;
    height: auto !important;
    min-height: auto !important;
    padding: 12px !important;
    order: 5;
  }

  .metrics-group {
    display: flex !important;
    justify-content: space-between !important;
    width: 100%;
    gap: 8px !important;
  }

  .metric {
    flex: 1;
    padding: 8px 6px;
    gap: 2px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 6px;
    align-items: center;
  }

  .metric .label {
    font-size: 9px;
    text-align: center;
  }

  .metric .value {
    font-size: 14px;
    text-align: center;
  }

  .operational-telemetry-hud {
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 10px !important;
    width: 100%;
    padding: 10px !important;
  }

  .hazard-breakdown-group {
    display: flex !important;
    justify-content: space-between !important;
    width: 100%;
    gap: 4px;
  }

  .hazard-pill {
    flex: 1;
    justify-content: center;
    padding: 6px 4px !important;
  }

  .telemetry-divider {
    display: none !important;
  }

  .latest-signal-pill {
    justify-content: center;
    width: 100%;
  }

  .signal-location {
    max-width: 160px;
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
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
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

  .country-filter-section {
    width: 100%;
  }

  .country-dropdown {
    width: 100%;
    font-size: 10px;
    padding: 4px 8px;
  }

  .filter-controls {
    flex-direction: column;
    width: 100%;
    gap: 6px;
  }

  .event-type-dropdown {
    font-size: 10px;
    padding: 4px 8px;
    width: 100%;
    min-width: auto;
  }

  .sort-dropdown {
    font-size: 10px;
    padding: 4px 8px;
    width: 100%;
    min-width: auto;
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
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
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

  .metric {
    padding: 6px;
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
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
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

/* ===== HIGH-TECH TACTICAL LOADING ANIMATION ===== */
.ai-tactical-loading {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 10px 4px;
}

.loading-radar-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.radar-ping-ring {
  position: relative;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.radar-ping-ring::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid #0ea5e9;
  animation: radarExpand 1.6s infinite ease-out;
}

@keyframes radarExpand {
  0% { transform: scale(0.6); opacity: 1; }
  100% { transform: scale(1.8); opacity: 0; }
}

.radar-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 10px #38bdf8;
}

.loading-telemetry-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-height: 34px;
}

.loading-phase-tag {
  font-size: 9px;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}

.cycling-step-text {
  font-size: 12px;
  color: #f1f5f9;
  font-weight: 600;
  line-height: 1.4;
  animation: textFadeIn 0.3s ease;
}

@keyframes textFadeIn {
  from { opacity: 0.3; transform: translateY(2px); }
  to { opacity: 1; transform: translateY(0); }
}

.tactical-progress-track {
  height: 3px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 99px;
  overflow: hidden;
  position: relative;
}

.tactical-scan-laser {
  position: absolute;
  width: 35%;
  height: 100%;
  background: linear-gradient(90deg, transparent, #38bdf8, transparent);
  box-shadow: 0 0 12px #38bdf8;
  animation: laserScan 1.3s infinite ease-in-out;
}

@keyframes laserScan {
  0% { left: -35%; }
  100% { left: 100%; }
}

/* Skeleton Shimmer Loaders */
.skeleton-action-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
}

.skeleton-tag {
  height: 24px;
  width: 70%;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
}

.skeleton-card {
  height: 48px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  padding: 0 12px;
  gap: 12px;
}

.sk-num {
  font-size: 11px;
  font-weight: 800;
  font-family: monospace;
  color: rgba(56, 189, 248, 0.4);
}

.sk-lines {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sk-line {
  height: 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
}

.sk-line.full { width: 90%; }
.sk-line.half { width: 55%; }

.skeleton-evac {
  height: 40px;
  border-radius: 6px;
  background: rgba(245, 158, 11, 0.06);
  border-left: 3px solid rgba(245, 158, 11, 0.3);
}

.shimmer {
  position: relative;
  overflow: hidden;
}

.shimmer::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background-image: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0) 0,
    rgba(56, 189, 248, 0.08) 50%,
    rgba(255, 255, 255, 0) 100%
  );
  animation: shimmerSweep 1.8s infinite;
}

@keyframes shimmerSweep {
  100% { transform: translateX(100%); }
}

/* ===== SIDEBAR SEARCH BOX ===== */
.sidebar-search-section {
  width: 100%;
}

.sidebar-search-box {
  display: flex;
  align-items: center;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 8px;
  padding: 6px 10px;
  gap: 8px;
  transition: all 0.2s ease;
}

.sidebar-search-box:focus-within {
  border-color: #38bdf8;
  background: rgba(15, 23, 42, 0.95);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
}

.sidebar-search-input {
  background: transparent;
  border: none;
  color: #f1f5f9;
  font-size: 12px;
  width: 100%;
  outline: none;
}

.sidebar-search-input::placeholder {
  color: #64748b;
  font-size: 11px;
}

.search-clear-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 11px;
  cursor: pointer;
  padding: 0 2px;
}

.search-clear-btn:hover {
  color: #ffffff;
}

/* ===== TACTICAL THREAT SCORE HOVER TOOLTIP ===== */
.tooltip-container {
  position: relative;
  cursor: help;
}

.tactical-tooltip {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  top: 100%;
  right: 0;
  transform: translateY(6px);
  width: 250px;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.6);
  z-index: 9999;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

.tooltip-container:hover .tactical-tooltip {
  visibility: visible;
  opacity: 1;
  transform: translateY(10px);
}

.tooltip-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.tooltip-header strong {
  font-size: 11px;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.tooltip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #38bdf8;
}

.tooltip-dot.critical { background: #ef4444; box-shadow: 0 0 8px #ef4444; }
.tooltip-dot.high { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }
.tooltip-dot.medium { background: #38bdf8; box-shadow: 0 0 8px #38bdf8; }

.tooltip-desc {
  font-size: 11px;
  line-height: 1.45;
  color: #cbd5e1;
  margin: 6px 0;
}

.tooltip-factors {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.factor-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 10px;
  color: #94a3b8;
}

.factor-row strong {
  color: #38bdf8;
  font-family: monospace;
}
</style>
