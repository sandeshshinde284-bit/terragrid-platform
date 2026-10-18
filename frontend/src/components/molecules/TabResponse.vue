<template>
  <div class="response-tab">
    <div class="tab-intro">
      <div>
        <h2>{{ $t('detail.tabTitles.response') }}</h2>
        <p>{{ $t('detail.tabTitles.responseDesc') }}</p>
      </div>
    </div>

    <!-- Preparedness Context from PREPARE phase -->
    <PreparednessContextCard v-if="incidentId" />

    <!-- No crisis report yet: the REPORT PENDING card below is the state, and its button starts generation. -->
    <ResponsePlanPanel
      v-if="incidentId && deepDossier"
      :incident-id="incidentId"
      :incident-type="incident?.event_type ?? null"
      :incident-location="incident?.location_name ?? null"
    />

    <!-- Supplemental AI context: available on the Response tab, collapsed by default so
         the officer's plan/review/summary remains the primary workspace. -->
    <section v-if="deepDossier" class="response-context">
      <button class="context-toggle" type="button" :aria-expanded="showContext" @click="showContext = !showContext">
        <span class="context-icon">◈</span>
        <span class="context-heading">
          <strong>AI Situation Brief & Suggested Priorities</strong>
          <small>Supporting context from the crisis report · {{ totalSuggestedActions }} suggested actions · Not yet approved tasks</small>
        </span>
        <span class="context-toggle-label">{{ showContext ? 'Hide details' : 'View details' }} {{ showContext ? '▴' : '▾' }}</span>
      </button>
      <div v-if="showContext" class="context-body">
        <div class="context-brief">
          <div class="context-title"><span>⚠</span> Situation assessment <span class="context-ai-label">AI-generated · verify before action</span></div>
          <p>{{ deepDossier.severity_assessment || $t('responseTab.situationalPending') }}</p>
        </div>
        <div class="context-priorities-header">
          <div><h3>Suggested response priorities</h3><p>Grouped by report urgency, not fixed operational deadlines.</p></div>
          <span class="context-count">{{ totalSuggestedActions }} suggestions</span>
        </div>
        <div v-if="totalSuggestedActions" class="context-priority-grid">
          <div v-for="group in populatedActionGroups" :key="group.key" class="context-priority-card" :class="group.key">
            <div class="priority-card-title"><span class="priority-dot"></span>{{ group.label }} <span class="priority-number">{{ group.actions.length }}</span></div>
            <ul><li v-for="(action, idx) in group.actions" :key="idx">{{ action }}</li></ul>
          </div>
        </div>
        <p v-else class="context-empty">No response actions were included in the current crisis report.</p>
        <p class="context-disclaimer">These are report suggestions, not approved response tasks. Use Create Response Plan and Review & Approve above to record officer decisions.</p>
      </div>
    </section>

    <div v-else-if="isAnalyzingDossier" class="deep-ai-tab-container">
      
      <!-- Status Banner at Top -->
      <div class="status-banner" style="margin-bottom: 20px; padding: 16px; background: rgba(14, 165, 233, 0.1); border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 8px;">
        <GenerationNotice variant="full" :startedAt="generationStartedAt ?? null" />
      </div>

    </div>

    <!-- INITIAL STATE: No report generated yet -->
    <div v-else-if="!isBackendMockModeEnabled" class="phase2-center-container">
      <div class="phase2-card glass-panel">
        <div class="phase2-icon">🚑</div>
        <div class="phase2-tag">REPORT PENDING</div>
        <h2 style="font-size:20px; font-weight:700; color: var(--text-primary); margin-bottom:12px;">Multi-Agency Resource Matrix</h2>
        <p style="color: var(--text-secondary); font-size: 16px; margin-bottom:18px;">Generate specialized equipment counts, first-responder squad deployment, and medical logistics matrices.</p>
        <button v-if="!isAnalyzingDossier" class="primary-button recon-trigger-btn" @click="$emit('launch')">
          {{ '⚡ Generate Full Crisis Report' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import GenerationNotice from './GenerationNotice.vue'
import ResponsePlanPanel from '@/components/molecules/ResponsePlanPanel.vue'
import PreparednessContextCard from '@/components/molecules/PreparednessContextCard.vue'

defineEmits(['launch'])

const props = defineProps<{
  deepDossier: any
  isAnalyzingDossier: boolean
  generationStartedAt?: number | null
  isBackendMockModeEnabled: boolean
  incidentId?: string
  incident?: any
}>()

const showContext = ref(false)
const populatedActionGroups = computed(() => [
  { key: 'immediate', label: 'IMMEDIATE', actions: props.deepDossier?.immediate_actions ?? [] },
  { key: 'high', label: 'HIGH', actions: props.deepDossier?.high_priority_actions ?? [] },
  { key: 'staged', label: 'STAGED', actions: props.deepDossier?.medium_priority_actions ?? [] },
].filter(group => Array.isArray(group.actions) && group.actions.length > 0))
const totalSuggestedActions = computed(() => populatedActionGroups.value.reduce((sum, group) => sum + group.actions.length, 0))
</script>

<style scoped>
/* Compact, on-demand AI context below the operational workflow */
.response-context { margin: 20px 0; border: 1px solid rgba(34, 211, 238, .22); border-radius: 12px; background: linear-gradient(120deg, rgba(6, 30, 50, .95), rgba(10, 20, 34, .95)); overflow: hidden; }
.context-toggle { width: 100%; padding: 17px 20px; background: transparent; border: 0; color: #e5f5ff; display: flex; align-items: center; gap: 14px; cursor: pointer; text-align: left; }
.context-toggle:hover { background: rgba(14, 165, 233, .07); }
.context-icon { font-size: 24px; color: #22d3ee; }
.context-heading { display: flex; flex: 1; flex-direction: column; gap: 5px; }
.context-heading strong { font-size: 15px; }
.context-heading small { color: #9fb7c9; font-size: 12px; }
.context-toggle-label { color: #38bdf8; font-size: 12px; white-space: nowrap; }
.context-body { padding: 0 20px 20px; }
.context-brief { padding: 16px; background: rgba(13, 39, 59, .75); border: 1px solid rgba(56, 189, 248, .15); border-radius: 9px; }
.context-title { font-size: 14px; font-weight: 700; color: #e7f6ff; display: flex; align-items: center; gap: 9px; flex-wrap: wrap; }
.context-title > span:first-child { color: #fbbf24; }
.context-ai-label { color: #9cb5c8; font-size: 11px; font-weight: 400; }
.context-brief p { font-size: 13px; line-height: 1.65; color: #c4d8e7; margin: 9px 0 0; }
.context-priorities-header { display: flex; justify-content: space-between; align-items: center; margin: 20px 0 12px; gap: 12px; }
.context-priorities-header h3 { font-size: 15px; margin: 0 0 4px; color: #e7f6ff; }
.context-priorities-header p { font-size: 12px; color: #91a9bc; margin: 0; }
.context-count { color: #7dd3fc; font-size: 12px; white-space: nowrap; }
.context-priority-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
.context-priority-card { padding: 15px; border-radius: 9px; border: 1px solid rgba(148, 163, 184, .2); background: rgba(15, 23, 42, .65); }
.context-priority-card.immediate { border-color: rgba(248, 113, 113, .35); }
.context-priority-card.high { border-color: rgba(251, 146, 60, .35); }
.context-priority-card.staged { border-color: rgba(251, 191, 36, .35); }
.priority-card-title { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 700; color: #dcebf5; }
.priority-dot { width: 8px; height: 8px; border-radius: 50%; background: #fbbf24; }
.immediate .priority-dot { background: #f87171; }
.high .priority-dot { background: #fb923c; }
.priority-number { margin-left: auto; color: #a7bfd2; }
.context-priority-card ul { padding-left: 18px; margin: 12px 0 0; }
.context-priority-card li { color: #cbddeb; font-size: 12px; line-height: 1.6; margin: 0 0 8px; }
.context-disclaimer, .context-empty { font-size: 12px; color: #95b1c5; margin: 15px 0 0; line-height: 1.5; }
@media (max-width: 640px) { .context-toggle { padding: 14px; } .context-body { padding: 0 14px 14px; } .context-toggle-label { font-size: 11px; } }

.ai-review-banner { margin-bottom: 20px; padding: 12px 16px; border-radius: 8px; font-size: 14px; color: #fde68a; background: rgba(251,191,36,0.1); border: 1px solid rgba(251,191,36,0.35); line-height: 1.5; }
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
.priority-tag {
  font-family: ui-monospace, monospace;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 700;
  font-size: 18px;
}
.priority-tag.immediate { background: #7f1d1d; color: #fca5a5; }
.priority-tag.high { background: #78350f; color: #fdba74; }
.priority-tag.staged { background: #1e3a8a; color: #93c5fd; }
.provenance-tag {
  display: block;
  font-family: ui-monospace, monospace;
  font-size: 16px;
  color: #475569;
  text-transform: uppercase;
  margin-top: 12px;
  text-align: right;
}
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

/* PHASED TIMELINE STYLES */
.phase-block {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px;
  padding: 16px;
  backdrop-filter: blur(4px);
}

.phase-badge {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  padding: 8px 12px;
  border-radius: 4px;
  width: fit-content;
  display: inline-block;
}

.phase-badge.immediate {
  background: rgba(239, 68, 68, 0.15);
  color: #fb7185;
  border-left: 3px solid #fb7185;
}

.phase-badge.urgent {
  background: rgba(249, 115, 22, 0.15);
  color: #fb923c;
  border-left: 3px solid #fb923c;
}

.phase-badge.sustained {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border-left: 3px solid #fbbf24;
}

.phase-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--bg-subtle);
  border-radius: 4px;
  font-size: 16px;
  color: var(--text-secondary);
}

.action-priority {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 600;
  min-width: 28px;
  text-align: center;
}

.action-text {
  flex: 1;
}

.action-deadline {
  font-size: 16px;
  color: var(--text-secondary);
  white-space: nowrap;
}

/* SKELETON LOADING STYLES */
.loading-state {
  opacity: 0.85;
  pointer-events: none;
}

.skeleton-section {
  pointer-events: auto;
}

.skeleton-line {
  height: 16px;
  background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  margin-bottom: 8px;
}

.skeleton-line.skeleton-sm {
  height: 14px;
  width: 30%;
}

.skeleton-line.skeleton-md {
  height: 18px;
  width: 60%;
}

.skeleton-line.skeleton-lg {
  height: 20px;
  width: 80%;
}

.skeleton-line.skeleton-xs {
  height: 12px;
  width: 40%;
}

.skeleton-table {
  width: 100%;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Workflow Steps Styling */
.workflow-steps-loading {
  margin-bottom: 28px;
  padding: 20px;
  background: var(--bg-panel);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--glass-border);
}

.workflow-step:last-child {
  border-bottom: none;
  padding-bottom: 0;
  padding-top: 16px;
}

.step-badge {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
  border: 2px solid rgba(59, 130, 246, 0.3);
  flex-shrink: 0;
}

.step-badge.active {
  background: rgba(14, 165, 233, 0.2);
  color: var(--accent-cyan);
  border-color: rgba(14, 165, 233, 0.4);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.step-label {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.step-desc {
  font-size: 14px;
  color: var(--text-secondary);
}

.status-banner {
  margin-bottom: 20px;
  padding: 16px;
  background: rgba(14, 165, 233, 0.1);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 8px;
  color: var(--accent-cyan);
  font-size: 16px;
  font-weight: 500;
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