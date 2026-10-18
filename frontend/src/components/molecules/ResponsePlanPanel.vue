<template>
  <section class="plan-panel">
    <!-- Header -->
    <header class="op-head">
      <div class="op-title">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="font-size: 20px;">📋</span>
          <h3>Response Operations</h3>
        </div>
        <p class="hint">Create a response plan from AI recommendations, review and approve actions, and track execution.</p>
      </div>
    </header>

    <!-- Officer name: typed, not logged in. Needed on every stage to save or decide. -->
    <label class="form-label officer-bar">
      <span>Officer (required to save or decide)</span>
      <input v-model="actor" class="form-input" maxlength="120" placeholder="Name of the officer" />
      <small style="color: #64748b; font-size: 11px;">There is no login yet. The name is recorded as typed.</small>
    </label>

    <!-- 3-Step Progress Bar -->
    <div class="stepper-new-wrapper">
      <ol class="stepper-new" aria-label="Response plan stages">
        <li class="step-item" :class="{ 'active': stage === 'select', 'done': stage === 'review' || stage === 'summary' }">
          <div class="step-content">
            <div class="step-circle" :class="{ 'active': stage === 'select', 'done': stage === 'review' || stage === 'summary' }">
              <span v-if="stage === 'review' || stage === 'summary'">✓</span>
              <span v-else>1</span>
            </div>
            <div class="step-text">
              <strong class="step-title">{{ $t('responseTab.stepPlanReview') }}</strong>
              <small class="step-desc">Create and review response plan</small>
            </div>
          </div>
        </li>

        <li class="step-item" :class="{ 'active': stage === 'review', 'done': stage === 'summary' }">
          <div class="step-content">
            <div class="step-circle" :class="{ 'active': stage === 'review', 'done': stage === 'summary' }">
              <span v-if="stage === 'summary'">✓</span>
              <span v-else>2</span>
            </div>
            <div class="step-text">
              <strong class="step-title">{{ $t('responseTab.stepReviewApprove') }}</strong>
              <small class="step-desc">Review and authorize actions</small>
            </div>
          </div>
        </li>

        <li class="step-item" :class="{ 'active': stage === 'summary' }">
          <div class="step-content">
            <div class="step-circle" :class="{ 'active': stage === 'summary' }">3</div>
            <div class="step-text">
              <strong class="step-title">{{ $t('responseTab.stepPlanSummary') }}</strong>
              <small class="step-desc">View plan status and outcomes</small>
            </div>
          </div>
        </li>
      </ol>
    </div>

    <div v-if="loadError" class="pp-error" role="alert">{{ loadError }}</div>

    <!-- No Report Placeholder -->
    <div v-if="plan && !plan.report" class="ai-banner ai-banner-placeholder" role="note">
      <div class="ai-banner-main">
        <strong>AI recommendations will appear here</strong>
        <span>{{ plan.message || 'Generate a crisis report first. Its recommendations appear here.' }}</span>
      </div>
    </div>

    <!-- Main Content when Report Exists -->
    <template v-else-if="plan && plan.report">
      <!-- Amber AI Banner -->
      <div class="ai-amber-banner">
        <div class="ai-amber-left">
          <div class="amber-icon-circle">💡</div>
          <div class="amber-text-stack">
            <strong>AI Recommendations Available</strong>
            <span>{{ plan.review?.total || plan.actions?.length || 0 }} recommendations from the latest crisis report (v{{ plan.report.version }}). Review and create a response plan.</span>
          </div>
        </div>
        <div class="ai-amber-right">
          <span class="report-meta">Generated: {{ formatTime(plan.report.generated_at) }}</span>
        </div>
      </div>

      <!-- STAGE 1: PLAN & REVIEW (Create Response Plan) -->
      <div v-if="stage === 'select'" class="plan-dashboard">
        <div class="dash-two-col">
          <!-- LEFT COLUMN -->
          <div class="dash-left">
            <!-- 4 Summary Tiles -->
            <div class="summary-tiles-grid">
              <div class="sum-tile glass-panel-new">
                <div class="tile-icon-box blue">🗄️</div>
                <div class="tile-data">
                  <span class="tile-lab">Total AI recommendations</span>
                  <strong class="tile-val">{{ plan.review?.total || plan.actions?.length || 0 }}</strong>
                </div>
              </div>
              <div class="sum-tile glass-panel-new">
                <div class="tile-icon-box green">✅</div>
                <div class="tile-data">
                  <span class="tile-lab">Selected for plan</span>
                  <strong class="tile-val">{{ selected.length }}</strong>
                </div>
              </div>
              <div class="sum-tile glass-panel-new">
                <div class="tile-icon-box cyan">⚙️</div>
                <div class="tile-data">
                  <span class="tile-lab">Converted to tasks</span>
                  <strong class="tile-val">{{ plan.review?.approved || 0 }}</strong>
                </div>
              </div>
              <div class="sum-tile glass-panel-new">
                <div class="tile-icon-box red">❌</div>
                <div class="tile-data">
                  <span class="tile-lab">Rejected</span>
                  <strong class="tile-val">{{ plan.review?.rejected || 0 }}</strong>
                </div>
              </div>
            </div>

            <!-- Recommendations Table -->
            <div class="table-section glass-panel-new">
              <div class="table-head-new">
                <div>
                  <h4>AI Recommendations from Crisis Report <span class="ai-tag">AI generated</span></h4>
                  <p class="hint">Select the recommendations to include. Selecting is not approval.</p>
                </div>
              </div>

              <div class="table-wrap">
                <table class="rec-table-new">
                  <thead>
                    <tr>
                      <th class="col-check">
                        <input type="checkbox" :checked="allSelected" @change="allSelected ? clearSelection() : selectAll()" />
                      </th>
                      <th class="col-num">#</th>
                      <th>Recommendation</th>
                      <th class="col-prio">AI priority</th>
                      <th class="col-cat">Category</th>
                      <th class="col-status">Status</th>
                      <th class="col-act">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="a in plan.actions" :key="a.index" :class="{ 'row-selected': isSelected(a.index) }">
                      <td class="col-check">
                        <input type="checkbox" :checked="isSelected(a.index)" @change="toggle(a.index)" />
                      </td>
                      <td class="col-num">
                        <div class="action-number-circle" :class="getPriorityClass(a)">{{ a.index + 1 }}</div>
                      </td>
                      <td class="rec-text">
                        {{ a.text }}<br/>
                        <span class="sub-link">View details &darr;</span>
                      </td>
                      <td class="col-prio">
                        <div class="action-badge-right" :class="getPriorityClass(a)">
                          {{ getPriorityLabel(a) }}
                        </div>
                      </td>
                      <td class="col-cat">
                        <span class="cat-pill" :style="getCategoryStyle(a)">
                          {{ getCategoryLabel(a) }}
                        </span>
                      </td>
                      <td class="col-status">
                        <span class="status-pill" :class="isSelected(a.index) ? 'pill-selected' : 'pill-unselected'">
                          {{ isSelected(a.index) ? 'Selected' : 'Not selected' }}
                        </span>
                      </td>
                      <td class="col-act">
                        <button class="btn-text" @click="toggle(a.index)">{{ isSelected(a.index) ? 'Deselect' : 'Select' }}</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- RIGHT COLUMN -->
          <div class="dash-right">
            <!-- Response Plan Details -->
            <div class="details-section glass-panel-new">
              <div class="details-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="font-size: 18px; color: #38bdf8;">📋</span>
                  <h4>Response Plan Details</h4>
                </div>
                <span class="draft-pill">{{ planStatus }}</span>
              </div>

              <div class="plan-form">
                <label class="form-label">
                  <span>Plan name</span>
                  <input v-model="customPlanName" class="form-input" :placeholder="suggestedPlanName" @blur="savePlanDetails" />
                </label>
                <label class="form-label">
                  <span>Description</span>
                  <textarea v-model="planDescription" class="form-textarea" rows="3" placeholder="Describe the response plan" @blur="savePlanDetails"></textarea>
                  <small v-if="detailsError" class="pp-error" role="alert" style="padding: 6px 8px;">{{ detailsError }}</small>
                  <small v-else-if="detailsSaved" style="color: #64748b; font-size: 11px;">Saved</small>
                </label>

                <div class="meta-list">
                  <div class="meta-row">
                    <span class="meta-lab">Linked report</span>
                    <span class="meta-val doc-link"><span class="doc-icon">📄</span> Version {{ plan.report?.version }}</span>
                  </div>
                  <div class="meta-row">
                    <span class="meta-lab">Created by</span>
                    <span class="meta-val">{{ plan.plan?.created_by || 'Not saved yet' }}</span>
                  </div>
                  <div class="meta-row">
                    <span class="meta-lab">Created on</span>
                    <span class="meta-val">{{ plan.plan ? formatTime(plan.plan.created_at) : '-' }}</span>
                  </div>
                  <div class="meta-row">
                    <span class="meta-lab">Status</span>
                    <span class="meta-val status-draft"><span class="dot"></span> {{ planStatus }}</span>
                  </div>
                  <div class="meta-row">
                    <span class="meta-lab">Selected actions</span>
                    <span class="meta-val">{{ selected.length }} of {{ plan.actions?.length || 0 }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Quick Actions -->
            <div class="actions-section glass-panel-new">
              <div class="details-header">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="font-size: 18px; color: #38bdf8;">📋</span>
                  <h4>Quick Actions</h4>
                </div>
              </div>

              <div class="quick-grid">
                <button class="btn-outline" @click="selectAll"><span class="icon">☑️</span> Select All</button>
                <button class="btn-outline" @click="clearSelection"><span class="icon">✖️</span> Clear Selection</button>
              </div>

              <button class="btn-primary-cyan full-width" :disabled="selected.length === 0" @click="goToReview">
                Continue to Review Plan &rarr;
              </button>
              <div style="text-align: center; margin-top: 8px;">
                <small style="color: #64748b; font-size: 11px;">Review all selected recommendations before approving.</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- STAGE 2: REVIEW & APPROVE PLAN -->
      <div v-else-if="stage === 'review'" class="plan-dashboard">
        <div class="dash-two-col">
          <!-- LEFT COLUMN -->
          <div class="dash-left">
            <div class="table-section glass-panel-new">
              <div class="table-head-new" style="flex-direction: row; justify-content: space-between; align-items: flex-start;">
                <div>
                  <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 18px;">📋</span>
                    <h4 style="margin: 0; font-size: 15px; color: #f8fafc;">Selected Recommendations for Review <span class="ai-tag" style="background: rgba(255,255,255,0.1); color: #e2e8f0; border: none;">{{ selected.length }} actions</span></h4>
                  </div>
                  <p class="hint" style="margin-top: 8px;">Review each action, modify priority if needed, assign responsible team and approve or reject.</p>
                </div>
                <button class="btn-outline" @click="backToSelect" style="padding: 6px 12px;">&larr; Back to Selection</button>
              </div>

              <div v-if="actionError" class="pp-error" role="alert" style="margin-bottom: 14px;">{{ actionError }}</div>

              <div class="table-wrap">
                <table class="rec-table-new">
                  <thead>
                    <tr>
                      <th class="col-num">#</th>
                      <th style="width: 250px;">Recommendation</th>
                      <th colspan="2" style="text-align: center; border-left: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05);">AI Suggestion<br/><div style="display: flex; justify-content: space-around; margin-top: 8px;"><span>Priority</span><span>Category</span></div></th>
                      <th colspan="3" style="text-align: center; border-right: 1px solid rgba(255,255,255,0.05);">Officer Decision<br/><div style="display: flex; justify-content: space-around; margin-top: 8px;"><span>Priority</span><span>Assign to</span><span>Due Date</span></div></th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="reviewActions.length === 0">
                      <td colspan="8" class="pp-empty" style="padding: 16px; text-align: center;">No actions are selected for review.</td>
                    </tr>
                    <tr v-for="a in reviewActions" :key="a.index" :class="a.decision ? 'decided ' + a.decision : ''">
                      <td class="col-num">
                        <div class="action-number-circle" :class="getPriorityClass(a)">{{ a.index + 1 }}</div>
                      </td>
                      <td class="rec-text" style="font-size: 13px;">
                        {{ a.text }}<br/>
                        <span class="sub-link">View details &darr;</span>
                      </td>
                      
                      <!-- AI Suggestion Columns -->
                      <td style="border-left: 1px solid rgba(255,255,255,0.05); text-align: center;">
                        <div class="action-badge-right" :class="getPriorityClass(a)">
                           {{ getPriorityLabel(a) }}
                        </div>
                      </td>
                      <td style="border-right: 1px solid rgba(255,255,255,0.05); text-align: center;">
                        <span class="cat-pill" :style="getCategoryStyle(a)">
                          {{ getCategoryLabel(a) }}
                        </span>
                      </td>

                      <!-- Officer Decision Columns -->
                      <td style="text-align: center;">
                        <select v-model="forms[a.index].priority" class="form-input" style="padding: 6px 4px; font-size: 11px; width: 90px;" :disabled="!!a.decision">
                          <option value="" disabled>Choose</option>
                          <option value="critical">CRITICAL</option>
                          <option value="high">HIGH</option>
                          <option value="medium">MEDIUM</option>
                          <option value="low">LOW</option>
                        </select>
                      </td>
                      <td style="text-align: center;">
                        <input v-model="forms[a.index].assignee" placeholder="Team..." class="form-input" style="padding: 6px 4px; font-size: 11px; width: 100px;" :disabled="!!a.decision" />
                      </td>
                      <td style="border-right: 1px solid rgba(255,255,255,0.05); text-align: center;">
                        <input type="date" v-model="forms[a.index].due" class="form-input" style="padding: 6px 8px; font-size: 11px; width: 130px;" :disabled="!!a.decision" />
                      </td>

                      <!-- Action Buttons -->
                      <td style="min-width: 100px;">
                        <div v-if="a.decision === 'approved'" style="color: #4ade80; font-size: 12px; font-weight: 700; text-align: center;">
                          ✓ Approved
                        </div>
                        <div v-else-if="a.decision === 'rejected'" style="color: #ef4444; font-size: 12px; font-weight: 700; text-align: center;">
                          ✕ Rejected
                        </div>
                        <div v-else style="display: flex; flex-direction: column; gap: 6px;">
                          <button class="btn-solid-green" @click="decide(a.index, 'approve')" :disabled="!canApprove(a.index)">✓ Approve</button>
                          <button class="btn-solid-red" @click="decide(a.index, 'reject')" :disabled="busy || !actor.trim()">✕ Reject</button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- RIGHT COLUMN -->
          <div class="dash-right">
            <!-- Review Progress -->
            <div class="details-section glass-panel-new">
              <div class="details-header" style="margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="font-size: 18px; color: #38bdf8;">🎯</span>
                  <h4 style="margin: 0; font-size: 15px; color: #f8fafc;">Review Progress</h4>
                </div>
              </div>
              
              <div style="display: flex; align-items: center; gap: 24px;">
                <div style="width: 80px; height: 80px; border-radius: 50%; border: 6px solid #fbbf24; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                  <strong style="font-size: 20px; color: #f8fafc;">{{ reviewActions.filter(a => a.decision).length }}/{{ reviewActions.length }}</strong>
                  <span style="font-size: 9px; color: #94a3b8;">Reviewed</span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; flex: 1;">
                  <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <span style="display: flex; align-items: center; gap: 6px;"><span style="color: #4ade80;">●</span> Approved</span>
                    <strong style="color: #f8fafc;">{{ reviewActions.filter(a => a.decision === 'approved').length }}</strong>
                  </div>
                  <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <span style="display: flex; align-items: center; gap: 6px;"><span style="color: #ef4444;">●</span> Rejected</span>
                    <strong style="color: #f8fafc;">{{ reviewActions.filter(a => a.decision === 'rejected').length }}</strong>
                  </div>
                  <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <span style="display: flex; align-items: center; gap: 6px;"><span style="color: #fbbf24;">●</span> Pending Review</span>
                    <strong style="color: #f8fafc;">{{ reviewActions.filter(a => !a.decision).length }}</strong>
                  </div>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="actions-section glass-panel-new" style="margin-top: 16px;">
              <div class="details-header" style="margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span style="font-size: 18px; color: #38bdf8;">📋</span>
                  <h4 style="margin: 0; font-size: 15px; color: #f8fafc;">Quick Actions</h4>
                </div>
              </div>

              <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 16px;">
                <button class="btn-outline" @click="backToSelect" style="width: 100%; justify-content: center;">Cancel Review</button>
                <button class="btn-primary-cyan full-width" style="padding: 14px;" :disabled="reviewActions.filter(a => !a.decision).length > 0" @click="goToSummary">
                  View Plan Summary &rarr;
                </button>
              </div>
              <div style="text-align: center; margin-top: 12px;">
                <small style="color: #64748b; font-size: 11px;">Review all selected recommendations before viewing the plan summary.</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- STAGE 3: PLAN SUMMARY -->
      <div v-else-if="stage === 'summary'" class="plan-dashboard">
        <div class="glass-panel-new" style="padding: 24px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div>
              <h3 style="margin: 0; color: #f8fafc; font-size: 18px;">Plan Summary</h3>
              <p class="hint">Overview of authorized response tasks and operational outcomes.</p>
            </div>
            <button class="btn-outline" @click="stage = 'review'">&larr; Back to Review</button>
          </div>

          <div class="summary-tiles-grid" style="margin-bottom: 24px;">
            <div class="sum-tile glass-panel-new">
              <div class="tile-icon-box green">✅</div>
              <div class="tile-data">
                <span class="tile-lab">Approved Tasks</span>
                <strong class="tile-val">{{ plan.review?.approved || 0 }}</strong>
              </div>
            </div>
            <div class="sum-tile glass-panel-new">
              <div class="tile-icon-box red">❌</div>
              <div class="tile-data">
                <span class="tile-lab">Rejected Actions</span>
                <strong class="tile-val">{{ plan.review?.rejected || 0 }}</strong>
              </div>
            </div>
            <div class="sum-tile glass-panel-new">
              <div class="tile-icon-box cyan">📋</div>
              <div class="tile-data">
                <span class="tile-lab">Total Actions Reviewed</span>
                <strong class="tile-val">{{ (plan.review?.approved || 0) + (plan.review?.rejected || 0) }}</strong>
              </div>
            </div>
          </div>

          <div class="table-wrap">
            <table class="rec-table-new">
              <thead>
                <tr>
                  <th class="col-num">#</th>
                  <th>Task Description</th>
                  <th>Task Status</th>
                  <th>Officer Priority</th>
                  <th>Assigned Team</th>
                  <th>Decided By</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!plan.actions?.some((a: any) => a.decision === 'approved')">
                  <td colspan="6" class="pp-empty" style="text-align: center;">No approved tasks yet.</td>
                </tr>
                <tr v-for="a in (plan.actions || []).filter((x: any) => x.decision === 'approved')" :key="a.index">
                  <td class="col-num">{{ a.index + 1 }}</td>
                  <td class="rec-text">{{ a.text }}</td>
                  <td><span class="status-pill pill-selected">{{ a.task ? (TASK_STATUS_LABELS[a.task.status] || a.task.status) : '-' }}</span></td>
                  <td>{{ a.officer_priority ? a.officer_priority.toUpperCase() : '-' }}</td>
                  <td>{{ a.task?.assignee || '-' }}</td>
                  <td>{{ a.decided_by || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!loadError" class="pp-empty">Loading the response plan...</div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch, onMounted } from 'vue'

const props = defineProps<{
  incidentId: string
  incidentType?: string | null
  incidentLocation?: string | null
}>()

const host = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)

const plan = ref<any | null>(null)
const loadError = ref<string | null>(null)
const actionError = ref<string | null>(null)
const busy = ref(false)
const actor = ref('')
const forms = reactive<Record<number, { assignee: string; priority: string; reason: string }>>({})

const customPlanName = ref('')
const planDescription = ref('')
const detailsError = ref<string | null>(null)
const detailsSaved = ref(false)
// Last saved values, so blur only saves when something changed.
const savedName = ref('')
const savedDescription = ref('')

// Stages: 'select' (Plan & Review), 'review' (Review & Approve), 'summary' (Plan Summary)
const stage = ref<'select' | 'review' | 'summary'>('select')
const selected = ref<number[]>([])

const allSelected = computed(() =>
  !!plan.value?.actions?.length && selected.value.length === plan.value.actions.length
)

// Actions shown during review: the ones selected on this screen, plus any already decided.
const reviewActions = computed(() =>
  (plan.value?.actions || []).filter((a: any) => a.decision || isSelected(a.index))
)

const isSelected = (index: number) => selected.value.includes(index)

const toggle = (index: number) => {
  selected.value = isSelected(index)
    ? selected.value.filter(i => i !== index)
    : [...selected.value, index].sort((a, b) => a - b)
}

const selectAll = () => {
  selected.value = (plan.value?.actions || []).map((a: any) => a.index)
}

const clearSelection = () => {
  selected.value = []
}

const goToReview = () => {
  actionError.value = null
  stage.value = 'review'
}

const backToSelect = () => {
  actionError.value = null
  stage.value = 'select'
}

const goToSummary = () => {
  actionError.value = null
  stage.value = 'summary'
}

// AI priority is IMMEDIATE / HIGH / STAGED (the report schema). Shown as saved; only colour is derived.
const getPriorityClass = (a: any) => {
  const p = (a?.priority || '').toUpperCase()
  if (p === 'IMMEDIATE') return 'critical'
  if (p === 'HIGH') return 'high'
  if (p === 'STAGED') return 'medium'
  return 'none'
}

const getPriorityLabel = (a: any) => a?.priority || 'Not in report'

const CATEGORY_COLORS: Record<string, string> = {
  'Command & Control': '#3b82f6',
  'Search & Rescue': '#a855f7',
  'Medical': '#f59e0b',
  'Logistics': '#10b981',
  'Evacuation': '#f97316',
  'Assessment': '#06b6d4',
  'Communications': '#ec4899',
  'Infrastructure': '#84cc16',
}

const getCategoryStyle = (a: any) => {
  const c = CATEGORY_COLORS[a?.category || ''] || '#64748b'
  return `border-color: ${c}; color: ${c};`
}

const getCategoryLabel = (a: any) => a?.category || 'Not in report'

const TASK_STATUS_LABELS: Record<string, string> = {
  open: 'Open',
  acknowledged: 'Acknowledged',
  in_progress: 'In progress',
  blocked: 'Blocked',
  done: 'Done',
}

// Officer priority is suggested from the AI priority, and the officer can change it.
const AI_TO_OFFICER: Record<string, string> = { IMMEDIATE: 'critical', HIGH: 'high', STAGED: 'medium' }

// Name suggested from the incident. Shown as a placeholder until the officer saves a name.
const suggestedPlanName = computed(() => {
  const type = props.incidentType ? props.incidentType.charAt(0).toUpperCase() + props.incidentType.slice(1) : 'Incident'
  const place = props.incidentLocation || ''
  return `${place ? place + ' ' : ''}${type} · Response Plan`
})

const planStatus = computed(() => {
  const r = plan.value?.review
  if (!r || r.approved + r.rejected === 0) return 'Draft'
  return r.pending > 0 ? 'In review' : 'Decided'
})

const formatTime = (iso: string) => {
  const d = new Date(iso)
  return isNaN(d.getTime()) ? 'time not recorded' : d.toLocaleString()
}

const ensureForm = (index: number) => {
  if (!forms[index]) {
    const a = (plan.value?.actions || []).find((x: any) => x.index === index)
    forms[index] = {
      assignee: '',
      priority: AI_TO_OFFICER[(a?.priority || '').toUpperCase()] || '',
      reason: '',
      due: '',
    }
  }
}

const canApprove = (index: number) => {
  ensureForm(index)
  const f = forms[index]
  return !busy.value && !!actor.value.trim() && !!f.assignee.trim() && !!f.priority
}

async function load() {
  loadError.value = null
  try {
    const res = await fetch(`${host}/api/v1/incidents/${props.incidentId}/response/plan`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    plan.value = await res.json()
    ;(plan.value.actions || []).forEach((a: any) => {
      ensureForm(a.index)
      if (a.decision) {
        forms[a.index].priority = a.officer_priority || ''
        forms[a.index].assignee = a.task?.assignee || ''
      }
    })
    
    if (selected.value.length === 0 && plan.value?.actions?.length) {
      selectAll()
    }

    customPlanName.value = plan.value.plan?.name || ''
    planDescription.value = plan.value.plan?.description || ''
    savedName.value = plan.value.plan?.name || ''
    savedDescription.value = plan.value.plan?.description || ''
  } catch (err) {
    loadError.value = 'Could not load the response plan. Try again.'
  }
}

async function savePlanDetails() {
  if (!plan.value?.report) return
  const name = customPlanName.value.trim()
  const description = planDescription.value.trim()
  if (name === savedName.value && description === savedDescription.value) return
  const who = actor.value.trim()
  if (!who) {
    detailsError.value = "Type the officer's name above to save plan details."
    return
  }
  detailsError.value = null
  detailsSaved.value = false
  try {
    const res = await fetch(`${host}/api/v1/incidents/${props.incidentId}/response/plan/details`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ actor: who, name: name || undefined, description: description || undefined }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      detailsError.value = typeof body.detail === 'string' ? body.detail : `Could not save plan details (HTTP ${res.status}).`
      return
    }
    const saved = await res.json()
    savedName.value = saved.name || ''
    savedDescription.value = saved.description || ''
    if (plan.value) plan.value.plan = saved
    detailsSaved.value = true
  } catch (err) {
    detailsError.value = 'Could not reach the server. The plan details were not saved.'
  }
}

async function decide(index: number, decision: 'approve' | 'reject') {
  if (!plan.value?.report) return
  const who = actor.value.trim()
  if (!who) {
    actionError.value = "Enter the officer's name before deciding."
    return
  }
  actionError.value = null
  busy.value = true
  ensureForm(index)
  const f = forms[index]
  try {
    const res = await fetch(`${host}/api/v1/incidents/${props.incidentId}/response/plan/decide`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        actor: who,
        report_id: plan.value.report.id,
        action_index: index,
        decision,
        assignee: decision === 'approve' ? f.assignee.trim() : undefined,
        priority: decision === 'approve' ? f.priority : undefined,
        // Date-only input; the backend stores a UTC timestamp, so the deadline is end of that day UTC.
        due_at: decision === 'approve' && f.due ? `${f.due}T23:59:00Z` : undefined,
        reason: decision === 'reject' && f.reason.trim() ? f.reason.trim() : undefined,
      }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      actionError.value = typeof body.detail === 'string' ? body.detail : `Could not save the decision (HTTP ${res.status}).`
      return
    }
    await load()
  } catch (err) {
    actionError.value = 'Could not reach the server. The decision was not saved.'
  } finally {
    busy.value = false
  }
}

onMounted(load)
watch(() => props.incidentId, () => {
  stage.value = 'select'
  selected.value = []
  load()
})
</script>

<style scoped>
.officer-bar { max-width: 360px; }

.plan-panel {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.op-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
}

.op-title h3 {
  margin: 0;
  font-size: 20px;
  color: var(--text-primary, #f8fafc);
}

.op-title .hint {
  margin: 4px 0 0;
  font-size: 14px;
  color: #94a3b8;
}

/* Stepper Box Layout (3 steps) */
.stepper-new-wrapper {
  margin: 8px 0 12px;
}

.stepper-new {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  list-style: none;
  padding: 0;
  margin: 0;
}

.step-item {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
}

.step-item.active {
  background: rgba(8, 145, 178, 0.15);
  border-color: #22d3ee;
}

.step-item.done {
  border-color: rgba(34, 197, 94, 0.4);
}

.step-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(71, 85, 105, 0.5);
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.step-circle.active {
  background: #22d3ee;
  color: #04141a;
}

.step-circle.done {
  background: #22c55e;
  color: #04141a;
}

.step-text {
  display: flex;
  flex-direction: column;
}

.step-title {
  font-size: 14px;
  color: #f8fafc;
}

.step-item.active .step-title {
  color: #22d3ee;
}

.step-desc {
  font-size: 11px;
  color: #64748b;
}

/* Amber AI Banner */
.ai-amber-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: rgba(245, 158, 11, 0.06);
  border: 1px solid #f59e0b;
  border-radius: 8px;
}

.ai-amber-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.amber-icon-circle {
  font-size: 26px;
  text-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
}

.amber-text-stack {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.amber-text-stack strong {
  color: #fcd34d;
  font-size: 15px;
}

.amber-text-stack span {
  color: #fbbf24;
  font-size: 13px;
}

.ai-amber-right .report-meta {
  color: #94a3b8;
  font-size: 12px;
}

/* 2-Column Dashboard */
.plan-dashboard {
  margin-top: 10px;
}

.dash-two-col {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 20px;
  align-items: start;
}

.dash-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.dash-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.glass-panel-new {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.35);
  border-radius: 8px;
}

/* Summary Tiles */
.summary-tiles-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.sum-tile {
  padding: 14px;
  display: flex;
  align-items: center;
  gap: 14px;
}

.tile-icon-box {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.tile-icon-box.blue { background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); }
.tile-icon-box.green { background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.3); }
.tile-icon-box.cyan { background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.3); }
.tile-icon-box.red { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); }

