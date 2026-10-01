<template>
  <div ref="containerRef" class="map-container">
    <canvas
      ref="mapCanvas"
      class="map-canvas"
      @click="handleMapClick"
      @wheel.prevent="handleWheel"
      @pointerdown="handlePointerDown"
      @pointermove="handlePointerMove"
      @pointerup="handlePointerUp"
      @pointerleave="handlePointerLeave"
      @pointercancel="handlePointerLeave"
    ></canvas>

    <div class="map-overlay legend-panel">
      <div class="overlay-title">California Incident Map</div>
      <div class="overlay-subtitle">
        {{ appStore.viewMode === '2d' ? '2D tactical view' : '3D preview uses 2D tactical map' }}
      </div>
      <div class="legend-list">
        <div
          v-for="legendItem in legendItems"
          :key="legendItem.label"
          class="legend-item"
        >
          <span :style="{ backgroundColor: legendItem.color }" class="legend-swatch"></span>
          <span>{{ legendItem.label }}</span>
        </div>
      </div>
      <div class="overlay-hint">Wheel to zoom • drag to pan • click marker for details</div>
    </div>

    <div
      v-if="hoveredIncident && hoveredMarker"
      class="map-tooltip"
      :style="getFloatingStyle(hoveredMarker.x, hoveredMarker.y, 170, 70)"
    >
      <strong>{{ hoveredIncident.displayName }}</strong>
      <span>Population at risk: {{ hoveredIncident.affectedPopulation.toLocaleString() }}</span>
    </div>

    <div
      v-if="selectedIncident && selectedMarker"
      class="map-popup"
      :style="getFloatingStyle(selectedMarker.x, selectedMarker.y, 260, 220)"
    >
      <button class="close-btn" type="button" @click="clearSelectedIncident">×</button>
      <div class="popup-header">
        <span class="popup-icon">{{ selectedIncident.icon }}</span>
        <div>
          <h4>{{ selectedIncident.displayName }}</h4>
          <p>{{ selectedIncident.location }}</p>
        </div>
      </div>
      <div class="popup-grid">
        <div>
          <span class="popup-label">Type</span>
          <span class="popup-value">{{ selectedIncident.typeLabel }}</span>
        </div>
        <div>
          <span class="popup-label">Affected Area</span>
          <span class="popup-value">{{ selectedIncident.affectedArea.toFixed(0) }} km²</span>
        </div>
        <div>
          <span class="popup-label">Population at Risk</span>
          <span class="popup-value">{{ selectedIncident.affectedPopulation.toLocaleString() }}</span>
        </div>
        <div>
          <span class="popup-label">Threat Score</span>
          <span class="popup-value">{{ selectedIncident.threatScore }}/100</span>
        </div>
        <div>
          <span class="popup-label">Status</span>
          <span class="popup-value status-pill">{{ selectedIncident.status }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useAppStore, useEventsStore } from '@/stores'
import type { IncidentLevel1 } from '@/types'

type SeverityLabel = 'critical' | 'high' | 'medium'

interface IncidentMetadata {
  latitude: number
  longitude: number
  icon: string
  displayName: string
  typeLabel: string
  severityLabel: SeverityLabel
  threatScore: number
}

interface MapIncident extends IncidentLevel1, IncidentMetadata {}

interface RenderedMarker {
  id: string
  x: number
  y: number
  radius: number
}

interface ThemePalette {
  backgroundStart: string
  backgroundEnd: string
  gridLine: string
  majorGridLine: string
  textPrimary: string
  textSecondary: string
  landFill: string
  landStroke: string
}

