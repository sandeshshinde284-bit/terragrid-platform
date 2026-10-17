/**
 * Shared lookup tables and helpers used across all 4 PREPARE screens
 * (ForecastDashboard, RiskTimeline, PreparednessChecklist, AgencyAlerts).
 *
 * These used to be copy-pasted independently into each of the 4 files -
 * same risk-rank table, same worst-risk/city-key logic, same weather-icon
 * map, duplicated 2-4x depending on the constant. That's exactly the kind
 * of thing that drifts: add a new risk level and it's easy to update 3 of
 * the 4 copies and forget the fourth. One copy, imported everywhere,
 * instead.
 *
 * Country-name lookup lives separately in `@/utils/countries` (not here)
 * - that's the single source of truth for it, reused below.
 */
import { computed, nextTick, ref, type Ref } from 'vue'
import type { PrepareCityForecast } from '@/stores'
import { getCountryName } from '@/utils/countries'

export const RISK_RANK: Record<string, number> = { GREEN: 0, YELLOW: 1, ORANGE: 2, RED: 3 }

export const worstRisk = (city: PrepareCityForecast): string => {
  return city.daily.reduce(
    (worst, day) => (RISK_RANK[day.risk_level] > RISK_RANK[worst] ? day.risk_level : worst),
    'GREEN'
  )
}

export const cityKey = (city: PrepareCityForecast): string => `${city.city}-${city.country}`

export const WEATHER_ICONS: Record<string, string> = {
  clear: '☀️', clouds: '☁️', rain: '🌧️', drizzle: '🌦️', thunderstorm: '⛈️',
  snow: '❄️', mist: '🌫️', fog: '🌫️', haze: '🌫️', smoke: '🌫️',
  dust: '🌪️', sand: '🌪️', ash: '🌋', squall: '💨', tornado: '🌪️',
}

export const weatherIcon = (label: string): string => WEATHER_ICONS[(label || '').toLowerCase()] || '🌡️'

export const flagUrl = (code: string): string => `https://flagcdn.com/w40/${code.toLowerCase()}.png`

/**
 * Per-component fallback tracking for flag images that fail to load
 * (flagcdn unreachable, or no flag art for that code). Each screen that
 * renders flags gets its own independent Set via this factory - same
 * behavior as before, just not re-declared by hand in every file.
 */
export function useFlagFallback() {
  const failedFlags = ref<Set<string>>(new Set())
  const onFlagError = (code: string) => {
    failedFlags.value = new Set(failedFlags.value).add(code)
  }
  return { failedFlags, onFlagError, flagUrl }
}

/**
 * Text search/filter over a worst-risk-sorted city list, plus the ref and
 * helper needed to keep the currently-selected rail item scrolled into
 * view. Shared by every PREPARE screen with a city rail (RiskTimeline,
 * PreparednessChecklist, AgencyAlerts) so the search box and its behavior
 * stay identical across screens instead of landing on only one of them.
 */
export function useCityRailFilter(sortedCities: Ref<PrepareCityForecast[]>) {
  const citySearch = ref('')
  const cityRailEl = ref<HTMLElement | null>(null)

  const filteredCities = computed<PrepareCityForecast[]>(() => {
    const q = citySearch.value.trim().toLowerCase()
    if (!q) return sortedCities.value
    return sortedCities.value.filter(
      (c) =>
        c.city.toLowerCase().includes(q) ||
        getCountryName(c.country).toLowerCase().includes(q) ||
        c.country.toLowerCase().includes(q)
    )
  })

  // Keeps the currently-selected row scrolled into view - without this,
  // picking a city (or searching, which can move it off-screen) can leave
  // the active row hidden, so there's no way to tell from the rail which
  // city the detail panel actually belongs to.
  const scrollActiveIntoView = () => {
    nextTick(() => {
      cityRailEl.value?.querySelector('.rail-item.active')?.scrollIntoView({ block: 'nearest', inline: 'nearest' })
    })
  }

  return { citySearch, cityRailEl, filteredCities, scrollActiveIntoView }
}
