<template>
  <div class="alerts-screen">
    <Header />

    <div class="alerts-container">
        <div class="filter-tabs glass-panel">
          <button 
            v-for="filter in filters"
            :key="filter"
            @click="activeFilter = filter"
            :class="['tab-btn', { active: activeFilter === filter }]"
          >
            {{ getFilterLabel(filter) }}
          </button>
        </div>

        <div class="disaster-brief glass-panel">
          <div class="brief-header">
            <h3>🤖 {{ $t('alerts.disasterBrief') }}</h3>
            <span class="update-time">{{ lastUpdateTime }}</span>
          </div>
          <div class="brief-content">
            <p>
              {{ briefText }}
            </p>
            <div class="brief-metrics">
              <div class="metric">
                <span class="label">{{ $t('alerts.confidence') }}</span>
                <span class="value">{{ avgConfidenceLabel }}</span>
              </div>
              <div class="metric">
                <span class="label">{{ $t('alerts.dataSources') }}</span>
                <span class="value">{{ liveSourceCount }} Live</span>
              </div>
              <div class="metric">
                <span class="label">{{ $t('alerts.activeThreats') }}</span>
                <span class="value">{{ totalCount }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="alerts-list-wrapper glass-panel">
          <div v-if="filteredAlerts.length === 0" class="no-alerts">
            <p>{{ $t('alerts.noAlerts') }}</p>
          </div>

          <div v-else class="alerts-list">
            <div 
              v-for="alert in filteredAlerts"
              :key="alert.id"
              :class="['alert-item', alert.severity]"
            >
              <div class="alert-icon">{{ alert.icon }}</div>
              
              <div class="alert-content">
                <div class="alert-title">{{ alert.title }}</div>
                <div class="alert-message">{{ alert.message }}</div>
                <div class="alert-meta">
                  <span class="location">📍 {{ alert.location }}</span>
                  <span class="timestamp">⏱️ {{ alert.time }}</span>
                </div>
              </div>

              <div class="alert-badge">
                <span class="severity-badge" :class="alert.severity">
                  {{ alert.severity.toUpperCase() }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="stats-grid">
          <div class="stat-card glass-panel">
            <div class="stat-icon">🚨</div>
            <div class="stat-info">
              <span class="label">{{ $t('common.critical') }}</span>
              <span class="value">{{ criticalCount }}</span>
            </div>
          </div>

          <div class="stat-card glass-panel">
            <div class="stat-icon">⚠️</div>
            <div class="stat-info">
              <span class="label">{{ $t('common.high') }}</span>
              <span class="value">{{ highCount }}</span>
            </div>
          </div>

          <div class="stat-card glass-panel">
            <div class="stat-icon">ℹ️</div>
            <div class="stat-info">
              <span class="label">{{ $t('alerts.info') }}</span>
              <span class="value">{{ infoCount }}</span>
            </div>
          </div>

          <div class="stat-card glass-panel">
            <div class="stat-icon">📊</div>
            <div class="stat-info">
              <span class="label">{{ $t('alerts.realTime') }}</span>
              <span class="value">{{ totalCount }}</span>
            </div>
          </div>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { impactMetricsFrom, fmtFixed, fmtCount, fmtThousands, fmtSigned, sumKnown, DASH } from '@/utils/impactMetrics'
import { ref, computed, onMounted } from 'vue'
import Header from '@/components/organisms/Header.vue'
import { useEventsStore } from '@/stores'
import { logWarn } from '@/utils/logger'
import { SOURCE_REGISTRY } from '@/config/sourceRegistry'

const eventsStore = useEventsStore()
const activeFilter = ref('all')

// Both of these were hardcoded ("94%" / "5 Live") regardless of what the
// store actually held - real numbers now: confidence averaged across
// whatever incidents actually carry a confidence score, and the source
// count read from the same registry the Source tab uses, not a literal.
const liveSourceCount = computed(() => Object.keys(SOURCE_REGISTRY).length)

const avgConfidenceLabel = computed(() => {
  const withConfidence = eventsStore.allIncidents.filter(i => i.confidence != null)
  if (withConfidence.length === 0) return 'N/A'
  const avg = withConfidence.reduce((sum, i) => sum + (i.confidence ?? 0), 0) / withConfidence.length
  return `${Math.round(avg * 100)}%`
})

interface Alert {
  id: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  icon: string
  title: string
  message: string
  location: string
  time: string
}

const filters = ['all', 'critical', 'high', 'medium', 'info']

const getIncidentIcon = (type: string) => {
  const icons: Record<string, string> = {
    fire: '🔥',
    flood: '💧',
    earthquake: '🌍',
    storm: '🌀',
    landslide: '🏔️',
  }
  return icons[type?.toLowerCase()] || '⚠️'
}

const formatTimeAgo = (date: Date) => {
  if (!date) return 'Recently'
  const diffMs = Date.now() - new Date(date).getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} min ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours} hr ago`
  return `${Math.floor(diffHours / 24)} days ago`
}

// Feature 7: Dynamically derive real-time emergency alerts from analyzed live incidents in store
const alerts = computed<Alert[]>(() => {
  return eventsStore.allIncidents.map((incident, index) => {
    // Severity uses the backend risk score when there is one; otherwise only
    // the incident's own recorded severity. No invented score stands in.
    const score = incident.threatScore ?? null
    let severity: 'critical' | 'high' | 'medium' | 'low' = 'low'
    if (score !== null && score >= 80) severity = 'critical'
    else if ((score !== null && score >= 65) || incident.severity === 'high') severity = 'high'
    else if ((score !== null && score >= 40) || incident.severity === 'medium') severity = 'medium'

    const icon = severity === 'critical' ? '🚨' : getIncidentIcon(incident.type)
    const title = `${(incident.type || 'Hazard').toUpperCase()} EMERGENCY ALERT`
    // Only state measured facts: omit a clause entirely when its value is unknown.
    const scoreClause = score !== null ? `Assessed threat level ${score}/100. ` : ''
    const areaClause = incident.affectedArea != null ? `Affected zone: ${incident.affectedArea.toFixed(0)} km²` : ''
    const popClause = incident.affectedPopulation != null
      ? `${areaClause ? ' with' : 'Affected population:'} ~${(incident.affectedPopulation / 1000).toFixed(0)}K residents`
      : ''
    const locationClause = areaClause || popClause ? `${areaClause}${popClause}. ` : ''
    const message = `${scoreClause}${locationClause}Tactical response advisory in effect.`

    return {
      id: incident.id || `alert-${index}`,
      severity,
      icon,
      title,
      message,
      location: incident.location || 'Global Incident',
      time: formatTimeAgo(incident.detectionTime),
    }
  })
})

const briefText = computed(() => {
  const incidents = eventsStore.allIncidents.length
  const area = eventsStore.totalAffectedArea.toFixed(0)
  const population = (eventsStore.totalAffectedPopulation / 1000).toFixed(0)
  const critical = eventsStore.allIncidents.filter(i => (i.threatScore ?? 0) >= 80 || i.severity === 'high').length
  
  return `GLOBAL THREAT INTELLIGENCE BRIEF: TerraGrid is actively monitoring ${incidents} verified disaster incidents worldwide across 5 real-time satellite and sensor feeds. High-threat clusters identify ${critical} priority emergencies affecting ~${population}K residents and ${area} km² of territory. AI decision support models are operational.`
})

const lastUpdateTime = computed(() => {
  const now = new Date()
  return `Last updated: ${now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}`
})

const filteredAlerts = computed(() => {
  if (activeFilter.value === 'all') return alerts.value
  if (activeFilter.value === 'info') return alerts.value.filter(a => a.severity === 'low')
  return alerts.value.filter(a => a.severity === activeFilter.value)
})

const criticalCount = computed(() => alerts.value.filter(a => a.severity === 'critical').length)
const highCount = computed(() => alerts.value.filter(a => a.severity === 'high').length)
const infoCount = computed(() => alerts.value.filter(a => a.severity === 'low').length)
const totalCount = computed(() => alerts.value.length)

const getFilterLabel = (filter: string) => {
  if (filter === 'all') return `All (${alerts.value.length})`
  if (filter === 'critical') return `🚨 Critical (${criticalCount.value})`
  if (filter === 'high') return `⚠️ High (${highCount.value})`
  if (filter === 'medium') return `📢 Medium (${alerts.value.filter(a => a.severity === 'medium').length})`
  if (filter === 'info') return `ℹ️ Info (${infoCount.value})`
  return filter
}

onMounted(async () => {
  // If navigated directly to /alerts, hydrate live incidents from PostgreSQL database
  if (eventsStore.allIncidents.length === 0) {
    try {
      const host = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)
      const res = await fetch(`${host}/api/v1/incidents?limit=50`)
      if (res.ok) {
        const rawIncidents = await res.json()
        if (Array.isArray(rawIncidents) && rawIncidents.length > 0) {
          const mapped = rawIncidents.map((event: any, index: number) => {
            const impact = event.impact || {}
            const severity = (event.severity || 'medium').toLowerCase()
            return {
              id: event.data?.id || event.data?.nasa_id || event.data?.gdacs_id || event.id || `event-${index}-${Date.now()}`,
              type: event.event_type || 'fire',
              location: event.location_name || 'Unknown',
              severity: (severity === 'critical' ? 'high' : severity === 'low' ? 'low' : severity === 'medium' ? 'medium' : 'high') as 'low' | 'medium' | 'high',
              status: event.status === 'detected' || event.status === 'active' ? 'active' : (event.status || 'active'),
              ...impactMetricsFrom(event),
              detectionTime: new Date(event.event_timestamp || Date.now()),
              coordinates: [event.latitude, event.longitude] as [number, number],
            }
          })
          eventsStore.setIncidents(mapped)
        }
      }
    } catch (err) {
      logWarn('Could not hydrate live incidents on the Alerts screen', err)
    }
  }
})
</script>

<style scoped>
.alerts-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.alerts-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.filter-tabs {
  display: flex;
  gap: 10px;
  padding: 12px;
  flex-wrap: wrap;
}

.tab-btn {
  padding: 10px 16px;
  background: transparent;
  border: 2px solid rgba(255, 255, 255, 0.2);
  color: #c5cdd2;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
  white-space: nowrap;
}

.tab-btn:hover {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.1);
}

.tab-btn.active {
  background: var(--accent-cyan);
  border-color: var(--accent-cyan);
  color: #04141a;
  font-weight: 700;
}

.disaster-brief {
  padding: 20px;
  background: linear-gradient(135deg, rgba(220, 38, 38, 0.1), rgba(220, 38, 38, 0.05));
  border: 1px solid rgba(220, 38, 38, 0.3);
}

.brief-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(220, 38, 38, 0.2);
}

.brief-header h3 {
  margin: 0;
  font-size: 16px;
}

.update-time {
  font-size: 11px;
  color: var(--text-muted);
}

.brief-content p {
  margin: 0 0 12px 0;
  line-height: 1.6;
  font-size: 13px;
}

.brief-metrics {
  display: flex;
  gap: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(220, 38, 38, 0.2);
}

.brief-metrics .metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.brief-metrics .metric .label {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 600;
}

.brief-metrics .metric .value {
  font-size: 14px;
  font-weight: 700;
  color: #ef4444;
}

.alerts-list-wrapper {
  flex: 1;
  overflow: auto;
  padding: 16px;
  min-height: 0;
}

/* Custom Scrollbars */
.alerts-list-wrapper::-webkit-scrollbar,
.alerts-container::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.alerts-list-wrapper::-webkit-scrollbar-track,
.alerts-container::-webkit-scrollbar-track {
  background: transparent;
}

.alerts-list-wrapper::-webkit-scrollbar-thumb,
.alerts-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 999px;
}

.alerts-list-wrapper::-webkit-scrollbar-thumb:hover,
.alerts-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.no-alerts {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-muted);
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  display: flex;
  gap: 14px;
  padding: 16px;
  border-radius: 6px;
  border-left: 6px solid;
  background: rgba(30, 64, 175, 0.05);
  animation: slideIn 0.3s ease-out;
  transition: all 200ms ease;
}

.alert-item:hover {
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.alert-item.critical {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.12);
}

.alert-item.critical .alert-icon {
  color: #ef4444;
}

.alert-item.high {
  border-left-color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
}

.alert-item.high .alert-icon {
  color: #f59e0b;
}

.alert-item.medium {
  border-left-color: #3b82f6;
  background: rgba(59, 130, 246, 0.12);
}

.alert-item.medium .alert-icon {
  color: #3b82f6;
}

.alert-item.low {
  border-left-color: #6b7280;
  background: rgba(107, 114, 128, 0.12);
}

.alert-item.low .alert-icon {
  color: #6b7280;
}

.alert-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.alert-title {
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
}

.alert-message {
  font-size: 12px;
  color: #c5cdd2;
  line-height: 1.4;
  font-weight: 500;
}

.alert-meta {
  display: flex;
  gap: 16px;
  font-size: 11px;
  color: var(--text-muted);
}

.alert-badge {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.severity-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 3px;
  font-weight: 700;
  font-size: 10px;
  text-transform: uppercase;
}

.severity-badge.critical {
  background: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.severity-badge.high {
  background: rgba(245, 158, 11, 0.3);
  color: #f59e0b;
}

.severity-badge.medium {
  background: rgba(59, 130, 246, 0.3);
  color: #3b82f6;
}

.severity-badge.low {
  background: rgba(107, 114, 128, 0.3);
  color: #6b7280;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-top: auto;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
}

.stat-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-info .label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-weight: 600;
}

.stat-info .value {
  font-size: 18px;
  font-weight: 700;
  color: var(--accent-cyan);
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .brief-metrics {
    gap: 12px;
  }
}

@media (max-width: 768px) {
  .alert-item {
    flex-direction: column;
  }

  .alert-badge {
    align-self: flex-start;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .filter-tabs {
    flex-direction: column;
  }

  .tab-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .alerts-screen {
    padding: 8px;
    gap: 8px;
  }

  .alerts-container {
    gap: 8px;
  }

  .filter-tabs {
    padding: 10px;
    gap: 6px;
  }

  .tab-btn {
    font-size: 11px;
    padding: 6px 12px;
  }

  .disaster-brief {
    padding: 12px;
  }

  .brief-header h3 {
    font-size: 14px;
  }

  .brief-content p {
    font-size: 12px;
  }

  .alerts-list-wrapper {
    padding: 12px;
  }

  .alert-item {
    padding: 12px;
    gap: 8px;
  }

  .alert-icon {
    font-size: 20px;
  }

  .alert-title {
    font-size: 12px;
  }

  .alert-message {
    font-size: 11px;
  }

  .alert-meta {
    flex-direction: column;
    gap: 4px;
  }

  .stat-card {
    padding: 12px;
    gap: 8px;
  }

  .stat-icon {
    font-size: 24px;
  }

  .stat-info .value {
    font-size: 16px;
  }
}

</style>
