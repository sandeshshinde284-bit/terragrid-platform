<template>
  <div class="tab-overview">
    <!-- 3. AI report status banner -->
    <section class="report-banner" :class="bannerState">
      <div class="banner-copy">
        <span class="banner-kicker">{{ bannerKicker }}</span>
        <p class="banner-text">{{ bannerText }}</p>
        <p v-if="reportError" class="banner-error" role="alert">{{ reportError }}</p>
      </div>
      <div class="banner-actions">
        <span v-if="report && report.generated_at" class="banner-time">Generated {{ formatTime(report.generated_at) }}</span>
        <button v-if="report" class="btn primary" :disabled="isGenerating" @click="emit('generate')">
          <span v-if="isGenerating" class="spin">⟳</span>
          {{ isGenerating ? 'Generating...' : 'Update crisis report' }}
        </button>
        <button v-else class="btn primary" :disabled="isGenerating" @click="emit('generate')">
          <span v-if="isGenerating" class="spin">⟳</span>
          {{ isGenerating ? 'Generating...' : 'Generate full report' }}
        </button>
        <button class="btn outline" :disabled="exportingZip" @click="emit('exportZip')">
          {{ exportingZip ? 'Compiling...' : 'Export SitRep (ZIP)' }}
        </button>
      </div>
    </section>

    <!-- 4. Incident snapshot: primary metrics -->
    <section class="block">
      <h2 class="block-title">Incident snapshot</h2>
      <div class="metric-row">
        <article class="metric">
          <span class="metric-label">Threat score</span>
          <strong class="metric-value">
            <template v-if="incident.threatScore != null">{{ incident.threatScore }}<small>/100</small></template>
            <template v-else>Not scored</template>
          </strong>
          <div class="bar"><span class="bar-fill" :style="{ width: `${incident.threatScore ?? 0}%` }"></span></div>
          <span class="metric-note">Risk score from impact analysis. Not a casualty probability.</span>
        </article>
        <article class="metric">
          <span class="metric-label">Est. population exposed</span>
          <strong class="metric-value">{{ fmtOrNa(incident.affectedPopulation, n => `~${Math.round(n).toLocaleString()}`) }}</strong>
          <span class="metric-note">People in potential impact zone. An estimate, not confirmed casualties or evacuations.</span>
        </article>
        <article class="metric">
          <span class="metric-label">Est. exposure area</span>
          <strong class="metric-value">{{ fmtOrNa(incident.affectedArea, n => `~${Math.round(n).toLocaleString()} km²`) }}</strong>
          <span class="metric-note">Based on current impact analysis.</span>
        </article>
        <article class="metric">
          <span class="metric-label">Incident status</span>
          <strong class="metric-value status">{{ statusLabel }}</strong>
          <span class="metric-note">{{ detectedAgo }}</span>
        </article>
      </div>

      <!-- 5. Supporting metadata -->
      <div class="meta-row">
        <div class="meta">
          <span class="meta-label">Primary data source</span>
          <strong>{{ incident.source || 'Not available' }}</strong>
          <small>{{ ingestText }}</small>
        </div>
        <div class="meta">
          <span class="meta-label">Detection confidence</span>
          <strong>Not available</strong>
          <small>The source does not report a per-event confidence.</small>
        </div>
        <div class="meta">
          <span class="meta-label">Forecast availability</span>
          <strong>{{ forecast.title }}</strong>
          <small>{{ forecast.note }}</small>
        </div>
        <div class="meta">
          <span class="meta-label">Coordinates</span>
          <strong>{{ coordsText }}</strong>
          <small>{{ incident.location || 'Location not available' }}</small>
        </div>
      </div>
    </section>

    <!-- 6–7. Situation summary and AI decision support -->
    <div class="two-col">
      <section class="block panel">
        <span class="kicker">Situation summary</span>
        <span v-if="report && report.situational_assessment" class="chip ai">AI-generated, not verified</span>
        <span v-else class="chip neutral">Factual summary from incident data</span>
        <p class="body-text">{{ situationText }}</p>

        <dl class="facts">
          <div><dt>Incident class</dt><dd>{{ typeLabel }}</dd></div>
          <div v-if="magnitude != null"><dt>Magnitude</dt><dd>{{ magnitude }}</dd></div>
          <div v-if="depthKm != null"><dt>Depth</dt><dd>{{ depthKm }} km</dd></div>
        </dl>
      </section>

      <section class="block panel">
        <span class="kicker">AI decision support</span>
        <h3 class="panel-title">Recommended actions</h3>
        <span class="chip ai">AI generated</span>

        <GenerationNotice v-if="isGenerating" :startedAt="generationStartedAt ?? null" />
        <p v-if="!report && !isGenerating" class="empty">No crisis report yet. Generate the full report to see AI recommendations.</p>
        <p v-else-if="report && !actions.length" class="empty">The latest report has no recommended actions.</p>
        <ol v-else-if="actions.length" class="actions">
          <li v-for="(action, i) in actions" :key="i">
            <span class="num">{{ String(i + 1).padStart(2, '0') }}</span>
            <span class="action-text">{{ action }}</span>
          </li>
        </ol>

        <div class="review-row">
          <button class="btn outline cyan" :disabled="!actions.length" @click="emit('reviewRecommendations')">
            Review all recommendations →
          </button>
          <p class="review-note">
            AI-generated recommendations require human review. Open the Response tab to review and convert selected recommendations into an operational plan.
          </p>
        </div>
      </section>
    </div>

    <!-- 8. AI-estimated resource requirements -->
    <section class="block">
      <h2 class="block-title">AI-estimated resource requirements</h2>
      <div class="warning">
        These are AI-estimated requirements based on the current assessment, not confirmed allocations. Actual deployment depends on approval, resource availability and coordination with relevant agencies.
      </div>

      <p v-if="!report" class="empty">Resource estimates are not available until a crisis report is generated.</p>
      <p v-else-if="!resources.length" class="empty">The latest report does not include resource estimates.</p>
      <div v-else class="resource-row">
        <article v-for="r in resources" :key="r.key" class="resource">
          <div class="resource-head">
            <span class="resource-icon" aria-hidden="true">{{ r.icon }}</span>
            <span class="badge">AI estimated</span>
          </div>
          <span class="resource-type">{{ r.label }}</span>
          <strong class="resource-qty">{{ r.quantity }} <small v-if="r.unit">{{ r.unit }}</small></strong>
          <span v-if="r.purpose" class="resource-purpose">{{ r.purpose }}</span>
          <span class="resource-note">{{ r.priorityLabel }}<template v-if="r.location"> · {{ r.location }}</template></span>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import GenerationNotice from './GenerationNotice.vue'
