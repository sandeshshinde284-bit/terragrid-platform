<template>
  <div class="alerts-screen">
    <Header />

    <div class="alerts-container">
      <!-- Filter Tabs -->
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

      <!-- AI Disaster Brief -->
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
              <span class="value">92%</span>
            </div>
            <div class="metric">
              <span class="label">Data Sources</span>
              <span class="value">7</span>
            </div>
            <div class="metric">
              <span class="label">Last Model Run</span>
              <span class="value">2m ago</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Alerts List -->
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

      <!-- Statistics -->
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
import { ref, computed, onMounted } from 'vue'
import Header from '@/components/organisms/Header.vue'
import { useEventsStore } from '@/stores'

const eventsStore = useEventsStore()
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

const alerts = ref<Alert[]>([
  {
    id: '1',
    severity: 'critical',
    icon: '🚨',
    title: 'Landslide Event Detected',
    message: 'Rapid area expansion detected near San Jose. 87/100 threat score. Evacuation recommended.',
    location: 'San Jose, CA',
    time: '1 min ago',
  },
  {
    id: '2',
    severity: 'critical',
    icon: '🔥',
    title: 'Fire Spread Acceleration',
    message: 'Santa Cruz fire expanding at 2.1 km²/h. 45,000 people in precautionary zones.',
    location: 'Santa Cruz, CA',
    time: '3 min ago',
  },
  {
    id: '3',
    severity: 'high',
    icon: '💧',
    title: 'Flood Level Rising',
    message: 'Russian River flood levels rising. Secondary flood risk zones identified.',
    location: 'Russian River, CA',
    time: '5 min ago',
  },
  {
    id: '4',
    severity: 'high',
    icon: '🌍',
    title: 'Seismic Activity',
    message: 'Magnitude 4.2 earthquake detected. Minor aftershock risk through tomorrow.',
    location: 'San Francisco Bay Area',
    time: '7 min ago',
  },
  {
    id: '5',
    severity: 'medium',
    icon: '⛔',
    title: 'Evacuation Zone Expansion',
    message: '2 new evacuation zones activated. 12,000 additional residents advised to prepare.',
    location: 'Marin County, CA',
    time: '10 min ago',
  },
  {
    id: '6',
    severity: 'medium',
    icon: '🛣️',
    title: 'Emergency Route Updated',
    message: 'Highway 101 North rerouted due to landslide debris. Use alternate Route 280.',
    location: 'Oakland, CA',
    time: '12 min ago',
  },
  {
    id: '7',
    severity: 'medium',
    icon: '👥',
    title: 'Population Alert',
    message: '8,500 residents in isolated areas. Rescue teams dispatched.',
    location: 'Sierra Nevada, CA',
    time: '15 min ago',
  },
  {
    id: '8',
    severity: 'low',
    icon: 'ℹ️',
    title: 'Data Updated',
    message: 'Real-time satellite imagery refreshed. 7 new data sources integrated.',
    location: 'All Zones',
    time: '20 min ago',
  },
  {
    id: '9',
    severity: 'critical',
    icon: '🚨',
    title: 'Critical Water Shortage',
    message: 'Water treatment facility compromised. Emergency water supplies initiated.',
    location: 'Santa Rosa, CA',
    time: '22 min ago',
  },
  {
    id: '10',
    severity: 'high',
    icon: '🏥',
    title: 'Medical Resources Alert',
    message: 'Hospitals near Santa Cruz at 85% capacity. Additional medical staff requested.',
    location: 'Santa Cruz County',
    time: '25 min ago',
  },
  {
    id: '11',
    severity: 'high',
    icon: '📡',
    title: 'Communication Infrastructure',
    message: '3 cell towers affected by fire. Alternative networks activated.',
    location: 'Santa Cruz & Surrounding',
    time: '28 min ago',
  },
  {
    id: '12',
    severity: 'medium',
    icon: '🚗',
    title: 'Transportation Disruption',
    message: '6 major roads closed. Public transit diverted to alternative routes.',
    location: 'Bay Area',
    time: '30 min ago',
  },
])

const briefText = computed(() => {
  const incidents = eventsStore.allIncidents.length
  const area = eventsStore.totalAffectedArea.toFixed(0)
  const population = (eventsStore.totalAffectedPopulation / 1000).toFixed(0)
  
  return `CRITICAL SITUATION UPDATE: ${incidents} active disaster incidents across California affecting approximately ${population}K people and ${area} km² of territory. Primary threats: Landslide near San Jose (87/100), Fire near Santa Cruz (82/100), Flood in Russian River (78/100). Evacuation zones expanding. Emergency response activated. Follow official directives and stay in safe zones.`
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
  if (filter === 'medium') return `📢 Medium`
  if (filter === 'info') return `ℹ️ Info (${infoCount.value})`
  return filter
}

onMounted(() => {
  if (eventsStore.allIncidents.length === 0) {
    eventsStore.initMockData()
  }

  // Simulate real-time alerts (WebSocket simulation)
  setInterval(() => {
    // In production, this would be a real WebSocket connection
    // For now, just show the mock data
  }, 30000)
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
</style>
