<template>
  <GlassPanel 
    :severity="incident.severity"
    clickable
    @click="selectIncident"
    :class="['incident-card', `incident-type-${incident.type}`, { selected: isSelected }]"
  >
    <div class="card-header">
      <div class="header-top">
        <span class="icon">{{ iconMap[incident.type] }}</span>
        <h3>{{ incident.type.toUpperCase() }}</h3>
      </div>
      <div class="header-bottom">
        <p class="location">{{ formatLocation(incident.location) }}</p>
        <Badge :severity="incident.severity" />
      </div>
    </div>

    <div class="card-body">
      <div class="metric-row">
        <span class="label">AREA</span>
        <span class="value">{{ incident.affectedArea.toFixed(0) }} km²</span>
      </div>
      <div class="metric-row">
        <span class="label">POPULATION</span>
        <span class="value">{{ (incident.affectedPopulation / 1000).toFixed(0) }}K</span>
      </div>
      <div class="metric-row">
        <span class="label">TREND</span>
        <span class="value trend-up">+{{ incident.trend.toFixed(1) }} km²/h</span>
      </div>
      <div class="metric-row">
        <span class="label">6h FORECAST</span>
        <span class="value trend-up">+{{ incident.forecast6h.toFixed(0) }} km²</span>
      </div>
    </div>

    <button class="action-btn" @click.stop="selectIncident">
      {{ isSelected ? $t('incidents.viewing') : $t('common.details') + ' →' }}
    </button>
  </GlassPanel>
</template>

<script setup lang="ts">
import { computed, defineProps, defineEmits } from 'vue'
import { useI18n } from 'vue-i18n'
import GlassPanel from '../atoms/GlassPanel.vue'
import Badge from '../atoms/Badge.vue'
import { useAppStore } from '@/stores'
import type { IncidentLevel1 } from '@/types'

const props = defineProps<{
  incident: IncidentLevel1
}>()

const emit = defineEmits<{
  expand: [id: string]
}>()

const appStore = useAppStore()

const formatLocation = (loc: string) => {
  if (!loc || !loc.includes(',')) return loc;
  const parts = loc.split(',');
  const code = parts[parts.length - 1].trim();
  if (code.length === 2 && code === code.toUpperCase()) {
     try {
       const displayNames = new Intl.DisplayNames(['en'], { type: 'region' });
       const countryName = displayNames.of(code);
       if (countryName && countryName !== code) {
         parts[parts.length - 1] = ' ' + countryName;
         return parts.join(',');
       }
     } catch (e) {
       return loc;
     }
  }
  return loc;
}
const { t } = useI18n()

const iconMap: Record<string, string> = {
  flood: '💧',
  earthquake: '🌍',
  fire: '🔥',
  hurricane: '🌀',
  volcano: '🌋',
  landslide: '⛰️',
}

const isSelected = computed(() => appStore.selectedIncident === props.incident.id)

const selectIncident = () => {
  appStore.setSelectedIncident(props.incident.id)
  emit('expand', props.incident.id)
}
</script>

<style scoped>
.incident-card {
  cursor: pointer;
  transition: all 200ms ease;
  background: rgba(20, 30, 48, 0.4);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 12px;
  min-height: max-content;
  height: auto;
  border: 1.5px solid rgba(30, 144, 255, 0.25);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  word-wrap: break-word;
  word-break: break-word;
  border: 2px solid rgba(30, 64, 175, 0.3);
  padding: 0;
  gap: 0;
}

.incident-card :deep(.content) {
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 8px;
  height: 100%;
}

/* Type-based border colors */
.incident-card.incident-type-fire {
  border-color: #ff6b35;
}

.incident-card.incident-type-flood {
  border-color: #0066cc;
}

.incident-card.incident-type-landslide {
  border-color: #8b6f47;
}

.incident-card.incident-type-earthquake {
  border-color: #9d4edd;
}

.incident-card.incident-type-hurricane {
  border-color: #00b4d8;
}

.incident-card.incident-type-volcano {
  border-color: #e63946;
}

.incident-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  border-color: var(--accent-cyan);
}

.incident-card.selected {
  border-color: var(--accent-cyan);
  background: rgba(30, 64, 175, 0.15);
  box-shadow: 0 0 20px rgba(30, 64, 175, 0.3);
}

.card-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 6px;
  border-bottom: 2px solid rgba(30, 64, 175, 0.3);
}

.header-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon {
  font-size: 24px;
  flex-shrink: 0;
  line-height: 1;
}

.header-top h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 800;
  line-height: 1.2;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.header-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.location {
  font-size: 11px;
  color: #cbd5e1;
  margin: 0;
  line-height: 1.3;
  flex: 1;
  font-weight: 600;
  word-break: break-word;
  overflow-wrap: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  line-height: 1.1;
}

.label {
  color: #94a3b8;
  font-weight: 700;
  text-transform: uppercase;
  font-size: 10px;
  letter-spacing: 0.8px;
  flex-shrink: 0;
  line-height: 1.4;
  margin-bottom: 2px;
}

