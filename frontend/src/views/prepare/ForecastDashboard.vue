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
        <div class="forecast-meta glass-panel">
          <span>{{ cities.length }} monitored {{ cities.length === 1 ? 'city' : 'cities' }}</span>
          <span class="dot">·</span>
          <span>Source: OpenWeatherMap 5-day/3-hour forecast</span>
        </div>

        <div class="city-grid">
          <div v-for="city in sortedCities" :key="`${city.city}-${city.country}`" class="city-card glass-panel">
            <div class="city-header">
              <span class="city-name">{{ city.city }}, {{ city.country }}</span>
              <span class="worst-badge" :class="worstRisk(city).toLowerCase()">{{ worstRisk(city) }}</span>
            </div>

            <div class="day-row">
              <div v-for="day in city.daily" :key="day.date" class="day-chip" :class="day.risk_level.toLowerCase()">
                <span class="day-date">{{ formatDay(day.date) }}</span>
                <span class="day-weather">{{ day.dominant_weather }}</span>
                <span class="day-rain">{{ day.total_rain_mm.toFixed(0) }}mm</span>
                <span class="day-wind">{{ day.max_wind_ms.toFixed(0) }}m/s</span>
              </div>
            </div>
          </div>
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

const { fetchWithMockMode } = useMockMode()

const cities = ref<CityForecast[]>([])
const loading = ref(true)
const error = ref('')

const RISK_RANK: Record<string, number> = { GREEN: 0, YELLOW: 1, ORANGE: 2, RED: 3 }

const worstRisk = (city: CityForecast): string => {
  return city.daily.reduce((worst, day) => {
    return RISK_RANK[day.risk_level] > RISK_RANK[worst] ? day.risk_level : worst
  }, 'GREEN')
}

// Cities with the most severe upcoming risk surface first - that's the point of a 7-day
// forecast dashboard: show what needs attention first, not an alphabetical list.
const sortedCities = computed(() => {
  return [...cities.value].sort((a, b) => RISK_RANK[worstRisk(b)] - RISK_RANK[worstRisk(a)])
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
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.forecast-meta {
  padding: 12px 16px;
  display: flex;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

.forecast-meta .dot {
  color: var(--text-muted);
}

.city-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.city-card {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

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
  min-width: 78px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 6px;
  border-radius: 6px;
  border: 1px solid var(--glass-border);
  font-size: 11px;
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

.day-weather {
  text-transform: capitalize;
  color: var(--text-primary);
}

.day-rain, .day-wind {
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
    min-width: 70px;
  }
}

@media (max-width: 480px) {
  .forecast-screen {
    padding: 8px;
    gap: 8px;
  }

  .forecast-container {
    gap: 8px;
  }
}
</style>
