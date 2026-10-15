<template>
  <div class="source-tab">
    <div class="tab-intro">
      <div>
        <h2>{{ $t('detail.tabTitles.source') }}</h2>
        <p>{{ $t('detail.tabTitles.sourceDesc') }}</p>
      </div>
    </div>

    <!-- INCIDENT-LEVEL DATA SOURCES: Show ONLY sources used for THIS incident -->
    <div v-if="incident" class="sources-container">
      <!-- Primary Source Information -->
      <article class="glass-panel" style="margin-bottom: 20px; padding: 20px;">
        <div class="panel-heading" style="margin-bottom: 16px;">
          <div>
            <span class="section-kicker">Primary Source</span>
            <h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">{{ incident.source || 'Unknown' }}</h3>
          </div>
          <div style="text-align: right;">
            <span style="color: var(--text-secondary); font-size: 16px;">Detection Time:</span>
            <div style="color: #4ade80; font-weight: 600; font-family: ui-monospace, monospace; font-size: 16px;">
              {{ formatTime(incident.event_timestamp) }}
            </div>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
          <!-- Column 1: API Details -->
          <div style="background: var(--bg-subtle); padding: 12px; border-radius: 6px;">
            <small style="color: var(--text-secondary); text-transform: uppercase; font-size: 16px; letter-spacing: 0.05em;">API Source</small>
            <div style="color: var(--text-primary); font-weight: 600; margin-top: 6px; font-size: 16px;">
              {{ getSourceDetails(incident.source).name }}
            </div>
            <small style="color: var(--text-secondary); margin-top: 4px; display: block;">{{ getSourceDetails(incident.source).description }}</small>
          </div>

          <!-- Column 2: Confidence Score -->
          <div style="background: var(--bg-subtle); padding: 12px; border-radius: 6px;">
            <small style="color: var(--text-secondary); text-transform: uppercase; font-size: 16px; letter-spacing: 0.05em;">Confidence</small>
            <div :style="{ color: getConfidenceColor(incident.confidence * 100), fontWeight: '600', marginTop: '6px', fontSize: '18px', fontFamily: 'ui-monospace, monospace' }">
              {{ Math.round(incident.confidence * 100) }}%
            </div>
            <small style="color: var(--text-secondary); margin-top: 4px; display: block; font-size: 15px;">
              {{ getConfidenceLabel(incident.confidence * 100) }}
            </small>
          </div>

          <!-- Column 3: Data Freshness -->
          <div style="background: var(--bg-subtle); padding: 12px; border-radius: 6px;">
            <small style="color: var(--text-secondary); text-transform: uppercase; font-size: 16px; letter-spacing: 0.05em;">Data Age</small>
            <div style="color: var(--text-primary); font-weight: 600; margin-top: 6px; font-size: 16px; font-family: ui-monospace, monospace;">
              {{ getDataAge() }} ago
            </div>
            <small :style="{ color: getFreznessColor(), marginTop: '4px', display: 'block', fontSize: '11px' }">
              {{ getFreshnessStatus() }}
            </small>
          </div>
        </div>
      </article>

      <!-- Source-Specific Details: Show actual data from this incident -->
      <article class="glass-panel" style="margin-bottom: 20px; padding: 20px;">
        <div class="panel-heading" style="margin-bottom: 16px;">
          <span class="section-kicker">Incident Data from {{ incident.source }}</span>
          <h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">Raw telemetry that was ingested</h3>
        </div>

        <div style="background: var(--bg-overlay); padding: 12px; border-radius: 6px; border-left: 2px solid var(--accent-cyan); font-family: ui-monospace, monospace; font-size: 16px; color: var(--text-secondary); line-height: 1.6; max-height: 300px; overflow-y: auto;">
          <div v-for="(value, key) in getIncidentDataDisplay()" :key="key" style="margin-bottom: 8px;">
            <span style="color: var(--accent-cyan);">{{ key }}:</span> <span style="color: var(--text-primary);">{{ value }}</span>
          </div>
        </div>
      </article>

      <!-- Location-Specific Accuracy -->
      <article class="glass-panel" style="margin-bottom: 20px; padding: 20px;">
        <div class="panel-heading" style="margin-bottom: 16px;">
          <span class="section-kicker">Location Accuracy</span>
          <h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">{{ incident.location_name }} ({{ getCountry(incident) }})</h3>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div style="background: var(--bg-subtle); padding: 12px; border-radius: 6px;">
            <small style="color: var(--text-secondary); text-transform: uppercase; font-size: 16px;">Historical Accuracy</small>
            <div style="color: #4ade80; font-weight: 600; margin-top: 4px; font-size: 16px;">
              {{ getSourceDetails(incident.source).accuracy }}%
            </div>
            <small style="color: var(--text-secondary); margin-top: 4px; display: block; font-size: 16px;">
              {{ getSourceDetails(incident.source).region }}
            </small>
          </div>

          <div style="background: var(--bg-subtle); padding: 12px; border-radius: 6px;">
            <small style="color: var(--text-secondary); text-transform: uppercase; font-size: 16px;">Known Limitations</small>
            <small style="color: #fbbf24; margin-top: 4px; display: block; font-size: 16px;">
              {{ getSourceDetails(incident.source).limitations }}
            </small>
          </div>
        </div>
      </article>

      <!-- Audit Trail: Who accessed this data -->
      <article class="glass-panel" style="margin-bottom: 20px; padding: 20px;">
        <div class="panel-heading" style="margin-bottom: 16px;">
          <span class="section-kicker">Audit Trail</span>
          <h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">Data custody & access log</h3>
        </div>

        <div style="display: flex; flex-direction: column; gap: 8px;">
          <div v-for="(log, idx) in getAuditLog()" :key="idx" style="background: var(--bg-subtle); padding: 10px; border-radius: 4px; border-left: 2px solid var(--accent-cyan); font-size: 16px;">
            <div style="color: var(--text-primary); font-weight: 600;">{{ log.action }}</div>
            <small style="color: var(--text-secondary);">{{ log.timestamp }} by {{ log.actor }}</small>
          </div>
          <small v-if="getAuditLog().length === 0" style="color: var(--text-muted); font-style: italic;">No access logs recorded yet</small>
        </div>
      </article>

      <!-- Data Completeness -->
      <article class="glass-panel" style="padding: 20px;">
        <div class="panel-heading" style="margin-bottom: 16px;">
          <span class="section-kicker">Data Completeness</span>
          <h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">Which fields are populated from this source</h3>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px;">
          <div v-for="field in getDataFields()" :key="field.name" style="background: var(--bg-subtle); padding: 8px; border-radius: 4px; text-align: center;">
            <div :style="{ color: field.present ? '#4ade80' : '#ef4444', fontWeight: '600', fontSize: '12px' }">
              {{ field.present ? '✓' : '✗' }}
            </div>
            <small style="color: var(--text-secondary); font-size: 15px; margin-top: 2px; display: block;">{{ field.name }}</small>
          </div>
        </div>
      </article>
    </div>

    <!-- Empty State -->
    <div v-else style="text-align: center; padding: 40px; color: var(--text-secondary);">
      <div style="font-size: 48px; margin-bottom: 12px;">⌁</div>
      <h3 style="color: var(--text-secondary);">No incident data available</h3>
      <p>Select an incident to view its source of truth information</p>
    </div>
  </div>
