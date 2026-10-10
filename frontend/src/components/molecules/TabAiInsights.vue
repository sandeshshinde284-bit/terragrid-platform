<template>
  <div class="ai-tab">
    <div class="tab-intro">
      <div>
        <h2>AI Insights</h2>
        <p>Executive tactical summaries and high-level directives synthesized from live multi-source telemetry.</p>
      </div>
    </div>

    <!-- NEW (Live Mode): Now displays REAL AI data from aiPlan and aiInsights -->
    <div v-if="aiLoading" class="loading-state">
      <span class="loading-spinner"></span>
      <p>Loading AI analysis...</p>
    </div>
    <div v-else-if="aiError" class="error-state">
      <span class="error-icon">⚠</span>
      <p>AI analysis unavailable: {{ aiError }}</p>
    </div>
    <div v-else-if="aiPlan" class="real-ai-content">
      <!-- AI STATUS WARNINGS -->
      <div v-if="aiPlan?.is_fallback" class="status-banner offline-banner">
        <span class="banner-icon">⚠️</span>
        <div>
          <strong>AI COGNITIVE ENGINE OFFLINE</strong>
          <span>Google Vertex AI cluster unreachable. Data shown is <strong>pre-computed reference only</strong> and NOT actively tracking this incident.</span>
        </div>
      </div>
      <div v-else-if="aiPlan?.is_mock_demo" class="status-banner demo-banner">
        <span class="banner-icon">📋</span>
        <div>
          <strong>DEMONSTRATION MODE</strong>
          <span>This is <strong>sample/demo data</strong> for testing purposes. Not real incident analysis.</span>
        </div>
      </div>
      
      <div class="insights-grid">
        <!-- Left Column: Context & Guidance -->
        <div class="insights-left-col">
          <CausalChainExplanation 
            v-if="hasCausalData"
            :causalData="{ trigger_event: aiPlan.trigger_event, infrastructure_factors: aiPlan.infrastructure_factors, predicted_outcome: aiPlan.predicted_outcome, historical_reference: aiPlan.historical_reference }"
          />
          <article class="glass-panel" style="margin-bottom: 18px;">
            <div class="panel-heading">
              <div>
                <span class="section-kicker">EXECUTIVE SUMMARY</span>
                <h2 style="font-size: 18px; margin: 4px 0 0 0; color: #f8fafc; line-height: 1.4;">{{ aiPlan.country_context }}</h2>
              </div>
            </div>
            <div class="text-content-block">
              <p>{{ aiPlan.severity_assessment }}</p>
            </div>
          </article>

          <article class="glass-panel">
            <div class="panel-heading">
              <div>
                <span class="section-kicker">EVACUATION PROTOCOL</span>
                <h3 style="margin:0; font-size: 16px; color:#f8fafc;">Critical Transit Instructions</h3>
              </div>
            </div>
            <div class="text-content-block alt-block">
              <p>{{ aiPlan.evacuation_guidance }}</p>
            </div>
          </article>
        </div>

        <!-- Right Column: Immediate Actions -->
        <div class="insights-right-col">
          <article class="glass-panel action-panel" style="height: 100%;">
            <div class="panel-heading" style="margin-bottom: 24px;">
              <div>
                <span class="section-kicker">TACTICAL DIRECTIVES</span>
                <h3 style="margin:0; font-size: 16px; color:#f8fafc;">Immediate Action Plan</h3>
              </div>
              <span class="ai-chip" :class="getStatusClass()">{{ getStatusLabel() }}</span>
            </div>
            <div class="phased-timeline">
            <!-- Immediate -->
            <div class="phase-section" style="margin-bottom: 24px;">
              <div class="phase-badge" style="display: inline-block; color: #ef4444; background: rgba(239,68,68,0.15); border: 1px solid rgba(239,68,68,0.3); padding: 4px 10px; border-radius: 4px; font-weight: 800; font-size: 15px; margin-bottom: 16px; letter-spacing: 0.5px;">
                🔴 IMMEDIATE (0-2h)
              </div>
              <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 14px;">
                <li v-for="(action, index) in (aiPlan.immediate_actions || []).slice(0, 2)" :key="'imm-'+index" style="display: flex; gap: 14px; align-items: flex-start; padding-bottom: 14px; border-bottom: 1px solid #1e293b;">
                  <span style="font-family: ui-monospace, monospace; color: #ef4444; font-weight: 800; font-size: 16px; margin-top: 2px;">0{{ index + 1 }}</span>
                  <div style="color: #cbd5e1; font-size: 15px; line-height: 1.5;"><strong>{{ action }}</strong></div>
                </li>
              </ul>
            </div>
            
            <!-- Urgent -->
            <div class="phase-section" style="margin-bottom: 24px;">
              <div class="phase-badge" style="display: inline-block; color: #f97316; background: rgba(249,115,22,0.15); border: 1px solid rgba(249,115,22,0.3); padding: 4px 10px; border-radius: 4px; font-weight: 800; font-size: 15px; margin-bottom: 16px; letter-spacing: 0.5px;">
                🟠 URGENT (2-6h)
              </div>
              <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 14px;">
                <li v-for="(action, index) in (aiPlan.immediate_actions || []).slice(2, 4)" :key="'urg-'+index" style="display: flex; gap: 14px; align-items: flex-start; padding-bottom: 14px; border-bottom: 1px solid #1e293b;">
                  <span style="font-family: ui-monospace, monospace; color: #f97316; font-weight: 800; font-size: 16px; margin-top: 2px;">0{{ index + 3 }}</span>
                  <div style="color: #cbd5e1; font-size: 15px; line-height: 1.5;"><strong>{{ action }}</strong></div>
                </li>
              </ul>
            </div>
            
            <!-- Sustained -->
            <div v-if="(aiPlan.immediate_actions || []).length > 4" class="phase-section">
              <div class="phase-badge" style="display: inline-block; color: #eab308; background: rgba(234,179,8,0.15); border: 1px solid rgba(234,179,8,0.3); padding: 4px 10px; border-radius: 4px; font-weight: 800; font-size: 15px; margin-bottom: 16px; letter-spacing: 0.5px;">
                🟡 SUSTAINED (6-12h)
              </div>
              <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 14px;">
                <li v-for="(action, index) in (aiPlan.immediate_actions || []).slice(4)" :key="'sus-'+index" style="display: flex; gap: 14px; align-items: flex-start; padding-bottom: 14px; border-bottom: 1px solid #1e293b;">
                  <span style="font-family: ui-monospace, monospace; color: #eab308; font-weight: 800; font-size: 16px; margin-top: 2px;">0{{ index + 5 }}</span>
                  <div style="color: #cbd5e1; font-size: 15px; line-height: 1.5;"><strong>{{ action }}</strong></div>
                </li>
              </ul>
            </div>
          </div>
          </article>
        </div>
      </div>
    </div>
    <div v-else class="loading-state">
      <p>No AI data available</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import CausalChainExplanation from '@/components/molecules/CausalChainExplanation.vue'