.tile-data {
  display: flex;
  flex-direction: column;
}

.tile-lab {
  font-size: 11px;
  color: #94a3b8;
}

.tile-val {
  font-size: 22px;
  color: #f8fafc;
  line-height: 1.2;
}

/* Tables */
.table-section {
  padding: 18px;
}

.table-head-new {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.table-head-new h4 {
  margin: 0;
  font-size: 15px;
  color: #f8fafc;
}

.table-wrap {
  overflow-x: auto;
}

.rec-table-new {
  width: 100%;
  border-collapse: collapse;
}

.rec-table-new th {
  text-align: left;
  padding: 10px 12px;
  font-size: 11px;
  color: #94a3b8;
  font-weight: 600;
  background: rgba(15, 23, 42, 0.8);
  border-bottom: 1px solid rgba(71, 85, 105, 0.4);
}

.rec-table-new td {
  padding: 12px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
  vertical-align: middle;
  color: #e2e8f0;
}

.row-selected td {
  background: rgba(34, 211, 238, 0.04);
}

.action-number-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
}

.action-number-circle.critical { background: #ef4444; }
.action-number-circle.high { background: #f97316; }
.action-number-circle.medium { background: #eab308; }
.action-number-circle.none { background: #475569; }

.action-badge-right {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
}

.action-badge-right.critical { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
.action-badge-right.high { background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.3); }
.action-badge-right.medium { background: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.3); }
.action-badge-right.none { background: rgba(71, 85, 105, 0.3); color: #94a3b8; border: 1px solid rgba(71, 85, 105, 0.4); }

.cat-pill {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  border: 1px solid;
  background: rgba(0, 0, 0, 0.2);
}

.status-pill {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 11px;
}

.status-pill.pill-selected {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.status-pill.pill-unselected {
  background: rgba(148, 163, 184, 0.15);
  color: #94a3b8;
}

.sub-link {
  color: #38bdf8;
  font-size: 11px;
  margin-top: 4px;
  display: inline-block;
  cursor: pointer;
}

/* Sidebar Details */
.details-section, .actions-section {
  padding: 18px;
}

.details-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.details-header h4 {
  margin: 0;
  font-size: 15px;
  color: #f8fafc;
}

.draft-pill {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc;
  font-size: 11px;
}

.plan-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #94a3b8;
}

.form-input, .form-textarea {
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  padding: 8px 10px;
  color: #f8fafc;
  font-size: 13px;
}

.meta-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
  padding-top: 10px;
  border-top: 1px solid rgba(71, 85, 105, 0.3);
}

.meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.meta-lab { color: #64748b; }
.meta-val { color: #f8fafc; }
.doc-link { color: #38bdf8; }

.quick-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 14px;
}

/* Buttons */
.btn-outline {
  background: transparent;
  border: 1px solid rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
}

.btn-outline:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(148, 163, 184, 0.5);
}

.btn-text {
  background: transparent;
  border: none;
  color: #38bdf8;
  font-size: 12px;
  cursor: pointer;
}

.btn-primary-cyan {
  background: #06b6d4;
  color: #04141a;
  border: none;
  border-radius: 6px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.btn-primary-cyan:hover:not(:disabled) {
  background: #22d3ee;
}

.btn-primary-cyan:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.full-width {
  width: 100%;
}

.btn-solid-green {
  background: rgba(16, 185, 129, 0.2);
  color: #4ade80;
  border: 1px solid rgba(16, 185, 129, 0.4);
  border-radius: 4px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  width: 100%;
  transition: all 0.2s;
}

.btn-solid-green:hover:not(:disabled) {
  background: rgba(16, 185, 129, 0.4);
}

.btn-solid-red {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: 4px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  width: 100%;
  transition: all 0.2s;
}

.btn-solid-red:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.4);
}

tr.decided {
  opacity: 0.5;
  background: rgba(0, 0, 0, 0.2);
}

.ai-tag {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: rgba(251, 191, 36, 0.18);
  color: #fcd34d;
}

.pp-error {
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #f87171;
  border-radius: 6px;
  font-size: 13px;
}

.pp-empty {
  padding: 14px;
  color: #94a3b8;
  font-size: 13px;
}

.ai-banner-placeholder {
  background: rgba(15, 23, 42, 0.5);
  border: 1px dashed rgba(251, 191, 36, 0.3);
  padding: 20px;
  border-radius: 8px;
}

@media (max-width: 900px) {
  .dash-two-col { grid-template-columns: 1fr; }
  .stepper-new { grid-template-columns: 1fr; }
  .summary-tiles-grid { grid-template-columns: 1fr 1fr; }
}
</style>
