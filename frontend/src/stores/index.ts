import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { IncidentLevel1, AIInsight, DashboardState } from '@/types'

// App Store
export const useAppStore = defineStore('app', () => {
  // State
  const isDarkMode = ref<boolean>(true)
  const viewMode = ref<'2d' | '3d'>('2d')
  const isLoading = ref<boolean>(false)
  const demoMode = ref<boolean>(true)
  const expandedIncident = ref<string | null>(null)
  const selectedIncident = ref<string | null>(null)

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

  return {
    // State
    isDarkMode,
    viewMode,
    isLoading,
    demoMode,
    expandedIncident,
    selectedIncident,

    // Getters
    state,

    // Actions
    toggleTheme,
    toggleViewMode,
    setLoading,
    setExpandedIncident,
    setSelectedIncident,
    toggleDemoMode,
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
  const setIncidents = (newIncidents: IncidentLevel1[]) => {
    incidents.value = newIncidents
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

  initMockData()

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

  initMockInsights()

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