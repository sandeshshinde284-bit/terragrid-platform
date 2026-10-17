<template>
  <div class="prepare-screen timeline-screen">
    <Header />

    <div class="timeline-container">
      <!-- Only block the whole page on the true first load (no cities yet) -
           see the matching comment in AgencyAlerts.vue for why. -->
      <div v-if="loading && cities.length === 0" class="empty-state glass-panel tactical-loading-container">
        <div class="radar-ping-ring">
          <span class="radar-dot"></span>
        </div>
        <div class="loading-telemetry-text">
          <strong class="cycling-step-text">{{ $t('prepare.timeline.loading') }}</strong>
        </div>
        <div class="tactical-progress-track">
          <div class="tactical-scan-laser"></div>
        </div>
      </div>

      <div v-else-if="error && cities.length === 0" class="empty-state glass-panel">
        <div class="empty-icon">⚠️</div>
        <h3>{{ $t('prepare.timeline.loadError') }}</h3>
        <p>{{ error }}</p>
      </div>

      <div v-else-if="cities.length === 0" class="empty-state glass-panel">
        <div class="empty-icon">📈</div>
        <h3>{{ $t('prepare.noForecastData') }}</h3>
        <p>{{ $t('prepare.noForecastDesc') }}</p>
      </div>

      <template v-else>
        <div class="timeline-hero glass-panel">
          <div class="hero-left">
            <h2>{{ $t('prepare.timeline.title') }}</h2>
            <span class="hero-meta">{{ $t('prepare.timeline.subtitle') }}</span>
          </div>
        </div>

        <div class="master-detail">
          <!-- Always-visible, worst-first city list: scan every city's status
               at a glance and jump straight to one with a single click - no
               dropdown to open/scroll/close per city. -->
          <nav class="city-rail glass-panel" aria-label="Cities by risk">
            <button
              v-for="city in sortedCities"
              :key="cityKey(city)"
              type="button"
              class="rail-item"
              :class="[worstRisk(city).toLowerCase(), { active: cityKey(city) === selectedKey }]"
              @click="selectedKey = cityKey(city)"
            >
              <span class="rail-dot"></span>
              <span class="rail-text">
                <span class="rail-name">{{ city.city }}</span>
                <span class="rail-country">{{ countryName(city.country) }}</span>
              </span>
              <span class="rail-risk">{{ worstRisk(city) }}</span>
            </button>
          </nav>

          <div class="detail-panel">
            <div v-if="selectedCity" class="escalation-summary glass-panel" :class="summary.toneClass">
              <span class="summary-icon">{{ summary.icon }}</span>
              <span class="summary-text">{{ summary.text }}</span>
            </div>

            <div v-if="selectedCity" class="timeline-strip glass-panel">
              <div class="timeline-track">
                <template v-for="(day, index) in selectedCity.daily" :key="day.date">
                  <div class="timeline-node">
                    <span class="node-day-label">{{ $t('prepare.timeline.day') }} {{ index + 1 }}</span>
                    <span class="node-date">{{ formatDay(day.date) }}</span>
                    <div class="node-dot-wrap">
                      <div class="node-dot" :class="day.risk_level.toLowerCase()">
                        <span class="node-dot-inner"></span>
                      </div>
                    </div>
                    <span class="node-risk-label" :class="day.risk_level.toLowerCase()">{{ day.risk_level }}</span>
                    <span
                      class="node-confidence"
                      :class="confidenceClass(day.confidence_pct)"
                      :title="confidenceTooltip(day)"
                    >{{ day.confidence_pct.toFixed(0) }}% {{ $t('prepare.timeline.agreement') }} &middot; {{ confidenceLabel(day.confidence_pct) }} <span class="info-hint" aria-hidden="true">ⓘ</span></span>
                    <span class="node-weather">{{ weatherIcon(day.dominant_weather) }} {{ day.dominant_weather }}</span>
                    <span class="node-metrics">{{ day.total_rain_mm.toFixed(0) }}mm · {{ day.max_wind_ms.toFixed(0) }}m/s</span>
                  </div>
                  <div
                    v-if="index < selectedCity.daily.length - 1"
                    class="timeline-connector"
                    :class="[day.risk_level.toLowerCase(), connectorTrend(day.risk_level, selectedCity.daily[index + 1].risk_level)]"
                  ></div>
                </template>
              </div>
            </div>

            
            <div v-if="selectedCity && hasQualifyingDay" class="evac-panel glass-panel">
              <div class="evac-header">
                <div class="evac-heading">
                  <h3>{{ $t('prepare.timeline.evacTitle') }}</h3>
                  <span class="evac-subtext">
                    {{ selectedCity.city }}'s {{ $t('prepare.timeline.evacDesc') }}
                  </span>
                </div>
                <button
                  type="button"
                  class="evac-calc-btn"
                  :disabled="evacLoading"
                  @click="fetchEvacuationRoutes"
                >
                  {{ evacLoading ? $t('prepare.timeline.calculating') : (evacRoutes.length ? $t('prepare.timeline.recalculate') : $t('prepare.timeline.precalculate')) }}
                </button>
              </div>

              <p v-if="evacError" class="evac-error">⚠️ {{ evacError }}</p>

              <div v-if="evacRoutes.length" class="evac-routes">
                <div v-for="route in evacRoutes" :key="route.route_id" class="evac-route-card">
                  <span class="evac-route-name">{{ route.name }}</span>
                  <span class="evac-route-metric">{{ route.distance_km.toFixed(1) }} km</span>
                  <span class="evac-route-metric">{{ route.estimated_time_hours.toFixed(1) }} {{ $t('prepare.timeline.hrs') }}</span>
                  <span class="evac-route-safety">{{ $t('prepare.timeline.safety') }} {{ route.safety_score }}/100</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import Header from '@/components/organisms/Header.vue'
