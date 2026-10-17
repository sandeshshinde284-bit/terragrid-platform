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
              <span class="hero-meta">{{ cities.length }} {{ $t('prepare.forecast.citiesMonitored') }} &middot; {{ forecastDayCount }} {{ $t('prepare.forecast.daysForecast') }} &middot; {{ lastUpdatedText }}</span>

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
                <span class="sot-chevron">{{ sotExpanded ? 'Hide details ▲' : 'Tap to view details ▼' }}</span>
              </button>
            </div>
          </div>
          <div class="hero-summary-wrap">
            <div class="hero-summary">
              <button
                v-for="level in ['RED', 'ORANGE', 'YELLOW', 'GREEN']"
                :key="level"
                type="button"
                class="summary-pill"
                :class="[level.toLowerCase(), {
                  active: selectedRiskLevel === level,
                  dimmed: selectedRiskLevel && selectedRiskLevel !== level,
                }]"
                :title="`Show only ${level} cities${selectedCountry !== 'ALL' ? ' in ' + countryName(selectedCountry) : ''}`"
                @click="toggleRiskFilter(level)"
              >
                <span class="summary-count">{{ riskCounts[level] }}</span>
                <span class="summary-label">{{ level }}</span>
              </button>
            </div>
            <span class="risk-filter-hint">Tap a number above to filter the list by risk level</span>
          </div>
        </div>

        <!-- What needs attention first, named up front - the RED/ORANGE/
             YELLOW/GREEN pills above are aggregate counts, not a reason or
             a next step. Only rendered when something's actually non-GREEN,
             and scoped to the whole board (not the country filter) since
             this is meant to answer "what's most urgent right now", not
             "what's urgent in the currently-open tab". -->
        <div v-if="priorityIncidents.length" class="priority-strip">
          <span class="priority-strip-label">{{ $t('prepare.forecast.priorityLabel') }}</span>
          <RouterLink
            v-for="entry in priorityIncidents"
            :key="`${entry.city.city}-${entry.city.country}`"
            :to="{ name: 'PrepareRiskTimeline', query: { city: entry.city.city, country: entry.city.country } }"
            class="priority-card glass-panel"
            :class="entry.day.risk_level.toLowerCase()"
            @click="prepareForecastStore.setSelectedCity(entry.city.city, entry.city.country)"
          >
            <div class="priority-card-head">
              <span class="priority-card-badge" :class="entry.day.risk_level.toLowerCase()">{{ riskEmoji(entry.day.risk_level) }} {{ entry.day.risk_level }}</span>
              <span class="priority-card-city">{{ entry.city.city }}, {{ countryName(entry.city.country) }}</span>
            </div>
            <p class="priority-card-reason">{{ entry.day.severity_reason }}</p>
            <span class="priority-card-action">{{ $t('prepare.forecast.viewTimeline') }} →</span>
          </RouterLink>
        </div>

        <div v-if="sotExpanded" class="sot-details glass-panel">
          <div v-if="sotLoading" class="sot-detail-row">Checking...</div>
          <div v-else-if="sotError" class="sot-detail-row sot-error">
            <span>⚠️ {{ sotError }}</span>
            <button type="button" class="sot-retry-btn" @click="fetchSourceOfTruth">{{ $t('prepare.forecast.retry') }}</button>
          </div>
          <template v-else-if="sourceOfTruth">
            <!-- Each row leads with a plain-language verdict (✅/⚠️ + short
                 phrase) so it reads at a glance - the exact numbers follow
                 for anyone who wants them, but understanding the row no
                 longer requires parsing "TTL" or "thin days" jargon. -->
            <div class="sot-detail-row">
              <span class="sot-row-icon">{{ sourceOfTruth.freshness.stale ? '⚠️' : '✅' }}</span>
              <strong>Freshness</strong>
              <span class="sot-row-verdict">{{ sourceOfTruth.freshness.stale ? 'Data may be outdated' : "Data is up to date" }}</span>
              <span class="sot-row-detail" v-if="sourceOfTruth.freshness.note">{{ sourceOfTruth.freshness.note }}</span>
              <span class="sot-row-detail" v-else>
                Last refreshed {{ sourceOfTruth.freshness.cache_age_seconds }}s ago
                (we refresh every {{ sourceOfTruth.freshness.cache_ttl_seconds }}s)
              </span>
            </div>
            <div class="sot-detail-row">
              <span class="sot-row-icon">{{ sourceOfTruth.completeness.returned_city_count === sourceOfTruth.completeness.monitored_city_count ? '✅' : '⚠️' }}</span>
              <strong>Completeness</strong>
              <span class="sot-row-verdict">{{ sourceOfTruth.completeness.returned_city_count }} of {{ sourceOfTruth.completeness.monitored_city_count }} monitored cities have data</span>
              <span class="sot-row-detail" v-if="sourceOfTruth.completeness.note">{{ sourceOfTruth.completeness.note }}</span>
              <span class="sot-row-detail" v-else-if="sourceOfTruth.completeness.missing_cities.length">
                Still waiting on: {{ sourceOfTruth.completeness.missing_cities.map((c: any) => c.city).join(', ') }}
              </span>
            </div>
            <div class="sot-detail-row">
              <span class="sot-row-icon">{{ sourceOfTruth.sufficiency.cities_with_thin_days.length === 0 ? '✅' : '⚠️' }}</span>
              <strong>Sufficiency</strong>
              <span class="sot-row-verdict">
                {{ sourceOfTruth.sufficiency.cities_with_thin_days.length === 0
                  ? 'Every forecast has enough data behind it'
                  : `${sourceOfTruth.sufficiency.cities_with_thin_days.length} ${sourceOfTruth.sufficiency.cities_with_thin_days.length === 1 ? 'city has' : 'cities have'} a low-data day` }}
              </span>
              <span class="sot-row-detail">
                Checked {{ sourceOfTruth.sufficiency.total_days_checked }} forecast-days total.
                <template v-if="sourceOfTruth.sufficiency.cities_with_thin_days.length">
                  Those days are shown with a lower confidence score rather than hidden, since there weren't enough weather readings to be fully sure.
                </template>
              </span>
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
            <img v-if="!failedFlags.has(group.country)" :src="flagUrl(group.country)" :alt="countryName(group.country)" class="filter-flag" @error="onFlagError(group.country)" />
            <span v-else class="flag-fallback">{{ group.country }}</span>
            {{ countryName(group.country) }} <span class="filter-count">{{ group.cities.length }}</span>
          </button>
        </div>

        <div class="filter-status">{{ filterStatusText }}</div>

        <div class="country-sections">
          <section v-for="group in filteredGroups" :key="group.country" class="country-section">
            <div class="country-header" :class="group.worstRisk.toLowerCase()">
              <img v-if="!failedFlags.has(group.country)" :src="flagUrl(group.country)" :alt="countryName(group.country)" class="country-flag" @error="onFlagError(group.country)" />
              <span v-else class="flag-fallback flag-fallback-lg">{{ group.country }}</span>
              <span class="country-name">{{ countryName(group.country) }}</span>
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
              <RouterLink
                v-for="city in sortedCities(group)"
                :key="`${city.city}-${city.country}`"
                :to="{ name: 'PrepareRiskTimeline', query: { city: city.city, country: city.country } }"
                class="city-card glass-panel"
                :class="worstRisk(city).toLowerCase()"
                :title="`Open ${city.city}'s risk timeline`"
                @click="prepareForecastStore.setSelectedCity(city.city, city.country)"
              >
                <div class="city-header">
                  <span class="city-name">{{ city.city }}</span>
                  <span class="worst-badge" :class="worstRisk(city).toLowerCase()">{{ riskEmoji(worstRisk(city)) }} {{ worstRisk(city) }}</span>
                </div>

                <div class="day-row">
                  <div
                    v-for="day in city.daily"
                    :key="day.date"
                    class="day-chip"
                    :class="[day.risk_level.toLowerCase(), { dimmed: selectedRiskLevel && day.risk_level !== selectedRiskLevel }]"
                  >
                    <span class="day-date">{{ formatDay(day.date) }}</span>
                    <span class="day-icon">{{ weatherIcon(day.dominant_weather) }}</span>
                    <span class="day-weather">{{ day.dominant_weather }}</span>
                    <span class="day-metrics">{{ day.total_rain_mm.toFixed(0) }}mm · {{ day.max_wind_ms.toFixed(0) }}m/s</span>
                  </div>
                </div>

                <!-- Always-visible navigation cue - the hover lift/shadow
                     below alone doesn't tell a first-time (or touch-screen)
                     viewer that this card goes anywhere else. -->
                <div class="city-card-footer">
                  <span>{{ $t('prepare.forecast.viewTimeline') }}</span>
                  <span class="city-card-arrow" aria-hidden="true">→</span>
                </div>
              </RouterLink>
            </div>
          </section>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import Header from '@/components/organisms/Header.vue'
