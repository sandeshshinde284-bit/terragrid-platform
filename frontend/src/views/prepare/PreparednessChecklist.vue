<template>
  <div class="prepare-screen checklist-screen">
    <Header />

    <div class="checklist-container">
      <div v-if="loading" class="empty-state glass-panel tactical-loading-container">
        <div class="radar-ping-ring">
          <span class="radar-dot"></span>
        </div>
        <div class="loading-telemetry-text">
          <strong class="cycling-step-text">Fetching 7-day weather forecast...</strong>
        </div>
        <div class="tactical-progress-track">
          <div class="tactical-scan-laser"></div>
        </div>
      </div>

      <div v-else-if="error" class="empty-state glass-panel">
        <div class="empty-icon">⚠️</div>
        <h3>Couldn't load the checklist</h3>
        <p>{{ error }}</p>
      </div>

      <div v-else-if="cities.length === 0" class="empty-state glass-panel">
        <div class="empty-icon">✅</div>
        <h3>No forecast data yet</h3>
        <p>This builds on the 7-Day Forecast Dashboard's data. If OPENWEATHERMAP_API_KEY isn't set on the backend, there's nothing to generate a checklist from yet.</p>
      </div>

      <template v-else>
        <div class="checklist-hero glass-panel">
          <div class="hero-left">
            <h2>Preparedness Checklist</h2>
            <span class="hero-meta">AI-generated actions tied to each city's forecast, grouped by urgency</span>
          </div>
          <select v-model="selectedKey" class="city-select">
            <option v-for="city in sortedCities" :key="cityKey(city)" :value="cityKey(city)">
              {{ city.city }}, {{ countryName(city.country) }} - worst: {{ worstRisk(city) }}
            </option>
          </select>
        </div>

        <div v-if="actionsLoading" class="empty-state glass-panel tactical-loading-container actions-loading">
          <div class="radar-ping-ring small">
            <span class="radar-dot"></span>
          </div>
          <div class="loading-telemetry-text">
            <strong class="cycling-step-text">Generating preparedness checklist for {{ selectedCity?.city }}...</strong>
          </div>
        </div>

        <div v-else-if="actionsError" class="empty-state glass-panel">
          <div class="empty-icon">⚠️</div>
          <h3>Couldn't generate the checklist</h3>
          <p>{{ actionsError }}</p>
        </div>

        <template v-else-if="actionsPlan">
          <div class="risk-context glass-panel" :class="selectedToneClass">
            <span class="context-icon">{{ selectedToneIcon }}</span>
            <span class="context-text">{{ actionsPlan.risk_context }}</span>
            <span class="source-badge" :class="sourceBadgeClass">{{ sourceLabel }}</span>
          </div>

          <div class="priority-section" v-for="tier in priorityTiers" :key="tier.priority" v-show="tier.actions.length > 0">
            <div class="tier-header" :class="tier.className">
              <span class="tier-dot"></span>
              <span class="tier-label">{{ tier.label }}</span>
              <span class="tier-count">{{ tier.actions.length }}</span>
            </div>

            <div class="action-grid">
              <div v-for="(action, idx) in tier.actions" :key="idx" class="action-card glass-panel">
                <div class="action-top">
                  <span class="category-chip" :class="action.category.toLowerCase()">{{ categoryIcon(action.category) }} {{ action.category }}</span>
                  <span class="deadline-chip">Before Day {{ action.deadline_day }}</span>
                </div>
                <p class="action-text">{{ action.action }}</p>
                <div class="action-agency">
                  <span class="agency-icon">🏛️</span>
                  <span>{{ action.agency }}</span>
                </div>
                <p class="action-rationale">{{ action.rationale }}</p>
              </div>
            </div>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import Header from '@/components/organisms/Header.vue'
import { useMockMode } from '@/composables/useMockMode'

interface DailyForecast {
  date: string
  risk_level: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED'
  dominant_weather: string
  max_wind_ms: number
  min_temp_c: number | null
  max_temp_c: number | null
  total_rain_mm: number
}

interface CityForecast {
  city: string
  country: string
  latitude: number
  longitude: number
  source: string
  daily: DailyForecast[]
}

interface PreparednessAction {
  action: string
  agency: string
  category: string
  priority: 1 | 2 | 3
  deadline_day: number
  rationale: string
}

