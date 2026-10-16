import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { IncidentLevel1, AIInsight, DashboardState } from '@/types'

// Prepare Forecast Store
//
// PERF FIX: ForecastDashboard, RiskTimeline, PreparednessChecklist, and
// AgencyAlerts each independently called GET /api/v1/prepare/forecast on
// mount to build their city list/rail - so navigating between the four
// PREPARE pages re-paid the cost of that fetch every single time, even
// right after another PREPARE page had just loaded the exact same data.
// This store fetches once and is shared by all four; ensureLoaded() is a
// no-op if the cached data is still fresh, so switching tabs is instant.
// The backend also carries its own short-lived cache (OpenWeatherService's
// FORECAST_CACHE_TTL_SECONDS) as a second line of defense for a cold store
// (e.g. a judge opening Agency Alerts directly via a shared link).
export interface PrepareDailyForecast {
  date: string
  risk_level: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED'
  dominant_weather: string
  max_wind_ms: number
  min_temp_c: number | null
  max_temp_c: number | null
  total_rain_mm: number
  // PR9 (confidence-based alerting): what % of the day's own 3-hour forecast
  // entries actually agreed with the chosen risk_level, computed from the
  // forecast data itself - not a fabricated score.
  confidence_pct: number
  alert_recommended: boolean
}

export interface PrepareCityForecast {
  city: string
  country: string
  latitude: number
  longitude: number
  source: string
  daily: PrepareDailyForecast[]
}

const PREPARE_FORECAST_FRESHNESS_MS = 5 * 60 * 1000 // 5 minutes