const INCIDENT_METADATA: Record<string, IncidentMetadata> = {
  'incident-1': {
    latitude: 34.27,
    longitude: -118.07,
    icon: '🔥',
    displayName: 'San Gabriel Wildfire',
    typeLabel: 'Wildfire',
    severityLabel: 'critical',
    threatScore: 96,
  },
  'incident-2': {
    latitude: 36.5,
    longitude: -119.5,
    icon: '💧',
    displayName: 'Central Valley Flooding',
    typeLabel: 'Flood',
    severityLabel: 'high',
    threatScore: 82,
  },
  'incident-3': {
    latitude: 37.77,
    longitude: -122.42,
    icon: '☁️',
    displayName: 'Bay Area AQI',
    typeLabel: 'Air Quality',
    severityLabel: 'medium',
    threatScore: 68,
  },
}

const MAP_BOUNDS = {
  minLat: 32,
  maxLat: 42.3,
  minLon: -124.8,
  maxLon: -114,
}

const MIN_SCALE = 0.5
const MAX_SCALE = 3

const mapCanvas = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const eventsStore = useEventsStore()
const appStore = useAppStore()

const scale = ref(1)
const panX = ref(0)
const panY = ref(0)
const canvasWidth = ref(0)
const canvasHeight = ref(0)
const renderedMarkers = ref<RenderedMarker[]>([])
const hoveredIncidentId = ref<string | null>(null)
const selectedIncidentId = ref<string | null>(null)

let resizeObserver: ResizeObserver | null = null
let animationFrameId = 0
let isDragging = false
let dragDistance = 0
let lastPointerX = 0
let lastPointerY = 0

const legendItems = [
  { label: 'Critical', color: '#dc2626' },
  { label: 'High', color: '#f59e0b' },
  { label: 'Medium', color: '#fbbf24' },
]

const mapIncidents = computed<MapIncident[]>(() =>
  eventsStore.allIncidents
    .map((incident) => {
      // Use coordinates from backend incident data
      const [latitude, longitude] = incident.coordinates || [0, 0]
      
      return {
        ...incident,
        latitude,
        longitude,
        icon: {
          fire: '🔥',
          flood: '💧',
          earthquake: '🌍',
          hurricane: '🌀',
          volcano: '🌋',
          landslide: '⛰️',
        }[incident.type] || '⚠️',
        displayName: incident.location,
        typeLabel: incident.type.charAt(0).toUpperCase() + incident.type.slice(1),
        severityLabel: (incident.severity === 'high' ? 'high' : incident.severity === 'low' ? 'medium' : incident.severity) as SeverityLabel,
        threatScore: incident.threatScore ?? 50,
        affectedArea: incident.affectedArea ?? 100,
        affectedPopulation: incident.affectedPopulation ?? 10000,
        location: incident.location,
        status: incident.status || 'active',
      } as MapIncident
    })
    .filter((incident): incident is MapIncident => incident && incident.latitude !== 0 && incident.longitude !== 0)
)

const hoveredIncident = computed(
  () => mapIncidents.value.find((incident) => incident.id === hoveredIncidentId.value) ?? null,
)

const selectedIncident = computed(
  () => mapIncidents.value.find((incident) => incident.id === selectedIncidentId.value) ?? null,
)

const hoveredMarker = computed(
  () => renderedMarkers.value.find((marker) => marker.id === hoveredIncidentId.value) ?? null,
)

const selectedMarker = computed(
  () => renderedMarkers.value.find((marker) => marker.id === selectedIncidentId.value) ?? null,
)

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))

const getMarkerColor = (severity: SeverityLabel) => {
  const colors: Record<SeverityLabel, string> = {
    critical: '#dc2626',
    high: '#f59e0b',
    medium: '#fbbf24',
  }

  return colors[severity]
}

const getMarkerRadius = (incident: MapIncident) => {
  const scaledPopulation = 10 + incident.affectedPopulation / 18000
  return clamp(scaledPopulation, 12, 22)
}

