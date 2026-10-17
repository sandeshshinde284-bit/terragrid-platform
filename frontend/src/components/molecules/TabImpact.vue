<template>
  <div class="impact-tab">
    <div class="tab-intro">
      <div>
        <h2>{{ $t('detail.tabTitles.impact') }}</h2>
        <p>{{ $t('detail.tabTitles.impactDesc') }}</p>
      </div>
    </div>

    <div v-if="deepDossier" class="deep-ai-tab-container">
      
      <!-- Critical Infrastructure Table -->
      <article class="glass-panel infrastructure-panel" style="padding: 20px; margin-bottom: 20px;">
        <div class="panel-heading">
          <div><span class="section-kicker">{{ $t('impactTab.vulnerabilityMatrix') }}</span><h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">{{ $t('impactTab.exposedInfrastructure') }}</h3></div>
          <span class="panel-code" style="color: #475569; font: 700 10px ui-monospace, monospace;">AI-IA-01</span>
        </div>
        <div class="ai-facility-grid">
          <div v-for="fac in facilityRows" :key="fac.facility_name" class="ai-facility-card glass-subpanel" :class="{ 'ai-suggested': !fac.fromOsm }">
            <div class="facility-top">
              <span class="facility-type-tag">{{ fac.facility_type }}</span>
              <span class="facility-risk" :class="fac.risk_level.toLowerCase()">{{ fac.risk_level }} Risk</span>
            </div>
            <span class="facility-source" :class="fac.fromOsm ? 'osm' : 'ai'">{{ fac.fromOsm ? $t('impactTab.sourceOsm') : $t('impactTab.sourceAi') }}</span>
            <h4 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 700; color: var(--text-primary); line-height: 1.3;">{{ fac.facility_name }}</h4>
            <div class="facility-meta">
              <span>📍 {{ $t('impactTab.distance') }} {{ fac.distance ?? '—' }} km {{ $t('impactTab.fromEpicenter') }}</span>
            </div>
            <div class="facility-action">
              <strong>{{ $t('impactTab.directive') }}</strong> {{ fac.action_required }}
            </div>
            <div class="facility-confidence" v-if="fac.confidence !== undefined" style="margin-top: 8px; display: flex; align-items: center; gap: 8px; font-size: 18px; color: var(--text-secondary);">
             <div style="flex: 1; background: rgba(255, 255, 255, 0.08); border-radius: 3px; height: 5px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #fbbf24, #38bdf8); height: 100%; width: 100%; border-radius: 3px;" :style="{ width: `${fac.confidence}%` }"></div>
              </div>
              <span style="min-width: 30px; text-align: right;">{{ fac.confidence }}%</span>
            </div>
          </div>
        </div>
      </article>

      <!-- Vulnerable Demographics -->
      <article class="glass-panel demographics-panel" style="padding: 20px;">
        <div class="panel-heading">
          <div><span class="section-kicker">{{ $t('impactTab.humanImpact') }}</span><h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">{{ $t('impactTab.vulnerableDemographics') }}</h3></div>
          <span class="panel-code" style="color: #475569; font: 700 10px ui-monospace, monospace;">AI-IA-02</span>
        </div>
        <div class="demographics-body">
          <div class="demo-stat-row" style="display: flex; gap: 24px; margin-bottom: 14px; flex-wrap: wrap;">
            <div class="demo-stat">
              <span class="stat-label" style="display: block; font-size: 13px; color: rgba(255,255,255,0.65); text-transform: none; font-weight: 600;">{{ $t('impactTab.estDisplaced') }} </span>
              <strong class="stat-value" style="font-size: 20px; color: var(--accent-cyan); font-weight: 700; margin-top: 4px; display: block;">{{ deepDossier.vulnerable_demographics.estimated_displaced_citizens.toLocaleString() }}</strong>
            </div>
            <div class="demo-stat">
              <span class="stat-label" style="display: block; font-size: 13px; color: rgba(255,255,255,0.65); text-transform: none; font-weight: 600;">{{ $t('impactTab.specialNeeds') }} </span>
              <span class="stat-desc" style="font-size: 16px; color: rgba(255,255,255,0.9); margin-top: 4px; display: block;">{{ deepDossier.vulnerable_demographics.special_needs_assistance_required }}</span>
            </div>
          </div>
          <div class="facilities-at-risk-list" style="margin-top: 14px;">
            <strong style="color: var(--accent-cyan); font-size: 14px; text-transform: none; font-weight: 600;">{{ $t('impactTab.highPriorityAtRisk') }}</strong>
            <ul style="margin: 8px 0 0 16px; color: var(--text-secondary); font-size: 18px;">
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
        <div class="phase2-tag">{{ $t('impactTab.aiPending') }}</div>
        <h2 style="font-size: 22px; font-weight: 700; color: var(--text-primary); margin: 0 0 12px 0;">{{ $t('impactTab.predictiveImpact') }}</h2>
        <p style="font-size: 16px; line-height: 1.6; color: var(--text-secondary); margin: 0 0 18px 0;">{{ $t('impactTab.impactDesc') }}</p>
        <button class="primary-button recon-trigger-btn" @click="$emit('launch')" :disabled="isAnalyzingDossier">
          <span v-if="isAnalyzingDossier" class="spinner">⟳</span>
          {{ isAnalyzingDossier ? 'Synthesizing...' : '⚡ Launch Tactical AI Reconnaissance' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  deepDossier: any
  isAnalyzingDossier: boolean
  isBackendMockModeEnabled: boolean
}>()

defineEmits(['launch'])

const normName = (s: string) => (s || '').trim().toLowerCase()

// Facilities the backend pulled from OpenStreetMap. Anything else in
// critical_infrastructure is the model's own suggestion and is labelled so.
const osmByName = computed(() => {
  const m = new Map<string, any>()
  for (const s of props.deepDossier?.osm_sources || []) m.set(normName(s.name), s)
  return m
})

const facilityRows = computed(() =>
  (props.deepDossier?.critical_infrastructure || []).map((fac: any) => {
    const osm = osmByName.value.get(normName(fac.facility_name))
    return {
      ...fac,
      fromOsm: !!osm,
      // Use the measured OSM distance when we have one.
      distance: osm?.distance_km ?? fac.distance_km ?? null,
    }
  })
)
</script>

<style scoped>
.impact-tab {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.tab-intro {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  margin-bottom: 24px;
}

.tab-intro h2 {
  margin: 0;
  font-size: 28px;
  color: var(--text-primary);
  font-weight: 700;
}

.tab-intro p {
  margin: 8px 0 0 0;
  color: var(--text-secondary);
  font-size: 16px;
}

.glass-panel {
  background: var(--bg-panel);
  border: 1px solid var(--glass-border);
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
  color: var(--text-secondary);
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


.facility-source {
  align-self: flex-start;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.03em;
}
.facility-source.osm { color: #4ade80; background: rgba(74, 222, 128, 0.12); border: 1px solid rgba(74, 222, 128, 0.3); }
.facility-source.ai { color: #fbbf24; background: rgba(251, 191, 36, 0.12); border: 1px dashed rgba(251, 191, 36, 0.5); }
.ai-facility-card.ai-suggested { opacity: 0.9; border-style: dashed; }

.ai-facility-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 280px;
  transition: all 0.2s ease;
}

.ai-facility-card:hover {
  background: var(--bg-overlay);
  border-color: rgba(56, 189, 248, 0.3);
  box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15);
  transform: translateY(-2px);
}

.facility-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 8px;
  flex-wrap: nowrap;
  min-width: 0;
}

.facility-type-tag {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--accent-cyan);
  background: rgba(14, 165, 233, 0.2);
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid rgba(14, 165, 233, 0.3);
  white-space: nowrap;
  flex-shrink: 0;
}

.facility-risk {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid;
  white-space: nowrap;
  flex-shrink: 0;
}

.facility-risk.critical { 
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.4);
}

.facility-risk.high { 
  color: #fcd34d;
  background: rgba(245, 158, 11, 0.2);
  border: 1px solid rgba(245, 158, 11, 0.4);
}

.facility-risk.moderate { 
  color: #93c5fd;
  background: rgba(56, 189, 248, 0.2);
  border: 1px solid rgba(56, 189, 248, 0.4);
}
.facility-meta {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.facility-action {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 10px;
  margin-top: 10px;
}

.facility-action strong {
  color: var(--text-primary);
  font-weight: 700;
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
  color: var(--accent-cyan);
  border: 1px solid rgba(14, 165, 233, 0.4);
  letter-spacing: 1px;
  margin-bottom: 16px;
}
.primary-button {
  background: #0284c7;
  border: 1px solid #0284c7;
  color: var(--text-primary);
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
  
  /* Facility grid responsive */
  .ai-facility-grid {
    grid-template-columns: 1fr !important;
  }
  
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