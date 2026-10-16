<template>
  <div class="prepare-screen forecast-screen">
    <Header />

    <div class="forecast-container">
      <!-- Only block the whole page on the true first load (no cities yet) -
           see the matching comment in AgencyAlerts.vue for why. -->
      <div v-if="loading && cities.length === 0" class="empty-state glass-panel tactical-loading-container">
        <div class="radar-ping-ring">
          <span class="radar-dot"></span>
        </div>
        <div class="loading-telemetry-text">
          <strong class="cycling-step-text">{{ $t('prepare.fetchingForecast') }}</strong>
        </div>
        <div class="tactical-progress-track">
          <div class="tactical-scan-laser"></div>
        </div>
      </div>

      <div v-else-if="error && cities.length === 0" class="empty-state glass-panel">
        <div class="empty-icon">⚠️</div>
        <h3>{{ $t('prepare.forecast.loadError') }}</h3>
        <p>{{ error }}</p>
      </div>

      <div v-else-if="cities.length === 0" class="empty-state glass-panel">
        <div class="empty-icon">🌦️</div>
        <h3>{{ $t('prepare.noForecastData') }}</h3>
        <p>{{ $t('prepare.noForecastDesc') }}</p>
      </div>

      <template v-else>
        <div class="forecast-hero glass-panel">
          <div class="hero-left">
            <h2>{{ $t('prepare.forecast.title') }}</h2>
            <div class="hero-meta-row">
              <span class="hero-meta">{{ cities.length }} {{ $t('prepare.forecast.citiesMonitored') }} &middot; {{ lastUpdatedText }}</span>

              <!-- PR10: Source of Truth. Audits the data behind every PREPARE
                   feature on this page (and PR9's alerts / PR5's routes, which
                   both build on the same fetch) - not whether the weather
                   prediction is right, but whether what's displayed is actually
                   backed by fresh, complete, sufficiently-sampled data.
                   Deliberately a small pill next to the meta line (not a
                   full-width banner) so it reads as supporting detail, not a
                   second headline - but it still needs to look clickable on
                   its own, so it spells out "Details" next to the arrow
                   instead of relying on a bare chevron or a hover-only cue. -->
              <button
                type="button"
                class="sot-chip"
                :class="sotStatusClass"
                :title="sotExpanded ? 'Hide data verification details' : 'Click to see data verification details'"
                :aria-expanded="sotExpanded"
                @click="sotExpanded = !sotExpanded"
              >
                <span class="sot-icon">{{ sotStatusIcon }}</span>
                <span class="sot-label">{{ $t('prepare.forecast.sourceOfTruth') }}</span>
                <span class="sot-divider">·</span>
                <span class="sot-text">{{ sotStatusText }}</span>
                <span class="sot-chevron">Details {{ sotExpanded ? '▲' : '▼' }}</span>
              </button>
            </div>
          </div>
          <div class="hero-summary">
            <div v-for="level in ['RED', 'ORANGE', 'YELLOW', 'GREEN']" :key="level" class="summary-pill" :class="level.toLowerCase()">
              <span class="summary-count">{{ riskCounts[level] }}</span>
              <span class="summary-label">{{ level }}</span>
            </div>
          </div>
        </div>

        <div v-if="sotExpanded" class="sot-details glass-panel">
          <div v-if="sotLoading" class="sot-detail-row">Checking...</div>
          <div v-else-if="sotError" class="sot-detail-row sot-error">
            <span>⚠️ {{ sotError }}</span>
            <button type="button" class="sot-retry-btn" @click="fetchSourceOfTruth">{{ $t('prepare.forecast.retry') }}</button>
          </div>
          <template v-else-if="sourceOfTruth">
            <div class="sot-detail-row">
              <strong>Freshness:</strong>
              <span v-if="sourceOfTruth.freshness.note">{{ sourceOfTruth.freshness.note }}</span>
              <span v-else>
                Cache is {{ sourceOfTruth.freshness.cache_age_seconds }}s old
                (TTL {{ sourceOfTruth.freshness.cache_ttl_seconds }}s) -
                {{ sourceOfTruth.freshness.stale ? 'stale' : 'fresh' }}
              </span>
            </div>
            <div class="sot-detail-row">
              <strong>Completeness:</strong>
              {{ sourceOfTruth.completeness.returned_city_count }} / {{ sourceOfTruth.completeness.monitored_city_count }} monitored cities returned.
              <span v-if="sourceOfTruth.completeness.note">{{ sourceOfTruth.completeness.note }}</span>
              <span v-else-if="sourceOfTruth.completeness.missing_cities.length">
                Missing: {{ sourceOfTruth.completeness.missing_cities.map((c: any) => c.city).join(', ') }}
              </span>
            </div>
            <div class="sot-detail-row">
              <strong>Sufficiency:</strong>
              {{ sourceOfTruth.sufficiency.total_days_checked }} forecast days checked;
              {{ sourceOfTruth.sufficiency.cities_with_thin_days.length }}
              {{ sourceOfTruth.sufficiency.cities_with_thin_days.length === 1 ? 'city has' : 'cities have' }}
              at least one day built from too few readings to fully trust its confidence score.
            </div>
          </template>
        </div>

        <div class="country-filter">
          <button
            class="filter-chip"
            :class="{ active: selectedCountry === 'ALL' }"
            @click="selectedCountry = 'ALL'"
          >
            All <span class="filter-count">{{ cities.length }}</span>
          </button>
          <button
            v-for="group in countryGroups"
            :key="group.country"
            class="filter-chip"
            :class="{ active: selectedCountry === group.country, [group.worstRisk.toLowerCase()]: true }"
            @click="selectedCountry = group.country"
          >
            <img v-if="!failedFlags.has(group.country)" :src="flagUrl(group.country)" :alt="countryMeta(group.country).name" class="filter-flag" @error="onFlagError(group.country)" />
            <span v-else class="flag-fallback">{{ group.country }}</span>
            {{ countryMeta(group.country).name }} <span class="filter-count">{{ group.cities.length }}</span>
          </button>
        </div>

        <div class="country-sections">
          <section v-for="group in filteredGroups" :key="group.country" class="country-section">
            <div class="country-header" :class="group.worstRisk.toLowerCase()">
              <img v-if="!failedFlags.has(group.country)" :src="flagUrl(group.country)" :alt="countryMeta(group.country).name" class="country-flag" @error="onFlagError(group.country)" />
              <span v-else class="flag-fallback flag-fallback-lg">{{ group.country }}</span>
              <span class="country-name">{{ countryMeta(group.country).name }}</span>
              <span class="country-count">{{ group.cities.length }} {{ group.cities.length === 1 ? 'city' : 'cities' }}</span>

              <!-- Sort control only makes sense once there's more than a
                   couple of cities to reorder - with 1-2 cities, "sorted by
                   risk" and "sorted by name" look identical, so the toggle
                   would just be a confusing no-op. -->
              <div v-if="group.cities.length > 2" class="sort-toggle">
                <button
                  type="button"
                  class="sort-btn"
                  :class="{ active: citySortMode === 'risk' }"
                  @click="citySortMode = 'risk'"
                >{{ $t('prepare.forecast.sortRisk') }}</button>
                <button
                  type="button"
                  class="sort-btn"
                  :class="{ active: citySortMode === 'name' }"
                  @click="citySortMode = 'name'"
                >{{ $t('prepare.forecast.sortName') }}</button>
              </div>

              <span class="country-worst" :class="group.worstRisk.toLowerCase()">{{ riskEmoji(group.worstRisk) }} {{ group.worstRisk }}</span>
            </div>

            <div class="city-grid">
              <div v-for="city in sortedCities(group)" :key="`${city.city}-${city.country}`" class="city-card glass-panel" :class="worstRisk(city).toLowerCase()">
                <div class="city-header">
                  <span class="city-name">{{ city.city }}</span>
                  <span class="worst-badge" :class="worstRisk(city).toLowerCase()">{{ riskEmoji(worstRisk(city)) }} {{ worstRisk(city) }}</span>
                </div>

                <div class="day-row">
                  <div v-for="day in city.daily" :key="day.date" class="day-chip" :class="day.risk_level.toLowerCase()">
                    <span class="day-date">{{ formatDay(day.date) }}</span>
                    <span class="day-icon">{{ weatherIcon(day.dominant_weather) }}</span>
                    <span class="day-weather">{{ day.dominant_weather }}</span>
                    <span class="day-metrics">{{ day.total_rain_mm.toFixed(0) }}mm · {{ day.max_wind_ms.toFixed(0) }}m/s</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import Header from '@/components/organisms/Header.vue'