import { useMockMode } from '@/composables/useMockMode'
import { usePrepareForecastStore, type PrepareCityForecast, type PrepareDailyForecast } from '@/stores'

type CityForecast = PrepareCityForecast

const { fetchWithMockMode } = useMockMode()

const apiHost = () =>
  import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)

// Shared across all 4 PREPARE pages - fetched once, reused on tab switches
// instead of each page re-fetching all ~40 cities independently (see
// stores/index.ts for why this used to make every page load take minutes).
const prepareForecastStore = usePrepareForecastStore()
const { cities, loading, error } = storeToRefs(prepareForecastStore)
const selectedKey = ref('')

const RISK_RANK: Record<string, number> = { GREEN: 0, YELLOW: 1, ORANGE: 2, RED: 3 }

const COUNTRY_NAMES: Record<string, string> = {
  IN: 'India', NP: 'Nepal', CN: 'China', HK: 'Hong Kong', BD: 'Bangladesh',
  PK: 'Pakistan', TH: 'Thailand', VN: 'Vietnam', SG: 'Singapore', MY: 'Malaysia',
  IQ: 'Iraq', AE: 'UAE', ET: 'Ethiopia', KE: 'Kenya', RW: 'Rwanda', US: 'United States',
}
const countryName = (code: string) => COUNTRY_NAMES[code] || code

const WEATHER_ICONS: Record<string, string> = {
  clear: '☀️', clouds: '☁️', rain: '🌧️', drizzle: '🌦️', thunderstorm: '⛈️',
  snow: '❄️', mist: '🌫️', fog: '🌫️', haze: '🌫️', smoke: '🌫️',
  dust: '🌪️', sand: '🌪️', ash: '🌋', squall: '💨', tornado: '🌪️',
}
const weatherIcon = (label: string) => WEATHER_ICONS[(label || '').toLowerCase()] || '🌡️'

// PR9 (confidence-based alerting): confidence_pct is the % of that day's own
// 3-hour forecast entries that agreed with the chosen risk_level - a high
// number means the whole day pointed the same way, a low number means only
// a brief spike drove the color. Styled as its own tier so a low-agreement
// RED doesn't read as confidently as a high-agreement one.
const confidenceClass = (pct: number): string => {
  if (pct >= 70) return 'confidence-high'
  if (pct >= 40) return 'confidence-medium'
  return 'confidence-low'
}

