<template>
  <div class="impact-tab">
    <div class="tab-intro">
      <div>
        <h2>Impact Assessment</h2>
        <p>Analysis of critical infrastructure exposure and vulnerable populations within the disaster perimeter.</p>
      </div>
    </div>

    <div v-if="deepDossier" class="deep-ai-tab-container">
      
      <!-- Critical Infrastructure Table -->
      <article class="glass-panel infrastructure-panel" style="padding: 20px; margin-bottom: 20px;">
        <div class="panel-heading">
          <div><span class="section-kicker">VULNERABILITY MATRIX</span><h3 style="margin: 0; font-size: 16px; color: #f8fafc;">Exposed Critical Infrastructure</h3></div>
          <span class="panel-code" style="color: #475569; font: 700 10px ui-monospace, monospace;">AI-IA-01</span>
        </div>
        <div class="ai-facility-grid">
          <div v-for="fac in deepDossier.critical_infrastructure" :key="fac.facility_name" class="ai-facility-card glass-subpanel">
            <div class="facility-top">
              <span class="facility-type-tag">{{ fac.facility_type }}</span>
              <span class="facility-risk" :class="fac.risk_level.toLowerCase()">{{ fac.risk_level }} RISK</span>
            </div>
            <h4 style="margin: 0; font-size: 16px; color: #ffffff;">{{ fac.facility_name }}</h4>
            <div class="facility-meta">
              <span>📍 Distance: {{ fac.distance_km }} km from epicenter</span>
            </div>
            <div class="facility-action">
              <strong>Directive:</strong> {{ fac.action_required }}
            </div>
            <div class="facility-confidence" v-if="fac.confidence !== undefined" style="margin-top: 8px; display: flex; align-items: center; gap: 8px; font-size: 18px; color: #94a3b8;">
              <div style="flex: 1; background: rgba(255, 255, 255, 0.1); border-radius: 2px; height: 4px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #fbbf24, #38bdf8); height: 100%; width: 100%;" :style="{ width: `${fac.confidence}%` }"></div>
              </div>
              <span style="min-width: 30px; text-align: right;">{{ fac.confidence }}%</span>
            </div>
          </div>
        </div>
      </article>

      <!-- Vulnerable Demographics -->
      <article class="glass-panel demographics-panel" style="padding: 20px;">
        <div class="panel-heading">
          <div><span class="section-kicker">HUMAN IMPACT</span><h3 style="margin: 0; font-size: 16px; color: #f8fafc;">Vulnerable Demographics & Facilities</h3></div>
          <span class="panel-code" style="color: #475569; font: 700 10px ui-monospace, monospace;">AI-IA-02</span>
        </div>
        <div class="demographics-body">
          <div class="demo-stat-row" style="display: flex; gap: 24px; margin-bottom: 14px; flex-wrap: wrap;">
            <div class="demo-stat">
              <span class="stat-label" style="display: block; font-size: 18px; color: #94a3b8; text-transform: uppercase;">Estimated Displaced Citizens: </span>
              <strong class="stat-value" style="font-size: 16px; color: #38bdf8;">{{ deepDossier.vulnerable_demographics.estimated_displaced_citizens.toLocaleString() }}</strong>
            </div>
            <div class="demo-stat">
              <span class="stat-label" style="display: block; font-size: 18px; color: #94a3b8; text-transform: uppercase;">Special Needs Transport: </span>
              <span class="stat-desc" style="font-size: 18px; color: #cbd5e1;">{{ deepDossier.vulnerable_demographics.special_needs_assistance_required }}</span>
            </div>
          </div>
          <div class="facilities-at-risk-list" style="margin-top: 14px;">
            <strong style="color: #38bdf8; font-size: 18px; text-transform: uppercase;">High-Priority Facilities at Risk:</strong>
            <ul style="margin: 8px 0 0 16px; color: #cbd5e1; font-size: 18px;">
              <li v-for="f in deepDossier.vulnerable_demographics.facilities_at_risk" :key="f">
                {{ f }}
              </li>
            </ul>
          </div>
        </div>
      </article>
    </div>

    <div v-else-if="!isBackendMockModeEnabled" class="phase2-center-container">
      <div class="phase2-card glass-panel">
        <div class="phase2-icon">🏢</div>
        <div class="phase2-tag">AI RECONNAISSANCE PENDING</div>
        <h2 style="font-size: 22px; font-weight: 700; color: #ffffff; margin: 0 0 12px 0;">Predictive Impact Assessment</h2>
        <p style="font-size: 16px; line-height: 1.6; color: #cbd5e1; margin: 0 0 18px 0;">Launch the cognitive AI reconnaissance to generate unscripted critical infrastructure exposure, hospital vulnerabilities, and demographic displacement models.</p>
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

.ai-facility-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
  margin-top: 14px;
}

.ai-facility-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.facility-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.facility-type-tag {
  font-size: 16px;
  font-weight: 800;
  color: #38bdf8;
  background: rgba(14, 165, 233, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
}

.facility-risk {
  font-size: 16px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 4px;
}
.facility-risk.critical { color: #ef4444; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); }
.facility-risk.high { color: #f59e0b; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); }
.facility-risk.moderate { color: #38bdf8; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); }

.facility-meta {
  font-size: 18px;
  color: #94a3b8;
}

.facility-action {
  font-size: 16px;
  line-height: 1.4;
  color: #cbd5e1;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 8px;
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