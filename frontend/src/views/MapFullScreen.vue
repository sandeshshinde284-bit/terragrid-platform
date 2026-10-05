<template>
  <div class="map-fullscreen">
    <Header />

    <div ref="containerRef" class="map-container">
      <!-- High Performance Mapbox GL JS WebGL Engine -->
      <div ref="mapContainer" class="mapbox-container"></div>

      <!-- 3-Way Tactical Mode Switcher HUD (Top Left) -->
      <div class="style-switcher-hud glass-panel">
        <button 
          :class="['mode-btn', { active: currentMode === 'tactical' }]"
          @click="setMode('tactical')"
          title="Tactical Navigation Night Radar (Vivid midnight blue & glowing borders)"
        >
          <span class="mode-icon">🌙</span>
          <span class="mode-label">TACTICAL</span>
        </button>
        <button 
          :class="['mode-btn', { active: currentMode === 'satellite' }]"
          @click="setMode('satellite')"
          title="Real-World Photorealistic Satellite Recon"
        >
          <span class="mode-icon">🛰️</span>
          <span class="mode-label">SATELLITE</span>
        </button>
        <button 
          :class="['mode-btn', { active: currentMode === 'globe' }]"
          @click="setMode('globe')"
          title="3D Orbital Globe with Atmospheric Lighting"
        >
          <span class="mode-icon">🌐</span>
          <span class="mode-label">3D GLOBE</span>
        </button>
      </div>

      <!-- Zoom & Viewport Controls HUD (Top Right) -->
      <div class="map-controls glass-panel">
        <button @click="zoomIn" title="Zoom In" class="control-btn" type="button">➕</button>
        <button @click="zoomOut" title="Zoom Out" class="control-btn" type="button">➖</button>
        <button @click="resetView" title="Reset Global View" class="control-btn" type="button">🎯</button>
        <button @click="toggleLayersPanel" title="Toggle GIS Layers" :class="['control-btn', { active: showLayersPanel }]" type="button">🗺️</button>
      </div>

      <!-- Advanced Multi-Layer GIS Control Panel -->
      <transition name="fade">
        <div v-if="showLayersPanel" class="layers-panel glass-panel">
          <div class="panel-header">
            <h4>🛰️ GIS Tactical Layers</h4>
            <span class="active-tag">{{ activeLayerCount }} Active</span>
          </div>

          <div class="layer-item">
            <input v-model="layers.incidents" type="checkbox" id="layer-incidents" @change="renderMarkers" />
            <label for="layer-incidents">📍 Live Disaster Markers</label>
          </div>

          <div class="layer-item">
            <input v-model="layers.threatGlow" type="checkbox" id="layer-glow" @change="renderMarkers" />
            <label for="layer-glow">🔥 Critical Threat Pulsing Rings</label>
          </div>
        </div>
      </transition>

      <!-- Live Cursor Coordinate Inspector HUD -->
      <div class="coord-inspector-hud glass-panel">
        <div class="hud-item">
          <span class="hud-label">GIS CURSOR</span>
          <span class="hud-value">{{ cursorCoordText }}</span>
        </div>
        <div class="hud-divider"></div>
        <div class="hud-item">
          <span class="hud-label">ZOOM</span>
          <span class="hud-value">{{ currentZoom.toFixed(2) }}x</span>
        </div>
        <div class="hud-divider"></div>
        <div class="hud-item">
          <span class="hud-label">POSTGRES FEED</span>
          <span class="hud-value live-pulse">{{ eventsStore.allIncidents.length }} VERIFIED 🟢</span>
        </div>
      </div>

      <!-- Tactical Legend with Real-Time Type Counts -->
      <div class="legend-panel glass-panel">
        <div class="legend-title">Multi-Hazard Telemetry</div>
        <div class="legend-items">
          <div class="legend-row">
            <span class="icon">🔥</span>
            <span class="name">Wildfires</span>
            <span class="count">{{ incidentCounts.fire }}</span>
          </div>
          <div class="legend-row">
            <span class="icon">💧</span>
            <span class="name">Floods</span>
            <span class="count">{{ incidentCounts.flood }}</span>
          </div>
          <div class="legend-row">
            <span class="icon">🌍</span>
            <span class="name">Seismic</span>
            <span class="count">{{ incidentCounts.earthquake }}</span>
          </div>
          <div class="legend-row">
            <span class="icon">🌀</span>
            <span class="name">Severe Storms</span>
            <span class="count">{{ incidentCounts.storm }}</span>
          </div>
          <div class="legend-row">
            <span class="icon">📍</span>
            <span class="name">Other Hazards</span>
            <span class="count">{{ incidentCounts.other }}</span>
          </div>
        </div>
      </div>

      <!-- Tactical Hover Tooltip -->
      <transition name="fade">
        <div
          v-if="hoveredIncident"
          class="tactical-tooltip glass-panel"
          :style="{ left: `${tooltipPos.x}px`, top: `${tooltipPos.y}px` }"
        >
          <div class="tooltip-header">
            <span class="tooltip-icon">{{ getIncidentIcon(hoveredIncident.type) }}</span>
            <div class="tooltip-title">
              <strong>{{ (hoveredIncident.type || 'Hazard').toUpperCase() }}</strong>
              <small>{{ hoveredIncident.location }}</small>
            </div>
            <span class="threat-tag" :class="getSeverityClass(hoveredIncident.threatScore)">
              {{ hoveredIncident.threatScore || 50 }}/100
            </span>
          </div>

          <div class="tooltip-body">
            <div class="metric">
              <span>AFFECTED AREA:</span>
              <strong>{{ hoveredIncident.affectedArea ? `${hoveredIncident.affectedArea.toFixed(1)} km²` : 'Active' }}</strong>
            </div>
            <div class="metric">
              <span>POPULATION AT RISK:</span>
              <strong>{{ hoveredIncident.affectedPopulation ? hoveredIncident.affectedPopulation.toLocaleString() : 'Estimating' }}</strong>
            </div>
            <div class="metric">
              <span>GROWTH TREND:</span>
              <strong style="color: #34d399">+{{ hoveredIncident.trend ? hoveredIncident.trend.toFixed(1) : '5.2' }} km²/h</strong>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import Header from '@/components/organisms/Header.vue'