.value {
  color: #ffffff;
  font-weight: 800;
  font-size: 14px;
  text-align: right;
  flex-shrink: 0;
  white-space: nowrap;
  line-height: 1.4;
}

.value.trend-up {
  color: #34d399;
  font-weight: 800;
}

.action-btn {
  background: linear-gradient(135deg, #1e40af, #0ea5e9);
  border: 2px solid var(--accent-cyan);
  color: #ffffff;
  padding: 8px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  transition: all 200ms ease;
  margin-top: auto;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 2px 12px rgba(30, 144, 255, 0.4);
}

.action-btn:hover {
  background: linear-gradient(135deg, #1e3a8a, #0284c7);
  box-shadow: 0 4px 20px rgba(30, 144, 255, 0.6);
  transform: translateY(-2px);
}

.action-btn:active {
  transform: translateY(0);
}

/* ===== RESPONSIVE MEDIA QUERIES ===== */

/* Laptop/Tablet (1024px - 1199px) */
@media (max-width: 1199px) {
  /* Commented out to use global max-content rules:
  .incident-card {
    min-height: 160px;
    padding: 12px;
    gap: 10px;
  }
  */

  .card-header {
    gap: 4px;
    padding-bottom: 6px;
  }

  .header-top {
    gap: 10px;
  }

  .header-top h3 {
    font-size: 12px;
    line-height: 1.2;
  }

  .icon {
    font-size: 20px;
  }

  .card-body {
    gap: 3px;
  }

  .label {
    font-size: 8px;
  }

  .value {
    font-size: 12px;
  }

  .action-btn {
    font-size: 11px;
    padding: 6px 10px;
  }
}

/* iPad/Landscape (768px - 1023px) */
@media (max-width: 1023px) {
  /* Commented out to use global max-content rules:
  .incident-card {
    min-height: 140px;
    padding: 10px;
    gap: 8px;
  }
  */

  .card-header {
    gap: 4px;
    padding-bottom: 6px;
  }

  .header-top {
    gap: 10px;
  }

  .header-top h3 {
    font-size: 11px;
    line-height: 1.2;
  }

  .icon {
    font-size: 18px;
  }

  .location {
    font-size: 10px;
  }

  .card-body {
    gap: 2px;
  }

  .label {
    font-size: 7px;
  }

  .value {
    font-size: 11px;
  }

  .action-btn {
    font-size: 10px;
    padding: 5px 8px;
  }
}

/* Mobile Large (480px - 767px) */
@media (max-width: 767px) {
  /* Commented out old rule as requested:
  .incident-card {
    min-height: 130px;
    padding: 8px;
    gap: 8px;
  }
  */

  .incident-card {
    min-height: max-content;
    height: auto;
    padding: 0;
    gap: 0;
  }

  .incident-card :deep(.content) {
    display: flex;
    flex-direction: column;
    padding: 10px;
    gap: 8px;
    height: 100%;
  }

  .card-header {
    gap: 4px;
    padding-bottom: 6px;
  }

  .header-top {
    gap: 8px;
  }

  .header-top h3 {
    font-size: 10px;
    line-height: 1.2;
  }

  .icon {
    font-size: 16px;
  }

  .location {
    font-size: 9px;
  }

  .card-body {
    gap: 2px;
  }

  .label {
    font-size: 7px;
  }

  .value {
    font-size: 11px;
  }

  .action-btn {
    font-size: 10px;
    padding: 5px 8px;
  }
}

/* Mobile Small (320px - 479px) */
@media (max-width: 479px) {
  /* Commented out old rule as requested:
  .incident-card {
    min-height: auto;
    max-height: none;
    padding: 8px;
    gap: 6px;
  }
  */

  .incident-card {
    min-height: max-content;
    height: auto;
    padding: 0;
    gap: 0;
  }

  .incident-card :deep(.content) {
    display: flex;
    flex-direction: column;
    padding: 10px;
    gap: 6px;
    height: 100%;
  }

  .card-header {
    gap: 4px;
    padding-bottom: 6px;
    border-bottom: 1.5px solid rgba(30, 64, 175, 0.4);
  }

  .header-top {
    gap: 8px;
  }

  .header-top h3 {
    font-size: 11px;
    line-height: 1.2;
  }

  .icon {
    font-size: 18px;
  }

  .location {
    font-size: 9px;
    font-weight: 600;
  }

  .card-body {
    gap: 4px;
    flex: 1;
  }

  .metric-row {
    display: flex;
    flex-direction: row;
    gap: 8px;
    line-height: 1.2;
    padding-bottom: 4px;
    border-bottom: 1px solid rgba(30, 64, 175, 0.15);
  }

  .metric-row:last-child {
    border-bottom: none;
    padding-bottom: 0;
  }

  .label {
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.4px;
  }

  .value {
    font-size: 12px;
    font-weight: 700;
    text-align: left;
  }

  .value.trend-up {
    color: #10b981;
  }

  .action-btn {
    font-size: 11px;
    padding: 8px 12px;
    width: 100%;
    margin-top: auto;
  }
}
</style>