export const usePrepareForecastStore = defineStore('prepareForecast', () => {
  // State
  // loading starts true (not false) so the very first page to mount shows
  // its loader immediately instead of a one-frame "no data yet" flash
  // before onMounted's ensureLoaded() call flips it. Once the first fetch's
  // finally{} block runs, it settles to false and stays false across fresh
  // navigations (ensureLoaded() is a no-op when isFresh, so it never touches
  // loading again until data goes stale or a forced refresh happens).
  const cities = ref<PrepareCityForecast[]>([])
  const loading = ref(true)
  const error = ref('')
  const lastFetchedAt = ref(0)

  // Getters
  const isFresh = computed(() => cities.value.length > 0 && (Date.now() - lastFetchedAt.value) < PREPARE_FORECAST_FRESHNESS_MS)

  const apiHost = () =>
    import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)

  // Actions
  //
  // fetchWithMockMode is passed in (from useMockMode() in the calling
  // component) rather than imported directly here, since useMockMode()
  // itself calls useAppStore() internally - cleaner to keep that composable
  // usage in components and just hand this store the fetch function it
  // produces.
  //
  // inFlight dedupes the case where two PREPARE pages mount in quick
  // succession before the first fetch has resolved (e.g. the user clicks
  // through tabs fast) - without it, both would see isFresh === false and
  // fire their own fetch instead of sharing the one already in progress.
  let inFlight: Promise<void> | null = null

  const ensureLoaded = async (
    fetchWithMockMode: (url: string, options?: Record<string, unknown>) => Promise<Response>,
    force = false
  ) => {
    if (isFresh.value && !force) return
    if (inFlight) return inFlight

    loading.value = true
    error.value = ''

    inFlight = (async () => {
      try {
        const response = await fetchWithMockMode(`${apiHost()}/api/v1/prepare/forecast`)
        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`)
        }
        const json = await response.json()
        cities.value = json.data || []
        lastFetchedAt.value = Date.now()
      } catch (e) {
        error.value = e instanceof Error ? e.message : 'Unknown error fetching forecast'
      } finally {
        loading.value = false
        inFlight = null
      }
    })()

    return inFlight
  }

  return {
    // State
    cities,
    loading,
    error,
    lastFetchedAt,

    // Getters
    isFresh,

    // Actions
    ensureLoaded,
  }
})

// App Store
export const useAppStore = defineStore('app', () => {
  // State
  const isDarkMode = ref<boolean>(true)
  const viewMode = ref<'2d' | '3d'>('2d')
  const isLoading = ref<boolean>(false)
  const demoMode = ref<boolean>(true)
  const expandedIncident = ref<string | null>(null)
  const selectedIncident = ref<string | null>(null)
  const isBackendMockModeEnabled = ref<boolean>(false)
  const mapboxToken = ref<string>('')

  // Getters
  const state = computed<DashboardState>(() => ({
    incidents: [],
    selectedIncident: null,
    expandedIncident: expandedIncident.value,
    aiInsights: [],
    viewMode: viewMode.value,
    isDarkMode: isDarkMode.value,
    isLoading: isLoading.value,
    demoMode: demoMode.value,
  }))

  // Actions
  const toggleTheme = () => {
    isDarkMode.value = !isDarkMode.value
  }

  const toggleViewMode = () => {
    viewMode.value = viewMode.value === '2d' ? '3d' : '2d'
  }

  const setLoading = (value: boolean) => {
    isLoading.value = value
  }

  const setExpandedIncident = (id: string | null) => {
    expandedIncident.value = id
  }

  const setSelectedIncident = (id: string | null) => {
    selectedIncident.value = id
  }

  const toggleDemoMode = () => {
    demoMode.value = !demoMode.value
  }
  const setBackendMockMode = (enabled: boolean) => {
    isBackendMockModeEnabled.value = enabled
  }

  const setMapboxToken = (token: string) => {
    mapboxToken.value = token
  }

  return {
    // State
    isDarkMode,
    viewMode,
    isLoading,
    demoMode,
    expandedIncident,
    selectedIncident,
    isBackendMockModeEnabled,
    mapboxToken,

    // Getters
    state,

    // Actions
    toggleTheme,
    toggleViewMode,
    setLoading,
    setExpandedIncident,
    setSelectedIncident,
    toggleDemoMode,
    setBackendMockMode,
    setMapboxToken,
  }
  })

// Events Store (Incidents)
export const useEventsStore = defineStore('events', () => {
  // State
  const incidents = ref<IncidentLevel1[]>([])
  const lastUpdated = ref<Date>(new Date())

  // Getters
  const allIncidents = computed(() => incidents.value)

  const highSeverityIncidents = computed(() =>
    incidents.value.filter(i => i.severity === 'high')
  )

  const totalAffectedPopulation = computed(() =>
    incidents.value.reduce((sum, i) => sum + i.affectedPopulation, 0)
  )

  const totalAffectedArea = computed(() =>
    incidents.value.reduce((sum, i) => sum + i.affectedArea, 0)
  )

  // Actions
  const setIncidents = (newIncidents: IncidentLevel1[], mergeMode: boolean = false) => {
    if (mergeMode && incidents.value.length > 0) {
      // Merge mode: upsert by ID to avoid duplicate key errors
      const existingMap = new Map(incidents.value.map(i => [i.id, i]))
      newIncidents.forEach(ni => existingMap.set(ni.id, ni))
      incidents.value = Array.from(existingMap.values())
    } else {
      incidents.value = newIncidents
    }
    lastUpdated.value = new Date()
  }

  const addIncident = (incident: IncidentLevel1) => {
    incidents.value.push(incident)
    lastUpdated.value = new Date()
  }

  const updateIncident = (id: string, updates: Partial<IncidentLevel1>) => {
    const index = incidents.value.findIndex(i => i.id === id)
    if (index !== -1) {
      incidents.value[index] = { ...incidents.value[index], ...updates }
      lastUpdated.value = new Date()
    }
  }

  const removeIncident = (id: string) => {
    incidents.value = incidents.value.filter(i => i.id !== id)
    lastUpdated.value = new Date()
  }

  const initMockData = () => {
    const mockIncidents: IncidentLevel1[] = [
      {
        id: 'incident-1',
        type: 'fire',
        location: 'San Gabriel Mountains, CA',
        severity: 'high',
        affectedArea: 1250,
        affectedPopulation: 85000,
        trend: 18.4,
        forecast6h: 110,
        detectionTime: new Date(),
        status: 'active',
      },
      {
        id: 'incident-2',
        type: 'flood',
        location: 'Central Valley, CA',
        severity: 'high',
        affectedArea: 850,
        affectedPopulation: 45000,
        trend: 12.6,
        forecast6h: 72,
        detectionTime: new Date(Date.now() - 3600000),
        status: 'active',
      },
      {
        id: 'incident-3',
        type: 'landslide',
        location: 'Bay Area Foothills, CA',
        severity: 'medium',
        affectedArea: 500,
        affectedPopulation: 120000,
        trend: 6.8,
        forecast6h: 34,
        detectionTime: new Date(Date.now() - 7200000),
        status: 'monitoring',
      },
    ]

    setIncidents(mockIncidents)
  }

  // [STRICT LIVE MODE] initMockData()

  return {
    // State
    incidents,
    lastUpdated,

    // Getters
    allIncidents,
    highSeverityIncidents,
    totalAffectedPopulation,
    totalAffectedArea,

    // Actions
    setIncidents,
    addIncident,
    updateIncident,
    removeIncident,
    initMockData,
  }
})

// Alerts Store
export interface Alert {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  message: string
  timestamp: Date
  duration?: number
}

export const useAlertsStore = defineStore('alerts', () => {
  // State
  const aiInsights = ref<AIInsight[]>([])
  const alerts = ref<Alert[]>([])

  // Getters
  const criticalInsights = computed(() =>
    aiInsights.value.filter(i => i.severity === 'critical')
  )

  const secondaryInsights = computed(() =>
    aiInsights.value.filter(i => i.severity === 'secondary')
  )

  // Actions
  const setAIInsights = (insights: AIInsight[]) => {
    aiInsights.value = insights
  }

  const addAlert = (alert: Omit<Alert, 'id' | 'timestamp'>) => {
    const newAlert: Alert = {
      id: Math.random().toString(36),
      timestamp: new Date(),
      ...alert,
    }
    alerts.value.push(newAlert)

    if (alert.duration) {
      setTimeout(() => {
        removeAlert(newAlert.id)
      }, alert.duration)
    }

    return newAlert
  }

  const removeAlert = (id: string) => {
    alerts.value = alerts.value.filter(a => a.id !== id)
  }

  const clearAlerts = () => {
    alerts.value = []
  }

  const initMockInsights = () => {
    const mockInsights: AIInsight[] = [
      {
        id: 'insight-1',
        eventId: 'incident-1',
        severity: 'critical',
        action: 'Evacuate Zone A immediately',
        reason: 'Wind conditions indicate rapid fire spread toward populated foothills.',
        confidence: 95,
        estimatedAffected: 8000,
        timeUrgent: 'Next 30 minutes',
      },
      {
        id: 'insight-2',
        eventId: 'incident-2',
        severity: 'critical',
        action: 'Activate emergency shelters',
        reason: 'Flood projections show road access degradation in low-lying communities.',
        confidence: 88,
        estimatedAffected: 12000,
        timeUrgent: 'Within 1 hour',
      },
    ]

    setAIInsights(mockInsights)
  }

  // COMMENTED OUT (Live Mode): Never initialize mock insights on store load
  // initMockInsights()

  return {
    // State
    aiInsights,
    alerts,

    // Getters
    criticalInsights,
    secondaryInsights,

    // Actions
    setAIInsights,
    addAlert,
    removeAlert,
    clearAlerts,
    initMockInsights,
  }
})