const getThemePalette = (): ThemePalette => {
  const styles = getComputedStyle(containerRef.value ?? document.documentElement)

  return {
    backgroundStart: styles.getPropertyValue('--bg-panel').trim() || '#1a1f2e',
    backgroundEnd: styles.getPropertyValue('--bg-dark').trim() || '#0f1419',
    gridLine: styles.getPropertyValue('--glass-border').trim() || 'rgba(255,255,255,0.15)',
    majorGridLine: styles.getPropertyValue('--accent-cyan-soft').trim() || 'rgba(0,188,212,0.1)',
    textPrimary: styles.getPropertyValue('--text-primary').trim() || '#e0e0e0',
    textSecondary: styles.getPropertyValue('--text-secondary').trim() || '#9e9e9e',
    landFill: appStore.isDarkMode ? 'rgba(15, 118, 110, 0.18)' : 'rgba(59, 130, 246, 0.08)',
    landStroke: appStore.isDarkMode ? 'rgba(45, 212, 191, 0.4)' : 'rgba(30, 64, 175, 0.25)',
  }
}

const latLonToWorld = (latitude: number, longitude: number) => ({
  x:
    ((longitude - MAP_BOUNDS.minLon) / (MAP_BOUNDS.maxLon - MAP_BOUNDS.minLon)) *
    canvasWidth.value,
  y:
    ((MAP_BOUNDS.maxLat - latitude) / (MAP_BOUNDS.maxLat - MAP_BOUNDS.minLat)) *
    canvasHeight.value,
})

const worldToScreen = (worldX: number, worldY: number) => ({
  x: worldX * scale.value + panX.value,
  y: worldY * scale.value + panY.value,
})

const drawBackground = (
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  palette: ThemePalette,
) => {
  const background = ctx.createLinearGradient(0, 0, width, height)
  background.addColorStop(0, palette.backgroundStart)
  background.addColorStop(1, palette.backgroundEnd)
  ctx.fillStyle = background
  ctx.fillRect(0, 0, width, height)

  const spacing = 64
  for (let x = 0; x <= width; x += spacing) {
    ctx.strokeStyle = x % (spacing * 2) === 0 ? palette.majorGridLine : palette.gridLine
    ctx.lineWidth = x % (spacing * 2) === 0 ? 1.2 : 0.8
    ctx.beginPath()
    ctx.moveTo(x, 0)
    ctx.lineTo(x, height)
    ctx.stroke()
  }

  for (let y = 0; y <= height; y += spacing) {
    ctx.strokeStyle = y % (spacing * 2) === 0 ? palette.majorGridLine : palette.gridLine
    ctx.lineWidth = y % (spacing * 2) === 0 ? 1.2 : 0.8
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(width, y)
    ctx.stroke()
  }

  const californiaSilhouette = [
    { x: width * 0.2, y: height * 0.16 },
    { x: width * 0.24, y: height * 0.08 },
    { x: width * 0.3, y: height * 0.18 },
    { x: width * 0.35, y: height * 0.28 },
    { x: width * 0.39, y: height * 0.37 },
    { x: width * 0.44, y: height * 0.49 },
    { x: width * 0.45, y: height * 0.6 },
    { x: width * 0.48, y: height * 0.72 },
    { x: width * 0.55, y: height * 0.94 },
    { x: width * 0.66, y: height * 0.96 },
    { x: width * 0.62, y: height * 0.76 },
    { x: width * 0.58, y: height * 0.58 },
    { x: width * 0.54, y: height * 0.42 },
    { x: width * 0.5, y: height * 0.27 },
    { x: width * 0.46, y: height * 0.14 },
  ]

  ctx.save()
  ctx.fillStyle = palette.landFill
  ctx.strokeStyle = palette.landStroke
  ctx.lineWidth = 2
  ctx.beginPath()
  californiaSilhouette.forEach((point, index) => {
    if (index === 0) {
      ctx.moveTo(point.x, point.y)
      return
    }

    ctx.lineTo(point.x, point.y)
  })
  ctx.closePath()
  ctx.fill()
  ctx.stroke()

  ctx.strokeStyle = palette.gridLine
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(width * 0.46, height * 0.12)
  ctx.lineTo(width * 0.54, height * 0.86)
  ctx.moveTo(width * 0.38, height * 0.34)
  ctx.lineTo(width * 0.59, height * 0.31)
  ctx.moveTo(width * 0.4, height * 0.52)
  ctx.lineTo(width * 0.61, height * 0.48)
  ctx.stroke()
  ctx.restore()
}