interface ActionsPlan {
  risk_context: string
  actions: PreparednessAction[]
  ai_available?: boolean
  is_fallback?: boolean
  is_mock_demo?: boolean
}

const { fetchWithMockMode } = useMockMode()

const cities = ref<CityForecast[]>([])
const loading = ref(true)
const error = ref('')
const selectedKey = ref('')

const actionsPlan = ref<ActionsPlan | null>(null)
const actionsLoading = ref(false)
const actionsError = ref('')
const actionsSource = ref('')

const RISK_RANK: Record<string, number> = { GREEN: 0, YELLOW: 1, ORANGE: 2, RED: 3 }

const COUNTRY_NAMES: Record<string, string> = {
  IN: 'India', NP: 'Nepal', CN: 'China', HK: 'Hong Kong', BD: 'Bangladesh',
  PK: 'Pakistan', TH: 'Thailand', VN: 'Vietnam', SG: 'Singapore', MY: 'Malaysia',
  IQ: 'Iraq', AE: 'UAE', ET: 'Ethiopia', KE: 'Kenya', RW: 'Rwanda', US: 'United States',
}
const countryName = (code: string) => COUNTRY_NAMES[code] || code

const CATEGORY_ICONS: Record<string, string> = {
  DRAINAGE: '🌊', MEDICAL: '🏥', EVACUATION: '🚤', SUPPLIES: '📦',
  COMMUNICATION: '📢', INFRASTRUCTURE: '🏗️',
}
const categoryIcon = (category: string) => CATEGORY_ICONS[(category || '').toUpperCase()] || '📋'

const cityKey = (city: CityForecast) => `${city.city}-${city.country}`

const worstRisk = (city: CityForecast): string => {
  return city.daily.reduce((worst, day) => (RISK_RANK[day.risk_level] > RISK_RANK[worst] ? day.risk_level : worst), 'GREEN')
}

const sortedCities = computed(() => {
  return [...cities.value].sort((a, b) => RISK_RANK[worstRisk(b)] - RISK_RANK[worstRisk(a)])
})

const selectedCity = computed<CityForecast | null>(() => {
  return cities.value.find(c => cityKey(c) === selectedKey.value) || null
})

const selectedToneClass = computed(() => {
  if (!selectedCity.value) return 'green'
  return worstRisk(selectedCity.value).toLowerCase()
})

const selectedToneIcon = computed(() => {
  const tone = selectedToneClass.value
  return tone === 'red' ? '🔴' : tone === 'orange' ? '🟠' : tone === 'yellow' ? '🟡' : '✅'
})

const sourceLabel = computed(() => actionsSource.value || '')
const sourceBadgeClass = computed(() => {
  if (actionsPlan.value?.is_mock_demo) return 'mock'
  if (actionsPlan.value?.is_fallback) return 'fallback'
  return 'live'
})

// Group the generated actions into IMMEDIATE / HIGH / STAGED tiers so the most
// urgent work is always first, regardless of the order the model returned them in.
const priorityTiers = computed(() => {
  const actions = actionsPlan.value?.actions || []
  return [
    { priority: 1, label: 'Immediate', className: 'immediate', actions: actions.filter(a => a.priority === 1) },
    { priority: 2, label: 'High Priority', className: 'high', actions: actions.filter(a => a.priority === 2) },
    { priority: 3, label: 'Staged', className: 'staged', actions: actions.filter(a => a.priority === 3) },
  ]
})

const apiHost = () => import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)

const fetchActionsForSelectedCity = async () => {
  const city = selectedCity.value
  if (!city) return

  actionsLoading.value = true
  actionsError.value = ''
  actionsPlan.value = null

  try {
    const host = apiHost()
    const params = new URLSearchParams({ city: city.city, country: city.country })
    const response = await fetchWithMockMode(`${host}/api/v1/prepare/actions?${params.toString()}`)

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const json = await response.json()
    actionsPlan.value = json.data
    actionsSource.value = json.source || ''
  } catch (e) {
    actionsError.value = e instanceof Error ? e.message : 'Unknown error generating checklist'
  } finally {
    actionsLoading.value = false
  }
}

