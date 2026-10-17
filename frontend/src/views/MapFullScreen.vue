<template>
  <div class="map-fullscreen">
    <Header />

    <div ref="containerRef" class="map-container">
      <!-- High Performance Mapbox GL JS WebGL Engine -->
      <div ref="mapContainer" class="mapbox-container"></div>

      <!-- Floating Back to Incident Navigation Pill (Only when coming from an incident) -->
      <transition name="fade">
        <div v-if="fromIncidentId" class="floating-incident-back">
          <button class="incident-back-pill" type="button" @click="returnToIncident">
            <span class="back-chevron">←</span>
            <span class="back-text">{{ $t('mapFull.returnToIncident') }} <strong>{{ fromIncidentLocation }}</strong></span>
          </button>
        </div>
      </transition>

      <!-- Selected incident (set by a marker click; same selection as Dashboard/Incidents) -->
      <transition name="fade">
        <div v-if="selectedIncident" class="selected-incident-card glass-panel">
          <div class="selected-head">
            <strong>{{ selectedIncident.type }} <span class="incident-id">{{ displayIncidentId(selectedIncident) }}</span></strong>
            <small>{{ selectedIncident.location }}</small>
          </div>
          <div class="selected-metrics">
            <span>{{ $t('overviewTab.threatScore') }}: {{ selectedIncident.threatScore ?? DASH }}</span>
            <span>{{ $t('mapFull.affectedArea') }}: {{ fmtFixed(selectedIncident.affectedArea, 0, ' km²') }}</span>
          </div>
          <div class="selected-actions">
            <button type="button" class="selected-btn primary" @click="openSelectedIncident">{{ $t('mapFull.openIncident') }}</button>
            <button type="button" class="selected-btn" @click="showSelectedInList">{{ $t('mapFull.showInList') }}</button>
            <button type="button" class="selected-btn" @click="appStore.setSelectedIncident(null)" aria-label="Clear selection">✕</button>
          </div>
        </div>
      </transition>

      <!-- 3-Way Tactical Mode Switcher HUD (Top Left) -->
      <div class="style-switcher-hud glass-panel">
        <button 
          :class="['mode-btn', { active: currentMode === 'tactical' }]"
          @click="setMode('tactical')"
          :title="$t('mapFull.tacticalTooltip')"
        >
          <span class="mode-icon">🌙</span>
          <span class="mode-label">{{ $t('mapFull.tactical') }}</span>
        </button>
        <button 
          :class="['mode-btn', { active: currentMode === 'satellite' }]"
          @click="setMode('satellite')"
          :title="$t('mapFull.satelliteTooltip')"
        >
          <span class="mode-icon">🛰️</span>
          <span class="mode-label">{{ $t('mapFull.satellite') }}</span>
        </button>
        <button 
          :class="['mode-btn', { active: currentMode === 'globe' }]"
          @click="setMode('globe')"
          :title="$t('mapFull.globeTooltip')"
        >
          <span class="mode-icon">🌐</span>
          <span class="mode-label">{{ $t('mapFull.globe') }}</span>
        </button>
      </div>

      <!-- Zoom & Viewport Controls HUD (Top Right) -->
      <div class="map-controls glass-panel">
        <button @click="zoomIn" :title="$t('mapFull.zoomIn')" class="control-btn" type="button">➕</button>
        <button @click="zoomOut" :title="$t('mapFull.zoomOut')" class="control-btn" type="button">➖</button>
        <button @click="resetView" :title="$t('mapFull.resetView')" class="control-btn" type="button">🎯</button>
        <button @click="toggleLayersPanel" :title="$t('mapFull.toggleLayers')" :class="['control-btn', { active: showLayersPanel }]" type="button">🗺️</button>
      </div>

      <!-- Advanced Multi-Layer GIS Control Panel -->
      <transition name="fade">
        <div v-if="showLayersPanel" class="layers-panel glass-panel">
          <div class="panel-header">
            <h4>🛰️ {{ $t('mapFull.layersTitle') }}</h4>
            <span class="active-tag">{{ activeLayerCount }} {{ $t('mapFull.active') }}</span>
          </div>

          <div class="layer-item">
            <input v-model="layers.incidents" type="checkbox" id="layer-incidents" @change="renderMarkers" />
            <label for="layer-incidents">📍 {{ $t('mapFull.layerIncidents') }}</label>
          </div>

          <div class="layer-item">
            <input v-model="layers.threatGlow" type="checkbox" id="layer-glow" @change="renderMarkers" />
            <label for="layer-glow">🔥 {{ $t('mapFull.layerGlow') }}</label>
          </div>
        </div>
      </transition>

      <!-- Live Cursor Coordinate Inspector HUD -->
      <div class="coord-inspector-hud glass-panel">
        <div class="hud-item">
          <span class="hud-label">{{ $t('mapFull.cursorLabel') }}</span>
          <span class="hud-value">{{ cursorCoordText }}</span>
        </div>
        <div class="hud-divider"></div>
        <div class="hud-item">
          <span class="hud-label">{{ $t('mapFull.zoomLabel') }}</span>
          <span class="hud-value">{{ currentZoom.toFixed(2) }}x</span>
        </div>
        <div class="hud-divider"></div>
        <div class="hud-item">
          <span class="hud-label">{{ $t('mapFull.feedLabel') }}</span>
          <span class="hud-value live-pulse">{{ eventsStore.allIncidents.length }} {{ $t('mapFull.verified') }} 🟢</span>
        </div>
      </div>

      <!-- Tactical Legend with Real-Time Type Counts -->
      <div class="legend-panel glass-panel">
        <div class="legend-title">{{ $t('mapFull.legendTitle') }}</div>
        <div class="legend-items">
          <div class="legend-row">
            <span class="icon">🔥</span>
            <span class="name">{{ $t('mapFull.wildfires') }}</span>
            <span class="count">{{ incidentCounts.fire }}</span>
          </div>
          <div class="legend-row">
            <span class="icon">💧</span>
            <span class="name">{{ $t('mapFull.floods') }}</span>
            <span class="count">{{ incidentCounts.flood }}</span>
          </div>
          <div class="legend-row">
            <span class="icon">🌍</span>
            <span class="name">{{ $t('mapFull.seismic') }}</span>
            <span class="count">{{ incidentCounts.earthquake }}</span>
          </div>
          <div class="legend-row">
            <span class="icon">🌀</span>
            <span class="name">{{ $t('mapFull.severeStorms') }}</span>
            <span class="count">{{ incidentCounts.storm }}</span>
          </div>
          <div class="legend-row">
            <span class="icon">📍</span>
            <span class="name">{{ $t('mapFull.otherHazards') }}</span>
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
            <span class="threat-tag" :class="getSeverityClass(hoveredIncident.threatScore ?? 0)">
              {{ hoveredIncident.threatScore !== null && hoveredIncident.threatScore !== undefined ? `${hoveredIncident.threatScore}/100` : $t('overviewTab.notScored') }}
            </span>
          </div>

          <div class="tooltip-body">
            <div class="metric">
              <span>AFFECTED AREA:</span>
              <strong>{{ fmtFixed(hoveredIncident.affectedArea, 1, ' km²') }}</strong>
            </div>
            <div class="metric">
              <span>POPULATION AT RISK:</span>
              <strong>{{ fmtCount(hoveredIncident.affectedPopulation) }}</strong>
            </div>
            <div class="metric">
              <span>GROWTH TREND:</span>
              <strong style="color: #34d399">{{ fmtSigned(hoveredIncident.trend, 1, ' km²/h') }}</strong>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { displayIncidentId } from '@/utils/incidentId'