import { useMockMode } from '@/composables/useMockMode'
import { usePrepareForecastStore, type PrepareCityForecast } from '@/stores'

type CityForecast = PrepareCityForecast

interface CountryGroup {
  country: string
  cities: CityForecast[]
  worstRisk: string
}

const { fetchWithMockMode } = useMockMode()
const { locale, t } = useI18n()

const apiHost = () =>
  import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)

// Shared across all 4 PREPARE pages - fetched once, reused on tab switches
// instead of each page re-fetching all ~40 cities independently (see
// stores/index.ts for why this used to make every page load take minutes).
const prepareForecastStore = usePrepareForecastStore()
const { cities, loading, error, lastFetchedAt } = storeToRefs(prepareForecastStore)

// Real elapsed time since the store's own fetch, not a fabricated "just
// synced" label - lastFetchedAt is set once by ensureLoaded() in
// stores/index.ts right after a successful response, and is the same
// timestamp AgencyAlerts/RiskTimeline/PreparednessChecklist share. Ticks
// every 30s via nowTick so "2 min ago" doesn't go stale while the page
// sits open; Intl.RelativeTimeFormat localizes the wording itself (so
// German gets "vor 2 Minuten" etc.) without a separate translation key
// per language for every possible minute count.
const nowTick = ref(Date.now())
let nowTickInterval: ReturnType<typeof setInterval> | undefined