import { useEventsStore, useAppStore } from '@/stores'
import type { IncidentLevel1 } from '@/types'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

const eventsStore = useEventsStore()
const appStore = useAppStore()

const mapContainer = ref<HTMLDivElement | null>(null)
const map = shallowRef<mapboxgl.Map | null>(null)
let markers: mapboxgl.Marker[] = []

const currentZoom = ref(1.5)
const DEFAULT_CENTER: [number, number] = [0, 20]
const DEFAULT_ZOOM = 1.5

type MapMode = 'tactical' | 'satellite' | 'globe'
const currentMode = ref<MapMode>('tactical')

const MAP_STYLES = {
  tactical: 'mapbox://styles/mapbox/navigation-night-v1', // Vivid midnight blue oceans, charcoal land, glowing neon borders
  satellite: 'mapbox://styles/mapbox/satellite-streets-v12', // Real-world photorealistic satellite imagery + street/border vectors
  globe: 'mapbox://styles/mapbox/satellite-streets-v12' // Real satellite on 3D rotating globe sphere
}

// Layer state
const showLayersPanel = ref(false)
const layers = reactive({
  incidents: true,
  threatGlow: true
})

const activeLayerCount = computed(() => {
  return Object.values(layers).filter(Boolean).length
})

// Cursor & hover state
const cursorCoordinates = ref<{ lat: number; lon: number } | null>(null)
const hoveredIncident = ref<IncidentLevel1 | null>(null)
const tooltipPos = ref({ x: 0, y: 0 })

