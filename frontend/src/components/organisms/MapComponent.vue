<template>
  <div class="map-wrapper">
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

    <!-- Custom Map Controls HUD (Top Right) -->
    <div class="map-controls glass-panel">
      <button class="control-btn" @click="zoomIn" title="Zoom In">➕</button>
      <button class="control-btn" @click="zoomOut" title="Zoom Out">➖</button>
      <button class="control-btn" @click="resetView" title="Reset Global View">🎯</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import { useEventsStore, useAppStore } from '@/stores'
import type { IncidentLevel1 } from '@/types'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'

interface Props {
  incidents?: IncidentLevel1[]
  selectedCountry?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  incidents: undefined,
  selectedCountry: null
})

const eventsStore = useEventsStore()
const appStore = useAppStore()

const activeIncidents = computed(() => {
  return props.incidents || eventsStore.allIncidents
})

const mapContainer = ref<HTMLElement | null>(null)
const map = shallowRef<mapboxgl.Map | null>(null)
let markers: mapboxgl.Marker[] = []

const DEFAULT_CENTER: [number, number] = [0, 20]
const DEFAULT_ZOOM = 1.5

type MapMode = 'tactical' | 'satellite' | 'globe'
const currentMode = ref<MapMode>('tactical')

const MAP_STYLES = {
  tactical: 'mapbox://styles/mapbox/standard', // Mapbox Standard with 3D buildings & twilight lighting (The Shard)
  satellite: 'mapbox://styles/mapbox/standard-satellite', // Clean vertical top-down photorealistic satellite
  globe: 'mapbox://styles/mapbox/standard-satellite' // Pristine Blue Marble 3D globe with glowing atmosphere
}

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
  if (s >= 80) return '#ef4444' // red
  if (s >= 65) return '#f59e0b' // orange
  return '#38bdf8' // bright cyan/sky blue
}

