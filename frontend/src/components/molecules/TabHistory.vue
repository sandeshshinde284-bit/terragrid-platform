<template>
  <div class="history-tab">
    <div class="tab-intro">
      <div>
        <h2>Spread Forecast</h2>
        <p>Trajectory forecasting based on atmospheric wind vectors, historical context, and local terrain topography.</p>
      </div>
    </div>

    <div v-if="deepDossier" class="deep-ai-tab-container">
      
      <div class="cascade-timeline-grid">
        <div v-for="(cascade, idx) in deepDossier.cascade_predictions" :key="idx" class="cascade-card glass-panel" :class="'cascade-border-' + cascade.color_code" style="padding: 20px; border-left-width: 4px;">
          <div class="cascade-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span class="time-tag" style="font-weight: 800; font-size: 16px;" :class="'text-' + cascade.color_code">
              ⏱️ +{{ cascade.timeframe_hours }} HOURS
            </span>
            <span class="delta-badge" style="font-family: ui-monospace, monospace; font-size: 18px; font-weight: 700; color: #cbd5e1; background: rgba(255, 255, 255, 0.05); padding: 4px 10px; border-radius: 4px;">
              +{{ cascade.perimeter_delta_km2.toFixed(1) }} km² EXPANSION
            </span>
          </div>
          
          <div class="cascade-vector" style="margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #1e293b;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="color: #94a3b8; font-size: 16px; text-transform: uppercase; font-weight: 700;">Wind Expansion Factor:</span>
              <span style="color: #38bdf8; font-family: ui-monospace, monospace; font-weight: 700;">{{ cascade.wind_influence_percent }}%</span>
            </div>
            <div class="progress-track" style="margin-top: 6px; background: #0f172a; border: 1px solid #1e293b; height: 6px; border-radius: 99px; overflow: hidden;">
              <span class="progress-fill" :style="{ width: `${cascade.wind_influence_percent}%`, background: getCascadeColorHex(cascade.color_code), display: 'block', height: '100%' }"></span>
            </div>
          </div>
          
          <div class="cascade-risks" style="display: flex; flex-direction: column; gap: 12px;">
            <span style="color: #94a3b8; font-size: 16px; text-transform: uppercase; font-weight: 700;">Facilities Entering Danger Zone:</span>
            <div v-if="!cascade.primary_risks || cascade.primary_risks.length === 0" style="color: #64748b; font-size: 16px; font-style: italic;">
              No major infrastructure predicted to fall within perimeter.
            </div>
            <div v-for="(risk, rIdx) in cascade.primary_risks" :key="rIdx" class="risk-group">
              <div style="display: flex; justify-content: space-between; font-size: 16px; margin-bottom: 4px;">
                <strong style="color: #cbd5e1;">{{ risk.facility_type }}</strong>
                <span style="color: #67e8f9; font-family: ui-monospace, monospace; font-weight: 700;">[{{ risk.count_affected }}]</span>
              </div>
              <ul style="margin: 0; padding-left: 16px; color: #94a3b8; font-size: 18px; line-height: 1.5;">
                <li v-for="name in risk.names" :key="name">{{ name }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else-if="!isBackendMockModeEnabled" class="phase2-center-container">
      <div class="phase2-card glass-panel">
        <div class="phase2-icon">🔮</div>
        <div class="phase2-tag">AI RECONNAISSANCE PENDING</div>
        <h2 style="font-size:20px; font-weight:700; color:#fff; margin-bottom:12px;">Predictive Cascade Simulation</h2>
        <p style="color:#cbd5e1; font-size: 16px; margin-bottom:18px;">Launch the cognitive AI reconnaissance to model 6-hour, 12-hour, and 24-hour crisis expansion trajectories using atmospheric wind vectors.</p>
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

defineEmits(['launch'])

function getCascadeColorHex(colorCode?: string): string {
  const code = (colorCode || 'RED').toUpperCase()
  switch (code) {
    case 'RED': return '#ef4444'
    case 'ORANGE': return '#f97316'
    case 'YELLOW': return '#eab308'
    case 'GREEN': return '#22c55e'
    default: return '#ef4444'
  }
}
</script>

<style scoped>
.glass-panel {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
}
.cascade-timeline-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.cascade-border-RED { border-left-color: #ef4444; }
.cascade-border-ORANGE { border-left-color: #f97316; }
.cascade-border-YELLOW { border-left-color: #eab308; }
.cascade-border-GREEN { border-left-color: #22c55e; }
.text-RED { color: #ef4444; }
.text-ORANGE { color: #f97316; }
.text-YELLOW { color: #eab308; }
.text-GREEN { color: #22c55e; }

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
}
.phase2-icon {
  font-size: 48px;
  margin-bottom: 16px;
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
@media (max-width: 900px) {
  .cascade-timeline-grid { grid-template-columns: 1fr; }
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