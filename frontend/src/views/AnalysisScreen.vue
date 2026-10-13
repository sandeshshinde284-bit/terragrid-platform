<template>
  <div class="analysis-screen">
    <Header />

    <div class="analysis-container">
      <div class="selector-panel glass-panel">
        <select id="analysis-select" aria-label="Select Incident" v-model="selectedIncidentId" class="incident-select">
          <option value="">{{ $t('analysis.selectIncident') }}</option>
          <option v-for="incident in eventsStore.allIncidents" :key="incident.id" :value="incident.id">
            {{ incident.type.toUpperCase() }} - {{ incident.location }}
          </option>
        </select>
      </div>

      <div v-if="selectedIncident" class="timeline-section">
        <div class="trends-section glass-panel">
          <h3>{{ $t('analysis.trends') }}</h3>
          <div class="trend-cards">
            <div class="trend-card">
              <div class="trend-icon">📈</div>
              <div class="trend-info">
                <span class="label">{{ $t('incidents.trend') }}</span>
                <span class="value">+{{ selectedIncident.trend.toFixed(1) }} km²/h</span>
                <span class="status positive">Accelerating</span>
              </div>
            </div>

            <div class="trend-card">
              <div class="trend-icon">🎯</div>
              <div class="trend-info">
                <span class="label">{{ $t('incidents.forecast') }} (6h)</span>
                <span class="value">+{{ selectedIncident.forecast6h.toFixed(0) }} km²</span>
                <span class="status">Projected</span>
              </div>
            </div>

            <div class="trend-card">
              <div class="trend-icon">⏱️</div>
              <div class="trend-info">
                <span class="label">Duration Since Detection</span>
                <span class="value">{{ getDurationHours(selectedIncident.detectionTime) }}h</span>
                <span class="status">Active</span>
              </div>
            </div>

            <div class="trend-card">
              <div class="trend-icon">👥</div>
              <div class="trend-info">
                <span class="label">People Affected Per km²</span>
                <span class="value">{{ (selectedIncident.affectedPopulation / selectedIncident.affectedArea).toFixed(0) }}</span>
                <span class="status">Density</span>
              </div>
            </div>
          </div>
        </div>

        <p class="future-note">
          Satellite before/after comparison and historical incident-matching aren't shown here yet - no real imagery or time-series data exists to back them.
        </p>
      </div>

      <div v-else class="empty-state glass-panel">
        <div class="empty-icon">📊</div>
        <h3>{{ $t('analysis.selectIncident') }}</h3>
        <p>Select an incident from the dropdown to view live trend data</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import Header from '@/components/organisms/Header.vue'
import { useEventsStore } from '@/stores'
import type { IncidentLevel1 } from '@/types'

const eventsStore = useEventsStore()
const selectedIncidentId = ref('')

const selectedIncident = computed<IncidentLevel1 | null>(() => {
  if (!selectedIncidentId.value) return null
  return eventsStore.allIncidents.find(i => i.id === selectedIncidentId.value) || null
})

const getDurationHours = (detectionTime: Date) => {
  const now = new Date()
  const diffMs = now.getTime() - detectionTime.getTime()
  return Math.floor(diffMs / (1000 * 60 * 60))
}
</script>

<style scoped>
.analysis-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.analysis-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.selector-panel {
  padding: 16px;
}

.incident-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--glass-border);
  border-radius: 6px;
  background: transparent;
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
}

.incident-select option {
  background: var(--bg-panel);
  color: var(--text-primary);
}

.timeline-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.trends-section {
  padding: 20px;
}

.future-note {
  margin: 0;
  padding: 0 4px;
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
}

.trends-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
}

.trend-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.trend-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(30, 64, 175, 0.05);
  border: 1px solid var(--glass-border);
  border-radius: 6px;
}

.trend-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.trend-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.trend-info .label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  font-weight: 600;
}

.trend-info .value {
  font-size: 16px;
  font-weight: 700;
  color: var(--accent-cyan);
}

.trend-info .status {
  font-size: 10px;
  color: var(--text-muted);
}

.trend-info .status.positive {
  color: #ef4444;
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
}

@media (max-width: 1024px) {
  .trend-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .trend-cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .analysis-screen {
    padding: 8px;
    gap: 8px;
  }

  .analysis-container {
    gap: 8px;
  }

  .selector-panel,
  .trends-section {
    padding: 12px;
  }
}
</style>