const drawScaleLabels = (
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  palette: ThemePalette,
) => {
  const latLines = [32, 34, 36, 38, 40, 42]
  const lonLines = [-124, -122, -120, -118, -116, -114]

  ctx.save()
  ctx.fillStyle = palette.textSecondary
  ctx.font = '12px Segoe UI, sans-serif'

  latLines.forEach((latitude) => {
    const y = latLonToWorld(latitude, MAP_BOUNDS.minLon).y
    ctx.fillText(`${latitude.toFixed(0)}°N`, 12, clamp(y - 6, 18, height - 10))
  })

  lonLines.forEach((longitude) => {
    const x = latLonToWorld(MAP_BOUNDS.minLat, longitude).x
    ctx.fillText(`${Math.abs(longitude).toFixed(0)}°W`, clamp(x + 4, 12, width - 46), height - 14)
  })
  ctx.restore()
}

const drawMarkers = (ctx: CanvasRenderingContext2D, palette: ThemePalette) => {
  const nextMarkers: RenderedMarker[] = []

  mapIncidents.value.forEach((incident) => {
    const world = latLonToWorld(incident.latitude, incident.longitude)
    const screen = worldToScreen(world.x, world.y)
    const radius = getMarkerRadius(incident)
    const outerRadius = radius + 6
    const markerColor = getMarkerColor(incident.severityLabel)

    if (
      screen.x < -60 ||
      screen.x > canvasWidth.value + 60 ||
      screen.y < -60 ||
      screen.y > canvasHeight.value + 60
    ) {
      return
    }

    nextMarkers.push({
      id: incident.id,
      x: screen.x,
      y: screen.y,
      radius: outerRadius,
    })

    ctx.save()

    ctx.beginPath()
    ctx.fillStyle = `${markerColor}33`
    ctx.arc(screen.x, screen.y, outerRadius + 4, 0, Math.PI * 2)
    ctx.fill()

    ctx.beginPath()
    ctx.fillStyle = markerColor
    ctx.arc(screen.x, screen.y, outerRadius, 0, Math.PI * 2)
    ctx.fill()

    ctx.beginPath()
    ctx.fillStyle = appStore.isDarkMode ? 'rgba(15, 20, 25, 0.92)' : 'rgba(255, 255, 255, 0.96)'
    ctx.arc(screen.x, screen.y, radius, 0, Math.PI * 2)
    ctx.fill()

    ctx.fillStyle = palette.textPrimary
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.font = `${Math.max(16, radius + 4)}px Segoe UI Emoji, Apple Color Emoji, sans-serif`
    ctx.fillText(incident.icon, screen.x, screen.y + 1)

    ctx.textBaseline = 'top'
    ctx.font = '600 12px Segoe UI, sans-serif'
    ctx.fillStyle = palette.textPrimary
    ctx.fillText(incident.displayName, screen.x, screen.y + outerRadius + 10)

    ctx.font = '11px Segoe UI, sans-serif'
    ctx.fillStyle = palette.textSecondary
    ctx.fillText(`Threat ${incident.threatScore}`, screen.x, screen.y + outerRadius + 28)
    ctx.restore()
  })

  renderedMarkers.value = nextMarkers
}

const drawMap = () => {
  animationFrameId = 0

  if (!mapCanvas.value || !containerRef.value) {
    return
  }

  const ctx = mapCanvas.value.getContext('2d')

  if (!ctx) {
    return
  }

  const width = canvasWidth.value
  const height = canvasHeight.value
  const palette = getThemePalette()

  ctx.setTransform(window.devicePixelRatio || 1, 0, 0, window.devicePixelRatio || 1, 0, 0)
  ctx.clearRect(0, 0, width, height)

  drawBackground(ctx, width, height, palette)
  drawScaleLabels(ctx, width, height, palette)
  drawMarkers(ctx, palette)

  ctx.save()
  ctx.fillStyle = palette.textSecondary
  ctx.font = '12px Segoe UI, sans-serif'
  ctx.fillText(`Zoom ${scale.value.toFixed(2)}×`, width - 90, 24)
  ctx.restore()
}

