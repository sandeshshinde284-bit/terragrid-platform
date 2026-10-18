<template>
  <section class="plan-panel glass-panel">
    <header>
      <span class="section-kicker">RESPONSE PLAN</span>
      <h3>{{ headline }}</h3>
      <p class="hint">{{ hintText }}</p>
    </header>

    <div v-if="loadError" class="pp-error" role="alert">{{ loadError }}</div>

    <div v-if="plan && !plan.report" class="pp-empty">
      {{ plan.message || 'Generate a crisis report first. Its recommendations appear here.' }}
    </div>

    <template v-else-if="plan && plan.report">
      <p class="pp-meta">
        Report v{{ plan.report.version }}, generated {{ formatTime(plan.report.generated_at) }} with {{ plan.report.model }}.
        AI-generated, not verified.
      </p>

      <!-- Overview: counts and the one button that matches the plan's state -->
      <template v-if="stage === 'overview'">
        <div class="pp-counts">
          <div><span>Recommendations</span><strong>{{ plan.review.total }}</strong></div>
          <div><span>Approved</span><strong>{{ plan.review.approved }}</strong></div>
          <div><span>Rejected</span><strong>{{ plan.review.rejected }}</strong></div>
          <div><span>Pending review</span><strong>{{ plan.review.pending }}</strong></div>
        </div>
        <p class="pp-note">AI recommendations are not operational decisions. Each action needs an officer's approval.</p>
        <div class="pp-buttons">
          <button class="pp-primary" @click="primaryAction">{{ primaryLabel }}</button>
        </div>
      </template>

      <!-- Selection: choose which recommendations belong in the plan. Local only; nothing is saved. -->
      <template v-else-if="stage === 'select'">
        <div class="pp-toolbar">
          <button class="pp-link" @click="selectAll">Select all</button>
          <button class="pp-link" @click="clearSelection">Clear selection</button>
          <span class="pp-count">{{ selected.length }} of {{ plan.actions.length }} selected for the plan</span>
        </div>
        <ol class="pp-list">
          <li v-for="a in plan.actions" :key="a.index" class="pp-item select-item" :class="{ on: isSelected(a.index) }">
            <label class="pp-check">
              <input type="checkbox" :checked="isSelected(a.index)" @change="toggle(a.index)" />
              <span class="pp-text">
                <span class="pp-num">{{ a.index + 1 }}</span>
                <span>{{ a.text }}</span>
              </span>
            </label>
            <div class="pp-tags">
              <span class="pp-tag">{{ a.priority ? `AI priority: ${a.priority}` : 'Priority not in report' }}</span>
              <span class="pp-tag">{{ a.category ? `Category: ${a.category}` : 'Category not in report' }}</span>
            </div>
          </li>
        </ol>
        <p class="pp-note">Selecting an action is not approval. Nothing is saved until an officer approves or rejects it.</p>
        <div class="pp-buttons">
          <button class="pp-secondary" @click="stage = 'overview'">Back</button>
          <button class="pp-primary" :disabled="selected.length === 0" @click="goToReview">
            Continue to review ({{ selected.length }})
          </button>
        </div>
      </template>

      <!-- Review: officer decisions on the selected actions and on any already decided -->
      <template v-else>
        <label class="pp-field">
          <span>Officer approving (required)</span>
          <input v-model="actor" maxlength="120" placeholder="e.g. Duty officer, District control room" />
          <small>There is no login yet. The name is recorded as typed.</small>
        </label>

        <div v-if="actionError" class="pp-error" role="alert">{{ actionError }}</div>

        <p v-if="reviewActions.length === 0" class="pp-empty">No actions are selected for review.</p>

        <ol class="pp-list">
          <li v-for="a in reviewActions" :key="a.index" class="pp-item" :class="a.decision ? 'decided ' + a.decision : ''">
            <div class="pp-text">
              <span class="pp-num">{{ a.index + 1 }}</span>
              <span>{{ a.text }}</span>
            </div>

            <div v-if="a.decision === 'approved'" class="pp-status ok">
              Approved by {{ a.decided_by }}. Task #{{ a.task_id }} created.
            </div>
            <div v-else-if="a.decision === 'rejected'" class="pp-status no">
              Rejected by {{ a.decided_by }}.<span v-if="a.reason"> Reason: {{ a.reason }}</span>
            </div>

            <div v-else class="pp-form">
              <label class="pp-field">
                <span>Assign to</span>
                <input v-model="forms[a.index].assignee" maxlength="120" placeholder="Team or person" />
              </label>
              <label class="pp-field">
                <span>Priority</span>
                <select v-model="forms[a.index].priority">
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </label>
              <label class="pp-field">
                <span>Reason if rejecting (optional)</span>
                <input v-model="forms[a.index].reason" maxlength="500" placeholder="Why it does not apply" />
              </label>
              <div class="pp-buttons">
                <button class="pp-approve" :disabled="busy || !canApprove(a.index)" @click="decide(a.index, 'approve')">Approve and create task</button>
                <button class="pp-reject" :disabled="busy || !actor.trim()" @click="decide(a.index, 'reject')">Reject</button>
              </div>
            </div>
          </li>
        </ol>

        <div class="pp-buttons">
          <button class="pp-secondary" @click="stage = 'overview'">Back to overview</button>
        </div>
      </template>
    </template>

    <div v-else-if="!loadError" class="pp-empty">Loading the response plan...</div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch, onMounted } from 'vue'

