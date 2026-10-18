<template>
  <div class="response-tab">
    <div class="tab-intro">
      <div>
        <h2>{{ $t('detail.tabTitles.response') }}</h2>
        <p>{{ $t('detail.tabTitles.responseDesc') }}</p>
      </div>
    </div>

    <!-- No crisis report yet: the REPORT PENDING card below is the state, and its button starts generation. -->
    <ResponsePlanPanel
      v-if="incidentId && deepDossier"
      :incident-id="incidentId"
      :incident-type="incident?.event_type ?? null"
      :incident-location="incident?.location_name ?? null"
    />

    <div v-if="deepDossier" class="deep-ai-tab-container">
      
      <!-- Tactical Briefing - Redesigned Card -->
      <div class="glass-panel-new" style="padding: 24px; margin-bottom: 20px; border-left: 4px solid var(--detail-accent);">
        <div style="display: flex; align-items: flex-start; gap: 16px;">
          <div style="font-size: 32px; flex-shrink: 0;">⚠️</div>
          <div>
            <h3 style="margin: 0 0 8px 0; color: var(--text-primary); font-size: 16px;">{{ $t('responseTab.tacticalBriefing') }}</h3>
            <p style="margin: 0; font-size: 14px; color: var(--text-secondary); line-height: 1.6;">
              {{ deepDossier.severity_assessment || $t('responseTab.situationalPending') }}
            </p>
          </div>
        </div>
      </div>

      <!-- PHASED RESPONSE TIMELINE - Redesigned -->
      <div class="glass-panel-new" style="padding: 24px; margin-bottom: 20px;">
        <div style="margin-bottom: 20px;">
          <h3 style="margin: 0 0 4px 0; color: var(--text-primary); font-size: 16px; font-weight: 700;">{{ $t('responseTab.operationalPhases') }}</h3>
          <p style="margin: 0; color: var(--text-secondary); font-size: 13px;">{{ $t('responseTab.responseTimeline') }}</p>
        </div>

        <!-- Phases Grid -->
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
          <!-- IMMEDIATE PHASE -->
          <div class="phase-card" style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 8px; padding: 16px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
              <div style="width: 28px; height: 28px; border-radius: 50%; background: rgba(239, 68, 68, 0.2); display: flex; align-items: center; justify-content: center; color: #f87171; font-weight: 700; font-size: 14px;">1</div>
              <div>
                <h4 style="margin: 0; color: #f87171; font-size: 13px; font-weight: 700; text-transform: uppercase;">{{ $t('responseTab.immediatePhase') }}</h4>
                <p style="margin: 0; color: var(--text-secondary); font-size: 11px;">{{ $t('responseTab.startNow') }}</p>
              </div>
            </div>
            <div v-if="deepDossier.immediate_actions && deepDossier.immediate_actions.length > 0" style="display: flex; flex-direction: column; gap: 8px;">
              <div v-for="(action, idx) in deepDossier.immediate_actions" :key="`imm-${idx}`" style="padding: 8px; background: rgba(0,0,0,0.2); border-radius: 4px; color: var(--text-primary); font-size: 12px; line-height: 1.4;">
                {{ action }}
              </div>
            </div>
            <div v-else style="color: var(--text-secondary); padding: 8px; font-size: 12px;">{{ $t('responseTab.noImmediate') }}</div>
          </div>

          <!-- URGENT PHASE -->
          <div class="phase-card" style="background: rgba(249, 115, 22, 0.08); border: 1px solid rgba(249, 115, 22, 0.25); border-radius: 8px; padding: 16px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
              <div style="width: 28px; height: 28px; border-radius: 50%; background: rgba(249, 115, 22, 0.2); display: flex; align-items: center; justify-content: center; color: #fb923c; font-weight: 700; font-size: 14px;">2</div>
              <div>
                <h4 style="margin: 0; color: #fb923c; font-size: 13px; font-weight: 700; text-transform: uppercase;">{{ $t('responseTab.urgentPhase') }}</h4>
                <p style="margin: 0; color: var(--text-secondary); font-size: 11px;">{{ $t('responseTab.completeBy') }}</p>
              </div>
            </div>
            <div v-if="deepDossier.high_priority_actions && deepDossier.high_priority_actions.length > 0" style="display: flex; flex-direction: column; gap: 8px;">
              <div v-for="(action, idx) in deepDossier.high_priority_actions" :key="`urg-${idx}`" style="padding: 8px; background: rgba(0,0,0,0.2); border-radius: 4px; color: var(--text-primary); font-size: 12px; line-height: 1.4;">
                {{ action }}
              </div>
            </div>
            <div v-else style="color: var(--text-secondary); padding: 8px; font-size: 12px;">{{ $t('responseTab.noUrgent') }}</div>
          </div>

          <!-- SUSTAINED PHASE -->
          <div class="phase-card" style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 8px; padding: 16px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
              <div style="width: 28px; height: 28px; border-radius: 50%; background: rgba(245, 158, 11, 0.2); display: flex; align-items: center; justify-content: center; color: #fbbf24; font-weight: 700; font-size: 14px;">3</div>
              <div>
                <h4 style="margin: 0; color: #fbbf24; font-size: 13px; font-weight: 700; text-transform: uppercase;">{{ $t('responseTab.sustainedPhase') }}</h4>
                <p style="margin: 0; color: var(--text-secondary); font-size: 11px;">{{ $t('responseTab.ongoing') }}</p>
              </div>
            </div>
            <div v-if="deepDossier.medium_priority_actions && deepDossier.medium_priority_actions.length > 0" style="display: flex; flex-direction: column; gap: 8px;">
              <div v-for="(action, idx) in deepDossier.medium_priority_actions" :key="`sus-${idx}`" style="padding: 8px; background: rgba(0,0,0,0.2); border-radius: 4px; color: var(--text-primary); font-size: 12px; line-height: 1.4;">
                {{ action }}
              </div>
            </div>
            <div v-else style="color: var(--text-secondary); padding: 8px; font-size: 12px;">{{ $t('responseTab.noSustained') }}</div>
          </div>
        </div>
      </div>

      <div class="glass-panel-new" style="padding: 24px;">
        <div style="margin-bottom: 20px;">
          <h3 style="margin: 0 0 4px 0; color: var(--text-primary); font-size: 16px; font-weight: 700;">{{ $t('responseTab.assetDeployment') }}</h3>
          <p style="margin: 0; color: var(--text-secondary); font-size: 13px;">{{ $t('responseTab.operationalLogistics') }}</p>
        </div>
        <div class="resource-matrix-table-wrapper" style="overflow-x: auto;">
          <table class="ai-resource-table" style="width: 100%; border-collapse: collapse;">
            <thead>
              <tr style="border-bottom: 2px solid #334155; text-align: left; color: var(--text-secondary); font-size: 18px;">
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">{{ $t('responseTab.colResource') }}</th>
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">{{ $t('responseTab.colQuantity') }}</th>
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">{{ $t('responseTab.colAgency') }}</th>
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">{{ $t('responseTab.colLocation') }}</th>
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">{{ $t('responseTab.colEta') }}</th>
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">{{ $t('responseTab.colPriority') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(res, idx) in deepDossier.resource_matrix" :key="idx" style="border-bottom: 1px solid var(--glass-border); font-size: 18px;">
                <td style="padding: 12px 10px; color: var(--text-primary); font-weight: 700;">{{ res.resource }}</td>
                <td style="padding: 12px 10px; color: var(--accent-cyan); font-family: ui-monospace, monospace;">{{ res.quantity ?? 'Not in report' }} {{ res.quantity != null ? res.unit_measure : '' }}</td>
                <td style="padding: 12px 10px; color: var(--text-secondary);">{{ res.assigned_agency }}</td>
                <td style="padding: 12px 10px; color: var(--text-secondary);">{{ res.deployment_location }}</td>
                <td style="padding: 12px 10px; color: #4ade80; font-family: ui-monospace, monospace;">{{ res.estimated_arrival_minutes != null ? res.estimated_arrival_minutes + ' min' : 'Not in report' }}</td>
                <td style="padding: 12px 10px;">
                  <span class="priority-tag" :class="getPriorityClass(res.priority)">
                    {{ getPriorityLabel(res.priority) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

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
import GenerationNotice from './GenerationNotice.vue'
import ResponsePlanPanel from '@/components/molecules/ResponsePlanPanel.vue'

defineProps<{
  deepDossier: any
  isAnalyzingDossier: boolean
  generationStartedAt?: number | null
  isBackendMockModeEnabled: boolean
  incidentId?: string
  incident?: any
}>()

defineEmits(['launch'])

function getPriorityClass(priority: number | string): string {
  const p = typeof priority === 'string' ? parseInt(priority) : priority
  if (p === 1) return 'priority-tag immediate'
  if (p === 2) return 'priority-tag high'
  if (p === 3) return 'priority-tag staged'
  return 'priority-tag'
}

function getPriorityLabel(priority: number | string): string {
  const p = typeof priority === 'string' ? parseInt(priority) : priority
  if (p === 1) return 'IMMEDIATE'
  if (p === 2) return 'HIGH'
  if (p === 3) return 'STAGED'
  return 'UNKNOWN'
}
</script>

<style scoped>
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