import { parseServerTime } from '@/utils/time'

const props = defineProps<{
  incident: any
  details: any | null   // raw fields from GET /api/v1/incidents/{id}: ingested_at, magnitude, depth_km
  report: any | null    // latest saved crisis report: version, generated_at, dossier fields
  isGenerating: boolean
  generationStartedAt?: number | null
  reportError: string | null
  exportingZip: boolean
}>()

const emit = defineEmits<{
  generate: []
  exportZip: []
  reviewRecommendations: []
}>()

// Relative times refresh once a minute.
const now = ref(Date.now())
let timer: number | undefined
onMounted(() => { timer = window.setInterval(() => { now.value = Date.now() }, 60000) })
onUnmounted(() => { if (timer) clearInterval(timer) })

const NA = 'Not available'

const fmtOrNa = (value: number | null | undefined, format: (n: number) => string) =>
  typeof value === 'number' && !Number.isNaN(value) ? format(value) : NA

const formatTime = (iso: string) => {
  const d = parseServerTime(iso)
  return d ? d.toLocaleString() : 'time not recorded'
}

const elapsed = (value: unknown): string | null => {
  const date = parseServerTime(value)
  if (!date) return null
  const mins = Math.max(0, Math.floor((now.value - date.getTime()) / 60000))
  const h = Math.floor(mins / 60)
  return h ? `${h}h ${mins % 60}m ago` : `${mins}m ago`
}