const props = defineProps<{ incidentId: string }>()

const host = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)

const plan = ref<any | null>(null)
const loadError = ref<string | null>(null)
const actionError = ref<string | null>(null)
const busy = ref(false)
const actor = ref('')
const forms = reactive<Record<number, { assignee: string; priority: string; reason: string }>>({})

// 'overview' shows counts and the state button; 'select' picks recommendations; 'review' records decisions.
const stage = ref<'overview' | 'select' | 'review'>('overview')
// Local to this screen. Not saved: a refresh clears it.
const selected = ref<number[]>([])

const started = computed(() => (plan.value?.review?.approved ?? 0) + (plan.value?.review?.rejected ?? 0) > 0)

const primaryLabel = computed(() => {
  if ((plan.value?.review?.approved ?? 0) > 0) return 'Manage Response Plan'
  if (started.value) return 'Continue Response Plan'
  return 'Create Response Plan'
})

const headline = computed(() => {
  if (stage.value === 'select') return 'Select recommendations for the plan'
  if (stage.value === 'review') return 'Review and approve actions'
  return 'Create a response plan from AI recommendations'
})

const hintText = computed(() => {
  if (stage.value === 'select') return 'Choose which recommendations belong in the plan. Selecting is not approval.'
  if (stage.value === 'review') return 'Approving an action creates a task. Rejecting records the reason.'
  return 'Recommendations come from the latest crisis report. Nothing is authorized until an officer approves it.'
})

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

const primaryAction = () => {
  if (started.value) {
    // Resume: review the actions that are still pending.
    selected.value = (plan.value?.actions || []).filter((a: any) => !a.decision).map((a: any) => a.index)
    stage.value = 'review'
  } else {
    selectAll()
    stage.value = 'select'
  }
}

const goToReview = () => {
  actionError.value = null
  stage.value = 'review'
}

const formatTime = (iso: string) => {
  const d = new Date(iso)
  return isNaN(d.getTime()) ? 'time not recorded' : d.toLocaleString()
}

const ensureForm = (index: number) => {
  if (!forms[index]) forms[index] = { assignee: '', priority: 'medium', reason: '' }
}

const canApprove = (index: number) => {
  ensureForm(index)
  return !busy.value && !!actor.value.trim() && !!forms[index].assignee.trim()
}