const lastUpdatedText = computed(() => {
  if (!lastFetchedAt.value) return ''
  const diffSeconds = Math.round((lastFetchedAt.value - nowTick.value) / 1000)
  if (Math.abs(diffSeconds) < 10) {
    return t('prepare.forecast.lastUpdatedJustNow')
  }
  try {
    const rtf = new Intl.RelativeTimeFormat(locale.value, { numeric: 'auto' })
    const diffMinutes = Math.round(diffSeconds / 60)
    const relative = Math.abs(diffMinutes) < 60
      ? rtf.format(diffMinutes, 'minute')
      : rtf.format(Math.round(diffMinutes / 60), 'hour')
    return t('prepare.forecast.lastUpdated', { time: relative })
  } catch {
    return ''
  }
})

const RISK_RANK: Record<string, number> = { GREEN: 0, YELLOW: 1, ORANGE: 2, RED: 3 }
const RISK_EMOJI: Record<string, string> = { GREEN: '🟢', YELLOW: '🟡', ORANGE: '🟠', RED: '🔴' }

// Country metadata is purely cosmetic (display name for the grouping header) -
// it never changes risk calculation, which stays entirely backend-derived.
const COUNTRY_META: Record<string, { name: string }> = {
  IN: { name: 'India' },
  NP: { name: 'Nepal' },
  CN: { name: 'China' },
  HK: { name: 'Hong Kong' },
  BD: { name: 'Bangladesh' },
  PK: { name: 'Pakistan' },
  TH: { name: 'Thailand' },
  VN: { name: 'Vietnam' },
  SG: { name: 'Singapore' },
  MY: { name: 'Malaysia' },
  IQ: { name: 'Iraq' },
  AE: { name: 'UAE' },
  ET: { name: 'Ethiopia' },
  KE: { name: 'Kenya' },
  RW: { name: 'Rwanda' },
  US: { name: 'United States' },
}

