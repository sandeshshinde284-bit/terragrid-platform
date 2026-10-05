<template>
  <div class="analysis-screen">
    <Header />

    <div class="analysis-container">
      <div v-if="!appStore.isBackendMockModeEnabled" class="phase2-center-container">
        <div class="phase2-card glass-panel">
          <div class="phase2-icon">🛰️</div>
          <div class="phase2-tag">PHASE 2 ROADMAP</div>
          <h2>Predictive Cascade & Satellite Analysis</h2>
          <p>
            Multi-spectral satellite change detection, historical RAG incident matching, and predictive cascade modeling (Feature 9) are scheduled for delivery in <strong>Phase 2</strong>.
          </p>
          <div class="phase2-note">
            Real-time multi-hazard disaster monitoring, threat scoring, and AI decision support are fully operational on the <strong>Dashboard</strong> and <strong>Incidents</strong> screens.
          </div>
          <router-link to="/" class="return-dashboard-btn">
            ← Return to Live Dashboard
          </router-link>
        </div>
      </div>

      <template v-else>
      <div class="selector-panel glass-panel">
        <select v-model="selectedIncidentId" class="incident-select">
          <option value="">{{ $t('analysis.selectIncident') }}</option>
          <option v-for="incident in eventsStore.allIncidents" :key="incident.id" :value="incident.id">
            {{ incident.type.toUpperCase() }} - {{ incident.location }}
          </option>
        </select>
      </div>

      <div v-if="selectedIncident" class="timeline-section">
        <div class="before-after-container glass-panel">
          <div class="before-after-wrapper">
            <div class="image-section">
              <div class="image-label">{{ $t('analysis.beforeAfter') }} - {{ $t('common.details') }}</div>
              <div class="before-image">
                <div class="placeholder">
                  <div class="iconography">📡</div>
                  <p>Satellite: Before</p>
                  <p class="date">{{ formatDate(new Date(selectedIncident.detectionTime.getTime() - 7 * 24 * 60 * 60 * 1000)) }}</p>
                </div>
              </div>
            </div>

            <div class="vs-divider">VS</div>

            <div class="image-section">
              <div class="image-label">{{ $t('analysis.beforeAfter') }} - NOW</div>
              <div class="after-image">
                <div class="placeholder">
                  <div class="iconography">🌍</div>
                  <p>Satellite: Current</p>
                  <p class="date">{{ formatDate(selectedIncident.detectionTime) }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="metrics-comparison">
            <div class="comparison-item">
              <span class="label">{{ $t('incidents.affectedArea') }}</span>
              <span class="before">{{ (selectedIncident.affectedArea * 0.3).toFixed(1) }} km²</span>
              <span class="arrow">→</span>
              <span class="after">{{ selectedIncident.affectedArea.toFixed(1) }} km²</span>
            </div>
            <div class="comparison-item">
              <span class="label">{{ $t('incidents.population') }}</span>
              <span class="before">{{ (selectedIncident.affectedPopulation * 0.4).toLocaleString() }}</span>
              <span class="arrow">→</span>
              <span class="after">{{ selectedIncident.affectedPopulation.toLocaleString() }}</span>
            </div>
            <div class="comparison-item">
              <span class="label">{{ $t('incidents.threatScore') }}</span>
              <span class="before">{{ Math.max(20, selectedIncident.threatScore - 30) }}/100</span>
              <span class="arrow">→</span>
              <span class="after">{{ selectedIncident.threatScore }}/100</span>
            </div>
          </div>
        </div>

        <div class="chart-section glass-panel">
          <h3>{{ $t('analysis.areaGrowth') }}</h3>
          <div class="chart-container">
            <canvas ref="chartCanvas"></canvas>
          </div>
          <div class="chart-legend">
            <div class="legend-item">
              <span class="color" style="background: #ef4444;"></span>
              <span>{{ $t('analysis.areaGrowth') }}</span>
            </div>
            <div class="legend-item">
              <span class="color" style="background: #3b82f6;"></span>
              <span>{{ $t('incidents.population') }}</span>
            </div>
          </div>
        </div>

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

        <div class="historical-section glass-panel">
          <h3>{{ $t('analysis.trends') }} - Historical</h3>
          <div class="historical-table">
            <table>
              <thead>
                <tr>
                  <th>{{ $t('common.details') }}</th>
                  <th>{{ $t('incidents.affectedArea') }}</th>
                  <th>{{ $t('incidents.population') }}</th>
                  <th>Growth Rate</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(point, idx) in historicalPoints" :key="idx">
                  <td>{{ idx * 6 }}h ago</td>
                  <td>{{ point.area.toFixed(1) }} km²</td>
                  <td>{{ point.population.toLocaleString() }}</td>
                  <td class="growth">{{ point.growth.toFixed(1) }} km²/h</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div v-else class="empty-state glass-panel">
        <div class="empty-icon">📊</div>
        <h3>{{ $t('analysis.selectIncident') }}</h3>
        <p>Select an incident from the dropdown to view before/after analysis and historical trends</p>
      </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import Header from '@/components/organisms/Header.vue'
import { useEventsStore, useAppStore } from '@/stores'
import type { IncidentLevel1 } from '@/types'

const eventsStore = useEventsStore()
const appStore = useAppStore()
const selectedIncidentId = ref('')
const chartCanvas = ref<HTMLCanvasElement | null>(null)

const selectedIncident = computed<IncidentLevel1 | null>(() => {
  if (!selectedIncidentId.value) return null
  return eventsStore.allIncidents.find(i => i.id === selectedIncidentId.value) || null
})

const historicalPoints = computed(() => {
  if (!selectedIncident.value) return []
  
  const points = []
  for (let i = 5; i >= 0; i--) {
    const progressFactor = (5 - i) / 5
    points.push({
      area: selectedIncident.value.affectedArea * (0.2 + progressFactor * 0.8),
      population: selectedIncident.value.affectedPopulation * (0.3 + progressFactor * 0.7),
      growth: selectedIncident.value.trend * (0.5 + progressFactor * 0.5),
    })
  }
  return points
})

const formatDate = (date: Date) =>
  date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

const getDurationHours = (detectionTime: Date) => {
  const now = new Date()
  const diffMs = now.getTime() - detectionTime.getTime()
  return Math.floor(diffMs / (1000 * 60 * 60))
}

const drawChart = () => {
  if (!chartCanvas.value || !selectedIncident.value) return
  
  const canvas = chartCanvas.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  canvas.width = canvas.parentElement?.clientWidth || 600
  canvas.height = 300
  
  const points = historicalPoints.value
  const maxArea = Math.max(...points.map(p => p.area))
  const maxPopulation = Math.max(...points.map(p => p.population))
  
  const padding = 40
  const width = canvas.width - 2 * padding
  const height = canvas.height - 2 * padding
  const pointSpacing = width / (points.length - 1)
  
  // Background
  ctx.fillStyle = 'transparent'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  
  // Grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.1)'
  ctx.lineWidth = 1
  for (let i = 0; i <= 5; i++) {
    const y = padding + (height / 5) * i
    ctx.beginPath()
    ctx.moveTo(padding, y)
    ctx.lineTo(canvas.width - padding, y)
    ctx.stroke()
  }
  
  // Area line
  ctx.strokeStyle = '#ef4444'
  ctx.lineWidth = 3
  ctx.beginPath()
  for (let i = 0; i < points.length; i++) {
    const x = padding + i * pointSpacing
    const y = padding + height - (points[i].area / maxArea) * height
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.stroke()
  
  // Population line
  ctx.strokeStyle = '#3b82f6'
  ctx.lineWidth = 3
  ctx.beginPath()
  for (let i = 0; i < points.length; i++) {
    const x = padding + i * pointSpacing
    const y = padding + height - (points[i].population / maxPopulation) * height
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.stroke()
  
  // Points
  ctx.fillStyle = '#ef4444'
  for (let i = 0; i < points.length; i++) {
    const x = padding + i * pointSpacing
    const y = padding + height - (points[i].area / maxArea) * height
    ctx.beginPath()
    ctx.arc(x, y, 4, 0, Math.PI * 2)
    ctx.fill()
  }
  
  ctx.fillStyle = '#3b82f6'
  for (let i = 0; i < points.length; i++) {
    const x = padding + i * pointSpacing
    const y = padding + height - (points[i].population / maxPopulation) * height
    ctx.beginPath()
    ctx.arc(x, y, 4, 0, Math.PI * 2)
    ctx.fill()
  }
  
  // Axes
  ctx.strokeStyle = 'rgba(255,255,255,0.3)'
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(padding, padding)
  ctx.lineTo(padding, canvas.height - padding)
  ctx.lineTo(canvas.width - padding, canvas.height - padding)
  ctx.stroke()
  
  // Labels
  ctx.fillStyle = 'var(--text-secondary)'
  ctx.font = '12px sans-serif'
  ctx.textAlign = 'center'
  for (let i = 0; i < points.length; i++) {
    const x = padding + i * pointSpacing
    ctx.fillText(`${i * 6}h`, x, canvas.height - 10)
  }
}

onMounted(() => {
  if (eventsStore.allIncidents.length === 0) {
    // [STRICT LIVE MODE] eventsStore.initMockData()
  }
})

watch(selectedIncident, () => {
  setTimeout(drawChart, 100)
}, { deep: true })

watch(() => chartCanvas.value, () => {
  drawChart()
})
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

.before-after-container {
  padding: 20px;
}

.before-after-wrapper {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.image-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.image-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-cyan);
  text-transform: uppercase;
}

.before-image,
.after-image {
  width: 100%;
  aspect-ratio: 4 / 3;
  border: 2px solid var(--glass-border);
  border-radius: 8px;
  overflow: hidden;
}

.placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.1), rgba(30, 64, 175, 0.05));
}

