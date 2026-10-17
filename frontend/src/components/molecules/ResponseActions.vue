<template>
  <section class="response-actions glass-panel">
    <header class="ra-head">
      <span class="section-kicker">RESPONSE ACTIONS</span>
      <h3>Operator actions for this incident</h3>
      <p class="access-note">
        Demo mode: there is no login yet. Names typed below are recorded exactly as entered and are not verified.
        Nothing is sent to anyone unless an operator approves it here.
      </p>
      <div class="state-chips">
        <span class="chip" :class="acknowledged ? 'ok' : 'todo'">{{ acknowledged ? 'Acknowledged' : 'Not acknowledged' }}</span>
        <span class="chip">Status: {{ statusLabel }}</span>
        <span class="chip">Tasks open: {{ openTaskCount }} of {{ tasks.length }}</span>
        <span class="chip">Alerts delivered: {{ deliveredAlertCount }}</span>
      </div>
    </header>

    <label class="field">
      <span>Operator name (required)</span>
      <input v-model="actor" maxlength="120" placeholder="e.g. Duty officer, District control room" />
    </label>

    <div v-if="error" class="ra-error" role="alert">{{ error }}</div>

    <!-- 1. Acknowledge -->
    <div class="ra-block">
      <h4>1. Acknowledge the incident</h4>
      <p class="hint">Records that someone has reviewed this incident.</p>
      <button class="ra-btn primary" :disabled="!canAct || acknowledged" @click="acknowledge">Acknowledge incident</button>
      <p v-if="acknowledged" class="hint">Acknowledged by {{ state.acknowledged_by }} at {{ fmtTime(state.acknowledged_at) }}</p>
    </div>

    <!-- 2. Status -->
    <div class="ra-block">
      <h4>2. Update incident status</h4>
      <div class="row">
        <select v-model="newStatus" class="ra-input">
          <option value="open">Open</option>
          <option value="investigating">Investigating</option>
          <option value="responding">Responding</option>
          <option value="resolved">Resolved</option>
        </select>
        <input v-model="statusNote" class="ra-input grow" maxlength="1000" placeholder="Note (optional)" />
        <button class="ra-btn" :disabled="!canAct" @click="setStatus">Update status</button>
      </div>
    </div>

    <!-- 3. Tasks -->
    <div class="ra-block">
      <h4>3. Assign response tasks</h4>
      <div class="row">
        <input v-model="taskTitle" class="ra-input grow" maxlength="255" placeholder="Task, e.g. Verify road access to hospital" />
        <input v-model="taskAssignee" class="ra-input" maxlength="120" placeholder="Assignee" />
        <button class="ra-btn" :disabled="!canAct || !taskTitle.trim() || !taskAssignee.trim()" @click="addTask">Add task</button>
      </div>
      <ul v-if="tasks.length" class="ra-list">
        <li v-for="t in tasks" :key="t.id">
          <span class="grow">{{ t.title }} <span class="muted">→ {{ t.assignee }}</span></span>
          <select class="ra-input" :value="t.status" :disabled="!canAct" @change="setTask(t.id, ($event.target as HTMLSelectElement).value)">
            <option value="open">Open</option>
            <option value="in_progress">In progress</option>
            <option value="done">Done</option>
          </select>
        </li>
      </ul>
      <p v-else class="hint">No tasks yet.</p>
    </div>

    <!-- 4. Alerts -->
    <div class="ra-block">
      <h4>4. Alerts (sent only after approval)</h4>
      <p v-if="!emailConfigured" class="hint warn">Email sending is not configured on this server. You can still draft and review alerts, but they cannot be sent.</p>
      <p v-else-if="!emailRecipients.length" class="hint warn">No email recipients are configured. Add them in Settings first.</p>

      <form class="draft-form" @submit.prevent="draftAlert">
        <input v-model="draftSubject" class="ra-input" maxlength="255" placeholder="Subject" />
        <textarea v-model="draftBody" class="ra-input" rows="4" maxlength="5000" placeholder="Message, reviewed by the operator before approval"></textarea>
        <div class="recipients">
          <label v-for="r in emailRecipients" :key="r.email" class="check">
            <input type="checkbox" :value="r.email" v-model="draftRecipients" />
            <span>{{ r.label }} <span class="muted">{{ r.email }}</span></span>
          </label>
        </div>
        <button class="ra-btn" type="submit" :disabled="!canAct || !draftSubject.trim() || !draftBody.trim() || !draftRecipients.length">Create draft</button>
      </form>

      <ul v-if="alerts.length" class="ra-list alerts">
        <li v-for="a in alerts" :key="a.id" class="alert-item">
          <div class="alert-main">
            <strong>{{ a.subject }}</strong>
            <span class="pill" :class="a.status">{{ alertStatusLabel(a.status) }}</span>
          </div>
          <div class="muted small">Drafted by {{ a.created_by }} at {{ fmtTime(a.created_at) }}<span v-if="a.decided_by"> · decided by {{ a.decided_by }}</span></div>
          <div class="muted small">To: {{ a.recipients.join(', ') }}</div>
          <p class="alert-body">{{ a.body }}</p>
          <ul v-if="a.delivery_results" class="delivery">
            <li v-for="d in a.delivery_results" :key="d.recipient" :class="d.success ? 'ok' : 'bad'">
              {{ d.recipient }}: {{ d.success ? 'delivered' : 'not delivered' }}<span v-if="!d.success && d.detail"> ({{ d.detail }})</span>
            </li>
          </ul>
          <div v-if="a.status === 'draft'" class="row">
            <button class="ra-btn primary" :disabled="!canAct" @click="approveAlert(a.id)">Approve and send</button>
            <button class="ra-btn" :disabled="!canAct" @click="rejectAlert(a.id)">Reject</button>
          </div>
        </li>
      </ul>
    </div>

    <!-- 5. Audit log -->
    <div class="ra-block">
      <h4>Audit log</h4>
      <ol v-if="log.length" class="ra-list log">
        <li v-for="(entry, i) in log" :key="i">
          <span class="muted small">{{ fmtTime(entry.at) }}</span>
          <span class="small">{{ entry.actor }}</span>
          <span class="small">{{ describe(entry) }}</span>
        </li>
      </ol>
      <p v-else class="hint">No actions recorded yet.</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

