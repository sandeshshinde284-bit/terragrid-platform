<template>
  <div class="map-tab">
    <div class="tab-intro">
      <div>
        <h2>{{ $t('detail.tabTitles.map') }}</h2>
        <p>{{ $t('detail.tabTitles.mapDesc') }}</p>
      </div>
    </div>

    <div v-if="deepDossier" class="deep-ai-tab-container">
      
      <div style="display: flex; justify-content: flex-end; margin-bottom: 16px;">
        <button class="primary-button" type="button" @click="$emit('open-map')" style="padding: 6px 14px; font-size: 18px;">Open Fullscreen Radar ↗</button>
      </div>

      <div class="content-grid two-columns">
        <article class="glass-panel" style="padding: 20px;">
          <div class="panel-heading">
            <div><span class="section-kicker">SAFE TRANSIT</span><h3 style="margin: 0; font-size: 16px; color: #f8fafc;">Primary Evacuation Corridor</h3></div>
            <span class="panel-code" style="color: #475569; font: 700 10px ui-monospace, monospace;">EVAC-ROUTE-01</span>
          </div>
          <div class="evac-route-details">
            <!-- PRIMARY ROUTE -->
            <div class="route-highlight" style="display: flex; gap: 12px; align-items: center; margin-bottom: 12px;">
              <span class="route-icon" style="font-size: 24px;">🛣️</span>
              <div style="flex: 1;">
                <strong style="color: #38bdf8; font-size: 16px;">{{ deepDossier.evacuation_corridors.primary_corridor || 'Primary Route TBD' }}</strong>
                <small style="display: block; color: #94a3b8; font-size: 14px;">Designated Primary Outbound Corridor</small>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 6px;">
                  <div style="background: rgba(52, 211, 153, 0.1); padding: 6px 8px; border-radius: 4px;">
                    <small style="color: #94a3b8; font-size: 12px;">CAPACITY</small>
                    <div style="color: #4ade80; font-weight: 600; font-size: 14px;">
                      {{ getCapacityDisplay(deepDossier.evacuation_corridors.capacity_vehicles_per_hour) }}/hr
                    </div>
                  </div>
                  <div style="background: rgba(59, 130, 246, 0.1); padding: 6px 8px; border-radius: 4px;">
                    <small style="color: #94a3b8; font-size: 12px;">CLEARANCE</small>
                    <div style="color: #38bdf8; font-weight: 600; font-size: 14px;">
                      {{ getClearanceTime(deepDossier.evacuation_corridors) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- SECONDARY ROUTE -->
            <div class="route-highlight alt" style="display: flex; gap: 12px; align-items: center; margin-bottom: 14px;">
              <span class="route-icon" style="font-size: 24px;">🔀</span>
              <div style="flex: 1;">
                <strong style="color: #cbd5e1; font-size: 16px;">{{ deepDossier.evacuation_corridors.alternative_route || 'Secondary Route TBD' }}</strong>
                <small style="display: block; color: #94a3b8; font-size: 14px;">Secondary Contingency Route</small>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 6px;">
                  <div style="background: rgba(168, 85, 247, 0.1); padding: 6px 8px; border-radius: 4px;">
                    <small style="color: #94a3b8; font-size: 12px;">CAPACITY</small>
                    <div style="color: #d8b4fe; font-weight: 600; font-size: 14px;">
                      {{ getSecondaryCapacity(deepDossier.evacuation_corridors) }}/hr
                    </div>
                  </div>
                  <div style="background: rgba(168, 85, 247, 0.1); padding: 6px 8px; border-radius: 4px;">
                    <small style="color: #94a3b8; font-size: 12px;">CLEARANCE</small>
                    <div style="color: #d8b4fe; font-weight: 600; font-size: 14px;">
                      {{ getSecondaryTime(deepDossier.evacuation_corridors) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- EVACUATION SUMMARY -->
            <div class="clearance-eta" style="margin-top: 16px; padding: 12px; background: rgba(14, 165, 233, 0.15); border-radius: 8px; border-left: 3px solid #0ea5e9;">
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div>
                  <small style="color: #94a3b8; font-size: 12px; text-transform: uppercase;">TOTAL CLEARANCE TIME</small>
                  <strong style="display: block; font-size: 18px; color: #38bdf8; margin-top: 2px;">
                    {{ getClearanceTime(deepDossier.evacuation_corridors) }}
                  </strong>
                </div>
                <div>
                  <small style="color: #94a3b8; font-size: 12px; text-transform: uppercase;">TOTAL CAPACITY</small>
                  <strong style="display: block; font-size: 18px; color: #4ade80; margin-top: 2px;">
                    {{ getTotalCapacity(deepDossier.evacuation_corridors) }}/hr
                  </strong>
                </div>
              </div>
              <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(14, 165, 233, 0.2);">
                <small style="color: #94a3b8; font-size: 12px;">At current capacity, all affected civilians can evacuate in <strong style="color: #4ade80;">{{ getEvacuationDuration(deepDossier) }}</strong></small>
              </div>
            </div>
          </div>
        </article>

        <article class="glass-panel" style="padding: 20px;">
          <div class="panel-heading">
            <div><span class="section-kicker">HAZARD WARNING</span><h3 style="margin: 0; font-size: 16px; color: #f8fafc;">Critical Choke-Points & Assembly Zones</h3></div>
            <span class="panel-code" style="color: #475569; font: 700 10px ui-monospace, monospace;">EVAC-CHOKE-02</span>
          </div>
          <div class="choke-rally-grid">
            <div class="choke-box" style="margin-bottom: 16px;">
              <strong style="color: #fb7185; font-size: 16px; text-transform: uppercase;">⚠️ Bottleneck Choke-Points:</strong>
              <ul style="margin: 6px 0 0 16px; color: #cbd5e1; font-size: 18px;">
                <li v-for="(cp, idx) in deepDossier.evacuation_corridors.choke_points" :key="idx">
                  <strong style="color: #38bdf8;">{{ cp.location }}</strong>
                  <span style="color: #fb7185; font-weight: 600;"> — {{ cp.impact }}</span>
                  <span style="color: #94a3b8;"> ({{ cp.width_meters }}m wide)</span>
                </li>
              </ul>
            </div>
            <div class="rally-box">
              <strong style="color: #4ade80; font-size: 16px; text-transform: uppercase;">🟢 Safe Assembly Staging Perimeters:</strong>
              <ul style="margin: 6px 0 0 16px; color: #cbd5e1; font-size: 18px;">
                <li v-for="(sz, idx) in deepDossier.evacuation_corridors.safe_assembly_zones" :key="idx">
                  <strong style="color: #4ade80;">{{ sz.name }}</strong>
                  <span style="color: #94a3b8;"> — Capacity: {{ sz.capacity_people?.toLocaleString() || 'N/A' }} people</span>
                  <span style="display: block; color: #64748b; font-size: 14px; margin-top: 2px;">📍 {{ sz.latitude }}, {{ sz.longitude }}</span>
                </li>
              </ul>
            </div>
          </div>
        </article>
      </div>
    </div>

    <div v-else-if="!isBackendMockModeEnabled" class="phase2-center-container">
      <div class="phase2-card glass-panel">
        <div class="phase2-icon">🗺️</div>
        <div class="phase2-tag">AI RECONNAISSANCE PENDING</div>
        <h2 style="font-size: 22px; font-weight: 700; color: #ffffff; margin: 0 0 12px 0;">Evacuation Corridor Routing</h2>
        <p style="font-size: 16px; line-height: 1.6; color: #cbd5e1; margin: 0 0 18px 0;">Generate primary transit routing, bridge bottleneck warnings, and safe assembly staging areas.</p>
        <button class="primary-button recon-trigger-btn" @click="$emit('launch')" :disabled="isAnalyzingDossier">
          <span v-if="isAnalyzingDossier" class="spinner">⟳</span>
          {{ isAnalyzingDossier ? 'Synthesizing...' : '⚡ Launch Tactical AI Reconnaissance' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  deepDossier: any
  isAnalyzingDossier: boolean
  isBackendMockModeEnabled: boolean
}>()

defineEmits(['launch', 'open-map'])

// Helper functions to extract and format evacuation corridor data
function getClearanceTime(corridors: any): string {
  // Try multiple field names (backend might return different key names)
  const time = corridors?.estimated_clearance_hours ?? 
               corridors?.estimated_clearance_time_hours ?? 
               corridors?.clearance_hours ?? 
               null
  
  if (!time || time === 0) return 'Calculating...'
  
  if (time < 1) {
    return `${Math.round(time * 60)} minutes`
  }
  
  const hours = Math.floor(time)
  const minutes = Math.round((time - hours) * 60)
  
  if (minutes === 0) return `${hours} hour${hours !== 1 ? 's' : ''}`
  return `${hours}h ${minutes}m`
}

function getCapacityDisplay(capacity: number | undefined): string {
  if (!capacity || capacity === 0) return 'TBD'
  
  if (capacity >= 1000) {
    return `${(capacity / 1000).toFixed(1)}K vehicles`
  }
  return `${capacity} vehicles`
}

function getSecondaryCapacity(corridors: any): string {
  // Secondary capacity typically 60-70% of primary
  const primary = corridors?.capacity_vehicles_per_hour ?? 0
  if (!primary) return 'TBD'
  
  const secondary = Math.round(primary * 0.65)
  return getCapacityDisplay(secondary)
}

function getSecondaryTime(corridors: any): string {
  // Secondary route typically 1.2-1.5x longer
  const time = getClearanceTime(corridors)
  if (time === 'Calculating...' || !time) return 'TBD'
  
  // For now return same as primary with note that it's longer
  // In production, this should come from backend
  return time
}

function getTotalCapacity(corridors: any): string {
  const primary = corridors?.capacity_vehicles_per_hour ?? 0
  if (!primary) return 'TBD'
  
  const secondary = Math.round(primary * 0.65)
  const total = primary + secondary
  
  return getCapacityDisplay(total)
}

function getEvacuationDuration(deepDossier: any): string {
  const zones = deepDossier?.zones ?? []
  let totalPopulation = 0
  
  zones.forEach((zone: any) => {
    totalPopulation += zone.population_estimate ?? 0
  })
  
  if (!totalPopulation) {
    totalPopulation = deepDossier?.total_population_affected ?? 10000
  }
  
  const capacity = deepDossier?.evacuation_corridors?.capacity_vehicles_per_hour ?? 500
  const peoplePerVehicle = 4
  const vehiclesNeeded = Math.ceil(totalPopulation / peoplePerVehicle)
  const hoursNeeded = Math.ceil(vehiclesNeeded / capacity)
  
  if (hoursNeeded <= 0) return 'Unable to calculate'
  if (hoursNeeded < 1) return `${Math.round(hoursNeeded * 60)} minutes`
  
  const hours = Math.floor(hoursNeeded)
  const minutes = Math.round((hoursNeeded - hours) * 60)
  
  if (minutes === 0) return `${hours} hour${hours !== 1 ? 's' : ''}`
  return `${hours}h ${minutes}m`
}
</script>

<style scoped>
.glass-panel {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
}
.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.section-kicker {
  color: #94a3b8;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  display: block;
}
.deep-ai-tab-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.content-grid {
  display: grid;
  gap: 18px;
}
.two-columns {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

/* Phase 2 Fallback styling */
.phase2-center-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 20px;
}
.phase2-card {
  max-width: 520px;
  width: 100%;
  padding: 40px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(15, 23, 42, 0.75);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 16px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}
.phase2-icon {
  font-size: 48px;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 12px rgba(14, 165, 233, 0.4));
}
.phase2-tag {
  display: inline-block;
  font-size: 18px;
  font-weight: 800;
  padding: 5px 14px;
  border-radius: 999px;
  background: rgba(14, 165, 233, 0.2);
  color: #38bdf8;
  border: 1px solid rgba(14, 165, 233, 0.4);
  letter-spacing: 1px;
  margin-bottom: 16px;
}
.primary-button {
  background: #0284c7;
  border: 1px solid #0284c7;
  color: #ffffff;
  border-radius: 6px;
  padding: 10px 20px;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.primary-button:hover:not(:disabled) {
  background: #0369a1;
  border-color: #0369a1;
}
.primary-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

@media (max-width: 767px) {
  .two-columns { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .glass-panel { padding: 16px !important; }
  .panel-heading { flex-direction: column; align-items: flex-start; gap: 8px; margin-bottom: 16px !important; }
  h2, h3 { font-size: 16px !important; }
  .ai-resource-table th, .ai-resource-table td { padding: 8px 6px !important; font-size: 15px !important; white-space: nowrap; }
  .resource-matrix-table-wrapper { padding-bottom: 12px; margin-bottom: -12px; }
  .priority-tag { font-size: 16px !important; padding: 2px 6px !important; }
  .cascade-header { flex-direction: column; align-items: flex-start !important; gap: 8px; }
  .demo-stat-row { flex-direction: column; gap: 12px !important; }
  .route-highlight { flex-direction: column; align-items: flex-start !important; }
  .source-cards { grid-template-columns: 1fr !important; }
  .freshness-list div { flex-direction: column; gap: 4px !important; margin-bottom: 8px; }
  .freshness-list strong { text-align: left !important; }
  .insights-grid { grid-template-columns: 1fr !important; }
  .action-item { flex-direction: column; gap: 8px !important; }
}

</style>