.placeholder .iconography {
  font-size: 48px;
}

.placeholder p {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.placeholder .date {
  font-size: 10px;
  color: var(--text-muted);
}

.vs-divider {
  font-weight: 700;
  color: var(--accent-cyan);
  font-size: 18px;
  flex-shrink: 0;
}

.metrics-comparison {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--glass-border);
}

.comparison-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
}

.comparison-item .label {
  flex: 1;
  color: var(--text-secondary);
  font-weight: 600;
}

.comparison-item .before {
  color: var(--text-muted);
}

.comparison-item .arrow {
  color: var(--accent-cyan);
  font-weight: 700;
}

.comparison-item .after {
  color: #ef4444;
  font-weight: 600;
}

.chart-section {
  padding: 20px;
}

.chart-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
}

.chart-container {
  height: 300px;
  margin-bottom: 16px;
}

.chart-container canvas {
  width: 100%;
  height: 100%;
}

.chart-legend {
  display: flex;
  gap: 24px;
  padding-top: 12px;
  border-top: 1px solid var(--glass-border);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.legend-item .color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.trends-section {
  padding: 20px;
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

.historical-section {
  padding: 20px;
}

.historical-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
}

.historical-table {
  overflow-x: auto;
}

.historical-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.historical-table th {
  padding: 10px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid var(--glass-border);
  color: var(--accent-cyan);
}

.historical-table td {
  padding: 10px;
  border-bottom: 1px solid var(--glass-border);
}

.historical-table .growth {
  color: #ef4444;
  font-weight: 600;
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
  .before-after-wrapper {
    gap: 12px;
  }

  .trend-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .before-after-wrapper {
    flex-direction: column;
  }

  .vs-divider {
    transform: rotate(90deg);
  }

  .image-section {
    width: 100%;
  }

  .trend-cards {
    grid-template-columns: 1fr;
  }

  .chart-container {
    height: 250px;
  }

  .metrics-comparison {
    gap: 8px;
  }

  .comparison-item {
    flex-wrap: wrap;
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
  .before-after-container,
  .chart-section,
  .trends-section,
  .historical-section {
    padding: 12px;
  }

  .image-label {
    font-size: 11px;
  }

  .placeholder {
    gap: 4px;
  }

  .placeholder .iconography {
    font-size: 32px;
  }

  .chart-container {
    height: 200px;
  }

  .historical-table {
    font-size: 11px;
  }

  .historical-table th,
  .historical-table td {
    padding: 6px;
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
  filter: drop-shadow(0 0 12px rgba(14, 165, 233, 0.4));
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