onMounted(async () => {
  try {
    const host = apiHost()
    const response = await fetchWithMockMode(`${host}/api/v1/prepare/forecast`)

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const json = await response.json()
    cities.value = json.data || []

    if (cities.value.length > 0) {
      selectedKey.value = cityKey(sortedCities.value[0])
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Unknown error fetching forecast'
  } finally {
    loading.value = false
  }
})

watch(cities, (newCities) => {
  if (newCities.length > 0 && !selectedCity.value) {
    selectedKey.value = cityKey(sortedCities.value[0])
  }
})

watch(selectedKey, () => {
  if (selectedCity.value) fetchActionsForSelectedCity()
})
</script>

<style scoped>
.checklist-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.checklist-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 48px 24px;
  text-align: center;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 32px;
}

.checklist-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 20px;
}

.hero-left h2 {
  margin: 0 0 4px 0;
  background: linear-gradient(90deg, #38bdf8, #22d3ee);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-meta {
  font-size: 13px;
  color: var(--text-secondary);
}

.city-select {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  min-width: 240px;
}

.actions-loading {
  padding: 32px 20px;
}

.risk-context {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-left: 3px solid var(--text-secondary);
  flex-wrap: wrap;
}

.risk-context.green { border-left-color: #22c55e; }
.risk-context.yellow { border-left-color: #eab308; }
.risk-context.orange { border-left-color: #f97316; }
.risk-context.red { border-left-color: #ef4444; }

.context-icon {
  font-size: 16px;
}

.context-text {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  flex: 1;
}

.source-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.source-badge.mock {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.source-badge.live {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.source-badge.fallback {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
  border: 1px solid rgba(234, 179, 8, 0.3);
}

.priority-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tier-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 2px;
}

.tier-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.tier-header.immediate .tier-dot { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.5); }
.tier-header.high .tier-dot { background: #f97316; box-shadow: 0 0 8px rgba(249, 115, 22, 0.5); }
.tier-header.staged .tier-dot { background: #38bdf8; box-shadow: 0 0 8px rgba(56, 189, 248, 0.5); }

.tier-label {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-primary);
}

.tier-count {
  font-size: 11px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.06);
  padding: 1px 7px;
  border-radius: 10px;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.action-card {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 6px;
}

.category-chip {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  white-space: nowrap;
}

.deadline-chip {
  font-size: 11px;
  font-weight: 600;
  color: #38bdf8;
  white-space: nowrap;
}

.action-text {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  line-height: 1.4;
}

.action-agency {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.action-rationale {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
  padding-top: 6px;
  border-top: 1px dashed rgba(255, 255, 255, 0.08);
}

/* Tactical Loading Animation (matches ForecastDashboard.vue / RiskTimeline.vue) */
.tactical-loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 60px 20px;
}
.radar-ping-ring {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: 2px solid rgba(14, 165, 233, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.radar-ping-ring.small {
  width: 36px;
  height: 36px;
}
.radar-ping-ring::before {
  content: '';
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  border: 1px solid rgba(14, 165, 233, 0.5);
  animation: radar-ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
}
.radar-dot {
  width: 12px;
  height: 12px;
  background-color: #0ea5e9;
  border-radius: 50%;
  box-shadow: 0 0 15px 4px rgba(14, 165, 233, 0.6);
}
.radar-ping-ring.small .radar-dot {
  width: 8px;
  height: 8px;
}
.loading-telemetry-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
}
.cycling-step-text {
  font-size: 14px;
  color: #94a3b8;
  font-family: monospace;
  animation: pulse-text 1.5s ease-in-out infinite;
}
.tactical-progress-track {
  width: 250px;
  height: 2px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}
.tactical-scan-laser {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 40%;
  background: linear-gradient(90deg, transparent, #0ea5e9, transparent);
  animation: scan-laser 2s linear infinite;
}
@keyframes radar-ping {
  0% { transform: scale(0.5); opacity: 1; }
  100% { transform: scale(2); opacity: 0; }
}
@keyframes pulse-text {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
@keyframes scan-laser {
  0% { left: -40%; }
  100% { left: 100%; }
}

@media (max-width: 480px) {
  .checklist-screen {
    padding: 8px;
    gap: 8px;
  }

  .checklist-hero {
    padding: 14px 16px;
  }

  .city-select {
    min-width: 0;
    width: 100%;
  }
}
</style>
