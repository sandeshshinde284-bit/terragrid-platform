// Event Types
export interface Event {
  id: string
  name: string
  type: 'earthquake' | 'flood' | 'fire' | 'hurricane' | 'volcano' | 'landslide'
  severity: 'low' | 'medium' | 'high'
  latitude: number
  longitude: number
  description: string
  affectedArea: number  // km²
  affectedPopulation: number
  trend: number  // km²/h (growth rate)
  forecast6h: number  // km² (6-hour forecast)
  forecast24h: number  // km² (24-hour forecast)
  created_at: Date
  updated_at: Date
  dataQuality?: number  // 0-100 confidence
}

// Incident Card Data (Level 1 - Progressive Disclosure)
export interface IncidentLevel1 {
  id: string
  type: Event['type']
  location: string
  severity: Event['severity']
  affectedArea: number
  affectedPopulation: number
  trend: number
  forecast6h: number
  detectionTime: Date
  status: 'active' | 'monitoring' | 'resolved'
  threatScore?: number  // Optional threat score (0-100)
  coordinates?: [number, number]  // lat, lng
  countryCode?: string  // Canonical 2-letter ISO country code (e.g., 'US', 'IN')
}

// Expanded Incident Data (Level 2 - Drawer)
export interface IncidentLevel2 extends IncidentLevel1 {
  villages: number
  hospitals: number
  roads: number
  bridges: number
  waterLevelTrend?: string
  historicalComparison?: string
}

// AI Insights (Level 3 - Decision panel)
export interface AIInsight {
  id: string
  eventId: string
  severity: 'critical' | 'secondary'
  action: string
  reason: string
  confidence: number
  estimatedAffected: number
  timeUrgent: string
  details?: string
}

// AI Reasoning (Level 4 - Modal with full chain)
export interface AIReasoning {
  id: string
  insightId: string
  inputs: {
    floodExpansion: number
    rainfall: number
    waterLevel: number
    terrainSlope: string
    populationExposure: number
  }
  processing: {
    riskScore: number
    patternMatch: number
    historicalComparison: string
  }
  forecast: {
    expansion6h: number
    expansion24h: number
    peakWaterLevel: number
    peakTime: Date
  }
  decision: {
    combinedRisk: number
    actionThreshold: number
    recommendation: string
  }
  sources: string[]
  confidence: number
}

// Dashboard State
export interface DashboardState {
  incidents: IncidentLevel1[]
  selectedIncident: IncidentLevel1 | null
  expandedIncident: string | null
  aiInsights: AIInsight[]
  viewMode: '2d' | '3d'
  isDarkMode: boolean
  isLoading: boolean
  demoMode: boolean
}

// API Response Types
export interface ApiResponse<T> {
  status: 'success' | 'error'
  data: T
  message?: string
  timestamp: Date
}