// Telemetry counts
const incidentCounts = computed(() => {
  const counts = { fire: 0, flood: 0, earthquake: 0, storm: 0, other: 0 }
  eventsStore.allIncidents.forEach((i) => {
    const t = (i.type || '').toLowerCase()
    if (t.includes('fire')) counts.fire++
    else if (t.includes('flood')) counts.flood++
    else if (t.includes('earthquake') || t.includes('seismic')) counts.earthquake++
    else if (t.includes('storm') || t.includes('weather')) counts.storm++
    else counts.other++
  })
  return counts
})

const cursorCoordText = computed(() => {
  if (!cursorCoordinates.value) return 'HOVER TO INSPECT'
  const { lat, lon } = cursorCoordinates.value
  const latStr = `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? 'N' : 'S'}`
  const lonStr = `${Math.abs(lon).toFixed(4)}° ${lon >= 0 ? 'E' : 'W'}`
  return `${latStr} | ${lonStr}`
})

const getIncidentIcon = (type: string) => {
  const t = (type || '').toLowerCase()
  if (t.includes('fire') || t.includes('wildfire')) return '🔥'
  if (t.includes('flood')) return '💧'
  if (t.includes('earthquake') || t.includes('seismic')) return '🌍'
  if (t.includes('storm') || t.includes('weather') || t.includes('cyclone') || t.includes('typhoon')) return '🌀'
  if (t.includes('drought')) return '🌾'
  if (t.includes('volcano')) return '🌋'
  return '📍'
}

const getSeverityClass = (score?: number) => {
  const s = score ?? 50
  if (s >= 80) return 'critical'
  if (s >= 65) return 'high'
  return 'medium'
}

const getSeverityColor = (score?: number) => {
  const s = score ?? 50
  if (s >= 80) return '#ef4444'
  if (s >= 65) return '#f59e0b'
  return '#38bdf8'
}

const applyAtmosphere = () => {
  if (!map.value) return
  if (currentMode.value === 'globe') {
    map.value.setProjection({ name: 'globe' })
    map.value.setFog({
      color: 'rgb(11, 19, 43)',
      'high-color': 'rgb(14, 165, 233)',
      'horizon-blend': 0.15,
      'space-color': 'rgb(8, 12, 22)',
      'star-intensity': 0.8
    })
  } else {
    map.value.setProjection({ name: 'mercator' })
    map.value.setFog(null as any)
  }
}

const setMode = (mode: MapMode) => {
  if (!map.value || currentMode.value === mode) return
  const prevMode = currentMode.value
  currentMode.value = mode

  if (MAP_STYLES[mode] !== MAP_STYLES[prevMode]) {
    map.value.setStyle(MAP_STYLES[mode])
    map.value.once('style.load', () => {
      applyAtmosphere()
      renderMarkers()
    })
  } else {
    applyAtmosphere()
  }
}

const initMap = () => {
  if (!mapContainer.value || !appStore.mapboxToken) return

  mapboxgl.accessToken = appStore.mapboxToken

  map.value = new mapboxgl.Map({
    container: mapContainer.value,
    style: MAP_STYLES.tactical,
    center: DEFAULT_CENTER,
    zoom: DEFAULT_ZOOM,
    projection: { name: 'mercator' },
    minZoom: 1,
    maxZoom: 18,
    attributionControl: false
  })

  map.value.on('load', () => {
    renderMarkers()
  })

  map.value.on('zoom', () => {
    if (map.value) currentZoom.value = map.value.getZoom()
  })

  map.value.on('mousemove', (e) => {
    cursorCoordinates.value = { lat: e.lngLat.lat, lon: e.lngLat.lng }
  })

  map.value.on('mouseleave', () => {
    cursorCoordinates.value = null
  })
}

// Watch for backend mapbox token arrival asynchronously
watch(() => appStore.mapboxToken, (token) => {
  if (token && !map.value) {
    initMap()
  }
})

const clearMarkers = () => {
  markers.forEach(marker => marker.remove())
  markers = []
}