const countryMeta = (code: string) => COUNTRY_META[code] || { name: code }

// Real flag images instead of flag emoji - emoji flags render as plain two-letter
// text on Windows (no flag-emoji glyphs in its default font stack until very
// recently), so they showed up as "IN"/"NP" instead of pictures. flagcdn.com
// serves small flag PNGs by ISO 3166-1 alpha-2 code, which renders identically
// across every OS/browser.
const flagUrl = (code: string) => `https://flagcdn.com/w40/${code.toLowerCase()}.png`

// If flagcdn.com is ever unreachable for a visitor, swap the broken-image
// icon for the ISO country code as text instead of just hiding it - an
// empty gap where a flag should be reads as a layout bug, while "IN"/"NP"
// at least still carries the information the flag was there to show.
const failedFlags = ref<Set<string>>(new Set())
const onFlagError = (countryCode: string) => {
  failedFlags.value.add(countryCode)
}

const riskEmoji = (level: string) => RISK_EMOJI[level] || '🟢'

const WEATHER_ICONS: Record<string, string> = {
  clear: '☀️',
  clouds: '☁️',
  rain: '🌧️',
  drizzle: '🌦️',
  thunderstorm: '⛈️',
  snow: '❄️',
  mist: '🌫️',
  fog: '🌫️',
  haze: '🌫️',
  smoke: '🌫️',
  dust: '🌪️',
  sand: '🌪️',
  ash: '🌋',
  squall: '💨',
  tornado: '🌪️',
}

const weatherIcon = (label: string) => WEATHER_ICONS[(label || '').toLowerCase()] || '🌡️'

const worstRisk = (city: CityForecast): string => {
  return city.daily.reduce((worst, day) => {
    return RISK_RANK[day.risk_level] > RISK_RANK[worst] ? day.risk_level : worst
  }, 'GREEN')
}

// Group by country, each group's cities sorted worst-risk-first, and the
// groups themselves sorted worst-risk-first - a country with a RED city
// surfaces before an all-GREEN one, same principle as the old flat sort,
// just organized the way the data actually comes in (country by country).
const countryGroups = computed<CountryGroup[]>(() => {
  const byCountry = new Map<string, CityForecast[]>()
  for (const city of cities.value) {
    if (!byCountry.has(city.country)) byCountry.set(city.country, [])
    byCountry.get(city.country)!.push(city)
  }

  const groups: CountryGroup[] = Array.from(byCountry.entries()).map(([country, countryCities]) => {
    const sortedCities = [...countryCities].sort((a, b) => RISK_RANK[worstRisk(b)] - RISK_RANK[worstRisk(a)])
    const worst = sortedCities.reduce((w, c) => (RISK_RANK[worstRisk(c)] > RISK_RANK[w] ? worstRisk(c) : w), 'GREEN')
    return { country, cities: sortedCities, worstRisk: worst }
  })

  return groups.sort((a, b) => {
    const riskDiff = RISK_RANK[b.worstRisk] - RISK_RANK[a.worstRisk]
    if (riskDiff !== 0) return riskDiff
    return countryMeta(a.country).name.localeCompare(countryMeta(b.country).name)
  })
})

// Per-country sort toggle. countryGroups already sorts cities worst-risk-
// first by default (unchanged) - this only lets the user flip a given
// country's own city list to alphabetical when they want to scan for a
// specific place instead of triaging by severity. Shared across all
// country sections rather than per-section state, since a judge comparing
// two countries side by side expects the same ordering convention in both.
const citySortMode = ref<'risk' | 'name'>('risk')

const sortedCities = (group: CountryGroup): CityForecast[] => {
  if (citySortMode.value === 'risk') return group.cities
  return [...group.cities].sort((a, b) => a.city.localeCompare(b.city))
}