const props = defineProps<{
  aiLoading: boolean
  aiError: string | null
  aiPlan: any
  deepDossier?: any
}>()

const hasCausalData = computed(() => {
  return props.aiPlan && props.aiPlan.trigger_event && props.aiPlan.infrastructure_factors && props.aiPlan.infrastructure_factors.length > 0
})

const getStatusClass = () => {
  if (props.aiPlan?.is_fallback) return 'offline'
  if (props.aiPlan?.is_mock_demo) return 'demo'
  return 'live'
}

const getStatusLabel = () => {
  if (props.aiPlan?.is_fallback) return 'OFFLINE DATA'
  if (props.aiPlan?.is_mock_demo) return 'DEMO MODE'
  return 'LIVE AI'
}
</script>

<style scoped>
.glass-panel {
  background: #0f172a;
  border: 1px solid #1e293b;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  padding: 20px;
}
.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.section-kicker {
  color: #94a3b8;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  display: block;
}
.tab-intro {
  margin-bottom: 24px;
}
.tab-intro h2 {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 8px 0;
}
.tab-intro p {
  font-size: 16px;
  color: #94a3b8;
  margin: 0;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: #cbd5e1;
}
.loading-spinner {
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #38bdf8;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}
.error-icon {
  font-size: 32px;
  margin-bottom: 12px;
  color: #ef4444;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

/* Status Banners */
.status-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 24px;
  border-radius: 6px;
  border-left: 4px solid;
}

.offline-banner {
  background: rgba(220, 38, 38, 0.15);
  border-left-color: #dc2626;
  border: 1px solid rgba(220, 38, 38, 0.5);
  color: #fecaca;
}

.offline-banner strong {
  display: block;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.demo-banner {
  background: rgba(59, 130, 246, 0.15);
  border-left-color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.5);
  color: #bfdbfe;
}

.demo-banner strong {
  display: block;
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.banner-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

.status-banner span:not(.banner-icon) {
  font-size: 13px;
  line-height: 1.5;
}

/* AI Chip Badges */
.ai-chip {
  font-size: 12px;
  font-weight: 800;
  padding: 6px 12px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.ai-chip.live {
  color: #34d399;
  background: rgba(52, 211, 153, 0.15);
  border: 1px solid rgba(52, 211, 153, 0.3);
}

.ai-chip.demo {
  color: #93c5fd;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.ai-chip.offline {
  color: #fca5a5;
  background: rgba(220, 38, 38, 0.15);
  border: 1px solid rgba(220, 38, 38, 0.3);
}

.action-list {
  list-style: none;
  padding: 0;
  margin: 16px 0 0 0;
}
.action-list li:last-child {
  border-bottom: none !important;
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}

/* New Structural Layout CSS */
.insights-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.insights-left-col {
  display: flex;
  flex-direction: column;
}
.text-content-block p {
  font-size: 18px;
  line-height: 1.7;
  color: #cbd5e1;
  margin: 12px 0 0 0;
  max-width: 85ch;
}
.action-panel {
  border-top: 3px solid #0ea5e9 !important;
}
.action-item {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #1e293b;
  align-items: flex-start;
}
.action-number-wrapper {
  background: rgba(14, 165, 233, 0.1);
  border: 1px solid rgba(14, 165, 233, 0.3);
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}
.action-number {
  font-family: ui-monospace, monospace;
  color: #38bdf8;
  font-weight: 800;
  font-size: 16px;
}
.action-text {
  color: #f1f5f9;
  font-size: 18px;
  line-height: 1.5;
  padding-top: 6px;
}

@media (max-width: 900px) {
  .insights-grid {
    grid-template-columns: 1fr;
  }
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