// Plain-language tier word shown inline next to the raw percentage. The
// hover tooltip (confidenceTooltip below) spells the metric out in full,
// but a recorded demo video can't show a hover state, so the percentage
// alone ("13% agreement") previously meant nothing to a first-time viewer
// without reading the tooltip - this makes the row self-explanatory at a
// glance, in the video and in the app.
const confidenceLabel = (pct: number): string => {
  if (pct >= 70) return 'High confidence'
  if (pct >= 40) return 'Medium confidence'
  return 'Low confidence'
}

const confidenceTooltip = (day: PrepareDailyForecast): string => {
  const base = `${day.confidence_pct.toFixed(0)}% of this day's 3-hour forecast readings agreed with the ${day.risk_level} call.`
  if (day.alert_recommended) {
    return `${base} Confidence is high enough to act on.`
  }
  if (day.risk_level === 'GREEN') {
    return base
  }
  return `${base} Below the 70% bar for an auto-recommended alert - likely a brief spike rather than a sustained risk.`
}

const cityKey = (city: CityForecast) => `${city.city}-${city.country}`

const worstRisk = (city: CityForecast): string => {
  return city.daily.reduce((worst, day) => (RISK_RANK[day.risk_level] > RISK_RANK[worst] ? day.risk_level : worst), 'GREEN')
}

// Worst-risk cities first, so the default selection (and the top of the
// dropdown) is whatever actually needs attention, not an alphabetical pick.
const sortedCities = computed(() => {
  return [...cities.value].sort((a, b) => RISK_RANK[worstRisk(b)] - RISK_RANK[worstRisk(a)])
})

const selectedCity = computed<CityForecast | null>(() => {
  return cities.value.find(c => cityKey(c) === selectedKey.value) || null
})

// PR5: whether this city has any day worth pre-calculating evacuation
// routes for - mirrors the backend's own gate (non-GREEN + PR9 confidence
// >= 70) so the button only appears when the backend would actually do
// something with it.
const hasQualifyingDay = computed(() => {
  return !!selectedCity.value?.daily.some(day => day.alert_recommended)
})

interface EvacRoute {
  route_id: string
  name: string
  distance_km: number
  estimated_time_hours: number
  safety_score: number
}

const evacLoading = ref(false)
const evacError = ref('')
const evacRoutes = ref<EvacRoute[]>([])

const fetchEvacuationRoutes = async () => {
  const city = selectedCity.value
  if (!city) return

  evacLoading.value = true
  evacError.value = ''

  try {
    const host = apiHost()
    const params = new URLSearchParams({ city: city.city, country: city.country })
    const response = await fetchWithMockMode(`${host}/api/v1/prepare/evacuation-routes?${params}`)
    const json = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new Error(json.detail || `Backend returned ${response.status}`)
    }
    evacRoutes.value = json.routes || []
    if (json.status === 'not_needed') {
      evacError.value = json.reason || "This city's forecast no longer qualifies for route pre-calculation."
    }
  } catch (e) {
    evacRoutes.value = []
    evacError.value = e instanceof Error ? e.message : 'Unknown error pre-calculating routes'
  } finally {
    evacLoading.value = false
  }
}

// A stale route set/error from the previous city shouldn't linger once the
// operator switches to a different one.
watch(selectedKey, () => {
  evacRoutes.value = []
  evacError.value = ''
})

