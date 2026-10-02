<template>
  <div class="safe-routes-viewer">
    <div class="viewer-header">
      <h3>Safe Evacuation Routes</h3>
      <button @click="$emit('close')" class="close-btn">✕</button>
    </div>

    <div v-if="loading" class="loading-state">
      <p>Calculating safe routes...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
    </div>

    <div v-else-if="routesData" class="routes-container">
      <!-- Route Cards -->
      <div class="routes-list">
        <div
          v-for="route in routesData.routes"
          :key="route.route_id"
          class="route-card"
          :class="{ active: selectedRoute?.route_id === route.route_id }"
          @click="selectRoute(route)"
        >
          <div class="route-header">
            <h4>{{ route.name }}</h4>
            <span class="safety-badge" :style="getSafetyColor(route.safety_score)">
              Safety: {{ route.safety_score }}%
            </span>
          </div>

          <div class="route-info">
            <div class="info-row">
              <span class="info-label">Distance:</span>
              <span class="info-value">{{ route.distance_km }}km</span>
            </div>
            <div class="info-row">
              <span class="info-label">Est. Time:</span>
              <span class="info-value">{{ route.estimated_time_hours }}h</span>
            </div>
            <div class="info-row">
              <span class="info-label">Capacity:</span>
              <span class="info-value">{{ formatNumber(route.capacity_vehicles_per_hour) }} vehicles/hr</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Selected Route Details -->
      <div v-if="selectedRoute" class="route-details">
        <h4>Route Details: {{ selectedRoute.name }}</h4>
        <div class="details-content">
          <div class="detail-section">
            <span class="section-label">Route Metrics</span>
            <div class="metric-grid">
              <div class="metric">
                <span class="metric-label">Distance</span>
                <span class="metric-value">{{ selectedRoute.distance_km }}km</span>
              </div>
              <div class="metric">
                <span class="metric-label">Time</span>
                <span class="metric-value">{{ selectedRoute.estimated_time_hours }}h</span>
              </div>
              <div class="metric">
                <span class="metric-label">Safety</span>
                <span class="metric-value" :style="getSafetyColor(selectedRoute.safety_score)">
                  {{ selectedRoute.safety_score }}%
                </span>
              </div>
              <div class="metric">
                <span class="metric-label">Capacity</span>
                <span class="metric-value">{{ formatNumber(selectedRoute.capacity_vehicles_per_hour) }}/hr</span>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <span class="section-label">Route Recommendations</span>
            <ul class="recommendations">
              <li>✓ Designated safe evacuation corridor</li>
              <li>✓ Verified traffic flow capacity</li>
              <li>✓ Emergency services prepared</li>
              <li>✓ Medical aid stations positioned</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button @click="shareRoutes" class="btn btn-primary">
          Share Routes
        </button>
        <button @click="downloadRoutes" class="btn btn-secondary">
          Download PDF
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'SafeRoutesViewer',
  props: {
    incidentId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      routesData: null,
      selectedRoute: null,
      loading: false,
      error: null,
    }
  },
  mounted() {
    this.fetchRoutes()
  },
  methods: {
    async fetchRoutes() {
      this.loading = true
      this.error = null

      try {
        const response = await fetch(`/api/zones/routes/${this.incidentId}`)

        if (!response.ok) {
          throw new Error(`API Error: ${response.statusText}`)
        }

        const data = await response.json()
        this.routesData = data.data
        if (this.routesData.routes && this.routesData.routes.length > 0) {
          this.selectedRoute = this.routesData.routes[0]
        }
      } catch (err) {
        this.error = `Failed to fetch routes: ${err.message}`
        console.error('Routes fetch error:', err)
      } finally {
        this.loading = false
      }
    },

    selectRoute(route) {
      this.selectedRoute = route
    },

    getSafetyColor(score) {
      if (score >= 90) return { color: '#00aa00' }
      if (score >= 75) return { color: '#ffff00' }
      if (score >= 60) return { color: '#ff9500' }
      return { color: '#ff0000' }
    },

    formatNumber(num) {
      if (!num) return '0'
      return new Intl.NumberFormat('en-US').format(Math.round(num))
    },

    shareRoutes() {
      const message = `Safe Evacuation Routes for ${this.routesData.incident_id}:\n\n`
      const routesText = this.routesData.routes
        .map(r => `${r.name}: ${r.distance_km}km, Safety: ${r.safety_score}%`)
        .join('\n')
      
      if (navigator.share) {
        navigator.share({
          title: 'Evacuation Routes',
          text: message + routesText,
        })
      } else {
        alert('Share functionality not available on this device')
      }
    },

    downloadRoutes() {
      // Generate simple CSV
      const headers = ['Route', 'Direction', 'Distance (km)', 'Time (h)', 'Safety (%)', 'Capacity']
      const rows = this.routesData.routes.map(r => [
        r.route_id,
        r.direction,
        r.distance_km,
        r.estimated_time_hours,
        r.safety_score,
        r.capacity_vehicles_per_hour,
      ])

      const csv = [headers, ...rows]
        .map(row => row.map(cell => `"${cell}"`).join(','))
        .join('\n')

      const blob = new Blob([csv], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `evacuation_routes_${Date.now()}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
    },
  },
})
</script>

<style scoped>
.safe-routes-viewer {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 8px;
  padding: 20px;
  color: #e2e8f0;
  border: 1px solid #334155;
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid #334155;
}

.viewer-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #f1f5f9;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #94a3b8;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(148, 163, 184, 0.1);
  color: #f1f5f9;
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

.routes-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.routes-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.route-card {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.route-card:hover {
  background: rgba(51, 65, 85, 0.8);
  border-color: #475569;
}

.route-card.active {
  background: rgba(59, 130, 246, 0.1);
  border-color: #3b82f6;
}

.route-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.route-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.safety-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.2);
}

.route-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  font-size: 12px;
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  color: #94a3b8;
  font-weight: 500;
}

.info-value {
  color: #f1f5f9;
  font-weight: 600;
}

.route-details {
  background: rgba(51, 65, 85, 0.5);
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 14px;
}

.route-details h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
}

.details-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.metric {
  background: rgba(30, 41, 59, 0.8);
  border-radius: 4px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.metric-label {
  color: #94a3b8;
}

.metric-value {
  color: #f1f5f9;
  font-weight: 600;
}

.recommendations {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
}

.recommendations li {
  color: #f1f5f9;
  padding-left: 0;
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
.routes-list::-webkit-scrollbar {
  width: 6px;
}

.routes-list::-webkit-scrollbar-track {
  background: rgba(148, 163, 184, 0.1);
  border-radius: 3px;
}

.routes-list::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 3px;
}

.routes-list::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}
</style>