const renderMarkers = () => {
  if (!map.value || !layers.incidents) {
    clearMarkers()
    return
  }
  
  clearMarkers()

  eventsStore.allIncidents.forEach(incident => {
    const lat = incident.coordinates ? incident.coordinates[0] : (incident as any).latitude
    const lon = incident.coordinates ? incident.coordinates[1] : (incident as any).longitude
    if (lat === undefined || lon === undefined) return

    const score = incident.threatScore ?? 50
    const color = getSeverityColor(score)
    const icon = getIncidentIcon(incident.type)

    const el = document.createElement('div')
    el.className = 'custom-marker'

    if (layers.threatGlow && score >= 80) {
      const pulseRing = document.createElement('div')
      pulseRing.className = 'pulse-ring'
      pulseRing.style.borderColor = color
      el.appendChild(pulseRing)
    }

    const dot = document.createElement('div')
    dot.className = `marker-dot ${getSeverityClass(score)}`
    dot.innerHTML = `<span>${icon}</span>`
    el.appendChild(dot)

    // Hover tooltip tracking
    el.addEventListener('mouseenter', (e) => {
      hoveredIncident.value = incident
      tooltipPos.value = {
        x: Math.min(e.clientX + 16, window.innerWidth - 320),
        y: Math.min(e.clientY + 16, window.innerHeight - 200)
      }
    })

    el.addEventListener('mouseleave', () => {
      hoveredIncident.value = null
    })

    el.addEventListener('click', (e) => {
      e.stopPropagation()
      map.value?.flyTo({
        center: [lon, lat],
        zoom: Math.max(map.value.getZoom(), 5),
        speed: 1.2
      })
    })

    const marker = new mapboxgl.Marker({ element: el })
      .setLngLat([lon, lat])
      .addTo(map.value)

    markers.push(marker)
  })
}

// Controls
const zoomIn = () => map.value?.zoomIn()
const zoomOut = () => map.value?.zoomOut()
const resetView = () => {
  map.value?.flyTo({
    center: DEFAULT_CENTER,
    zoom: DEFAULT_ZOOM,
    speed: 1.5
  })
}

const toggleLayersPanel = () => {
  showLayersPanel.value = !showLayersPanel.value
}

watch(() => eventsStore.allIncidents.length, () => {
  if (map.value?.isStyleLoaded()) {
    renderMarkers()
  }
})

onMounted(() => {
  if (appStore.mapboxToken) {
    initMap()
  }
})

onUnmounted(() => {
  clearMarkers()
  if (map.value) map.value.remove()
})
</script>

<style>
.map-fullscreen {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  overflow: hidden;
}

.map-container {
  position: relative;
  flex: 1;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.mapbox-container {
  width: 100%;
  height: 100%;
  background-color: #0b0f19;
}

/* 3-Way Tactical Mode Switcher HUD */
.style-switcher-hud {
  position: absolute;
  top: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 8px;
  z-index: 10;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}

.mode-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid transparent;
  background: transparent;
  color: #94a3b8;
  border-radius: 6px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  transition: all 0.2s ease;
}

.mode-btn:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
}

.mode-btn.active {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.3), rgba(30, 64, 175, 0.4));
  color: #38bdf8;
  border-color: rgba(56, 189, 248, 0.5);
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
}

.mode-icon {
  font-size: 13px;
}

/* Map Controls HUD */
.map-controls {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 8px;
  z-index: 10;
}