const formatDay = (dateStr: string): string => {
  const d = new Date(dateStr)
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

// A connector is "rising" if risk increases from one day to the next, "falling"
// if it eases, "flat" otherwise - drives the connector's color/thickness so the
// trajectory itself (not just each day's color) reads at a glance.
const connectorTrend = (from: string, to: string): string => {
  const diff = RISK_RANK[to] - RISK_RANK[from]
  if (diff > 0) return 'rising'
  if (diff < 0) return 'falling'
  return 'flat'
}

// Plain-language summary of the whole trajectory: when risk peaks, what it
// peaks at, and whether it's still climbing, already past its peak, or flat
// the entire week - the actual "Day 5: YELLOW, Day 3: ORANGE, Day 1: RED"
// escalation story PR7 is meant to tell, derived from real forecast data.
const summary = computed(() => {
  const city = selectedCity.value
  if (!city || city.daily.length === 0) {
    return { text: '', icon: '📈', toneClass: 'green' }
  }

  const daily = city.daily
  let peakIndex = 0
  for (let i = 1; i < daily.length; i++) {
    if (RISK_RANK[daily[i].risk_level] > RISK_RANK[daily[peakIndex].risk_level]) peakIndex = i
  }
  const peak = daily[peakIndex]
  const peakLabel = `Day ${peakIndex + 1} (${formatDay(peak.date)})`

  if (peak.risk_level === 'GREEN') {
    return { text: `${city.city} stays GREEN across all ${daily.length} days - no escalation expected.`, icon: '✅', toneClass: 'green' }
  }

  const isStillRising = peakIndex === daily.length - 1 && RISK_RANK[peak.risk_level] > RISK_RANK[daily[0].risk_level]
  const afterPeakEases = peakIndex < daily.length - 1 && RISK_RANK[daily[daily.length - 1].risk_level] < RISK_RANK[peak.risk_level]

  let trendText = ''
  if (isStillRising) trendText = 'and is still climbing at the end of the window'
  else if (afterPeakEases) trendText = `then eases back to ${daily[daily.length - 1].risk_level} by Day ${daily.length}`
  else trendText = 'then holds'

  return {
    text: `${city.city} escalates to ${peak.risk_level} by ${peakLabel} - ${peak.dominant_weather.toLowerCase()}, ${peak.total_rain_mm.toFixed(0)}mm expected - ${trendText}.`,
    icon: peak.risk_level === 'RED' ? '🔴' : peak.risk_level === 'ORANGE' ? '🟠' : '🟡',
    toneClass: peak.risk_level.toLowerCase(),
  }
})

onMounted(async () => {
  // If another PREPARE page already loaded fresh forecast data, this
  // resolves immediately and the watch(cities, ...) below picks the
  // default selection from what's already there.
  await prepareForecastStore.ensureLoaded(fetchWithMockMode)
  if (cities.value.length > 0 && !selectedCity.value) {
    selectedKey.value = cityKey(sortedCities.value[0])
  }
})

// Guard against the selected city disappearing from a future fetch (data refresh).
watch(cities, (newCities) => {
  if (newCities.length > 0 && !selectedCity.value) {
    selectedKey.value = cityKey(sortedCities.value[0])
  }
})
</script>

<style scoped>
/* Tactical Loading Animation (matches ForecastDashboard.vue) */
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

.timeline-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.timeline-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.timeline-hero {
  padding: 18px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  background: var(--accent-cyan-soft);
}

.hero-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hero-left h2 {
  margin: 0;
  font-size: 20px;
  color: var(--accent-cyan);
}

.hero-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Master-detail layout: an always-visible, worst-first city list beside the
   detail panel, so every city's status is scannable at once - no dropdown
   to open/scroll/close per city. */
.master-detail {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
  align-items: flex-start;
}

.city-rail {
  flex: 0 0 260px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  max-height: 70vh;
  overflow-y: auto;
  /* Themed scrollbar instead of the browser's default light-gray one, which
     clashes against this panel's dark background. The mobile media query
     below already themes this for horizontal scrolling; this covers the
     vertical desktop case the same way. */
  scrollbar-width: thin;
  scrollbar-color: var(--accent-primary, #22d3ee) transparent;
}

.city-rail::-webkit-scrollbar {
  width: 6px;
}

.city-rail::-webkit-scrollbar-button {
  display: none;
  width: 0;
  height: 0;
}

.city-rail::-webkit-scrollbar-track {
  background: transparent;
}

.city-rail::-webkit-scrollbar-thumb {
  background: var(--accent-primary, #22d3ee);
  border-radius: 3px;
}

.rail-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.rail-item:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateX(4px);
}

.rail-item.active {
  background: rgba(56, 189, 248, 0.2);
  border-color: rgba(56, 189, 248, 0.5);
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.3), inset 0 0 8px rgba(56, 189, 248, 0.1);
}

.rail-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
}