import { useMockMode } from '@/composables/useMockMode'
import { useFlagFallback, weatherIcon, worstRisk, RISK_RANK } from '@/composables/usePrepareLookups'
import { getCountryName as countryName } from '@/utils/countries'
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

const RISK_EMOJI: Record<string, string> = { GREEN: '🟢', YELLOW: '🟡', ORANGE: '🟠', RED: '🔴' }
const riskEmoji = (level: string) => RISK_EMOJI[level] || '🟢'

// Country names, risk ranking, worst-risk, flag URLs and weather icons used
// to be copy-pasted into this file independently of the other 3 PREPARE
// screens - see usePrepareLookups.ts for why that moved to one shared copy.
const { failedFlags, onFlagError, flagUrl } = useFlagFallback()

// The actual number of calendar days behind each city's forecast - computed
// from the real data instead of a hardcoded "7", since OpenWeatherMap's
// free-tier endpoint is a 5-day/3-hour-step forecast, not a 7-day one (the
// exact count can be 5 or 6 depending on time of day). Using the longest
// daily list present avoids under-reporting on the rare city whose window
// starts slightly earlier than the rest.
const forecastDayCount = computed(() => {
  return cities.value.reduce((max, city) => Math.max(max, city.daily.length), 0)
})

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
    return countryName(a.country).localeCompare(countryName(b.country))
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

