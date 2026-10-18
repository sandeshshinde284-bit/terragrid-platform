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
      
      <!-- Tactical Briefing -->
      <article class="glass-panel" style="padding: 16px; margin-bottom: 20px; border-left: 4px solid var(--detail-accent);">
        <p style="margin: 0; font-size: 18px; color: var(--text-primary); line-height: 1.6;">
          <strong style="color: var(--detail-accent); font-family: ui-monospace, monospace; margin-right: 8px;">{{ $t('responseTab.tacticalBriefing') }}</strong>
          {{ deepDossier.severity_assessment || $t('responseTab.situationalPending') }}
        </p>
      </article>

      <!-- PHASED RESPONSE TIMELINE -->
      <article class="glass-panel" style="padding: 20px; margin-bottom: 20px;">
        <div class="panel-heading">
          <div><span class="section-kicker">{{ $t('responseTab.operationalPhases') }}</span><h3 style="margin:0; font-size: 16px; color: var(--text-primary);">{{ $t('responseTab.responseTimeline') }}</h3></div>
          <span class="panel-code" style="color: #475569; font: 700 10px ui-monospace, monospace;">PHASE-RESP-01</span>
        </div>

        <!-- IMMEDIATE PHASE -->
        <div class="phase-block immediate" style="margin-bottom: 16px;">
          <div class="phase-badge immediate">{{ $t('responseTab.immediatePhase') }}</div>
          <div class="phase-actions">
            <div v-if="deepDossier.immediate_actions && deepDossier.immediate_actions.length > 0">
              <div v-for="(action, idx) in deepDossier.immediate_actions" :key="`imm-${idx}`" class="action-item">
                <span class="action-priority">P1</span>
                <span class="action-text">{{ action }}</span>
                <span class="action-deadline">{{ $t('responseTab.startNow') }}</span>
              </div>
            </div>
            <div v-else style="color: var(--text-secondary); padding: 8px; font-size: 16px;">{{ $t('responseTab.noImmediate') }}</div>
          </div>
        </div>

        <!-- URGENT PHASE -->
        <div class="phase-block urgent" style="margin-bottom: 16px;">
          <div class="phase-badge urgent">{{ $t('responseTab.urgentPhase') }}</div>
          <div class="phase-actions">
            <div v-if="deepDossier.high_priority_actions && deepDossier.high_priority_actions.length > 0">
              <div v-for="(action, idx) in deepDossier.high_priority_actions" :key="`urg-${idx}`" class="action-item">
                <span class="action-priority">P2</span>
                <span class="action-text">{{ action }}</span>
                <span class="action-deadline">{{ $t('responseTab.completeBy') }}</span>
              </div>
            </div>
            <div v-else style="color: var(--text-secondary); padding: 8px; font-size: 16px;">{{ $t('responseTab.noUrgent') }}</div>
          </div>
        </div>

        <!-- SUSTAINED PHASE -->
        <div class="phase-block sustained">
          <div class="phase-badge sustained">{{ $t('responseTab.sustainedPhase') }}</div>
          <div class="phase-actions">
            <div v-if="deepDossier.medium_priority_actions && deepDossier.medium_priority_actions.length > 0">
              <div v-for="(action, idx) in deepDossier.medium_priority_actions" :key="`sus-${idx}`" class="action-item">
                <span class="action-priority">P3</span>
                <span class="action-text">{{ action }}</span>
                <span class="action-deadline">{{ $t('responseTab.ongoing') }}</span>
              </div>
            </div>
            <div v-else style="color: var(--text-secondary); padding: 8px; font-size: 16px;">{{ $t('responseTab.noSustained') }}</div>
          </div>
        </div>
      </article>

      <article class="glass-panel" style="padding: 20px;">
        <div class="panel-heading">
          <div><span class="section-kicker">{{ $t('responseTab.assetDeployment') }}</span><h3 style="margin:0; font-size: 16px; color: var(--text-primary);">{{ $t('responseTab.operationalLogistics') }}</h3></div>
          <span class="panel-code" style="color: #475569; font: 700 10px ui-monospace, monospace;">LOG-ASSET-01</span>
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
          <span class="provenance-tag">[Logistics: TerraGrid Tactical Engine | Confidence Scored]</span>
        </div>
      </article>
    </div>

    <div v-else-if="isAnalyzingDossier" class="deep-ai-tab-container">
      
      <!-- Status Banner at Top -->
      <div class="status-banner" style="margin-bottom: 20px; padding: 16px; background: rgba(14, 165, 233, 0.1); border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 8px;">
        <GenerationNotice variant="full" :startedAt="generationStartedAt ?? null" />
      </div>

      <!-- RESPONSE OPERATIONS SECTION (matching mock) -->
      <article class="glass-panel" style="padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px;">
          <div>
            <h2 style="font-size: 20px; font-weight: 700; color: var(--text-primary); margin: 0 0 4px 0;">Response Operations</h2>
            <p style="font-size: 16px; color: var(--text-secondary); margin: 0;">Create a response plan from AI recommendations, review and approve actions, and track execution.</p>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">Linked to Crisis Report</div>
            <div style="font-size: 14px; color: #0284c7; font-weight: 600;">Not generated yet</div>
            <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">Waiting for AI crisis report</div>
          </div>
        </div>

        <!-- Workflow Progress Steps -->
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
          <div style="display: flex; align-items: center; gap: 8px; padding: 12px; background: rgba(14, 165, 233, 0.1); border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 6px;">
            <div style="width: 36px; height: 36px; background: var(--accent-cyan); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #0f172a; flex-shrink: 0;">1</div>
            <div>
              <div style="font-size: 13px; font-weight: 600; color: var(--text-primary);">Plan & Review</div>
              <div style="font-size: 12px; color: var(--text-secondary);">Create and review plan</div>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px; padding: 12px; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 6px;">
            <div style="width: 36px; height: 36px; background: rgba(59, 130, 246, 0.3); border: 2px solid rgba(59, 130, 246, 0.5); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #3b82f6; flex-shrink: 0;">2</div>
            <div>
              <div style="font-size: 13px; font-weight: 600; color: var(--text-primary);">Approve Plan</div>
              <div style="font-size: 12px; color: var(--text-secondary);">Officer decisions</div>
            </div>
          </div>
          <!-- <div style="display: flex; align-items: center; gap: 8px; padding: 12px; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 6px;">
            <div style="width: 36px; height: 36px; background: rgba(59, 130, 246, 0.3); border: 2px solid rgba(59, 130, 246, 0.5); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #3b82f6; flex-shrink: 0;">3</div>
            <div>
              <div style="font-size: 13px; font-weight: 600; color: var(--text-primary);">Active Tasks</div>
              <div style="font-size: 12px; color: var(--text-secondary);">Track progress</div>
            </div>
          </div> -->
          <div style="display: flex; align-items: center; gap: 8px; padding: 12px; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 6px;">
            <div style="width: 36px; height: 36px; background: rgba(59, 130, 246, 0.3); border: 2px solid rgba(59, 130, 246, 0.5); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #3b82f6; flex-shrink: 0;">4</div>
            <div>
              <div style="font-size: 13px; font-weight: 600; color: var(--text-primary);">Plan Summary</div>
              <div style="font-size: 12px; color: var(--text-secondary);">View outcomes</div>
            </div>
          </div>
        </div>

        <!-- AI Recommendations Available Banner (Yellow) -->
        <div style="margin-bottom: 20px; padding: 16px; background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 6px; display: flex; align-items: center; gap: 12px;">
          <div style="font-size: 24px;">💡</div>
          <div style="flex: 1;">
            <div style="font-size: 14px; font-weight: 600; color: #fbbf24;">AI Recommendations Available</div>
            <div style="font-size: 13px; color: var(--text-secondary); margin-top: 2px;">Generating specialized recommendations based on crisis report...</div>
          </div>
          <button style="background: #0284c7; border: 1px solid #0284c7; color: var(--text-primary); border-radius: 4px; padding: 8px 16px; font-size: 14px; font-weight: 600; cursor: pointer;">Create Response Plan</button>
        </div>

        <!-- Recommendations Summary Stats Section Header -->
        <div style="margin-bottom: 16px;">
          <h3 style="font-size: 16px; font-weight: 600; color: var(--text-primary); margin: 0;">Recommendations Summary</h3>
        </div>

        <!-- Recommendations Summary Stats (4 Cards with Icons) -->
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
          <!-- Total AI Recommendations (Blue) -->
          <div style="padding: 16px; background: rgba(14, 165, 233, 0.08); border: 1px solid rgba(14, 165, 233, 0.2); border-radius: 8px; display: flex; align-items: flex-start; gap: 12px;">
            <div style="font-size: 28px; min-width: 40px; margin-top: 4px;">📋</div>
            <div style="flex: 1;">
              <div style="font-size: 28px; font-weight: 700; color: #0284c7; line-height: 1;">5</div>
              <div style="font-size: 13px; color: var(--text-secondary); margin-top: 6px; line-height: 1.3;">Total AI recommendations<br>From crisis report v3</div>
            </div>
          </div>

          <!-- Selected for Plan (Green) -->
          <div style="padding: 16px; background: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.2); border-radius: 8px; display: flex; align-items: flex-start; gap: 12px;">
            <div style="font-size: 28px; min-width: 40px; margin-top: 4px; display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; background: rgba(34, 197, 94, 0.2); border-radius: 50%; color: #22c55e;">✓</div>
            <div style="flex: 1;">
              <div style="font-size: 28px; font-weight: 700; color: #22c55e; line-height: 1;">0</div>
              <div style="font-size: 13px; color: var(--text-secondary); margin-top: 6px; line-height: 1.3;">Selected for plan<br>Not yet selected</div>
            </div>
          </div>

          <!-- Converted to Tasks (Blue) -->
          <div style="padding: 16px; background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 8px; display: flex; align-items: flex-start; gap: 12px;">
            <div style="font-size: 28px; min-width: 40px; margin-top: 4px; display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; background: rgba(59, 130, 246, 0.2); border-radius: 50%; color: #3b82f6;">⚙️</div>
            <div style="flex: 1;">
              <div style="font-size: 28px; font-weight: 700; color: #3b82f6; line-height: 1;">0</div>
              <div style="font-size: 13px; color: var(--text-secondary); margin-top: 6px; line-height: 1.3;">Converted to tasks<br>After approval</div>
            </div>
          </div>

          <!-- Rejected (Red) -->
          <div style="padding: 16px; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 8px; display: flex; align-items: flex-start; gap: 12px;">
            <div style="font-size: 28px; min-width: 40px; margin-top: 4px; display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; background: rgba(239, 68, 68, 0.2); border-radius: 50%; color: #ef4444;">✕</div>
            <div style="flex: 1;">
              <div style="font-size: 28px; font-weight: 700; color: #ef4444; line-height: 1;">0</div>
              <div style="font-size: 13px; color: var(--text-secondary); margin-top: 6px; line-height: 1.3;">Rejected<br>Not required for response</div>
            </div>
          </div>
        </div>
      </article>

      <!-- AI Recommendations from Crisis Report (Skeleton Table) -->
      <article class="glass-panel" style="padding: 20px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <div>
            <h3 style="margin: 0 0 4px 0; font-size: 16px; color: var(--text-primary);">AI Recommendations from Crisis Report</h3>
            <div style="font-size: 13px; color: var(--text-secondary);">Review the recommendations below and select the ones to include in your response plan.</div>
          </div>
          <div style="display: inline-block; background: rgba(251, 191, 36, 0.2); color: #fbbf24; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">AI GENERATED</div>
        </div>
        <div class="resource-matrix-table-wrapper" style="overflow-x: auto;">
          <table class="ai-resource-table skeleton-table" style="width: 100%;">
            <thead>
              <tr style="border-bottom: 2px solid #334155;">
                <th style="padding: 12px 10px;"><input type="checkbox" disabled style="width: 18px; height: 18px; cursor: pointer;"></th>
                <th style="padding: 12px 10px;"><div class="skeleton-line skeleton-sm"></div></th>
                <th style="padding: 12px 10px;"><div class="skeleton-line skeleton-sm"></div></th>
                <th style="padding: 12px 10px;"><div class="skeleton-line skeleton-sm"></div></th>
                <th style="padding: 12px 10px;"><div class="skeleton-line skeleton-sm"></div></th>
                <th style="padding: 12px 10px;"><div class="skeleton-line skeleton-sm"></div></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="n in 5" :key="n" style="border-bottom: 1px solid var(--glass-border);">
                <td style="padding: 12px 10px;"><input type="checkbox" disabled style="width: 18px; height: 18px; cursor: pointer;"></td>
                <td style="padding: 12px 10px;"><div class="skeleton-line skeleton-sm"></div></td>
                <td style="padding: 12px 10px;"><div class="skeleton-line skeleton-sm"></div></td>
                <td style="padding: 12px 10px;"><div class="skeleton-line skeleton-sm"></div></td>
                <td style="padding: 12px 10px;"><div class="skeleton-line skeleton-sm"></div></td>
                <td style="padding: 12px 10px;"><div class="skeleton-line skeleton-sm"></div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <!-- Response Plan Details Panel (Right Side) -->
      <article class="glass-panel" style="padding: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">Response Plan Details</h3>
          <div style="display: inline-block; background: rgba(147, 51, 234, 0.2); color: #c084fc; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: 600;">Draft</div>
        </div>
        <div style="display: flex; flex-direction: column; gap: 12px;">
          <div>
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Plan name</div>
            <div class="skeleton-line" style="height: 18px;"></div>
          </div>
          <div>
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Description</div>
            <div class="skeleton-line" style="height: 18px;"></div>
          </div>
          <div>
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Created by</div>
            <div class="skeleton-line skeleton-sm" style="width: 60%;"></div>
          </div>
          <div>
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Status</div>
            <div class="skeleton-line skeleton-sm" style="width: 40%;"></div>
          </div>
          <div>
            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Selected actions</div>
            <div class="skeleton-line skeleton-sm" style="width: 50%;"></div>
          </div>
        </div>
      </article>
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