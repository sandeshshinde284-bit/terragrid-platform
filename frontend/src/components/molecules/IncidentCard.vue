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
        <span class="incident-id">{{ displayIncidentId(incident) }}</span>
      </div>
      <div class="header-bottom">
        <p class="location">{{ formatLocation(incident.location) }}</p>
        <Badge :severity="incident.severity" />
      </div>
    </div>

    <div class="card-body">
      <div class="metric-row">
        <span class="label">AREA</span>
        <span class="value">{{ fmtFixed(incident.affectedArea, 0, ' km²') }}</span>
      </div>
      <div class="metric-row">
        <span class="label">POPULATION</span>
        <span class="value">{{ fmtThousands(incident.affectedPopulation) }}</span>
      </div>
      <div class="metric-row">
        <span class="label">TREND</span>
        <span class="value trend-up">{{ fmtSigned(incident.trend, 1, ' km²/h') }}</span>
      </div>
      <div class="metric-row">
        <span class="label">6h FORECAST</span>
        <span class="value trend-up">{{ fmtSigned(incident.forecast6h, 0, ' km²') }}</span>
      </div>
    </div>

    <button class="action-btn" @click.stop="selectIncident">
      {{ isSelected ? $t('incidents.viewing') : $t('common.details') + ' →' }}
    </button>
  </GlassPanel>
</template>

<script setup lang="ts">
import { displayIncidentId } from '@/utils/incidentId'
import { impactMetricsFrom, fmtFixed, fmtCount, fmtThousands, fmtSigned, sumKnown, DASH } from '@/utils/impactMetrics'
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

/* Type-based border colors - pulled from the shared --hazard-* palette in
   style.css instead of per-component hex literals, and deliberately muted
   so six hazard types don't read as six clashing neon colors on one
   screen. Six distinct types still need six distinguishable colors (it's
   the fastest way to tell hazard type apart at a glance in a dense grid),
   so the fix here is toning them down, not removing the coding. */
.incident-card.incident-type-fire {
  border-color: var(--hazard-fire);
}

.incident-card.incident-type-flood {
  border-color: var(--hazard-flood);
}

.incident-card.incident-type-landslide {
  border-color: var(--hazard-landslide);
}

.incident-card.incident-type-earthquake {
  border-color: var(--hazard-earthquake);
}

.incident-card.incident-type-hurricane {
  border-color: var(--hazard-hurricane);
}

.incident-card.incident-type-volcano {
  border-color: var(--hazard-volcano);
}

.incident-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  border-color: var(--accent-cyan);
}

.incident-card.selected {
  /* Was a 20px neon bloom (rgba(30,64,175,0.3)) on top of an already
     colored type border - a tight highlight ring reads as "selected"
     just as clearly without the glow. */
  border-color: var(--accent-cyan);
  background: rgba(30, 64, 175, 0.15);
  box-shadow: 0 0 0 1px var(--accent-cyan);
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
  color: var(--text-primary);
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
  color: var(--text-secondary);
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
  color: var(--text-secondary);
  font-weight: 700;
  text-transform: uppercase;
  font-size: 10px;
  letter-spacing: 0.8px;
  flex-shrink: 0;
  line-height: 1.4;
  margin-bottom: 2px;
}

.value {
  color: var(--text-primary);
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
  /* Flat accent fill, no gradient or glow - the DETAILS button doesn't
     need to out-shine the hazard-type border and risk badges already on
     this card. */
  background: var(--accent-cyan);
  border: 2px solid var(--accent-cyan);
  color: #04141a;
  padding: 8px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  transition: all 200ms ease;
  margin-top: auto;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.action-btn:hover {
  background: #26c6da;
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

.incident-id {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #cbd5e1;
  background: rgba(148, 163, 184, 0.15);
  vertical-align: middle;
  white-space: nowrap;
}
</style>
