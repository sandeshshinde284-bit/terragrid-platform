<template>
  <div class="zone-stats-panel">
    <div class="panel-header">
      <h3>Evacuation Zones Analysis</h3>
      <span class="incident-name">{{ incident?.location_name || 'Loading...' }}</span>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Calculating evacuation zones...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
    </div>

    <div v-else-if="zonesData" class="zones-container">
      <!-- Summary Stats -->
      <div class="summary-stats">
        <div class="stat-card">
          <span class="stat-label">Total Population At Risk</span>
          <span class="stat-value">{{ formatNumber(zonesData.total_population_affected) }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Threat Score</span>
          <span class="stat-value" :style="getThreatColor(zonesData.threat_score)">
            {{ zonesData.threat_score || 'N/A' }}/100
          </span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Event Type</span>
          <span class="stat-value">{{ formatEventType(zonesData.event_type) }}</span>
        </div>
        <div class="stat-card">
          <span class="stat-label">Severity</span>
          <span class="stat-value" :class="`severity-${zonesData.incident_severity}`">
            {{ zonesData.incident_severity?.toUpperCase() || 'N/A' }}
          </span>
        </div>
      </div>

      <!-- Zones Details -->
      <div class="zones-list">
        <div
          v-for="zone in zonesData.zones"
          :key="zone.zone_id"
          class="zone-card"
          :style="{ borderLeftColor: zone.color }"
        >
          <div class="zone-header">
            <h4 class="zone-title">
              <span class="zone-badge" :style="{ backgroundColor: zone.color }">
                Z{{ zone.zone_number }}
              </span>
              {{ zone.properties?.name }}
            </h4>
            <span class="zone-severity">{{ zone.severity?.toUpperCase() }}</span>
          </div>

          <div class="zone-details">
            <div class="detail-row">
              <span class="detail-label">Radius:</span>
              <span class="detail-value">
                {{ zone.radius_min_km }}km - {{ zone.radius_max_km }}km
              </span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Area:</span>
              <span class="detail-value">{{ zone.area_km2 }}km²</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">Population:</span>
              <span class="detail-value">{{ formatNumber(zone.population_estimate) }}</span>
            </div>
            <div class="detail-row" v-if="zonesData.evacuation_times_hours">
              <span class="detail-label">Evac. Time:</span>
              <span class="detail-value">
                {{ zonesData.evacuation_times_hours[zone.zone_id] || 'N/A' }} hours
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button @click="viewRoutes" class="btn btn-primary">
          View Safe Routes
        </button>
        <button @click="viewResources" class="btn btn-secondary">
          Resource Needs
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ZoneStatsPanel',
  props: {
    incident: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      zonesData: null,
      loading: false,
      error: null,
    }
  },
  computed: {
    incidentId() {
      return this.incident?.data?.nasa_id ||
             this.incident?.data?.usgs_id ||
             this.incident?.location_name ||
             ''
    },
  },
  watch: {
    incident: {
      handler() {
        this.calculateZones()
      },
      deep: true,
    },
  },
  mounted() {
    this.calculateZones()
  },
  methods: {
    async calculateZones() {
      if (!this.incidentId) {
        this.error = 'No incident data available'
        return
      }

      this.loading = true
      this.error = null

      try {
        const response = await fetch(
          `/api/zones/calculate?latitude=${this.incident.latitude}&longitude=${this.incident.longitude}&severity=${this.incident.severity || 'medium'}&event_type=${this.incident.event_type || 'other'}&location_name=${encodeURIComponent(this.incident.location_name || 'Incident')}&threat_score=${this.incident.threat_score || 50}`,
          {
            method: 'POST',
          }
        )

        if (!response.ok) {
          throw new Error(`API Error: ${response.statusText}`)
        }

        const data = await response.json()
        this.zonesData = data.data
        this.$emit('zones-loaded', data.data)
      } catch (err) {
        this.error = `Failed to calculate zones: ${err.message}`
        console.error('Zone calculation error:', err)
      } finally {
        this.loading = false
      }
    },

    formatNumber(num) {
      if (!num) return '0'
      return new Intl.NumberFormat('en-US').format(Math.round(num))
    },

    formatEventType(type) {
      if (!type) return 'Unknown'
      return type.replace(/_/g, ' ').toUpperCase()
    },

    getThreatColor(score) {
      if (!score) return {}
      if (score >= 80) return { color: '#FF0000' }
      if (score >= 60) return { color: '#FF9500' }
      if (score >= 40) return { color: '#FFFF00' }
      return { color: '#00AA00' }
    },

    viewRoutes() {
      this.$emit('view-routes', this.incidentId)
    },

    viewResources() {
      this.$emit('view-resources', this.incidentId)
    },
  },
})
</script>

<style scoped>
.zone-stats-panel {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 8px;
  padding: 20px;
  color: #e2e8f0;
  max-height: 600px;
  overflow-y: auto;
  border: 1px solid #334155;
}

.panel-header {
  margin-bottom: 20px;
  border-bottom: 2px solid #334155;
  padding-bottom: 12px;
}

.panel-header h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #f1f5f9;
}

.incident-name {
  font-size: 13px;
  color: #94a3b8;
}

.loading-state,
.error-state {
  padding: 20px;
  text-align: center;
}

.error-state {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.1);
  border-radius: 4px;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-label {
  font-size: 12px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
}

.severity-low {
  color: #00aa00;
}

.severity-medium {
  color: #ffff00;
}

.severity-high {
  color: #ff9500;
}

.severity-critical {
  color: #ff0000;
}

.zones-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.zone-card {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid #334155;
  border-left: 4px solid;
  border-radius: 6px;
  padding: 12px;
  transition: all 0.3s ease;
}

.zone-card:hover {
  background: rgba(51, 65, 85, 0.8);
  border-color: #475569;
}

.zone-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.zone-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.zone-badge {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  color: #000;
}

.zone-severity {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  padding: 4px 8px;
  background: rgba(148, 163, 184, 0.2);
  border-radius: 3px;
}

.zone-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.detail-label {
  color: #94a3b8;
  font-weight: 500;
}

.detail-value {
  color: #f1f5f9;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  flex: 1;
  min-width: 120px;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%);
}

.btn-secondary {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: white;
}

.btn-secondary:hover {
  background: linear-gradient(135deg, #78909c 0%, #546e7a 100%);
}

/* Scrollbar styling */
.zone-stats-panel::-webkit-scrollbar {
  width: 6px;
}

.zone-stats-panel::-webkit-scrollbar-track {
  background: rgba(148, 163, 184, 0.1);
  border-radius: 3px;
}

.zone-stats-panel::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 3px;
}

.zone-stats-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}
</style>
