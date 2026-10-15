<template>
  <div class="analysis-screen">
    <Header />

    <div class="analysis-container">
      <div class="selector-panel glass-panel" ref="dropdownRef">
        <div class="custom-dropdown">
          <div 
            class="dropdown-trigger" 
            :class="{ 'is-open': isDropdownOpen }"
            @click="isDropdownOpen = !isDropdownOpen"
          >
            <span class="selected-text">
              {{ selectedIncident ? `${selectedIncident.type.toUpperCase()} - ${selectedIncident.location}` : $t('analysis.selectIncident') }}
            </span>
            <span class="chevron" :class="{ 'is-open': isDropdownOpen }">▾</span>
          </div>

          <div v-if="isDropdownOpen" class="dropdown-options">
            <div 
              class="dropdown-option" 
              :class="{ active: !selectedIncidentId }"
              @click="selectIncident('')"
            >
              {{ $t('analysis.selectIncident') }}
            </div>
            <div 
              v-for="incident in eventsStore.allIncidents" 
              :key="incident.id" 
              class="dropdown-option"
              :class="{ active: selectedIncidentId === incident.id }"
              @click="selectIncident(incident.id)"
            >
              <span class="option-type">{{ incident.type.toUpperCase() }}</span>
              <span class="option-separator">-</span>
              <span class="option-loc">{{ incident.location }}</span>
            </div>
          </div>
        </div>
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
                <span class="status positive">{{ $t('analysis.accelerating') }}</span>
              </div>
            </div>

            <div class="trend-card">
              <div class="trend-icon">🎯</div>
              <div class="trend-info">
                <span class="label">{{ $t('incidents.forecast') }} (6h)</span>
                <span class="value">+{{ selectedIncident.forecast6h.toFixed(0) }} km²</span>
                <span class="status">{{ $t('analysis.projected') }}</span>
              </div>
            </div>

            <div class="trend-card">
              <div class="trend-icon">⏱️</div>
              <div class="trend-info">
                <span class="label">{{ $t('analysis.duration') }}</span>
                <span class="value">{{ getDurationHours(selectedIncident.detectionTime) }}h</span>
                <span class="status">{{ $t('common.active') }}</span>
              </div>
            </div>

            <div class="trend-card">
              <div class="trend-icon">👥</div>
              <div class="trend-info">
                <span class="label">{{ $t('analysis.density') }}</span>
                <span class="value">{{ (selectedIncident.affectedPopulation / selectedIncident.affectedArea).toFixed(0) }}</span>
                <span class="status">{{ $t('analysis.densityLabel') }}</span>
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
import { computed, ref, onMounted, onUnmounted } from 'vue'
import Header from '@/components/organisms/Header.vue'
import { useEventsStore } from '@/stores'
import type { IncidentLevel1 } from '@/types'

const eventsStore = useEventsStore()
const selectedIncidentId = ref('')
const isDropdownOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const selectIncident = (id: string) => {
  selectedIncidentId.value = id
  isDropdownOpen.value = false
}

const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isDropdownOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

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

/* Custom Scrollbars */
.analysis-container::-webkit-scrollbar,
.dropdown-options::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.analysis-container::-webkit-scrollbar-track,
.dropdown-options::-webkit-scrollbar-track {
  background: transparent;
}

.analysis-container::-webkit-scrollbar-thumb,
.dropdown-options::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 999px;
}

.analysis-container::-webkit-scrollbar-thumb:hover,
.dropdown-options::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.selector-panel {
  padding: 16px;
  position: relative;
  z-index: 50;
}

.custom-dropdown {
  position: relative;
  width: 100%;
}

.dropdown-trigger {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--glass-border);
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.7);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  user-select: none;
  transition: all 0.2s ease;
}

.dropdown-trigger:hover,
.dropdown-trigger.is-open {
  border-color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.1);
}

.selected-text {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chevron {
  font-size: 14px;
  color: var(--accent-cyan);
  transition: transform 0.2s ease;
  margin-left: 8px;
}

.chevron.is-open {
  transform: rotate(180deg);
}

.dropdown-options {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: #0f172a;
  border: 1px solid var(--accent-cyan);
  border-radius: 6px;
  max-height: 280px;
  overflow-y: auto;
  z-index: 100;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.7);
}

.dropdown-option {
  padding: 10px 14px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.15s ease;
}

.dropdown-option:last-child {
  border-bottom: none;
}

.dropdown-option:hover {
  background: rgba(0, 188, 212, 0.15);
  color: #ffffff;
}

.dropdown-option.active {
  background: rgba(0, 188, 212, 0.25);
  color: var(--accent-cyan);
  font-weight: 600;
}

.option-type {
  font-weight: 700;
  color: #38bdf8;
  font-size: 12px;
  letter-spacing: 0.5px;
}

.option-separator {
  color: var(--text-muted);
}

.option-loc {
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
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
