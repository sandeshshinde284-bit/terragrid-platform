<template>
  <div class="alerts-screen">
    <Header />

    <div class="alerts-container">
      <div v-if="!appStore.isBackendMockModeEnabled" class="phase2-center-container">
        <div class="phase2-card glass-panel">
          <div class="phase2-icon">🚨</div>
          <div class="phase2-tag">PHASE 2 ROADMAP</div>
          <h2>Alert Management & Dispatch Engine</h2>
          <p>
            Automated SMS, WhatsApp, and multi-channel emergency broadcast dispatchers are scheduled for delivery in <strong>Phase 2</strong>.
          </p>
          <div class="phase2-note">
            Real-time multi-hazard disaster monitoring and AI decision support are fully operational on the <strong>Dashboard</strong> and <strong>Incidents</strong> screens.
          </div>
          <router-link to="/" class="return-dashboard-btn">
            ← Return to Live Dashboard
          </router-link>
        </div>
      </div>

      <!-- ORIGINAL MOCK UI (Dynamically rendered if Backend USE_MOCK_DATA=true) -->
      <template v-else>
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
                <span class="label">Confidence</span>
                <span class="value">94%</span>
              </div>
              <div class="metric">
                <span class="label">Data Sources</span>
                <span class="value">5 Live</span>
              </div>
              <div class="metric">
                <span class="label">Active Threats</span>
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
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Header from '@/components/organisms/Header.vue'
import { useEventsStore, useAppStore } from '@/stores'

const eventsStore = useEventsStore()
const appStore = useAppStore()
const activeFilter = ref('all')

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
    const score = incident.threatScore ?? 50
    let severity: 'critical' | 'high' | 'medium' | 'low' = 'low'
    if (score >= 80 || incident.severity === 'critical') severity = 'critical'
    else if (score >= 65 || incident.severity === 'high') severity = 'high'
    else if (score >= 40 || incident.severity === 'medium') severity = 'medium'

    const icon = severity === 'critical' ? '🚨' : getIncidentIcon(incident.type)
    const title = `${(incident.type || 'Hazard').toUpperCase()} EMERGENCY ALERT`
    const area = incident.affectedArea ? `${incident.affectedArea.toFixed(0)} km²` : 'Active perimeter'
    const pop = incident.affectedPopulation ? `${(incident.affectedPopulation / 1000).toFixed(0)}K residents` : 'Monitored area'
    const message = `Assessed threat level ${score}/100. Affected zone: ${area} with ~${pop} in proximity. Tactical response advisory in effect.`

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
  const critical = eventsStore.allIncidents.filter(i => (i.threatScore ?? 0) >= 80 || i.severity === 'critical').length
  
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
      const host = window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin
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
              severity: (severity === 'critical' ? 'high' : severity) as 'low' | 'medium' | 'high',
              status: event.status === 'detected' || event.status === 'active' ? 'active' : (event.status || 'active'),
              threatScore: impact.risk_score ?? 50,
              detectionTime: new Date(event.event_timestamp || Date.now()),
              affectedArea: impact.affected_area_km2 ?? 150,
              affectedPopulation: impact.affected_population ?? 50000,
              trend: impact.trend_km2_per_hour ?? 5.2,
              forecast6h: impact.forecast_6h_km2 ?? 31.2,
              coordinates: [event.latitude, event.longitude] as [number, number],
            }
          })
          eventsStore.setIncidents(mapped)
        }
      }
    } catch (err) {
      console.warn('AlertsScreen: Failed to hydrate live incidents:', err)
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
  gap: 8px;
  padding: 12px;
  flex-wrap: wrap;
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
  box-shadow: 0 0 8px rgba(30, 144, 255, 0.3);
}

.tab-btn.active {
  background: linear-gradient(135deg, #1e40af, #0ea5e9);
  border-color: var(--accent-cyan);
  color: #ffffff;
  font-weight: 700;
  box-shadow: 0 0 16px rgba(30, 144, 255, 0.5);
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

/* ===== PHASE 2 ROADMAP STYLES ===== */
.phase2-center-container {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 420px;
  padding: 40px 20px;
}

.phase2-card {
  max-width: 520px;
  width: 100%;
  padding: 40px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(15, 23, 42, 0.75);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 16px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}

.phase2-icon {
  font-size: 48px;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 12px rgba(239, 68, 68, 0.4));
}

.phase2-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 800;
  padding: 5px 14px;
  border-radius: 999px;
  background: rgba(14, 165, 233, 0.2);
  color: var(--accent-cyan);
  border: 1px solid rgba(14, 165, 233, 0.4);
  letter-spacing: 1px;
  margin-bottom: 16px;
}

.phase2-card h2 {
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 12px 0;
}

.phase2-card p {
  font-size: 14px;
  line-height: 1.6;
  color: #cbd5e1;
  margin: 0 0 18px 0;
}

.phase2-note {
  font-size: 12px;
  line-height: 1.5;
  color: #94a3b8;
  background: rgba(30, 41, 59, 0.6);
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 24px;
}

.return-dashboard-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 8px;
  background: linear-gradient(135deg, #1e40af, #0ea5e9);
  color: #ffffff;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s ease;
  border: 1px solid var(--accent-cyan);
}

.return-dashboard-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(14, 165, 233, 0.4);
}
</style>