const props = defineProps<{ incidentId: string }>()

const host = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)
const base = computed(() => `${host}/api/v1/incidents/${props.incidentId}/response`)

const state = ref<any>({ acknowledged: false, status: 'open', tasks: [], alerts: [], log: [] })
const emailRecipients = ref<{ label: string; email: string }[]>([])
const emailConfigured = ref(true)
const actor = ref('')
const busy = ref(false)
const error = ref('')

const newStatus = ref('investigating')
const statusNote = ref('')
const taskTitle = ref('')
const taskAssignee = ref('')
const draftSubject = ref('')
const draftBody = ref('')
const draftRecipients = ref<string[]>([])

const canAct = computed(() => !!actor.value.trim() && !busy.value)
const acknowledged = computed(() => !!state.value.acknowledged)
const tasks = computed<any[]>(() => state.value.tasks || [])
const alerts = computed<any[]>(() => state.value.alerts || [])
const log = computed<any[]>(() => state.value.log || [])
const openTaskCount = computed(() => tasks.value.filter(t => t.status !== 'done').length)
const deliveredAlertCount = computed(() => alerts.value.filter(a => a.status === 'sent').length)

const STATUS_LABELS: Record<string, string> = {
  open: 'Open',
  investigating: 'Investigating',
  responding: 'Responding',
  resolved: 'Resolved',
}
const statusLabel = computed(() => STATUS_LABELS[state.value.status] || 'Open')

function alertStatusLabel(s: string): string {
  return ({ draft: 'Awaiting approval', sent: 'Sent', partially_failed: 'Partly sent', failed: 'Not sent', rejected: 'Rejected' } as Record<string, string>)[s] || s
}

function fmtTime(iso?: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`)
  return isNaN(d.getTime()) ? iso : d.toLocaleString()
}

function describe(entry: any): string {
  const d = entry.detail || {}
  switch (entry.action) {
    case 'acknowledge': return 'acknowledged the incident'
    case 'status_change': return `set status to ${STATUS_LABELS[d.status] || d.status}${d.note ? `: ${d.note}` : ''}`
    case 'task_created': return `added task "${d.title}" for ${d.assignee}`
    case 'task_updated': return `set task #${d.task_id} to ${d.status}`
    case 'alert_drafted': return `drafted an alert to ${(d.recipients || []).length} recipient(s)`
    case 'alert_approved': return `approved alert #${d.alert_id}`
    case 'alert_sent': return `alert #${d.alert_id} ${alertStatusLabel(d.status).toLowerCase()} (${d.delivered} of ${d.total} delivered)`
    case 'alert_rejected': return `rejected alert #${d.alert_id}${d.reason ? `: ${d.reason}` : ''}`
    default: return entry.action
  }
}

