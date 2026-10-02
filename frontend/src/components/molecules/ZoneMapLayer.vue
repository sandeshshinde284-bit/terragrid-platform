<template>
  <div class="zone-map-layer">
    <div v-if="zones.length > 0" class="zones-overlay">
      <!-- Zone Visualization -->
      <svg v-if="mapCanvas" class="zones-svg" :width="mapWidth" :height="mapHeight">
        <!-- Background circles for each zone -->
        <g class="zones-group">
          <circle
            v-for="(zone, index) in zones"
            :key="`zone-${zone.zone_id}`"
            :cx="mapWidth / 2"
            :cy="mapHeight / 2"
            :r="getZoneRadius(zone, index)"
            :fill="zone.color"
            :opacity="0.15"
            class="zone-circle"
            @mouseover="hoveredZone = zone"
            @mouseout="hoveredZone = null"
          />
        </g>

        <!-- Zone borders -->
        <g class="zone-borders">
          <circle
            v-for="zone in zones"
            :key="`border-${zone.zone_id}`"
            :cx="mapWidth / 2"
            :cy="mapHeight / 2"
            :r="getZoneRadius(zone, zones.indexOf(zone))"
            :stroke="zone.color"
            :stroke-width="2"
            fill="none"
            :opacity="hoveredZone?.zone_id === zone.zone_id ? 1 : 0.6"
            class="zone-border"
          />
        </g>

        <!-- Zone labels -->
        <g class="zone-labels" font-family="Arial, sans-serif" font-size="12">
          <text
            v-for="zone in zones"
            :key="`label-${zone.zone_id}`"
            :x="mapWidth / 2"
            :y="mapHeight / 2 - getZoneRadius(zone, zones.indexOf(zone)) + 30"
            text-anchor="middle"
            :fill="zone.color"
            font-weight="bold"
            class="zone-label"
          >
            Zone {{ zone.zone_number }} ({{ zone.radius_max_km }}km)
          </text>
        </g>

        <!-- Center point (incident) -->
        <circle
          cx="50%"
          cy="50%"
          r="8"
          fill="#FF1493"
          stroke="white"
          stroke-width="2"
          class="incident-marker"
        />
      </svg>

      <!-- Zone Legend -->
      <div class="zone-legend">
        <div class="legend-title">Evacuation Zones</div>
        <div v-for="zone in zones" :key="`legend-${zone.zone_id}`" class="legend-item">
          <span
            class="legend-color"
            :style="{ backgroundColor: zone.color }"
          ></span>
          <span class="legend-text">
            Zone {{ zone.zone_number }}: {{ zone.severity }} ({{ zone.population_estimate }} people)
          </span>
        </div>
      </div>

      <!-- Hovered Zone Info -->
      <div v-if="hoveredZone" class="zone-tooltip">
        <div class="tooltip-title">{{ hoveredZone.properties?.name }}</div>
        <div class="tooltip-info">
          <div>Radius: {{ hoveredZone.radius_max_km }}km</div>
          <div>Area: {{ hoveredZone.area_km2 }}km²</div>
          <div>Population: {{ formatNumber(hoveredZone.population_estimate) }}</div>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <p>No evacuation zones calculated</p>
    </div>
  </div>
</template>

<script>
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ZoneMapLayer',
  props: {
    zones: {
      type: Array,
      default: () => [],
    },
    mapWidth: {
      type: Number,
      default: 400,
    },
    mapHeight: {
      type: Number,
      default: 400,
    },
  },
  data() {
    return {
      hoveredZone: null,
      mapCanvas: true,
    }
  },
  methods: {
    getZoneRadius(zone, index) {
      // Scale zones to fit in map
      // Assume max radius is ~50km, map is 400x400
      // 1 degree latitude ≈ 111 km
      // Map width = 400px = 10 degrees = 1110 km
      // So 1 degree = 40 px
      
      const scaleFactor = 40 // pixels per degree
      const radiusDegrees = zone.radius_max_km / 111.0
      const pixelRadius = radiusDegrees * scaleFactor * (index + 1)
      
      return Math.min(pixelRadius, 150) // Cap at 150px for visibility
    },

    formatNumber(num) {
      if (!num) return '0'
      return new Intl.NumberFormat('en-US').format(Math.round(num))
    },
  },
})
</script>

<style scoped>
.zone-map-layer {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.zones-overlay {
  position: relative;
  width: 100%;
  height: 100%;
}

.zones-svg {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.zone-circle {
  transition: opacity 0.3s ease;
  pointer-events: auto;
  cursor: pointer;
}

.zone-circle:hover {
  opacity: 0.25 !important;
}

.zone-border {
  transition: opacity 0.3s ease;
  pointer-events: auto;
  cursor: pointer;
}

.zone-label {
  pointer-events: none;
  text-shadow: 0 0 3px rgba(0, 0, 0, 0.8);
  font-size: 12px;
}

.incident-marker {
  pointer-events: none;
  filter: drop-shadow(0 0 3px rgba(255, 20, 147, 0.8));
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    r: 8;
  }
  50% {
    r: 12;
  }
  100% {
    r: 8;
  }
}

.zone-legend {
  position: absolute;
  bottom: 16px;
  left: 16px;
  background: rgba(30, 41, 59, 0.95);
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 12px;
  max-width: 280px;
  font-size: 12px;
  color: #e2e8f0;
  backdrop-filter: blur(4px);
}

.legend-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #f1f5f9;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  line-height: 1.4;
}

.legend-item:last-child {
  margin-bottom: 0;
}

.legend-color {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 2px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.legend-text {
  color: #e2e8f0;
  flex: 1;
}

.zone-tooltip {
  position: absolute;
  top: 16px;
  right: 16px;
  background: rgba(30, 41, 59, 0.95);
  border: 2px solid #3b82f6;
  border-radius: 6px;
  padding: 12px;
  max-width: 250px;
  font-size: 12px;
  color: #e2e8f0;
  backdrop-filter: blur(4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tooltip-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #f1f5f9;
}

.tooltip-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tooltip-info div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #94a3b8;
  font-size: 14px;
}
</style>
