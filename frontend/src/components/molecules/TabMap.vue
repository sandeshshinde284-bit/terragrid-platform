<template>
  <div class="map-tab">
    <div class="tab-intro">
      <div>
        <h2>Evacuation Routes</h2>
        <p>Real-time calculated transit clearance times, primary corridors, and bottleneck choke-points.</p>
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
            <div class="route-highlight" style="display: flex; gap: 12px; align-items: center; margin-bottom: 12px;">
              <span class="route-icon" style="font-size: 24px;">🛣️</span>
              <div>
                <strong style="color: #38bdf8; font-size: 16px;">{{ deepDossier.evacuation_corridors.primary_corridor }}</strong>
                <small style="display: block; color: #94a3b8; font-size: 18px;">Designated Primary Outbound Corridor</small>
              </div>
            </div>
            <div class="route-highlight alt" style="display: flex; gap: 12px; align-items: center; margin-bottom: 14px;">
              <span class="route-icon" style="font-size: 24px;">🔀</span>
              <div>
                <strong style="color: #cbd5e1; font-size: 18px;">{{ deepDossier.evacuation_corridors.alternative_route }}</strong>
                <small style="display: block; color: #94a3b8; font-size: 18px;">Secondary Contingency Route</small>
              </div>
            </div>
            <div class="clearance-eta" style="margin-top: 14px; padding: 12px; background: rgba(14, 165, 233, 0.1); border-radius: 8px;">
              <span style="color: #94a3b8; font-size: 18px; text-transform: uppercase;">Estimated Corridor Clearance Time:</span>
              <strong style="display: block; font-size: 20px; color: #38bdf8; margin-top: 2px;">{{ deepDossier.evacuation_corridors.estimated_clearance_time_hours }} Hours</strong>
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
                <li v-for="cp in deepDossier.evacuation_corridors.choke_points" :key="cp">
                  {{ cp }}
                </li>
              </ul>
            </div>
            <div class="rally-box">
              <strong style="color: #4ade80; font-size: 16px; text-transform: uppercase;">🟢 Safe Assembly Staging Perimeters:</strong>
              <ul style="margin: 6px 0 0 16px; color: #cbd5e1; font-size: 18px;">
                <li v-for="sz in deepDossier.evacuation_corridors.safe_assembly_zones" :key="sz">
                  {{ sz }}
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