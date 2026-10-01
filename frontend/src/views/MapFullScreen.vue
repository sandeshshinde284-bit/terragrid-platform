<template>
  <div class="map-fullscreen">
    <Header />

    <div class="map-container">
      <canvas ref="mapCanvas" class="map-canvas"></canvas>

      <!-- Map Controls -->
      <div class="map-controls glass-panel">
        <button @click="zoomIn" title="Zoom In" class="control-btn">➕</button>
        <button @click="zoomOut" title="Zoom Out" class="control-btn">➖</button>
        <button @click="toggleLayers" class="control-btn">🗺️</button>
      </div>

      <!-- Layer Toggle -->
      <div class="layers-panel glass-panel">
        <div class="layer-item">
          <input v-model="layers.incidents" type="checkbox" id="incidents-layer" />
          <label for="incidents-layer">🌍 {{ $t('incidents.title') }}</label>
        </div>
        <div class="layer-item">
          <input v-model="layers.evacuationZones" type="checkbox" id="evacuation-layer" />
          <label for="evacuation-layer">⛔ {{ $t('map.evacuationZones') }}</label>
        </div>
        <div class="layer-item">
          <input v-model="layers.emergencyRoutes" type="checkbox" id="routes-layer" />
          <label for="routes-layer">🛣️ {{ $t('map.emergencyRoutes') }}</label>
        </div>
        <div class="layer-item">
          <input v-model="layers.isolatedAreas" type="checkbox" id="isolated-layer" />
          <label for="isolated-layer">🚫 {{ $t('map.isolatedAreas') }}</label>
        </div>
        <div class="layer-item">
          <input v-model="layers.heatMap" type="checkbox" id="heat-layer" />
          <label for="heat-layer">🔥 {{ $t('map.heatMap') }}</label>
        </div>
      </div>

      <!-- Stats Panel -->
      <div class="stats-panel glass-panel">
        <div class="stat">
          <span class="label">{{ $t('dashboard.activeIncidentsCount') }}</span>
          <span class="value">{{ eventsStore.allIncidents.length }}</span>
        </div>
        <div class="stat">
          <span class="label">{{ $t('map.evacuationZones') }}</span>
          <span class="value">{{ evacuationStats }}</span>
        </div>
        <div class="stat">
          <span class="label">{{ $t('map.isolatedAreas') }}</span>
          <span class="value">{{ isolatedStats }}</span>
        </div>
      </div>

      <!-- Legend -->
      <div class="legend-panel glass-panel">
        <h3>{{ $t('common.details') }}</h3>
        <div class="legend-item">
          <span class="legend-color fire"></span>
          <span>🔥 Fire Zone</span>
        </div>
        <div class="legend-item">
          <span class="legend-color flood"></span>
          <span>💧 Flood Risk</span>
        </div>
        <div class="legend-item">
          <span class="legend-color earthquake"></span>
          <span>🌍 Seismic Activity</span>
        </div>
        <div class="legend-item">
          <span class="legend-color landslide"></span>
          <span>⛰️ Landslide Risk</span>
        </div>
        <div class="legend-item">
          <span class="legend-color evacuation"></span>
          <span>⛔ Evacuation Zone</span>
        </div>
        <div class="legend-item">
          <span class="legend-color isolated"></span>
          <span>🚫 Isolated Area</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import Header from '@/components/organisms/Header.vue'
import { useEventsStore } from '@/stores'

const eventsStore = useEventsStore()
const mapCanvas = ref<HTMLCanvasElement | null>(null)
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)

const layers = reactive({
  incidents: true,
  evacuationZones: true,
  emergencyRoutes: true,
  isolatedAreas: true,
  heatMap: false,
})

const evacuationStats = ref('8')
const isolatedStats = ref('3')

const colorMap: Record<string, string> = {
  fire: '#ef4444',
  flood: '#3b82f6',
  earthquake: '#f59e0b',
  landslide: '#8b5cf6',
  evacuation: '#dc2626',
  isolated: '#6b21a8',
  route: '#10b981',
}

const zoomIn = () => {
  zoom.value = Math.min(zoom.value + 0.2, 3)
  redrawMap()
}

const zoomOut = () => {
  zoom.value = Math.max(zoom.value - 0.2, 0.5)
  redrawMap()
}