const applyModeSettings = () => {
  if (!map.value) return

  // Support 3D tilt perspective if appStore.viewMode is '3d'
  const targetPitch = appStore.viewMode === '3d' ? 55 : 0
  const targetBearing = appStore.viewMode === '3d' ? -20 : 0
  map.value.easeTo({ pitch: targetPitch, bearing: targetBearing, duration: 600 })

  if (currentMode.value === 'globe') {
    // 1. Pristine Blue Marble 3D Orbital Globe (matching unnamed.jpg)
    map.value.setProjection({ name: 'globe' })
    map.value.setFog({
      color: 'rgb(11, 19, 43)', // Lower atmosphere
      'high-color': 'rgb(14, 165, 233)', // Glowing cyan halo
      'horizon-blend': 0.15,
      'space-color': 'rgb(8, 12, 22)', // Deep space
      'star-intensity': 0.8
    })
  } else if (currentMode.value === 'satellite') {
    // 2. Crystal-Clear Standard Satellite (Clean Vertical Top-Down)
    map.value.setFog(null as any)
    map.value.setProjection({ name: 'mercator' })
  } else {
    // 3. Tactical Mapbox Standard (Dusk/Night preset with 3D buildings like The Shard)
    map.value.setFog(null as any)
    map.value.setProjection({ name: 'mercator' })
    try {
      (map.value as any).setConfigProperty('basemap', 'lightPreset', 'dusk')
    } catch {
      // Fallback if preset unavailable
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
    // Same style, apply globe projection dynamically
    applyModeSettings()
  }
}

const initMap = () => {
  if (!mapContainer.value || !appStore.mapboxToken) {
    return
  }

  mapboxgl.accessToken = appStore.mapboxToken

  map.value = new mapboxgl.Map({
    container: mapContainer.value,
    style: MAP_STYLES.tactical, // Default to high-contrast tactical navigation night
    center: DEFAULT_CENTER,
    zoom: DEFAULT_ZOOM,
    projection: { name: 'mercator' },
    minZoom: 1,
    maxZoom: 18,
    attributionControl: false
  })

  map.value.on('load', () => {
    console.log('Mapbox initialized successfully')
    renderMarkers()
  })

  map.value.on('error', (e) => {
    console.error('Mapbox rendering error:', e)
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
  if (!map.value) return
  
  clearMarkers()

  activeIncidents.value.forEach(incident => {
    const lat = incident.coordinates ? incident.coordinates[0] : (incident as any).latitude
    const lon = incident.coordinates ? incident.coordinates[1] : (incident as any).longitude
    
    if (lat === undefined || lon === undefined) return
    
    const score = incident.threatScore ?? 50
    const color = getSeverityColor(score)
    const icon = getIncidentIcon(incident.type)
    const isSelected = appStore.selectedIncident === incident.id
    const isExpanded = appStore.expandedIncident === incident.id

    // Create custom DOM element for the marker
    const el = document.createElement('div')
    el.className = 'custom-marker'
    
    // Add pulsing effect for critical threats
    if (score >= 80) {
      const pulseRing = document.createElement('div')
      pulseRing.className = 'pulse-ring'
      pulseRing.style.borderColor = color
      el.appendChild(pulseRing)
    }

    const dot = document.createElement('div')
    dot.className = `marker-dot ${getSeverityClass(score)}`
    if (isSelected || isExpanded) {
      dot.classList.add('selected')
    }
    
    dot.innerHTML = `<span>${icon}</span>`
    el.appendChild(dot)

    // Handle clicks to open the dashboard sidebar
    el.addEventListener('click', (e) => {
      e.stopPropagation()
      appStore.setSelectedIncident(incident.id)
      
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

// Map Controls
const zoomIn = () => map.value?.zoomIn()
const zoomOut = () => map.value?.zoomOut()
const resetView = () => {
  map.value?.flyTo({
    center: DEFAULT_CENTER,
    zoom: DEFAULT_ZOOM,
    speed: 1.5
  })
}

// Watchers: Re-render markers whenever the filtered incident list updates
watch(() => activeIncidents.value, () => {
  if (map.value?.isStyleLoaded()) {
    renderMarkers()
  }
}, { deep: true })

// Real 3D Perspective Tilt Watcher
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

// Auto-Fly camera to center on the selected country!
watch(() => props.selectedCountry, (newCountry) => {
  if (!map.value) return
  
  if (newCountry && activeIncidents.value.length > 0) {
    let sumLat = 0
    let sumLon = 0
    let count = 0
    
    activeIncidents.value.forEach(inc => {
      const lat = inc.coordinates ? inc.coordinates[0] : (inc as any).latitude
      const lon = inc.coordinates ? inc.coordinates[1] : (inc as any).longitude
      if (lat !== undefined && lon !== undefined) {
        sumLat += lat
        sumLon += lon
        count++
      }
    })

    if (count > 0) {
      map.value.flyTo({
        center: [sumLon / count, sumLat / count],
        zoom: Math.min(Math.max(map.value.getZoom(), 4.2), 6),
        speed: 1.2,
        curve: 1.4
      })
    }
  } else if (!newCountry) {
    // When switched back to 'All Countries', smoothly return to the global view
    resetView()
  }
})

// Highlight selected marker and fly to it
watch(() => appStore.selectedIncident, (newId) => {
  if (!map.value || !newId) return
  
  renderMarkers()
  
  const incident = eventsStore.allIncidents.find(i => i.id === newId)
  if (incident) {
    const lat = incident.coordinates ? incident.coordinates[0] : (incident as any).latitude
    const lon = incident.coordinates ? incident.coordinates[1] : (incident as any).longitude
    if (lat !== undefined && lon !== undefined) {
      map.value.flyTo({
        center: [lon, lat],
        zoom: Math.max(map.value.getZoom(), 4),
        speed: 0.8
      })
    }
  }
})

onMounted(() => {
  if (appStore.mapboxToken) {
    initMap()
  }
})

onUnmounted(() => {
  clearMarkers()
  if (map.value) {
    map.value.remove()
  }
})
</script>

<style>
/* 
  NOTE: Mapbox requires these styles to be unscoped or applied globally 
  so it can target the dynamically injected DOM elements.
*/
.map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 8px;
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
  top: 12px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 8px;
  z-index: 100;
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

.marker-dot:hover, .marker-dot.selected {
  transform: scale(1.35);
  box-shadow: 0 0 20px rgba(56, 189, 248, 0.8);
  z-index: 30;
}

/* Severity Colors with bright contrast glow */
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

/* Pulsing effect for critical alerts */
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

/* HUD Controls */
.map-controls {
  position: absolute;
  top: 12px;
  right: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 8px;
  z-index: 100;
}

.control-btn {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(14, 165, 233, 0.4);
  background: rgba(15, 23, 42, 0.7);
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.control-btn:hover {
  background: rgba(14, 165, 233, 0.3);
  border-color: #38bdf8;
  transform: scale(1.05);
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
</style>