.rail-item.green .rail-dot { background: #22c55e; }
.rail-item.yellow .rail-dot { background: #eab308; box-shadow: 0 0 4px rgba(234, 179, 8, 0.35); }
.rail-item.orange .rail-dot { background: #f97316; box-shadow: 0 0 6px rgba(249, 115, 22, 0.45); }
.rail-item.red .rail-dot { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.55); }

.rail-text {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.rail-name {
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rail-country {
  font-size: 11px;
  color: var(--text-secondary);
}

.rail-risk {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.06em;
  flex-shrink: 0;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
}

.rail-item.green .rail-risk {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.15);
  text-shadow: 0 0 4px rgba(34, 197, 94, 0.3);
}

.rail-item.yellow .rail-risk {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.15);
  text-shadow: 0 0 4px rgba(251, 191, 36, 0.3);
}

.rail-item.orange .rail-risk {
  color: #fb923c;
  background: rgba(251, 147, 60, 0.2);
  text-shadow: 0 0 4px rgba(251, 147, 60, 0.4);
}

.rail-item.red .rail-risk {
  color: #fca5a5;
  background: rgba(252, 165, 165, 0.15);
  text-shadow: 0 0 4px rgba(252, 165, 165, 0.3);
}

.detail-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.escalation-summary {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-left: 4px solid var(--glass-border);
}

.escalation-summary.green { border-left-color: #22c55e; }
.escalation-summary.yellow { border-left-color: #eab308; }
.escalation-summary.orange { border-left-color: #f97316; }
.escalation-summary.red { border-left-color: #ef4444; }

.summary-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.summary-text {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
}

.timeline-strip {
  padding: 32px 24px;
  overflow-x: auto;
  position: relative;
  scrollbar-width: thin;
  scrollbar-color: var(--accent-primary, #22d3ee) transparent;
}

.timeline-strip::-webkit-scrollbar {
  height: 6px;
}

.timeline-strip::-webkit-scrollbar-button {
  display: none;
  width: 0;
  height: 0;
}

.timeline-strip::-webkit-scrollbar-track {
  background: transparent;
}

.timeline-strip::-webkit-scrollbar-thumb {
  background: var(--accent-primary, #22d3ee);
  border-radius: 3px;
}

.timeline-track {
  display: flex;
  align-items: flex-start;
  min-width: min-content;
}

.evac-panel {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.evac-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.evac-heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.evac-heading h3 {
  font-size: 15px;
  margin: 0;
}

.evac-subtext {
  font-size: 12px;
  color: var(--text-muted);
  max-width: 560px;
}

.evac-calc-btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid rgba(249, 115, 22, 0.6);
  background: rgba(249, 115, 22, 0.25);
  color: #fb923c;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 0 1px rgba(249, 115, 22, 0.2);
}

.evac-calc-btn:hover:not(:disabled) {
  background: rgba(249, 115, 22, 0.35);
  border-color: rgba(249, 115, 22, 0.8);
  box-shadow: 0 0 8px rgba(249, 115, 22, 0.4), inset 0 0 6px rgba(249, 115, 22, 0.1);
  transform: translateY(-2px);
}

.evac-calc-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.evac-error {
  font-size: 12px;
  color: #eab308;
  margin: 0;
}

.evac-routes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}

.evac-route-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.evac-route-name {
  font-size: 12px;
  font-weight: 700;
}

.evac-route-metric {
  font-size: 11px;
  color: var(--text-muted);
}

.evac-route-safety {
  font-size: 11px;
  color: #22c55e;
  font-weight: 600;
}

.timeline-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 120px;
  text-align: center;
  padding: 12px 8px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.timeline-node:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.node-day-label {
  font-size: 12px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.65);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.node-date {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

.node-dot-wrap {
  padding: 8px 0;
}

.node-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid currentColor;
}

.node-dot-inner {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: currentColor;
}

.node-dot.green { color: #22c55e; box-shadow: 0 0 12px rgba(34, 197, 94, 0.3); }
.node-dot.yellow { color: #eab308; box-shadow: 0 0 12px rgba(234, 179, 8, 0.35); }
.node-dot.orange { color: #f97316; box-shadow: 0 0 14px rgba(249, 115, 22, 0.4); }
.node-dot.red { color: #ef4444; box-shadow: 0 0 16px rgba(239, 68, 68, 0.5); }

.node-risk-label {
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.4px;
  padding: 3px 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.06);
}

.node-risk-label.green {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.12);
  text-shadow: 0 0 4px rgba(34, 197, 94, 0.3);
}

.node-risk-label.yellow {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.12);
  text-shadow: 0 0 4px rgba(251, 191, 36, 0.3);
}

.node-risk-label.orange {
  color: #fb923c;
  background: rgba(251, 147, 60, 0.15);
  text-shadow: 0 0 4px rgba(251, 147, 60, 0.3);
}

.node-risk-label.red {
  color: #fca5a5;
  background: rgba(252, 165, 165, 0.12);
  text-shadow: 0 0 4px rgba(252, 165, 165, 0.3);
}

.node-confidence {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.2px;
  padding: 2px 8px;
  border-radius: 999px;
  cursor: help;
}

.info-hint {
  font-size: 9px;
  opacity: 0.75;
}

.node-confidence.confidence-high {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.12);
}

.node-confidence.confidence-medium {
  color: #eab308;
  background: rgba(234, 179, 8, 0.12);
}

.node-confidence.confidence-low {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.12);
}

.node-weather {
  font-size: 13px;
  color: var(--text-primary);
}

.node-metrics {
  font-size: 11px;
  color: var(--text-muted);
}

.timeline-connector {
  height: 3px;
  flex: 1;
  min-width: 40px;
  margin-top: 55px;
  border-radius: 2px;
  opacity: 0.6;
}

.timeline-connector.green { background: #22c55e; }
.timeline-connector.yellow { background: #eab308; }
.timeline-connector.orange { background: #f97316; }
.timeline-connector.red { background: #ef4444; }

.timeline-connector.rising { opacity: 1; height: 4px; }
.timeline-connector.falling { opacity: 0.35; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  gap: 16px;
  margin: auto;
}

.empty-icon {
  font-size: 64px;
}

.empty-state h3 {
  margin: 0;
  font-size: 18px;
}

.empty-state p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  max-width: 420px;
}

@media (max-width: 768px) {
  .timeline-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  /* Stack the city rail above the detail panel, and lay it out as a
     horizontally scrollable row of compact chips rather than a tall
     vertical list eating the screen before the timeline even shows. */
  .master-detail {
    flex-direction: column;
  }

  .city-rail {
    flex: 0 0 auto;
    flex-direction: row;
    max-height: none;
    overflow-x: auto;
    overflow-y: hidden;
    width: 100%;
    position: relative;
    scrollbar-width: thin;
    scrollbar-color: var(--accent-primary, #22d3ee) transparent;
  }

  .city-rail::-webkit-scrollbar {
    height: 6px;
  }

  .city-rail::-webkit-scrollbar-button {
    display: none;
    width: 0;
    height: 0;
  }

  .city-rail::-webkit-scrollbar-track {
    background: transparent;
  }

  .city-rail::-webkit-scrollbar-thumb {
    background: var(--accent-primary, #22d3ee);
    border-radius: 3px;
  }

  .rail-item {
    flex: 0 0 auto;
    min-width: 150px;
  }

  .timeline-node {
    min-width: 90px;
  }
}

@media (max-width: 480px) {
  .timeline-screen {
    padding: 8px;
    gap: 8px;
  }

  .timeline-container {
    gap: 12px;
  }

  .timeline-strip {
    padding: 20px 12px;
  }

  .timeline-strip::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    bottom: 6px;
    width: 32px;
    background: linear-gradient(to right, transparent, rgba(10, 14, 22, 0.85));
    pointer-events: none;
  }

  .city-rail {
    padding: 8px;
  }

  .city-rail::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    bottom: 6px;
    width: 24px;
    background: linear-gradient(to right, transparent, rgba(10, 14, 22, 0.85));
    pointer-events: none;
  }
}
</style>