const TYPE_LABELS: Record<string, string> = {
  flood: 'Flood', earthquake: 'Earthquake', fire: 'Wildfire', storm: 'Storm',
  volcano: 'Volcano', landslide: 'Landslide', weather: 'Weather',
}
const typeLabel = computed(() => TYPE_LABELS[props.incident.type] || props.incident.type || NA)

const statusLabel = computed(() => {
  const s = props.incident.status || ''
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : NA
})

const detectedAgo = computed(() => {
  const ago = elapsed(props.incident.detectionTime)
  return ago ? `Detected ${ago}` : 'Detection time not available'
})

const ingestText = computed(() => {
  const ago = elapsed(props.details?.ingested_at)
  return ago ? `Last ingest ${ago}` : 'Ingest time unavailable'
})

const coordsText = computed(() => {
  const c = props.incident.coordinates
  if (!c || c[0] == null || c[1] == null) return NA
  return `${Number(c[0]).toFixed(4)}, ${Number(c[1]).toFixed(4)}`
})

const magnitude = computed(() => (typeof props.details?.magnitude === 'number' ? props.details.magnitude : null))
const depthKm = computed(() => (typeof props.details?.depth_km === 'number' ? props.details.depth_km : null))

// Forecast depends on the hazard. Only show a projection the model produced for this hazard.
const forecast = computed(() => {
  if (props.incident.type === 'earthquake') {
    return { title: 'No spread forecast available', note: 'Monitor aftershocks and secondary hazards' }
  }
  if (typeof props.incident.forecast6h === 'number') {
    return { title: `${Math.round(props.incident.forecast6h)} km² in 6 hours`, note: 'Model estimate, not verified' }
  }
  return { title: NA, note: 'No spread forecast for this hazard type' }
})

const bannerState = computed(() => (props.isGenerating ? 'busy' : props.report ? 'ready' : 'empty'))
const bannerKicker = computed(() => {
  if (props.isGenerating) return 'GENERATING CRISIS REPORT'
  return props.report ? 'AI REPORT GENERATED · NOT VERIFIED' : 'CRISIS REPORT NOT GENERATED'
})
const bannerText = computed(() => {
  if (props.isGenerating) return 'The AI assessment is running. Recommendations and resource estimates will update when it finishes.'
  if (props.report) {
    return 'This report was generated using available incident data and AI analysis. Recommendations and resource estimates require review and verification by an authorized officer.'
  }
  return 'Generate an AI-assisted incident assessment to review potential impacts, recommended actions and estimated resource requirements.'
})

// Summary: the AI text when present; otherwise a plain summary built only from fields that exist.
const situationText = computed(() => {
  if (props.report?.situational_assessment) return props.report.situational_assessment
  const i = props.incident
  const score = i.threatScore != null ? `threat score ${i.threatScore}/100` : 'no threat score yet'
  const area = i.affectedArea != null ? `about ${Math.round(i.affectedArea)} km²` : 'an area not yet estimated'
  const pop = i.affectedPopulation != null ? `about ${Math.round(i.affectedPopulation).toLocaleString()} people` : 'an exposed population not yet estimated'
  return `${typeLabel.value} reported near ${i.location || 'an unknown location'}, with ${score}. Estimated exposure: ${area}, ${pop} (model estimates). Field verification is required to establish damage, access and response needs.`
})

const actions = computed<string[]>(() => (props.report?.immediate_actions || []).slice(0, 5))

const RESOURCE_META: Record<string, { label: string; icon: string }> = {
  'Helicopter': { label: 'Helicopters', icon: '🚁' },
  'Ambulance': { label: 'Ambulances', icon: '🚑' },
  'Fire Engine': { label: 'Fire engines', icon: '🚒' },
  'Water Truck': { label: 'Water trucks', icon: '💧' },
  'Search Dog': { label: 'Search dogs', icon: '🐕' },
  'Rescue Team': { label: 'Rescue teams', icon: '🧗' },
  'Mobile Hospital': { label: 'Mobile hospitals', icon: '🏥' },
  'Water Purification Unit': { label: 'Water purification units', icon: '🚰' },
}
const PRIORITY_LABEL: Record<number, string> = { 1: 'Immediate', 2: 'High priority', 3: 'Staged' }