const scheduleDraw = () => {
  if (animationFrameId) {
    return
  }

  animationFrameId = window.requestAnimationFrame(drawMap)
}

const resizeCanvas = () => {
  if (!mapCanvas.value || !containerRef.value) {
    return
  }

  const rect = containerRef.value.getBoundingClientRect()
  const nextWidth = Math.max(rect.width, 320)
  const nextHeight = Math.max(rect.height, 280)
  const pixelRatio = window.devicePixelRatio || 1

  canvasWidth.value = nextWidth
  canvasHeight.value = nextHeight
  mapCanvas.value.width = Math.round(nextWidth * pixelRatio)
  mapCanvas.value.height = Math.round(nextHeight * pixelRatio)
  mapCanvas.value.style.width = `${nextWidth}px`
  mapCanvas.value.style.height = `${nextHeight}px`

  scheduleDraw()
}

const getCanvasPoint = (event: MouseEvent | PointerEvent | WheelEvent) => {
  const rect = mapCanvas.value?.getBoundingClientRect()

  if (!rect) {
    return { x: 0, y: 0 }
  }

  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
  }
}

const getMarkerAtPoint = (x: number, y: number) =>
  renderedMarkers.value.find((marker) => Math.hypot(marker.x - x, marker.y - y) <= marker.radius)

const handleMapClick = (event: MouseEvent) => {
  if (dragDistance > 6) {
    dragDistance = 0
    return
  }

  const point = getCanvasPoint(event)
  const marker = getMarkerAtPoint(point.x, point.y)

  selectedIncidentId.value = marker?.id ?? null
  appStore.setSelectedIncident(marker?.id ?? null)
  appStore.setExpandedIncident(marker?.id ?? null)
}

const clearSelectedIncident = () => {
  selectedIncidentId.value = null
  appStore.setSelectedIncident(null)
  appStore.setExpandedIncident(null)
}

const handleWheel = (event: WheelEvent) => {
  const point = getCanvasPoint(event)
  const zoomFactor = event.deltaY < 0 ? 1.12 : 0.9
  const nextScale = clamp(scale.value * zoomFactor, MIN_SCALE, MAX_SCALE)

  if (nextScale === scale.value) {
    return
  }

  const worldX = (point.x - panX.value) / scale.value
  const worldY = (point.y - panY.value) / scale.value

  scale.value = nextScale
  panX.value = point.x - worldX * nextScale
  panY.value = point.y - worldY * nextScale
  scheduleDraw()
}

const handlePointerDown = (event: PointerEvent) => {
  isDragging = true
  dragDistance = 0
  lastPointerX = event.clientX
  lastPointerY = event.clientY
  mapCanvas.value?.setPointerCapture(event.pointerId)
}

const handlePointerMove = (event: PointerEvent) => {
  const point = getCanvasPoint(event)
  const hoveredMarkerMatch = getMarkerAtPoint(point.x, point.y)
  hoveredIncidentId.value = hoveredMarkerMatch?.id ?? null

  if (!isDragging) {
    return
  }

  const deltaX = event.clientX - lastPointerX
  const deltaY = event.clientY - lastPointerY

  if (deltaX === 0 && deltaY === 0) {
    return
  }

  panX.value += deltaX
  panY.value += deltaY
  dragDistance += Math.abs(deltaX) + Math.abs(deltaY)
  lastPointerX = event.clientX
  lastPointerY = event.clientY
  scheduleDraw()
}

const handlePointerUp = (event: PointerEvent) => {
  isDragging = false

  if (mapCanvas.value?.hasPointerCapture(event.pointerId)) {
    mapCanvas.value.releasePointerCapture(event.pointerId)
  }
}