async function load() {
  loadError.value = null
  try {
    const res = await fetch(`${host}/api/v1/incidents/${props.incidentId}/response/plan`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    plan.value = await res.json()
    ;(plan.value.actions || []).forEach((a: any) => ensureForm(a.index))
  } catch (err) {
    loadError.value = 'Could not load the response plan. Try again.'
  }
}

async function decide(index: number, decision: 'approve' | 'reject') {
  if (!plan.value?.report) return
  actionError.value = null
  busy.value = true
  ensureForm(index)
  const f = forms[index]
  try {
    const res = await fetch(`${host}/api/v1/incidents/${props.incidentId}/response/plan/decide`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        actor: actor.value.trim(),
        report_id: plan.value.report.id,
        action_index: index,
        decision,
        assignee: decision === 'approve' ? f.assignee.trim() : undefined,
        priority: f.priority,
        reason: decision === 'reject' ? (f.reason.trim() || undefined) : undefined,
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
  stage.value = 'overview'
  selected.value = []
  load()
})
</script>

<style scoped>
.plan-panel { padding: 18px; margin-top: 16px; display: flex; flex-direction: column; gap: 12px; }
.plan-panel h3 { margin: 4px 0 0; font-size: 17px; color: var(--text-primary); }
.hint, .pp-meta { margin: 0; font-size: 13px; color: #94a3b8; }
.pp-error { padding: 8px 10px; border-radius: 6px; background: rgba(239,68,68,.12); color: #fca5a5; font-size: 13px; }
.pp-empty { padding: 12px; color: #94a3b8; font-size: 13px; }
.pp-note { margin: 0; font-size: 13px; color: #94a3b8; }
.pp-field { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: #94a3b8; }
.pp-field input, .pp-field select { padding: 7px 9px; border-radius: 6px; background: rgba(15,23,42,.7); border: 1px solid rgba(71,85,105,.5); color: #e2e8f0; font-size: 13px; }
.pp-field small { color: #64748b; font-size: 11px; }
.pp-counts { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; }
.pp-counts > div { padding: 10px 12px; border-radius: 8px; background: rgba(15,23,42,.5); border: 1px solid rgba(71,85,105,.35); display: flex; flex-direction: column; gap: 4px; }
.pp-counts span { font-size: 12px; color: #94a3b8; }
.pp-counts strong { font-size: 20px; color: #e2e8f0; }
.pp-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; }
.pp-count { margin-left: auto; font-size: 13px; color: #94a3b8; }
.pp-link { background: none; border: none; color: #38bdf8; font-size: 13px; cursor: pointer; padding: 0; }
.pp-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.pp-item { padding: 12px; border-radius: 8px; background: rgba(15,23,42,.5); border: 1px solid rgba(71,85,105,.35); display: flex; flex-direction: column; gap: 10px; }
.pp-item.select-item.on { border-color: rgba(34,211,238,.5); }
.pp-item.decided.approved { border-color: rgba(74,222,128,.4); }
.pp-item.decided.rejected { opacity: .7; }
.pp-check { display: flex; gap: 10px; align-items: flex-start; cursor: pointer; }
.pp-check input { margin-top: 4px; }
.pp-text { display: flex; gap: 10px; font-size: 14px; color: #e2e8f0; line-height: 1.45; }
.pp-num { font-family: var(--font-mono); color: #38bdf8; flex-shrink: 0; }
.pp-tags { display: flex; flex-wrap: wrap; gap: 6px; padding-left: 26px; }
.pp-tag { font-size: 12px; padding: 3px 8px; border-radius: 999px; background: rgba(71,85,105,.35); color: #cbd5e1; }
.pp-status { font-size: 13px; }
.pp-status.ok { color: #86efac; }
.pp-status.no { color: #fca5a5; }
.pp-form { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px; align-items: end; }
.pp-buttons { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.pp-buttons { grid-column: 1 / -1; }
.pp-buttons button, .pp-primary, .pp-secondary, .pp-approve, .pp-reject { padding: 8px 14px; border-radius: 6px; font-size: 13px; cursor: pointer; border: none; }
.pp-buttons button:disabled, .pp-primary:disabled { opacity: .45; cursor: not-allowed; }
.pp-primary { background: var(--accent-cyan, #22d3ee); color: #04141a; font-weight: 600; }
.pp-secondary { background: transparent; color: #cbd5e1; border: 1px solid rgba(148,163,184,.4) !important; }
.pp-approve { background: var(--accent-cyan, #22d3ee); color: #04141a; font-weight: 600; }
.pp-reject { background: transparent; color: #fca5a5; border: 1px solid rgba(248,113,113,.5) !important; }
</style>