const toggleLayers = () => {
  // Implement layer visibility toggle if needed
}

const drawIncidents = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
  eventsStore.allIncidents.forEach((incident) => {
    const x = (incident.id.charCodeAt(0) / 255) * width
    const y = (incident.id.charCodeAt(1) / 255) * height
    
    ctx.fillStyle = colorMap[incident.type] || '#999'
    ctx.beginPath()
    ctx.arc(x, y, 8 * zoom.value, 0, Math.PI * 2)
    ctx.fill()
    
    ctx.fillStyle = '#fff'
    ctx.font = `${10 * zoom.value}px sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(incident.type.charAt(0).toUpperCase(), x, y)
  })
}

const drawEvacuationZones = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
  ctx.strokeStyle = colorMap.evacuation
  ctx.fillStyle = 'rgba(220, 38, 38, 0.1)'
  ctx.lineWidth = 2
  
  // Draw 8 evacuation zones
  for (let i = 0; i < 8; i++) {
    const angle = (i / 8) * Math.PI * 2
    const centerX = width / 2 + Math.cos(angle) * (width / 3)
    const centerY = height / 2 + Math.sin(angle) * (height / 3)
    
    ctx.beginPath()
    ctx.arc(centerX, centerY, 60 * zoom.value, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()
  }
}

const drawEmergencyRoutes = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
  ctx.strokeStyle = colorMap.route
  ctx.lineWidth = 3 * zoom.value
  ctx.setLineDash([5, 5])
  
  // Draw route network
  ctx.beginPath()
  ctx.moveTo(width * 0.1, height * 0.1)
  ctx.lineTo(width * 0.9, height * 0.5)
  ctx.lineTo(width * 0.1, height * 0.9)
  ctx.stroke()
  
  ctx.beginPath()
  ctx.moveTo(width * 0.9, height * 0.1)
  ctx.lineTo(width * 0.5, height * 0.5)
  ctx.lineTo(width * 0.9, height * 0.9)
  ctx.stroke()
  
  ctx.setLineDash([])
}

const drawIsolatedAreas = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
  ctx.strokeStyle = colorMap.isolated
  ctx.fillStyle = 'rgba(107, 33, 168, 0.15)'
  ctx.lineWidth = 2
  
  // Draw 3 isolated areas
  const isolatedPoints = [
    { x: width * 0.3, y: height * 0.3 },
    { x: width * 0.7, y: height * 0.7 },
    { x: width * 0.5, y: height * 0.2 },
  ]
  
  isolatedPoints.forEach((point) => {
    ctx.beginPath()
    ctx.rect(point.x - 40 * zoom.value, point.y - 40 * zoom.value, 80 * zoom.value, 80 * zoom.value)
    ctx.fill()
    ctx.stroke()
  })
}

const drawHeatMap = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
  const imageData = ctx.createImageData(width, height)
  const data = imageData.data
  
  for (let i = 0; i < data.length; i += 4) {
    const intensity = Math.sin(i / 1000) * 127 + 128
    data[i] = intensity
    data[i + 1] = intensity / 2
    data[i + 2] = 50
    data[i + 3] = 100
  }
  
  ctx.putImageData(imageData, 0, 0)
}

const redrawMap = () => {
  if (!mapCanvas.value) return
  
  const canvas = mapCanvas.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const width = canvas.width
  const height = canvas.height
  
  ctx.save()
  ctx.scale(zoom.value, zoom.value)
  ctx.translate(panX.value / zoom.value, panY.value / zoom.value)
  
  // Clear background
  ctx.fillStyle = '#1a2332'
  ctx.fillRect(0, 0, width / zoom.value, height / zoom.value)
  
  // Draw grid
  ctx.strokeStyle = 'rgba(255,255,255,0.05)'
  ctx.lineWidth = 1
  for (let i = 0; i < width / zoom.value; i += 50) {
    ctx.beginPath()
    ctx.moveTo(i, 0)
    ctx.lineTo(i, height / zoom.value)
    ctx.stroke()
  }
  for (let i = 0; i < height / zoom.value; i += 50) {
    ctx.beginPath()
    ctx.moveTo(0, i)
    ctx.lineTo(width / zoom.value, i)
    ctx.stroke()
  }
  
  // Draw layers
  if (layers.heatMap) {
    drawHeatMap(ctx, width / zoom.value, height / zoom.value)
  }
  
  if (layers.evacuationZones) {
    drawEvacuationZones(ctx, width / zoom.value, height / zoom.value)
  }
  
  if (layers.emergencyRoutes) {
    drawEmergencyRoutes(ctx, width / zoom.value, height / zoom.value)
  }
  
  if (layers.isolatedAreas) {
    drawIsolatedAreas(ctx, width / zoom.value, height / zoom.value)
  }
  
  if (layers.incidents) {
    drawIncidents(ctx, width / zoom.value, height / zoom.value)
  }
  
  ctx.restore()
}

onMounted(() => {
  if (eventsStore.allIncidents.length === 0) {
    eventsStore.initMockData()
  }
  
  if (mapCanvas.value) {
    const canvas = mapCanvas.value
    canvas.width = window.innerWidth - 32
    canvas.height = window.innerHeight - 92
    
    redrawMap()
  }
  
  window.addEventListener('resize', () => {
    if (mapCanvas.value) {
      mapCanvas.value.width = window.innerWidth - 32
      mapCanvas.value.height = window.innerHeight - 92
      redrawMap()
    }
  })
})

watch(() => layers, () => {
  redrawMap()
}, { deep: true })
</script>

<style scoped>
.map-fullscreen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.map-container {
  flex: 1;
  position: relative;
  min-height: 0;
}

.map-canvas {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  background: #1a2332;
  cursor: grab;
}

.map-canvas:active {
  cursor: grabbing;
}

.map-controls {
  position: absolute;
  top: 16px;
  left: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  z-index: 10;
}

.control-btn {
  width: 50px;
  height: 50px;
  border: 2px solid var(--accent-cyan);
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.3), rgba(14, 165, 233, 0.2));
  color: var(--accent-cyan);
  border-radius: 6px;
  cursor: pointer;
  font-size: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(30, 64, 175, 0.3);
}

.control-btn:hover {
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.5), rgba(14, 165, 233, 0.4));
  border-color: var(--accent-cyan);
  color: #ffffff;
  box-shadow: 0 4px 16px rgba(30, 64, 175, 0.5);
  transform: scale(1.05);
}

.layers-panel {
  position: absolute;
  top: 16px;
  right: 16px;
  padding: 16px;
  max-height: 50vh;
  overflow-y: auto;
  z-index: 10;
  border: 2px solid var(--accent-cyan);
  border-radius: 8px;
  background: rgba(30, 64, 175, 0.15);
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.layer-item input {
  cursor: pointer;
  width: 18px;
  height: 18px;
  accent-color: var(--accent-cyan);
  border-radius: 3px;
}

.legend-panel {
  position: absolute;
  bottom: 16px;
  right: 16px;
  padding: 16px;
  max-width: 240px;
  z-index: 10;
  border: 2px solid var(--accent-cyan);
  border-radius: 8px;
  background: rgba(30, 64, 175, 0.15);
}

.legend-panel h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 700;
  color: var(--accent-cyan);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.legend-color {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  flex-shrink: 0;
}

.legend-color.fire {
  background: #ef4444;
}

.legend-color.flood {
  background: #3b82f6;
}

.legend-color.earthquake {
  background: #f59e0b;
}

.legend-color.landslide {
  background: #8b5cf6;
}

.legend-color.evacuation {
  background: #dc2626;
}

.legend-color.isolated {
  background: #6b21a8;
}

@media (max-width: 768px) {
  .map-fullscreen {
    padding: 8px;
    gap: 8px;
  }

  .map-controls {
    top: 8px;
    left: 8px;
  }

  .control-btn {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }

  .layers-panel {
    top: 8px;
    right: 8px;
    padding: 12px;
    font-size: 12px;
  }

  .layer-item {
    margin-bottom: 10px;
  }

  .stats-panel {
    bottom: 8px;
    left: 8px;
    gap: 16px;
    padding: 12px;
  }

  .stat .value {
    font-size: 18px;
  }

  .legend-panel {
    bottom: 8px;
    right: 8px;
    padding: 12px;
    max-width: 180px;
  }
}
</style>