// Risk-level filter (click a RED/ORANGE/YELLOW/GREEN pill above the city
// list). Works at any country scope, including "All" - clicking ORANGE
// with every country visible filters the whole board down to ORANGE
// cities globally, same as clicking it after picking one country filters
// just that country's list.
const selectedRiskLevel = ref<string | null>(null)

// Switching country (or back to "All") clears any active risk filter -
// a RED filter chosen for one country shouldn't silently carry over and
// hide cities in the next one you look at.
watch(selectedCountry, () => {
  selectedRiskLevel.value = null
})

const toggleRiskFilter = (level: string) => {
  selectedRiskLevel.value = selectedRiskLevel.value === level ? null : level
}

const filteredGroups = computed<CountryGroup[]>(() => {
  let groups = selectedCountry.value === 'ALL'
    ? countryGroups.value
    : countryGroups.value.filter(g => g.country === selectedCountry.value)

  if (selectedRiskLevel.value) {
    groups = groups
      .map(g => ({ ...g, cities: g.cities.filter(c => worstRisk(c) === selectedRiskLevel.value) }))
      .filter(g => g.cities.length > 0)
  }

  return groups
})

// Scoped to whatever country is currently selected (or every city, under
// "All") so the pill counts and the country filter always agree - picking
// a country updates the RED/ORANGE/YELLOW/GREEN counts to that country's
// own cities instead of staying pinned to the global totals.
const riskCounts = computed(() => {
  const counts: Record<string, number> = { RED: 0, ORANGE: 0, YELLOW: 0, GREEN: 0 }
  const relevantCities = selectedCountry.value === 'ALL'
    ? cities.value
    : cities.value.filter(c => c.country === selectedCountry.value)
  for (const city of relevantCities) {
    counts[worstRisk(city)]++
  }
  return counts
})

// Top 3 highest-risk cities across the whole board (not scoped to the
// country filter - this is meant to be "what needs attention right now"
// regardless of which country tab happens to be open), each paired with
// its own worst day and the real rule that set that day's risk level.
// Only shown once something actually crosses out of GREEN - an all-green
// board has no incident to lead with.
const priorityIncidents = computed(() => {
  return cities.value
    .map(city => {
      let worstDay = city.daily[0]
      for (const day of city.daily) {
        if (RISK_RANK[day.risk_level] > RISK_RANK[worstDay.risk_level]) worstDay = day
      }
      return { city, day: worstDay }
    })
    .filter(entry => entry.day.risk_level !== 'GREEN')
    .sort((a, b) => RISK_RANK[b.day.risk_level] - RISK_RANK[a.day.risk_level])
    .slice(0, 3)
})