// Estimates from the report's resource_matrix, grouped by resource type. Nothing is invented.
const resources = computed(() => {
  const rows: any[] = props.report?.resource_matrix || []
  const groups = new Map<string, { quantity: number; unit: string; priority: number | null; location: string | null; purpose: string | null }>()
  for (const r of rows) {
    const name = String(r.resource || '')
    // A null quantity means the input does not support a number. It is left out, not counted as 0.
    const qty = r.quantity === null || r.quantity === undefined ? NaN : Number(r.quantity)
    if (!name || Number.isNaN(qty)) continue
    const g = groups.get(name) || { quantity: 0, unit: r.unit_measure || '', priority: null, location: r.deployment_location || null, purpose: null }
    // Purpose comes from the report only. Older reports do not include it, so nothing is shown.
    if (!g.purpose && typeof r.purpose === 'string' && r.purpose.trim()) g.purpose = r.purpose.trim()
    g.quantity += qty
    const p = Number(r.priority)
    if (!Number.isNaN(p) && (g.priority === null || p < g.priority)) g.priority = p
    groups.set(name, g)
  }
  return Array.from(groups.entries()).map(([name, g]) => ({
    key: name,
    label: RESOURCE_META[name]?.label || name,
    icon: RESOURCE_META[name]?.icon || '•',
    quantity: g.quantity,
    unit: g.unit,
    priorityLabel: g.priority !== null ? (PRIORITY_LABEL[g.priority] || '') : '',
    location: g.location,
    purpose: g.purpose,
  }))
})
</script>