.control-btn {
  width: 36px;
  height: 36px;
  border: 1px solid rgba(14, 165, 233, 0.4);
  background: rgba(15, 23, 42, 0.7);
  color: var(--accent-cyan);
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.control-btn:hover {
  background: rgba(14, 165, 233, 0.25);
  border-color: var(--accent-cyan);
  transform: scale(1.05);
}

.control-btn.active {
  background: linear-gradient(135deg, #1e40af, #0ea5e9);
  color: #ffffff;
  border-color: #38bdf8;
}

/* Multi-Layer Control Panel */
.layers-panel {
  position: absolute;
  top: 16px;
  right: 70px;
  width: 260px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 10;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.panel-header h4 {
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
}

.active-tag {
  font-size: 10px;
  font-weight: 700;
  color: var(--accent-cyan);
  background: rgba(14, 165, 233, 0.15);
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(14, 165, 233, 0.3);
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #cbd5e1;
  cursor: pointer;
}

.layer-item input {
  accent-color: var(--accent-cyan);
  cursor: pointer;
  width: 15px;
  height: 15px;
}

/* Cursor & GIS Inspector HUD */
.coord-inspector-hud {
  position: absolute;
  bottom: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 8px 16px;
  z-index: 10;
  pointer-events: none;
}

.hud-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.hud-label {
  font-size: 9px;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

.hud-value {
  font-size: 12px;
  font-weight: 700;
  color: #ffffff;
  font-family: monospace;
}

.hud-value.live-pulse {
  color: #10b981;
}

.hud-divider {
  width: 1px;
  height: 24px;
  background: rgba(255, 255, 255, 0.15);
}

/* Legend Panel */
.legend-panel {
  position: absolute;
  bottom: 16px;
  left: 16px;
  padding: 12px 16px;
  z-index: 10;
  max-width: 220px;
  pointer-events: none;
}

.legend-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--accent-cyan);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.legend-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: #cbd5e1;
}

.legend-row .name {
  flex: 1;
  margin-left: 6px;
}

.legend-row .count {
  font-weight: 700;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
  padding: 1px 6px;
  border-radius: 4px;
}

/* Tactical Hover Tooltip */
.tactical-tooltip {
  position: absolute;
  width: 280px;
  padding: 14px;
  z-index: 20;
  pointer-events: none;
  border: 1px solid var(--accent-cyan);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
  animation: fadeIn 0.15s ease-out;
}

.tooltip-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 10px;
}

.tooltip-icon {
  font-size: 24px;
}

.tooltip-title {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.tooltip-title strong {
  font-size: 13px;
  color: #ffffff;
}

.tooltip-title small {
  font-size: 11px;
  color: var(--accent-cyan);
}

.threat-tag {
  font-size: 11px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 4px;
}

.threat-tag.critical {
  background: rgba(239, 68, 68, 0.25);
  color: #ef4444;
  border: 1px solid #ef4444;
}

.threat-tag.high {
  background: rgba(245, 158, 11, 0.25);
  color: #f59e0b;
  border: 1px solid #f59e0b;
}

.threat-tag.medium {
  background: rgba(59, 130, 246, 0.25);
  color: #3b82f6;
  border: 1px solid #3b82f6;
}

.tooltip-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.tooltip-body .metric {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #94a3b8;
}

.tooltip-body .metric strong {
  color: #ffffff;
}

/* Custom Marker Styling */
.custom-marker {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  cursor: pointer;
  z-index: 5;
}

.marker-dot {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  background-color: #1e293b;
  border: 2.5px solid;
  border-radius: 50%;
  font-size: 13px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.7);
  transition: all 0.2s ease;
  z-index: 10;
}

.marker-dot:hover {
  transform: scale(1.35);
  box-shadow: 0 0 20px rgba(56, 189, 248, 0.8);
  z-index: 30;
}

.marker-dot.critical {
  border-color: #ef4444;
  box-shadow: 0 0 16px rgba(239, 68, 68, 0.8);
}

.marker-dot.high {
  border-color: #f59e0b;
  box-shadow: 0 0 14px rgba(245, 158, 11, 0.8);
}

.marker-dot.medium, .marker-dot.low {
  border-color: #38bdf8;
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.7);
}

.pulse-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid;
  animation: pulse-animation 2s infinite cubic-bezier(0.4, 0, 0.6, 1);
  z-index: 1;
}

@keyframes pulse-animation {
  0% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.8; }
  100% { transform: translate(-50%, -50%) scale(2.5); opacity: 0; }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
