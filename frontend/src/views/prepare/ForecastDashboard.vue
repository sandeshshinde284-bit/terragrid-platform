<template>
  <div class="prepare-screen forecast-screen">
    <Header />

    <div class="forecast-container">
      <div v-if="loading" class="empty-state glass-panel">
        <div class="empty-icon">🌦️</div>
        <h3>Loading 7-day forecast...</h3>
      </div>

      <div v-else-if="error" class="empty-state glass-panel">
        <div class="empty-icon">⚠️</div>
        <h3>Couldn't load the forecast</h3>
        <p>{{ error }}</p>
      </div>

      <div v-else-if="cities.length === 0" class="empty-state glass-panel">
        <div class="empty-icon">🌦️</div>
        <h3>No forecast data yet</h3>
        <p>No cities returned a forecast. If OPENWEATHERMAP_API_KEY isn't set on the backend, this stays empty rather than showing invented numbers.</p>
      </div>

      <template v-else>
        <div class="forecast-hero glass-panel">
          <div class="hero-left">
            <h2>7-Day Risk Escalation</h2>
            <span class="hero-meta">{{ cities.length }} monitored {{ cities.length === 1 ? 'city' : 'cities' }} across {{ countryGroups.length }} {{ countryGroups.length === 1 ? 'country' : 'countries' }} · OpenWeatherMap 5-day/3-hour forecast</span>
          </div>
          <div class="hero-summary">
            <div v-for="level in ['RED', 'ORANGE', 'YELLOW', 'GREEN']" :key="level" class="summary-pill" :class="level.toLowerCase()">
              <span class="summary-count">{{ riskCounts[level] }}</span>
              <span class="summary-label">{{ level }}</span>
            </div>
          </div>
        </div>

        <div class="country-sections">
          <section v-for="group in countryGroups" :key="group.country" class="country-section">
            <div class="country-header" :class="group.worstRisk.toLowerCase()">
              <span class="country-flag">{{ countryMeta(group.country).flag }}</span>
              <span class="country-name">{{ countryMeta(group.country).name }}</span>
              <span class="country-count">{{ group.cities.length }} {{ group.cities.length === 1 ? 'city' : 'cities' }}</span>
              <span class="country-worst" :class="group.worstRisk.toLowerCase()">{{ riskEmoji(group.worstRisk) }} {{ group.worstRisk }}</span>
            </div>

            <div class="city-grid">
              <div v-for="city in group.cities" :key="`${city.city}-${city.country}`" class="city-card glass-panel" :class="worstRisk(city).toLowerCase()">
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
import { ref, computed, onMounted } from 'vue'
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

interface CountryGroup {
  country: string
  cities: CityForecast[]
  worstRisk: string
}

const { fetchWithMockMode } = useMockMode()

const cities = ref<CityForecast[]>([])
const loading = ref(true)
const error = ref('')

const RISK_RANK: Record<string, number> = { GREEN: 0, YELLOW: 1, ORANGE: 2, RED: 3 }
const RISK_EMOJI: Record<string, string> = { GREEN: '🟢', YELLOW: '🟡', ORANGE: '🟠', RED: '🔴' }

// Country metadata is purely cosmetic (name + flag for the grouping header) -
// it never changes risk calculation, which stays entirely backend-derived.
const COUNTRY_META: Record<string, { name: string; flag: string }> = {
  IN: { name: 'India', flag: '🇮🇳' },
  NP: { name: 'Nepal', flag: '🇳🇵' },
  CN: { name: 'China', flag: '🇨🇳' },
  HK: { name: 'Hong Kong', flag: '🇭🇰' },
  BD: { name: 'Bangladesh', flag: '🇧🇩' },
  PK: { name: 'Pakistan', flag: '🇵🇰' },
  TH: { name: 'Thailand', flag: '🇹🇭' },
  VN: { name: 'Vietnam', flag: '🇻🇳' },
  SG: { name: 'Singapore', flag: '🇸🇬' },
  MY: { name: 'Malaysia', flag: '🇲🇾' },
  IQ: { name: 'Iraq', flag: '🇮🇶' },
  AE: { name: 'UAE', flag: '🇦🇪' },
  ET: { name: 'Ethiopia', flag: '🇪🇹' },
  KE: { name: 'Kenya', flag: '🇰🇪' },
  RW: { name: 'Rwanda', flag: '🇷🇼' },
  US: { name: 'United States', flag: '🇺🇸' },
}

const countryMeta = (code: string) => COUNTRY_META[code] || { name: code, flag: '🌐' }

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

onMounted(async () => {
  try {
    const host = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)
    const response = await fetchWithMockMode(`${host}/api/v1/prepare/forecast`)

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const json = await response.json()
    cities.value = json.data || []
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Unknown error fetching forecast'
  } finally {
    loading.value = false
  }
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
}

/* ---- Hero / summary strip ---- */

.forecast-hero {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  background: linear-gradient(135deg, rgba(34, 211, 238, 0.08), rgba(59, 130, 246, 0.04));
}

.hero-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hero-left h2 {
  margin: 0;
  font-size: 20px;
  background: linear-gradient(90deg, var(--accent-cyan), #60a5fa);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
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

/* ---- Country sections ---- */

.country-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
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
  font-size: 20px;
}

.country-name {
  font-weight: 700;
  font-size: 15px;
}

.country-count {
  font-size: 12px;
  color: var(--text-muted);
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
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  gap: 6px;
  overflow-x: auto;
}

.day-chip {
  flex: 1;
  min-width: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 10px 6px;
  border-radius: 8px;
  border: 1px solid var(--glass-border);
  font-size: 11px;
  transition: transform 0.15s ease;
}

.day-chip:hover {
  transform: translateY(-2px);
}

.day-chip.green { border-color: rgba(34, 197, 94, 0.4); background: rgba(34, 197, 94, 0.06); }
.day-chip.yellow { border-color: rgba(234, 179, 8, 0.4); background: rgba(234, 179, 8, 0.06); }
.day-chip.orange { border-color: rgba(249, 115, 22, 0.4); background: rgba(249, 115, 22, 0.06); }
.day-chip.red { border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.08); }

.day-date {
  font-weight: 700;
  font-size: 10px;
  color: var(--text-secondary);
}

.day-icon {
  font-size: 18px;
  line-height: 1;
}

.day-weather {
  color: var(--text-primary);
  font-weight: 600;
}

.day-metrics {
  color: var(--text-muted);
  font-size: 10px;
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
</style>
