<template>
  <div class="response-tab">
    <div class="tab-intro">
      <div>
        <h2>Resource Deployment</h2>
        <p>Operational logistics and multi-agency resource allocations calculated for this sector.</p>
      </div>
    </div>

    <div v-if="deepDossier" class="deep-ai-tab-container">
      
      <!-- Tactical Briefing -->
      <article class="glass-panel" style="padding: 16px; margin-bottom: 20px; border-left: 4px solid var(--detail-accent);">
        <p style="margin: 0; font-size: 18px; color: #f8fafc; line-height: 1.6;">
          <strong style="color: var(--detail-accent); font-family: ui-monospace, monospace; margin-right: 8px;">TACTICAL BRIEFING:</strong> 
          {{ deepDossier.situational_assessment }}
        </p>
      </article>

      <!-- PHASED RESPONSE TIMELINE -->
      <article class="glass-panel" style="padding: 20px; margin-bottom: 20px;">
        <div class="panel-heading">
          <div><span class="section-kicker">OPERATIONAL PHASES</span><h3 style="margin:0; font-size: 16px; color:#f8fafc;">Response Timeline by Action Urgency</h3></div>
          <span class="panel-code" style="color: #475569; font: 700 10px ui-monospace, monospace;">PHASE-RESP-01</span>
        </div>

        <!-- IMMEDIATE PHASE -->
        <div class="phase-block immediate" style="margin-bottom: 16px;">
          <div class="phase-badge immediate">🔴 IMMEDIATE (0-2h)</div>
          <div class="phase-actions">
            <div v-if="deepDossier.immediate_actions && deepDossier.immediate_actions.length > 0">
              <div v-for="(action, idx) in deepDossier.immediate_actions" :key="`imm-${idx}`" class="action-item">
                <span class="action-priority">P1</span>
                <span class="action-text">{{ action }}</span>
                <span class="action-deadline">START NOW</span>
              </div>
            </div>
            <div v-else style="color: #94a3b8; padding: 8px; font-size: 16px;">No immediate actions identified</div>
          </div>
        </div>

        <!-- URGENT PHASE -->
        <div class="phase-block urgent" style="margin-bottom: 16px;">
          <div class="phase-badge urgent">🟠 URGENT (2-6h)</div>
          <div class="phase-actions">
            <div v-if="deepDossier.high_priority_actions && deepDossier.high_priority_actions.length > 0">
              <div v-for="(action, idx) in deepDossier.high_priority_actions" :key="`urg-${idx}`" class="action-item">
                <span class="action-priority">P2</span>
                <span class="action-text">{{ action }}</span>
                <span class="action-deadline">Complete by T+4h</span>
              </div>
            </div>
            <div v-else style="color: #94a3b8; padding: 8px; font-size: 16px;">No urgent actions identified</div>
          </div>
        </div>

        <!-- SUSTAINED PHASE -->
        <div class="phase-block sustained">
          <div class="phase-badge sustained">🟡 SUSTAINED (6-12h)</div>
          <div class="phase-actions">
            <div v-if="deepDossier.medium_priority_actions && deepDossier.medium_priority_actions.length > 0">
              <div v-for="(action, idx) in deepDossier.medium_priority_actions" :key="`sus-${idx}`" class="action-item">
                <span class="action-priority">P3</span>
                <span class="action-text">{{ action }}</span>
                <span class="action-deadline">Ongoing</span>
              </div>
            </div>
            <div v-else style="color: #94a3b8; padding: 8px; font-size: 16px;">No sustained actions identified</div>
          </div>
        </div>
      </article>

      <article class="glass-panel" style="padding: 20px;">
        <div class="panel-heading">
          <div><span class="section-kicker">ASSET DEPLOYMENT</span><h3 style="margin:0; font-size: 16px; color:#f8fafc;">Operational Logistics Matrix</h3></div>
          <span class="panel-code" style="color: #475569; font: 700 10px ui-monospace, monospace;">LOG-ASSET-01</span>
        </div>
        <div class="resource-matrix-table-wrapper" style="overflow-x: auto;">
          <table class="ai-resource-table" style="width: 100%; border-collapse: collapse;">
            <thead>
              <tr style="border-bottom: 2px solid #334155; text-align: left; color: #94a3b8; font-size: 18px;">
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">Resource Asset</th>
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">Required Quantity</th>
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">Assigned Agency</th>
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">Deployment Location</th>
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">ETA</th>
                <th style="padding: 12px 10px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase;">Priority</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(res, idx) in deepDossier.resource_matrix" :key="idx" style="border-bottom: 1px solid #1e293b; font-size: 18px;">
                <td style="padding: 12px 10px; color: #ffffff; font-weight: 700;">{{ res.resource }}</td>
                <td style="padding: 12px 10px; color: #38bdf8; font-family: ui-monospace, monospace;">{{ res.quantity }} {{ res.unit_measure }}</td>
                <td style="padding: 12px 10px; color: #cbd5e1;">{{ res.assigned_agency }}</td>
                <td style="padding: 12px 10px; color: #cbd5e1;">{{ res.deployment_location }}</td>
                <td style="padding: 12px 10px; color: #4ade80; font-family: ui-monospace, monospace;">{{ res.estimated_arrival_minutes }} min</td>
                <td style="padding: 12px 10px;">
                  <span class="priority-tag" :class="getPriorityClass(res.priority)">
                    {{ getPriorityLabel(res.priority) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          <span class="provenance-tag">[Logistics: TerraGrid Tactical Engine | Confidence Scored]</span>
        </div>
      </article>
    </div>

    <div v-else-if="!isBackendMockModeEnabled" class="phase2-center-container">
      <div class="phase2-card glass-panel">
        <div class="phase2-icon">🚑</div>
        <div class="phase2-tag">REPORT PENDING</div>
        <h2 style="font-size:20px; font-weight:700; color:#fff; margin-bottom:12px;">Multi-Agency Resource Matrix</h2>
        <p style="color:#cbd5e1; font-size: 16px; margin-bottom:18px;">Generate specialized equipment counts, first-responder squad deployment, and medical logistics matrices.</p>
        <button class="primary-button recon-trigger-btn" @click="$emit('launch')" :disabled="isAnalyzingDossier">
          <span v-if="isAnalyzingDossier" class="spinner">⟳</span>
          {{ isAnalyzingDossier ? 'Synthesizing...' : '⚡ Generate Full Crisis Report' }}
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
  background: rgba(51, 65, 85, 0.4);
  border-radius: 4px;
  font-size: 16px;
  color: #cbd5e1;
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
  color: #94a3b8;
  white-space: nowrap;
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