import { impactMetricsFrom, fmtFixed, fmtCount, fmtThousands, fmtSigned, sumKnown, DASH } from '@/utils/impactMetrics'
import { ref, reactive, computed, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '@/components/organisms/Header.vue'
import { useEventsStore, useAppStore } from '@/stores'
import type { IncidentLevel1 } from '@/types'
import * as mapboxgl from 'mapbox-gl/esm'
import 'mapbox-gl/dist/mapbox-gl.css'

const route = useRoute()
const router = useRouter()
const eventsStore = useEventsStore()
const appStore = useAppStore()

const fromIncidentId = computed(() => (route.query.fromIncident as string) || '')
const fromIncidentLocation = computed(() => (route.query.location as string) || 'Incident')

function returnToIncident() {
  if (fromIncidentId.value) {
    router.push(`/incident/${fromIncidentId.value}`)
  } else {
    router.push('/incidents')
  }
}

const mapContainer = ref<HTMLDivElement | null>(null)
const map = shallowRef<mapboxgl.Map | null>(null)
let markers: mapboxgl.Marker[] = []

const currentZoom = ref(1.5)
const DEFAULT_CENTER: [number, number] = [0, 20]
const DEFAULT_ZOOM = 1.5

type MapMode = 'tactical' | 'satellite' | 'globe'
const currentMode = ref<MapMode>('tactical')

const MAP_STYLES = {
  tactical: 'mapbox://styles/mapbox/standard', // Mapbox Standard with 3D buildings & twilight lighting (The Shard)
  satellite: 'mapbox://styles/mapbox/standard-satellite', // Clean vertical top-down photorealistic satellite
  globe: 'mapbox://styles/mapbox/standard-satellite' // Pristine Blue Marble 3D globe with glowing atmosphere
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

const applyModeSettings = () => {
  if (!map.value) return

  // Respect appStore.viewMode (55° pitch in 3D mode, 0° top-down in 2D mode)
  const targetPitch = appStore.viewMode === '3d' ? 55 : 0
  const targetBearing = appStore.viewMode === '3d' ? -20 : 0
  map.value.easeTo({ pitch: targetPitch, bearing: targetBearing, duration: 600 })

  if (currentMode.value === 'globe') {
    // 1. 3D Orbital Globe projection
    map.value.setProjection({ name: 'globe' })
    map.value.setFog({
      color: 'rgb(11, 19, 43)', // Lower atmosphere
      'high-color': 'rgb(14, 165, 233)', // Upper atmosphere
      'horizon-blend': 0.15,
      'space-color': 'rgb(8, 12, 22)', // Deep space
      'star-intensity': 0.8
    })
  } else if (currentMode.value === 'satellite') {
    // 2. Standard Satellite view (vertical top-down)
    map.value.setFog(null as any)
    map.value.setProjection({ name: 'mercator' })
  } else {
    // 3. Standard map view (dusk lighting with 3D buildings)
    map.value.setFog(null as any)
    map.value.setProjection({ name: 'mercator' })
    try {
      (map.value as any).setConfigProperty('basemap', 'lightPreset', 'dusk')
    } catch {
      // Fallback
    }
  }
}

const setMode = (mode: MapMode) => {
  if (!map.value || currentMode.value === mode) return
  const prevMode = currentMode.value
  currentMode.value = mode

  // If style changes, reload style
  if (MAP_STYLES[mode] !== MAP_STYLES[prevMode]) {
    map.value.setStyle(MAP_STYLES[mode])
    map.value.once('style.load', () => {
      applyModeSettings()
      renderMarkers()
    })
  } else {
    applyModeSettings()
  }
}

const initMap = () => {
  if (!mapContainer.value || !appStore.mapboxToken) return

  map.value = new mapboxgl.Map({
  accessToken: appStore.mapboxToken,
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
  const mapInstance = map.value  

  clearMarkers()

  eventsStore.allIncidents.forEach(incident => {
    const lat = incident.coordinates ? incident.coordinates[0] : (incident as any).latitude
    const lon = incident.coordinates ? incident.coordinates[1] : (incident as any).longitude
    if (lat === undefined || lon === undefined) return

    // Unscored incidents are drawn in the lowest colour bucket, with no number shown.
    const score = incident.threatScore ?? null
    const color = getSeverityColor(score ?? 0)
    const icon = getIncidentIcon(incident.type)

    const el = document.createElement('div')
    el.className = 'custom-marker'

    if (layers.threatGlow && score !== null && score >= 80) {
      const pulseRing = document.createElement('div')
      pulseRing.className = 'pulse-ring'
      pulseRing.style.borderColor = color
      el.appendChild(pulseRing)
    }

    const dot = document.createElement('div')
    dot.className = `marker-dot ${getSeverityClass(score ?? 0)}`
    if (appStore.selectedIncident === incident.id) dot.classList.add('selected')
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
      // Same shared selection the Dashboard and Incidents page use, so the
      // incident is highlighted everywhere.
      appStore.setSelectedIncident(incident.id)
      // Open the actual incident page, as the Dashboard map does.
      router.push({ name: 'IncidentDetail', params: { id: incident.id } })
    })

    const marker = new mapboxgl.Marker({ element: el })
      .setLngLat([lon, lat])
      .addTo(mapInstance)

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

watch(() => appStore.selectedIncident, () => {
  if (map.value?.isStyleLoaded()) {
    renderMarkers()
  }
})

const selectedIncident = computed(() =>
  eventsStore.allIncidents.find(i => i.id === appStore.selectedIncident) ?? null
)

const openSelectedIncident = () => {
  if (selectedIncident.value) router.push(`/incident/${selectedIncident.value.id}`)
}

const showSelectedInList = () => {
  router.push('/incidents')
}

// Watch for 2D / 3D Mode Toggle from Header.vue
watch(() => appStore.viewMode, (mode) => {
  if (!map.value) return
  if (mode === '3d') {
    map.value.easeTo({
      pitch: 55,
      bearing: -20,
      duration: 1000
    })
  } else {
    map.value.easeTo({
      pitch: 0,
      bearing: 0,
      duration: 1000
    })
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
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border-color: rgba(56, 189, 248, 0.5);
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
  background: var(--accent-cyan);
  color: #04141a;
  border-color: var(--accent-cyan);
}

/* Responsive HUD Controls for Mobile (< 640px) to prevent overlap */
@media (max-width: 640px) {
  .style-switcher-hud {
    top: 8px;
    left: 8px;
    gap: 2px;
    padding: 2px 4px;
  }
  .mode-btn {
    padding: 6px 8px;
  }
  .mode-btn .mode-label {
    display: none;
  }
  .map-controls {
    top: 8px;
    right: 8px;
    gap: 4px;
    padding: 4px;
  }
  .control-btn {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }
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
  box-shadow: 0 0 8px rgba(56, 189, 248, 0.5);
  z-index: 30;
}

.marker-dot.critical {
  border-color: #ef4444;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.55);
}

.marker-dot.high {
  border-color: #f59e0b;
  box-shadow: 0 0 7px rgba(245, 158, 11, 0.4);
}

.marker-dot.medium, .marker-dot.low {
  border-color: #38bdf8;
  box-shadow: none;
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

/* Floating Back to Incident Button */
.floating-incident-back {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
}

.incident-back-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(16px);
  border: 1px solid #38bdf8;
  color: #f1f5f9;
  padding: 8px 18px;
  border-radius: 999px;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
  font-size: 13px;
  transition: all 0.2s ease;
}

.incident-back-pill:hover {
  background: #0ea5e9;
  color: #03111b;
  transform: scale(1.03);
}

.incident-back-pill strong {
  color: #38bdf8;
}

.incident-back-pill:hover strong {
  color: #03111b;
}

.back-chevron {
  font-size: 16px;
  font-weight: 800;
}

@media (max-width: 640px) {
  .floating-incident-back {
    top: 52px;
    width: 90%;
    display: flex;
    justify-content: center;
  }
  .incident-back-pill {
    padding: 6px 14px;
    font-size: 11px;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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
}
</style>

.selected-incident-card {
  position: absolute;
  left: 50%;
  bottom: 20px;
  transform: translateX(-50%);
  z-index: 20;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 280px;
  padding: 12px 14px;
}
.selected-head { display: flex; flex-direction: column; }
.selected-head small { opacity: 0.75; }
.selected-metrics { display: flex; gap: 12px; font-size: 13px; opacity: 0.9; }
.selected-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.selected-btn {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(15, 23, 42, 0.6);
  color: inherit;
  cursor: pointer;
  font-size: 13px;
}
.selected-btn.primary { border-color: #22d3ee; color: #67e8f9; }
.marker-dot.selected { box-shadow: 0 0 0 3px #facc15, 0 0 14px rgba(250, 204, 21, 0.7); transform: scale(1.15); }