const handlePointerLeave = (event: PointerEvent) => {
  hoveredIncidentId.value = null
  isDragging = false

  if (mapCanvas.value?.hasPointerCapture(event.pointerId)) {
    mapCanvas.value.releasePointerCapture(event.pointerId)
  }
}

const getFloatingStyle = (x: number, y: number, width: number, height: number) => {
  const margin = 16
  const maxLeft = Math.max(margin, canvasWidth.value - width - margin)
  const maxTop = Math.max(margin, canvasHeight.value - height - margin)

  return {
    left: `${clamp(x + 20, margin, maxLeft)}px`,
    top: `${clamp(y - height / 2, margin, maxTop)}px`,
  }
}

watch(mapIncidents, () => {
  if (selectedIncidentId.value && !mapIncidents.value.some((incident) => incident.id === selectedIncidentId.value)) {
    clearSelectedIncident()
  }

  scheduleDraw()
})

watch(
  () => appStore.selectedIncident,
  (incidentId) => {
    selectedIncidentId.value = incidentId
    scheduleDraw()
  },
)

watch(
  () => [appStore.isDarkMode, appStore.viewMode],
  () => {
    scheduleDraw()
  },
)

onMounted(() => {
  resizeCanvas()
  resizeObserver = new ResizeObserver(() => resizeCanvas())

  if (containerRef.value) {
    resizeObserver.observe(containerRef.value)
  }

  window.addEventListener('resize', resizeCanvas)
  scheduleDraw()
})

onBeforeUnmount(() => {
  if (animationFrameId) {
    window.cancelAnimationFrame(animationFrameId)
  }

  resizeObserver?.disconnect()
  window.removeEventListener('resize', resizeCanvas)
})
</script>

<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 320px;
  background: var(--bg-panel);
  border-radius: 8px;
  overflow: hidden;
}

.map-canvas {
  width: 100%;
  height: 100%;
  display: block;
  cursor: grab;
  touch-action: none;
}

.map-canvas:active {
  cursor: grabbing;
}

.map-overlay,
.map-tooltip,
.map-popup {
  position: absolute;
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: 10px;
  pointer-events: auto;
}

.legend-panel {
  top: 12px;
  left: 12px;
  background: var(--glass-bg);
  color: var(--text-primary);
  padding: 12px;
  width: min(250px, calc(100% - 24px));
  font-size: 12px;
}

.overlay-title {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.overlay-subtitle,
.overlay-hint {
  color: var(--text-secondary);
  margin-top: 4px;
}

.legend-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-swatch {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.08);
}

.map-tooltip {
  width: 170px;
  padding: 10px 12px;
  background: var(--bg-overlay);
  color: var(--text-primary);
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  pointer-events: none;
}

.map-tooltip span {
  color: var(--text-secondary);
}

.map-popup {
  width: 260px;
  padding: 14px;
  background: var(--bg-overlay);
  color: var(--text-primary);
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.22);
}

.close-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 26px;
  height: 26px;
  border: none;
  border-radius: 999px;
  background: var(--accent-cyan-soft);
  color: var(--accent-cyan);
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}

.popup-header {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding-right: 22px;
  margin-bottom: 12px;
}

.popup-icon {
  font-size: 24px;
  line-height: 1;
}

.popup-header h4 {
  margin: 0;
  font-size: 16px;
}

.popup-header p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 12px;
}

.popup-grid {
  display: grid;
  gap: 10px;
}

.popup-grid > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.popup-label {
  color: var(--text-secondary);
  font-size: 12px;
}

.popup-value {
  color: var(--text-primary);
  font-weight: 600;
  text-align: right;
}

.status-pill {
  text-transform: capitalize;
}

@media (max-width: 900px) {
  .legend-panel {
    width: min(220px, calc(100% - 24px));
  }

  .map-popup {
    width: min(240px, calc(100% - 24px));
  }
}
</style>