<style scoped>
.tab-overview { display: flex; flex-direction: column; gap: 16px; color: #e2e8f0; }
.block { background: #0f172a; border: 1px solid rgba(56, 189, 248, 0.16); border-radius: 10px; padding: 18px; display: flex; flex-direction: column; gap: 12px; }
.block-title { margin: 0; font-size: 16px; color: #f8fafc; }
.panel { min-width: 0; }
.two-col { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; align-items: start; }
.kicker { font-size: 11px; letter-spacing: 0.08em; color: #64748b; text-transform: uppercase; }
.panel-title { margin: 0; font-size: 18px; color: #f8fafc; }
.body-text { margin: 0; line-height: 1.6; color: #cbd5e1; font-size: 14px; }
.empty { margin: 0; color: #94a3b8; font-size: 14px; }

.chip { align-self: flex-start; font-size: 11px; padding: 3px 8px; border-radius: 999px; border: 1px solid; }
.chip.ai { color: #67e8f9; border-color: rgba(34, 211, 238, 0.5); }
.chip.neutral { color: #94a3b8; border-color: rgba(148, 163, 184, 0.4); }
.badge { font-size: 10px; padding: 2px 6px; border-radius: 4px; color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.5); }

/* Report banner */
.report-banner { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 14px; padding: 16px 18px; border-radius: 10px; border: 1px solid; }
.report-banner.ready { background: rgba(120, 53, 15, 0.22); border-color: rgba(245, 158, 11, 0.5); }
.report-banner.empty { background: #0f172a; border-color: rgba(56, 189, 248, 0.25); }
.report-banner.busy { background: #0f172a; border-color: rgba(34, 211, 238, 0.5); }
.banner-copy { display: flex; flex-direction: column; gap: 4px; max-width: 760px; min-width: 0; }
.banner-kicker { font-size: 13px; font-weight: 700; letter-spacing: 0.04em; }
.report-banner.ready .banner-kicker { color: #fbbf24; }
.report-banner.empty .banner-kicker, .report-banner.busy .banner-kicker { color: #67e8f9; }
.banner-text { margin: 0; font-size: 13px; color: #cbd5e1; line-height: 1.5; }
.banner-error { margin: 4px 0 0; font-size: 13px; color: #fca5a5; }
.banner-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.banner-time { font-size: 12px; color: #94a3b8; }

.btn { display: inline-flex; align-items: center; gap: 6px; padding: 9px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: 1px solid transparent; white-space: nowrap; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn.primary { background: #22d3ee; color: #04141a; }
.btn.primary:hover:not(:disabled) { background: #67e8f9; }
.btn.outline { background: transparent; color: #e2e8f0; border-color: rgba(148, 163, 184, 0.45); }
.btn.outline.cyan { color: #67e8f9; border-color: rgba(34, 211, 238, 0.6); }
.btn.outline:hover:not(:disabled) { border-color: #22d3ee; }
.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Metrics */
.metric-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.metric { background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(56, 189, 248, 0.14); border-radius: 8px; padding: 14px; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.metric-label { font-size: 12px; color: #94a3b8; }
.metric-value { font-size: 26px; color: #f8fafc; line-height: 1.15; overflow-wrap: anywhere; }
.metric-value small { font-size: 14px; color: #94a3b8; }
.metric-value.status { color: #4ade80; font-size: 20px; }
.metric-note { font-size: 12px; color: #64748b; line-height: 1.4; }
.bar { height: 5px; border-radius: 99px; background: rgba(100, 116, 139, 0.25); overflow: hidden; margin-top: 4px; }
.bar-fill { display: block; height: 100%; background: #ef4444; }

.meta-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.meta { display: flex; flex-direction: column; gap: 3px; padding: 10px 12px; border-left: 2px solid rgba(56, 189, 248, 0.25); min-width: 0; }
.meta-label { font-size: 11px; color: #64748b; }
.meta strong { font-size: 14px; color: #e2e8f0; overflow-wrap: anywhere; }
.meta small { font-size: 12px; color: #64748b; line-height: 1.4; }

/* Situation summary */
.facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin: 6px 0 0; }
.facts div { display: flex; flex-direction: column; gap: 2px; }
.facts dt { font-size: 11px; color: #64748b; }
.facts dd { margin: 0; font-size: 14px; color: #e2e8f0; }

/* Recommendations */
.actions { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.actions li { display: flex; gap: 12px; align-items: flex-start; }
.num { font-family: var(--font-mono, ui-monospace, monospace); font-size: 12px; color: #22d3ee; flex-shrink: 0; padding-top: 2px; }
.action-text { font-size: 14px; color: #e2e8f0; line-height: 1.5; }
.review-row { display: flex; flex-direction: column; gap: 8px; margin-top: auto; padding-top: 10px; border-top: 1px solid rgba(56, 189, 248, 0.12); }
.review-row .btn { align-self: flex-start; }
.review-note { margin: 0; font-size: 12px; color: #64748b; line-height: 1.5; }

/* Resources */
.warning { padding: 10px 12px; border-radius: 6px; background: rgba(120, 53, 15, 0.22); border: 1px solid rgba(245, 158, 11, 0.45); color: #fde68a; font-size: 13px; line-height: 1.5; }
.resource-row { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
.resource { background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(56, 189, 248, 0.14); border-radius: 8px; padding: 14px; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.resource-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.resource-icon { font-size: 20px; }
.resource-type { font-size: 13px; color: #94a3b8; }
.resource-qty { font-size: 22px; color: #f8fafc; }
.resource-qty small { font-size: 13px; color: #94a3b8; }
.resource-note { font-size: 12px; color: #64748b; line-height: 1.4; }
.resource-purpose { font-size: 13px; color: #cbd5e1; line-height: 1.4; }

/* Responsive: tablet and mobile */
@media (max-width: 1100px) {
  .metric-row, .meta-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .resource-row { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 800px) {
  .two-col { grid-template-columns: minmax(0, 1fr); }
  .resource-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 520px) {
  .metric-row, .meta-row, .resource-row { grid-template-columns: minmax(0, 1fr); }
  .banner-actions { width: 100%; }
}
</style>