</template>

<script setup lang="ts">

import type { IncidentLevel1 } from '@/types'
import { getSourceDetails } from '@/config/sourceRegistry'

const props = defineProps<{
  incident?: IncidentLevel1
}>()

// Helper: Get confidence color
function getConfidenceColor(confidence: number): string {
  if (confidence >= 90) return '#4ade80'
  if (confidence >= 70) return '#fbbf24'
  if (confidence >= 50) return '#fb923c'
  return '#ef4444'
}

// Helper: Get confidence label
function getConfidenceLabel(confidence: number): string {
  if (confidence >= 90) return 'Excellent'
  if (confidence >= 70) return 'Good'
  if (confidence >= 50) return 'Fair'
  return 'Low'
}

// Helper: Format timestamp
function formatTime(timestamp: string | Date): string {
  if (!timestamp) return 'Unknown'
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Helper: Get data age
function getDataAge(): string {
  if (!props.incident?.event_timestamp) return 'Unknown'
  const now = new Date()
  const eventTime = new Date(props.incident.event_timestamp)
  const diffMinutes = Math.floor((now.getTime() - eventTime.getTime()) / 60000)
  
  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes < 60) return `${diffMinutes}m`
  const hours = Math.floor(diffMinutes / 60)
  if (hours < 24) return `${hours}h`
  const days = Math.floor(hours / 24)
  return `${days}d`
}

// Helper: Get freshness color & status
function getFreznessColor(): string {
  if (!props.incident?.event_timestamp) return '#94a3b8'
  const now = new Date()
  const eventTime = new Date(props.incident.event_timestamp)
  const diffMinutes = Math.floor((now.getTime() - eventTime.getTime()) / 60000)
  
  if (diffMinutes < 5) return '#4ade80'
  if (diffMinutes < 30) return '#fbbf24'
  return '#ef4444'
}