// A single always-visible line stating the combined effect of the country
// filter and the risk-level filter together, so it's never ambiguous
// whether a RED/ORANGE/YELLOW/GREEN pill click filtered the whole board
// or just the currently-selected country.
const filterStatusText = computed(() => {
  const shownCount = filteredGroups.value.reduce((sum, g) => sum + g.cities.length, 0)
  const cityWord = shownCount === 1 ? 'city' : 'cities'
  const countryPart = selectedCountry.value === 'ALL' ? 'all countries' : countryName(selectedCountry.value)

  if (selectedRiskLevel.value) {
    return `Showing ${shownCount} ${selectedRiskLevel.value} ${cityWord} - ${countryPart}`
  }
  return `Showing all ${shownCount} ${cityWord} - ${countryPart}`
})

const formatDay = (dateStr: string): string => {
  const d = new Date(dateStr)
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

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
  // line, not a full-width banner - the chevron label already in the
  // template says explicitly that there's more to click into.
  if (sotLoading.value) return 'Verifying data source...'
  if (sotError.value) return "Couldn't verify data source"
  const sot = sourceOfTruth.value
  if (!sot || sot.overall === 'verified') return 'Data source verified'

  // "Degraded" alone, sitting right next to "updated this minute" in the
  // meta row, reads as a contradiction - as if the data were both fresh
  // and stale at once. Name which check actually failed so the badge
  // doesn't imply a freshness problem when the real cause is unrelated
  // (e.g. a few forecast-days with thin underlying data).
  const reasons: string[] = []
  if (sot.freshness.stale) reasons.push('may be outdated')
  if (sot.completeness.returned_city_count < sot.completeness.monitored_city_count) reasons.push('some cities missing')
  if (sot.sufficiency.cities_with_thin_days.length > 0) reasons.push('some days have thin data')
  return reasons.length ? `Degraded - ${reasons.join(', ')}` : 'Data source degraded'
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

/* Source of Truth Status */
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
  font-size: 12px;
  font-weight: 700;
  opacity: 1;
  color: var(--accent-cyan, #22d3ee);
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
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px 8px;
}

.sot-detail-row strong {
  color: var(--text-primary);
  margin-right: 2px;
}

.sot-row-icon {
  font-size: 13px;
}

.sot-row-verdict {
  color: var(--text-primary);
  font-weight: 600;
}

.sot-row-detail {
  flex-basis: 100%;
  font-size: 13px;
  color: var(--text-secondary);
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

/* ---- Risk-level summary pills ----
   These had no base styling at all before this fix - .hero-summary,
   .summary-pill, .summary-count and .summary-label were only ever touched
   inside a max-width media query (layout tweaks), never given a base rule.
   They rendered as unstyled, uncolored stacked text with no visual
   distinction between RED/ORANGE/YELLOW/GREEN - exactly what showed up in
   the screenshot this was reported from. Now they're real color-coded,
   clickable filter pills, matching the palette already used by
   .country-worst / .worst-badge / .day-chip elsewhere in this file. */

.hero-summary-wrap {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.hero-summary {
  display: flex;
  gap: 10px;
}

.summary-pill {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 16px;
  border-radius: 10px;
  border: 1.5px solid transparent;
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  font: inherit;
  transition: all 0.15s ease;
}

.summary-count {
  font-size: 20px;
  font-weight: 800;
  line-height: 1;
}

.summary-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.summary-pill.red { color: #ef4444; border-color: rgba(239, 68, 68, 0.25); background: rgba(239, 68, 68, 0.1); }
.summary-pill.orange { color: #f97316; border-color: rgba(249, 115, 22, 0.25); background: rgba(249, 115, 22, 0.1); }
.summary-pill.yellow { color: #eab308; border-color: rgba(234, 179, 8, 0.25); background: rgba(234, 179, 8, 0.1); }
.summary-pill.green { color: #22c55e; border-color: rgba(34, 197, 94, 0.25); background: rgba(34, 197, 94, 0.1); }

.summary-pill:hover:not(.disabled) {
  transform: translateY(-1px);
  filter: brightness(1.15);
}

.summary-pill.active {
  border-width: 2px;
  box-shadow: 0 0 0 1px currentColor;
}

.summary-pill.dimmed {
  opacity: 0.35;
}

.summary-pill.disabled {
  cursor: not-allowed;
  opacity: 0.45;
  filter: grayscale(0.4);
}

/* Always visible now (previously only rendered when the filter was
   disabled, which this page no longer does) - without it, nothing on
   screen tells a first-time visitor that the RED/ORANGE/YELLOW/GREEN
   numbers above are clickable filters rather than plain stats. */
.risk-filter-hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

/* Combined-filter-state readout - always on screen so it's never
   ambiguous whether a risk-level pill filtered the whole board or just
   the currently-selected country; updates with both filters together. */
.filter-status {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 2px 0 2px;
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

/* Each country chip shows its own worst risk level, mirroring the
   .country-worst / .worst-badge palette used elsewhere on this page -
   previously the [group.worstRisk.toLowerCase()] class was added by the
   template but no matching CSS rule existed, so every chip rendered in
   the same neutral cyan regardless of how severe that country's forecast
   was. */
.filter-chip.red { border-color: rgba(239, 68, 68, 0.35); background: rgba(239, 68, 68, 0.1); color: #ef4444; }
.filter-chip.orange { border-color: rgba(249, 115, 22, 0.35); background: rgba(249, 115, 22, 0.1); color: #f97316; }
.filter-chip.yellow { border-color: rgba(234, 179, 8, 0.35); background: rgba(234, 179, 8, 0.1); color: #eab308; }
.filter-chip.green { border-color: rgba(34, 197, 94, 0.35); background: rgba(34, 197, 94, 0.1); color: #22c55e; }

.filter-chip.red.active,
.filter-chip.orange.active,
.filter-chip.yellow.active,
.filter-chip.green.active {
  box-shadow: 0 0 8px currentColor, inset 0 0 6px currentColor;
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
  color: var(--text-secondary);
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
  color: var(--text-secondary);
  font-size: 11px;
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

/* ---- Priority incident strip ---- */

.priority-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 10px;
  margin-bottom: 16px;
}

.priority-strip-label {
  display: flex;
  align-items: center;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-secondary);
  flex-basis: 100%;
}

.priority-card {
  flex: 1 1 260px;
  min-width: 220px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-left: 3px solid var(--glass-border);
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  transition: transform 150ms ease, box-shadow 150ms ease;
}

.priority-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}

.priority-card.red { border-left-color: #ef4444; }
.priority-card.orange { border-left-color: #f97316; }
.priority-card.yellow { border-left-color: #eab308; }

.priority-card-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.priority-card-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
  white-space: nowrap;
}

.priority-card-badge.red { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.priority-card-badge.orange { background: rgba(249, 115, 22, 0.15); color: #f97316; }
.priority-card-badge.yellow { background: rgba(234, 179, 8, 0.15); color: #eab308; }

.priority-card-city {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
}

.priority-card-reason {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-secondary);
}

.priority-card-action {
  font-size: 11px;
  font-weight: 600;
  color: #38bdf8;
}

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
  /* Now a RouterLink into that city's Risk Timeline - reset link defaults
     and add a hover cue so it reads as navigable, not just decorative. */
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  transition: transform 150ms ease, box-shadow 150ms ease;
}

.city-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
}

.city-card:hover .city-card-arrow {
  transform: translateX(3px);
}

.city-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-top: 2px;
  padding-top: 8px;
  border-top: 1px dashed rgba(255, 255, 255, 0.08);
  font-size: 11px;
  font-weight: 600;
  color: #38bdf8;
}

.city-card-arrow {
  transition: transform 150ms ease;
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
  transition: transform 0.15s ease, opacity 0.15s ease;
  background-clip: padding-box;
}

.day-chip:hover {
  transform: translateY(-2px);
}

.day-chip.green { border-color: rgba(34, 197, 94, 0.4); background: rgba(34, 197, 94, 0.12); }
.day-chip.yellow { border-color: rgba(234, 179, 8, 0.4); background: rgba(234, 179, 8, 0.12); }
.day-chip.orange { border-color: rgba(249, 115, 22, 0.4); background: rgba(249, 115, 22, 0.12); }
.day-chip.red { border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.14); }

/* When a risk-level filter is active, the city still shows its full week
   for context, but the days that AREN'T why this city matched the filter
   should visibly recede instead of looking just as prominent as the one
   that did - otherwise clicking "ORANGE" and seeing a row of mostly green
   chips reads as if the filter didn't work. */
.day-chip.dimmed {
  opacity: 0.35;
}

.day-date {
  font-weight: 700;
  font-size: 11px;
  color: var(--text-secondary);
}

.day-icon {
  font-size: 16px;
  line-height: 1;
}

.day-weather {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 11px;
  line-height: 1.2;
}

.day-metrics {
  color: var(--text-secondary);
  font-size: 11px;
  margin-top: 1px;
  line-height: 1.3;
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