const selectedCountry = ref<string>('ALL')

const filteredGroups = computed<CountryGroup[]>(() => {
  if (selectedCountry.value === 'ALL') return countryGroups.value
  return countryGroups.value.filter(g => g.country === selectedCountry.value)
})

const riskCounts = computed(() => {
  const counts: Record<string, number> = { RED: 0, ORANGE: 0, YELLOW: 0, GREEN: 0 }
  for (const city of cities.value) {
    counts[worstRisk(city)]++
  }
  return counts
})

const formatDay = (dateStr: string): string => {
  const d = new Date(dateStr)
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

// PR10: Source of Truth
interface SourceOfTruth {
  overall: 'verified' | 'degraded'
  freshness: { cache_age_seconds: number | null; cache_ttl_seconds: number; stale: boolean; note: string | null }
  completeness: { monitored_city_count: number; returned_city_count: number; missing_cities: Array<{ city: string; country: string }>; note: string | null }
  sufficiency: { total_days_checked: number; cities_with_thin_days: Array<{ city: string; country: string; thin_days: unknown[] }> }
}

const sourceOfTruth = ref<SourceOfTruth | null>(null)
const sotLoading = ref(false)
const sotError = ref('')
const sotExpanded = ref(false)

const sotStatusClass = computed(() => {
  if (sotLoading.value) return 'checking'
  if (sotError.value) return 'unknown'
  return sourceOfTruth.value?.overall === 'verified' ? 'verified' : 'degraded'
})

const sotStatusIcon = computed(() => {
  if (sotLoading.value) return '⏳'
  if (sotError.value) return '❓'
  return sourceOfTruth.value?.overall === 'verified' ? '✅' : '⚠️'
})

const sotStatusText = computed(() => {
  // Short on purpose now that this lives as a small pill next to the meta
  // line, not a full-width banner - the "Details ▼" label already in the
  // template says explicitly that there's more to click into.
  if (sotLoading.value) return 'Verifying data source...'
  if (sotError.value) return "Couldn't verify data source"
  return sourceOfTruth.value?.overall === 'verified'
    ? 'Data source verified'
    : 'Data source degraded'
})

const fetchSourceOfTruth = async () => {
  sotLoading.value = true
  sotError.value = ''
  try {
    const host = apiHost()
    const response = await fetchWithMockMode(`${host}/api/v1/prepare/source-of-truth`)
    const json = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new Error(json.detail || `Backend returned ${response.status}`)
    }
    sourceOfTruth.value = json
  } catch (e) {
    sourceOfTruth.value = null
    sotError.value = e instanceof Error ? e.message : 'Unknown error checking data source'
  } finally {
    sotLoading.value = false
  }
}

// Keyboard navigation for country filter buttons. Defined at setup's top
// level (not inside onMounted's async callback) specifically so the
// matching onUnmounted() below is a valid, synchronous lifecycle-hook
// registration - Vue requires onUnmounted to be called while the
// component's setup is still active, which an async callback loses after
// its first await.
const handleKeyboardNavigation = (e: KeyboardEvent) => {
  const filterButtons = document.querySelectorAll('.filter-chip')
  if (filterButtons.length === 0) return

  const activeIndex = Array.from(filterButtons).findIndex((btn) => btn === document.activeElement)
  let nextIndex = activeIndex

  if (e.key === 'ArrowRight' && activeIndex < filterButtons.length - 1) {
    nextIndex = activeIndex + 1
    e.preventDefault()
  } else if (e.key === 'ArrowLeft' && activeIndex > 0) {
    nextIndex = activeIndex - 1
    e.preventDefault()
  } else {
    return
  }

  ;(filterButtons[nextIndex] as HTMLButtonElement).focus()
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeyboardNavigation)
  nowTickInterval = setInterval(() => { nowTick.value = Date.now() }, 30_000)

  await prepareForecastStore.ensureLoaded(fetchWithMockMode)
  await fetchSourceOfTruth()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyboardNavigation)
  if (nowTickInterval) clearInterval(nowTickInterval)
})
</script>