function getFreshnessStatus(): string {
  if (!props.incident?.event_timestamp) return 'Unknown'
  const now = new Date()
  const eventTime = new Date(props.incident.event_timestamp)
  const diffMinutes = Math.floor((now.getTime() - eventTime.getTime()) / 60000)
  
  if (diffMinutes < 5) return '🟢 Fresh (< 5 min)'
  if (diffMinutes < 30) return '🟡 Acceptable (< 30 min)'
  return '🔴 Stale (> 30 min)'
}

// Helper: Get country from incident
function getCountry(incident: IncidentLevel1): string {
  return incident.countryCode || 'UN'
}

// Helper: Get incident data for display (clean JSON)
function getIncidentDataDisplay(): Record<string, string> {
  if (!props.incident) return {}

  const display: Record<string, string> = {}

  // 1. Primary: Use incident.data if it exists and has content
  if (props.incident.data && Object.keys(props.incident.data).length > 0) {
    const data = props.incident.data
    const importantFields = ['id', 'event_type', 'location_name', 'severity', 'status', 'latitude', 'longitude', 'threatScore', 'affectedArea', 'affectedPopulation']
    
    for (const field of importantFields) {
      if (data[field] !== undefined && data[field] !== null) {
        display[field] = String(data[field])
      }
    }
  }

  // 2. Fallback: If data is empty or missing, extract from incident-level fields
  if (Object.keys(display).length === 0) {
    if (props.incident.event_type) display['event_type'] = String(props.incident.event_type)
    if (props.incident.location_name) display['location'] = String(props.incident.location_name)
    if (props.incident.latitude) display['latitude'] = String(props.incident.latitude)
    if (props.incident.longitude) display['longitude'] = String(props.incident.longitude)
    if (props.incident.severity) display['severity'] = String(props.incident.severity)
    if (props.incident.status) display['status'] = String(props.incident.status)
    display['confidence'] = `${Math.round((props.incident.confidence || 0) * 100)}%`
    display['source'] = String(props.incident.source || 'Unknown')
  }

  return display
}

// Helper: Get audit log
function getAuditLog(): Array<{action: string, timestamp: string, actor: string}> {
  return [
    {
      action: 'Incident detected',
      timestamp: props.incident?.event_timestamp ? new Date(props.incident.event_timestamp).toLocaleTimeString() : 'Unknown',
      actor: props.incident?.source || 'System'
    }
  ]
}

// Helper: Get data fields - checks both incident.data and top-level incident fields
function getDataFields(): Array<{name: string, present: boolean}> {
  if (!props.incident) return []

  const data = props.incident.data || {}
  const incident = props.incident

  return [
    { name: 'Type', present: !!(data.event_type || incident.event_type) },
    { name: 'Location', present: !!(data.location_name || incident.location_name || incident.location) },
    { name: 'Severity', present: !!(data.severity || incident.severity) },
    { name: 'Status', present: !!(data.status || incident.status) },
    { name: 'Coordinates', present: !!(
      (data.latitude && data.longitude) ||
      (incident.latitude && incident.longitude)
    ) },
    { name: 'Threat', present: !!(data.threatScore || incident.threatScore) },
    { name: 'Area', present: !!(data.affectedArea || incident.affectedArea) },
    { name: 'Population', present: !!(data.affectedPopulation || incident.affectedPopulation) }
  ]
}
</script>

<style scoped>
.source-tab {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.tab-intro {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  margin-bottom: 24px;
}

.tab-intro h2 {
  margin: 0;
  font-size: 28px;
  color: var(--text-primary);
  font-weight: 700;
}

.tab-intro p {
  margin: 8px 0 0 0;
  color: var(--text-secondary);
  font-size: 16px;
}

.sources-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.glass-panel {
  background: var(--bg-panel);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.section-kicker {
  display: block;
  font-size: 16px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 700;
  margin-bottom: 6px;
}

@media (max-width: 768px) {
  .tab-intro {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .tab-intro h2 {
    font-size: 24px;
  }

  .panel-heading {
    flex-direction: column;
    align-items: flex-start;
  }

  /* Stack all grids to 1 column on mobile */
  [style*="grid-template-columns: 1fr 1fr 1fr"] {
    grid-template-columns: 1fr !important;
  }

  [style*="grid-template-columns: 1fr 1fr"] {
    grid-template-columns: 1fr !important;
  }

  /* Reduce font sizes on mobile */
  .section-kicker {
    font-size: 12px;
  }
}
</style>