async function call(path: string, method: 'GET' | 'POST' = 'GET', body?: Record<string, unknown>): Promise<any | null> {
  busy.value = true
  error.value = ''
  try {
    const res = await fetch(`${base.value}${path}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      error.value = typeof data.detail === 'string' ? data.detail : `Request failed (${res.status})`
      return null
    }
    return data
  } catch {
    error.value = 'Cannot reach the server. Nothing was saved.'
    return null
  } finally {
    busy.value = false
  }
}

async function reload() {
  const data = await call('')
  if (data) state.value = data
}

async function loadRecipients() {
  try {
    const res = await fetch(`${host}/api/v1/prepare/alerts/email-recipients`)
    const data = await res.json()
    emailRecipients.value = data.recipients || []
    emailConfigured.value = !!data.configured
  } catch {
    emailConfigured.value = false
  }
}

function actorName(): string {
  return actor.value.trim()
}

async function acknowledge() {
  const data = await call('/acknowledge', 'POST', { actor: actorName() })
  if (data) state.value = data
}

async function setStatus() {
  const data = await call('/status', 'POST', { actor: actorName(), status: newStatus.value, note: statusNote.value.trim() || null })
  if (data) {
    state.value = data
    statusNote.value = ''
  }
}

async function addTask() {
  const data = await call('/tasks', 'POST', { actor: actorName(), title: taskTitle.value.trim(), assignee: taskAssignee.value.trim() })
  if (data) {
    state.value = data
    taskTitle.value = ''
    taskAssignee.value = ''
  }
}

async function setTask(taskId: number, status: string) {
  const data = await call(`/tasks/${taskId}/status`, 'POST', { actor: actorName(), status })
  if (data) state.value = data
}

async function draftAlert() {
  const data = await call('/alerts', 'POST', {
    actor: actorName(),
    subject: draftSubject.value.trim(),
    body: draftBody.value.trim(),
    recipients: draftRecipients.value,
  })
  if (data) {
    state.value = data
    draftSubject.value = ''
    draftBody.value = ''
    draftRecipients.value = []
  }
}

async function approveAlert(alertId: number) {
  if (!window.confirm('Send this alert to the listed recipients now?')) return
  const data = await call(`/alerts/${alertId}/approve`, 'POST', { actor: actorName() })
  if (data) state.value = data
}

async function rejectAlert(alertId: number) {
  const reason = window.prompt('Reason for rejecting (optional)') || null
  const data = await call(`/alerts/${alertId}/reject`, 'POST', { actor: actorName(), reason })
  if (data) state.value = data
}

onMounted(() => {
  reload()
  loadRecipients()
})

watch(() => props.incidentId, () => reload())
</script>

<style scoped>
.response-actions { padding: 20px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 16px; }
.ra-head h3 { margin: 4px 0 6px; font-size: 18px; color: var(--text-primary); }
.access-note { margin: 0; font-size: 14px; color: #fbbf24; }
.state-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.chip { font-size: 13px; padding: 4px 10px; border-radius: 999px; background: rgba(148,163,184,0.15); color: #cbd5e1; }
.chip.ok { background: rgba(74,222,128,0.15); color: #4ade80; }
.chip.todo { background: rgba(251,191,36,0.15); color: #fbbf24; }
.field { display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #cbd5e1; }
.ra-block { border-top: 1px solid rgba(255,255,255,0.08); padding-top: 14px; display: flex; flex-direction: column; gap: 10px; }
.ra-block h4 { margin: 0; font-size: 15px; color: var(--text-primary); }
.hint { margin: 0; font-size: 13px; color: #94a3b8; }
.hint.warn { color: #fbbf24; }
.muted { color: #64748b; }
.small { font-size: 13px; }
.row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.grow { flex: 1; min-width: 180px; }
.ra-input { background: rgba(15,23,42,0.7); border: 1px solid rgba(255,255,255,0.12); color: #e2e8f0; border-radius: 6px; padding: 8px 10px; font-size: 14px; }
textarea.ra-input { width: 100%; box-sizing: border-box; }
.ra-btn { background: rgba(148,163,184,0.15); color: #e2e8f0; border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; padding: 8px 12px; font-size: 14px; cursor: pointer; }
.ra-btn.primary { background: rgba(56,189,248,0.2); border-color: rgba(56,189,248,0.5); color: #bae6fd; }
.ra-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.ra-error { color: #fca5a5; font-size: 14px; background: rgba(239,68,68,0.12); border-radius: 6px; padding: 8px 10px; }
.ra-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.ra-list li { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; font-size: 14px; color: #cbd5e1; }
.ra-list.log li { gap: 8px; }
.draft-form { display: flex; flex-direction: column; gap: 8px; }
.recipients { display: flex; flex-wrap: wrap; gap: 12px; }
.check { display: flex; gap: 6px; align-items: center; font-size: 14px; color: #cbd5e1; }
.alert-item { flex-direction: column; align-items: stretch !important; background: rgba(15,23,42,0.5); border-radius: 8px; padding: 12px; }
.alert-main { display: flex; justify-content: space-between; gap: 10px; align-items: center; }
.alert-body { margin: 4px 0; white-space: pre-wrap; font-size: 14px; color: #e2e8f0; }
.pill { font-size: 12px; padding: 2px 8px; border-radius: 4px; background: rgba(148,163,184,0.15); }
.pill.draft { color: #fbbf24; background: rgba(251,191,36,0.15); }
.pill.sent { color: #4ade80; background: rgba(74,222,128,0.15); }
.pill.partially_failed, .pill.failed, .pill.rejected { color: #fca5a5; background: rgba(239,68,68,0.15); }
.delivery { list-style: none; padding: 0; margin: 4px 0 0; font-size: 13px; }
.delivery li.ok { color: #4ade80; }
.delivery li.bad { color: #fca5a5; }
</style>