<style scoped>
.forecast-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.forecast-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: var(--accent-primary, #22d3ee) transparent;
}
.forecast-container::-webkit-scrollbar { width: 6px; }
.forecast-container::-webkit-scrollbar-button { display: none; width: 0; height: 0; }
.forecast-container::-webkit-scrollbar-track { background: transparent; }
.forecast-container::-webkit-scrollbar-thumb { background: var(--accent-primary, #22d3ee); border-radius: 3px; }

/* ---- Hero / summary strip ---- */

.forecast-hero {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
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

.hero-meta-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  /* Consistent spacing with country sections */
}

.hero-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

.hero-summary {
  display: flex;
  gap: 10px;
}

.summary-pill {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 56px;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid var(--glass-border);
}

.summary-count {
  font-size: 20px;
  font-weight: 800;
  line-height: 1.1;
}

.summary-label {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.5px;
  opacity: 0.85;
}

.summary-pill.red { background: rgba(239, 68, 68, 0.12); border-color: rgba(239, 68, 68, 0.4); color: #ef4444; }
.summary-pill.orange { background: rgba(249, 115, 22, 0.12); border-color: rgba(249, 115, 22, 0.4); color: #f97316; }
.summary-pill.yellow { background: rgba(234, 179, 8, 0.12); border-color: rgba(234, 179, 8, 0.4); color: #eab308; }
.summary-pill.green { background: rgba(34, 197, 94, 0.12); border-color: rgba(34, 197, 94, 0.4); color: #22c55e; }

/* ---- PR10: Source of Truth ----
   A compact pill next to the hero's meta line, not a full-width banner -
   it's supporting detail about data trust, not a second headline competing
   with the forecast itself. But a small chip can easily read as "just a
   label" instead of a button, so this leans on several cues at once so it's
   unambiguous: a visible border (pill/button shape, matching the
   .filter-chip buttons used elsewhere on this page), an explicit "Details ▼"
   segment (not just a bare arrow), a hover state that visibly reacts, and a
   native title tooltip for anyone who pauses over it. */
.sot-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  /* This is a <button>, and "glass-panel" in the template was never actually
     defined in this file's scoped styles - every other element wearing that
     class here (.forecast-hero, .empty-state) happens to set its own
     background directly, so the missing class never showed. This one didn't,
     so the "checking" state fell through to the browser's native button
     background (flat light gray) instead of the app's dark theme. Setting
     the background here directly instead of depending on that class. */
  background: rgba(22, 29, 39, 0.72);
  border: 1.5px solid var(--glass-border);
  border-radius: 999px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  text-align: left;
  color: var(--text-primary);
  transition: border-color 0.15s ease, background 0.15s ease, transform 0.1s ease;
}

.sot-chip:hover {
  border-color: var(--accent-cyan, #22d3ee);
  transform: translateY(-1px);
}

.sot-chip.verified { border-color: rgba(34, 197, 94, 0.4); background: rgba(34, 197, 94, 0.1); }
.sot-chip.verified:hover { border-color: rgba(34, 197, 94, 0.7); }
.sot-chip.degraded { border-color: rgba(234, 179, 8, 0.45); background: rgba(234, 179, 8, 0.14); }
.sot-chip.degraded:hover { border-color: rgba(234, 179, 8, 0.75); }
.sot-chip.checking,
.sot-chip.unknown { border-color: var(--glass-border); opacity: 0.85; }

.sot-icon {
  font-size: 15px;
}

/* Explicit "Source of Truth" label - without this the chip was just an
   unlabeled status word ("Verified" / "Data source degraded"), so it read
   as a vague warning rather than the name of the data-verification feature
   it actually is. */
.sot-label {
  font-weight: 800;
  letter-spacing: 0.2px;
  color: var(--accent-cyan, #22d3ee);
}

.sot-chip.verified .sot-label { color: #22c55e; }
.sot-chip.degraded .sot-label { color: #eab308; }

.sot-divider {
  opacity: 0.45;
}

.sot-chevron {
  font-size: 11px;
  opacity: 0.8;
  padding-left: 8px;
  border-left: 1px solid rgba(255, 255, 255, 0.15);
}

.sot-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 18px;
  /* Same missing-glass-panel-class issue as .sot-badge above. */
  background: rgba(22, 29, 39, 0.72);
  backdrop-filter: blur(14px);
  border: 1px solid var(--glass-border);
  border-radius: 10px;
}

.sot-detail-row {
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-muted);
}

.sot-detail-row strong {
  color: var(--text-primary);
  margin-right: 4px;
}

.sot-detail-row.sot-error {
  color: #eab308;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.sot-retry-btn {
  padding: 5px 14px;
  border-radius: 20px;
  border: 1px solid rgba(234, 179, 8, 0.6);
  background: rgba(234, 179, 8, 0.18);
  color: #fbbf24;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 0 1px rgba(234, 179, 8, 0.15);
}

.sot-retry-btn:hover {
  background: rgba(234, 179, 8, 0.28);
  border-color: rgba(234, 179, 8, 0.8);
  box-shadow: 0 0 8px rgba(234, 179, 8, 0.3), inset 0 0 6px rgba(234, 179, 8, 0.1);
  transform: translateY(-1px);
}

/* ---- Country filter ---- */

.country-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border-radius: 20px;
  border: 1px solid rgba(56, 189, 248, 0.25);
  background: rgba(56, 189, 248, 0.06);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
  outline-offset: 2px;
}

.filter-chip:hover {
  border-color: rgba(56, 189, 248, 0.5);
  background: rgba(56, 189, 248, 0.12);
  color: var(--text-primary);
}

.filter-chip:focus {
  outline: 2px solid var(--accent-cyan);
}

.filter-chip:focus:not(:focus-visible) {
  outline: none;
}

.filter-chip:focus-visible {
  outline: 2px solid var(--accent-cyan);
  outline-offset: 2px;
}

.filter-chip.active {
  background: rgba(56, 189, 248, 0.25);
  border-color: rgba(56, 189, 248, 0.6);
  color: #38bdf8;
  box-shadow: 0 0 8px rgba(56, 189, 248, 0.25), inset 0 0 6px rgba(56, 189, 248, 0.1);
}

.filter-chip .filter-count {
  opacity: 0.7;
  font-size: 11px;
}

.filter-chip.active .filter-count {
  opacity: 0.8;
}

.filter-flag {
  width: 16px;
  height: 12px;
  object-fit: cover;
  border-radius: 2px;
  flex-shrink: 0;
  /* Match country-flag shadow for consistency */
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08);
}

/* Text fallback shown in place of the flag image if flagcdn.com is
   unreachable - sized and weighted to sit inline without looking like an
   error state, since a missing flag isn't actually a data problem. */
.flag-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 12px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 7px;
  font-weight: 800;
  letter-spacing: 0.3px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.flag-fallback-lg {
  width: 28px;
  height: 20px;
  font-size: 9px;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08);
}

/* ---- Country sections ---- */
.country-sections {
  display: flex;
  flex-direction: column;
  gap: 20px;
  /* Consistent spacing scale throughout */
}

.country-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.country-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 8px;
  border-left: 4px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.02);
}

.country-header.red { border-left-color: #ef4444; }
.country-header.orange { border-left-color: #f97316; }
.country-header.yellow { border-left-color: #eab308; }
.country-header.green { border-left-color: #22c55e; }

.country-flag {
  width: 28px;
  height: 20px;
  object-fit: cover;
  border-radius: 3px;
  flex-shrink: 0;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.country-name {
  font-weight: 700;
  font-size: 15px;
}

.country-count {
  font-size: 12px;
  color: var(--text-muted);
}

.sort-toggle {
  display: flex;
  gap: 4px;
}

.sort-btn {
  padding: 3px 10px;
  border-radius: 12px;
  border: 1px solid var(--glass-border);
  background: transparent;
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.2px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.sort-btn:hover {
  color: var(--text-primary);
  border-color: var(--accent-cyan);
}

.sort-btn.active {
  background: var(--accent-cyan);
  border-color: var(--accent-cyan);
  color: #04141a;
}

.country-worst {
  margin-left: auto;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.3px;
}

.country-worst.green { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.country-worst.yellow { background: rgba(234, 179, 8, 0.15); color: #eab308; }
.country-worst.orange { background: rgba(249, 115, 22, 0.15); color: #f97316; }
.country-worst.red { background: rgba(239, 68, 68, 0.15); color: #ef4444; }

/* ---- City cards ---- */

.city-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
}

.city-card {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  /* Tighter padding and gaps for better density while maintaining readability */
  border-top: 3px solid var(--glass-border);
}

.city-card.red { border-top-color: #ef4444; }
.city-card.orange { border-top-color: #f97316; }
.city-card.yellow { border-top-color: #eab308; }
.city-card.green { border-top-color: #22c55e; }

.city-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.city-name {
  font-weight: 700;
  font-size: 14px;
}

.worst-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  letter-spacing: 0.3px;
  white-space: nowrap;
}

.worst-badge.green { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.worst-badge.yellow { background: rgba(234, 179, 8, 0.15); color: #eab308; }
.worst-badge.orange { background: rgba(249, 115, 22, 0.15); color: #f97316; }
.worst-badge.red { background: rgba(239, 68, 68, 0.15); color: #ef4444; }

.day-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  /* Tighter spacing to reduce density without horizontal scroll */
}

.day-chip {
  flex: 1 1 85px;
  min-width: 85px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 4px;
  border-radius: 8px;
  border: 1px solid var(--glass-border);
  font-size: 11px;
  transition: transform 0.15s ease;
  background-clip: padding-box;
}

.day-chip:hover {
  transform: translateY(-2px);
}

.day-chip.green { border-color: rgba(34, 197, 94, 0.4); background: rgba(34, 197, 94, 0.12); }
.day-chip.yellow { border-color: rgba(234, 179, 8, 0.4); background: rgba(234, 179, 8, 0.12); }
.day-chip.orange { border-color: rgba(249, 115, 22, 0.4); background: rgba(249, 115, 22, 0.12); }
.day-chip.red { border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.14); }

.day-date {
  font-weight: 700;
  font-size: 10px;
  color: var(--text-secondary);
}

.day-icon {
  font-size: 16px;
  line-height: 1;
}

.day-weather {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 10px;
  line-height: 1.2;
}

.day-metrics {
  color: var(--text-muted);
  font-size: 10px;
  margin-top: 1px;
  line-height: 1.3;
  /* Metrics now readable - font size kept at 10px, better spacing */
}

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
  .city-grid {
    grid-template-columns: 1fr;
  }

  .day-row {
    flex-wrap: wrap;
  }

  .day-chip {
    min-width: 72px;
  }

  .forecast-hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .country-header {
    flex-wrap: wrap;
  }

  .sort-toggle {
    order: 1;
    width: 100%;
    margin-left: 38px;
  }

  .country-worst {
    margin-left: auto;
  }

  .hero-summary {
    width: 100%;
    justify-content: space-between;
  }

  .summary-pill {
    flex: 1;
    min-width: 0;
  }
}

@media (max-width: 480px) {
  .forecast-screen {
    padding: 8px;
    gap: 8px;
  }

  .forecast-container {
    gap: 12px;
  }

  .forecast-hero {
    padding: 14px 16px;
  }
}

/* Tactical Loading Animation */
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
.loading-phase-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: #38bdf8;
  background: rgba(14, 165, 233, 0.1);
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid rgba(14, 165, 233, 0.2);
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

</style>
