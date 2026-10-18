<template>
  <div class="tab-overview">
    <!-- 3. AI report status banner -->
    <section class="report-banner" :class="bannerState">
      <div class="banner-left">
        <div class="warning-circle">
          <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
        </div>
        <div class="banner-copy">
          <span class="banner-kicker">{{ bannerKicker }}</span>
          <p class="banner-text">{{ bannerText }}</p>
          <p v-if="reportError" class="banner-error" role="alert">{{ reportError }}</p>
        </div>
      </div>
      <div class="banner-actions">
        <span v-if="report && report.generated_at" class="banner-time">Generated: {{ formatTime(report.generated_at) }}</span>
        <button v-if="report" class="btn primary" :disabled="isGenerating" @click="emit('generate')">
          <span v-if="isGenerating" class="spin">⟳</span>
          <span v-else>⟳</span>
          {{ isGenerating ? 'Generating...' : 'Update Crisis Report' }}
        </button>
        <button v-else class="btn primary" :disabled="isGenerating" @click="emit('generate')">
          <span v-if="isGenerating" class="spin">⟳</span>
          <span v-else>⟳</span>
          {{ isGenerating ? 'Generating...' : 'Generate full report' }}
        </button>
        <button class="btn outline" :disabled="exportingZip" @click="emit('exportZip')">
          <span v-if="exportingZip" class="spin">⟳</span>
          <span v-else>📥</span>
          {{ exportingZip ? 'Compiling...' : 'Export SitRep (ZIP)' }}
        </button>
      </div>
    </section>

    <!-- 4. Incident snapshot: primary metrics -->
    <section class="block">
      <div class="panel-header-row">
        <span class="section-icon">📋</span>
        <h2 class="block-title">Incident Snapshot</h2>
      </div>
      <div class="snapshot-grid">
        
        <article class="snapshot-tile">
          <div class="tile-icon-circle threat-icon">🎯</div>
          <div class="tile-content">
            <span class="metric-label">Threat score</span>
            <strong class="metric-value threat-value">
              <template v-if="incident.threatScore != null">{{ incident.threatScore }}<small>/100</small></template>
              <template v-else>Not scored</template>
            </strong>
            <div class="bar"><span class="bar-fill" :style="{ width: `${incident.threatScore ?? 0}%` }"></span></div>
          </div>
        </article>

        <article class="snapshot-tile">
          <div class="tile-icon-circle blue-icon">👥</div>
          <div class="tile-content">
            <span class="metric-label">Est. population exposed</span>
            <strong class="metric-value">{{ fmtOrNa(incident.affectedPopulation, n => `~${Math.round(n).toLocaleString()}`) }}</strong>
            <span class="metric-note">People in potential impact zone</span>
          </div>
        </article>

        <article class="snapshot-tile">
          <div class="tile-icon-circle blue-icon">🔲</div>
          <div class="tile-content">
            <span class="metric-label">Est. exposure area</span>
            <strong class="metric-value">{{ fmtOrNa(incident.affectedArea, n => `~${Math.round(n).toLocaleString()} km²`) }}</strong>
            <span class="metric-note">Based on current impact analysis</span>
          </div>
        </article>

        <article class="snapshot-tile">
          <div class="tile-icon-circle green-icon">💓</div>
          <div class="tile-content">
            <span class="metric-label">Incident status</span>
            <strong class="metric-value status-active">{{ statusLabel }}</strong>
            <span class="metric-note">Detected {{ detectedAgo }}</span>
          </div>
        </article>

        <article class="snapshot-tile">
          <div class="tile-icon-circle blue-icon">🗄️</div>
          <div class="tile-content">
            <span class="metric-label">Primary data source</span>
            <strong class="metric-value-small">{{ incident.source || 'Not available' }}</strong>
            <span class="metric-note">{{ ingestText }}</span>
          </div>
        </article>

        <article class="snapshot-tile">
          <div class="tile-icon-circle blue-icon">🎯</div>
          <div class="tile-content">
            <span class="metric-label">Detection confidence</span>
            <strong class="metric-value-small">98%</strong>
            <span class="metric-note">Reported by data source</span>
          </div>
        </article>

        <article class="snapshot-tile">
          <div class="tile-icon-circle blue-icon">📉</div>
          <div class="tile-content">
            <span class="metric-label">Forecast availability</span>
            <strong class="metric-value-small">{{ forecast.title }}</strong>
            <span class="metric-note">{{ forecast.note }}</span>
          </div>
        </article>

        <article class="snapshot-tile">
          <div class="tile-icon-circle blue-icon">🌐</div>
          <div class="tile-content">
            <span class="metric-label">Coordinates</span>
            <strong class="metric-value-small">{{ coordsText }}</strong>
            <span class="metric-note">{{ incident.location || 'Location not available' }}</span>
          </div>
        </article>

      </div>
    </section>

    <!-- 6–7. Situation summary and AI decision support -->
    <div class="two-col">
      <section class="block panel">
        <div class="panel-header-row">
          <span class="section-icon">📄</span>
          <h3 class="panel-title">Situation Summary</h3>
        </div>
        <p class="body-text" style="margin-top: 12px;">{{ situationText }}</p>

        <dl class="facts">
          <div><dt>Incident class</dt><dd>{{ typeLabel }}</dd></div>
          <div v-if="magnitude != null"><dt>Magnitude</dt><dd>{{ magnitude }}</dd></div>
          <div v-if="depthKm != null"><dt>Depth</dt><dd>{{ depthKm }} km</dd></div>
          <div><dt>Operational posture</dt><dd>Full response</dd></div>
        </dl>
      </section>

      <section class="block panel">
        <div class="panel-header-row">
          <span class="section-icon amber">💡</span>
          <div>
            <span class="kicker">AI decision support</span>
            <div style="display:flex; align-items:center; gap:12px;">
              <h3 class="panel-title">Recommended actions</h3>
              <span class="chip ai">AI GENERATED</span>
            </div>
          </div>
        </div>

        <GenerationNotice v-if="isGenerating" :startedAt="generationStartedAt ?? null" />
        <p v-if="!report && !isGenerating" class="empty">No crisis report yet. Generate the full report to see AI recommendations.</p>
        <p v-else-if="report && !actions.length" class="empty">The latest report has no recommended actions.</p>
        <ol v-else-if="actions.length" class="actions-new">
          <li v-for="(action, i) in actions" :key="i">
            <div class="action-number-circle" :class="i === 0 ? 'critical' : (i < 3 ? 'high' : 'medium')">{{ i + 1 }}</div>
            <span class="action-text-new">{{ action }}</span>
            <div class="action-badge-right" :class="i === 0 ? 'critical' : (i < 3 ? 'high' : 'medium')">
               {{ i === 0 ? 'CRITICAL' : (i < 3 ? 'HIGH' : 'MEDIUM') }}
            </div>
          </li>
        </ol>

        <div class="review-row-new">
          <button class="btn-ghost-cyan" :disabled="!actions.length" @click="emit('reviewRecommendations')">
            Review All Recommendations >
          </button>
          <div class="footer-disclaimer">
            <span class="info-icon">ⓘ</span>
            <span class="disclaimer-text">These recommendations are AI-generated and require review and approval by an authorized officer. Review and convert them into a response plan in the Response tab.</span>
          </div>
        </div>
      </section>
    </div>

    <!-- 8. AI-estimated resource requirements -->
    <section class="block">
      <div class="panel-header-row">
        <span class="section-icon">🚛</span>
        <h2 class="block-title">AI-Estimated Resource Requirements</h2>
      </div>
      <div class="warning-amber">
        <span class="info-icon-amber">ⓘ</span>
        <span>These are AI-estimated requirements based on current analysis and are not confirmed allocations. Actual deployment is subject to approval, availability and coordination with relevant agencies.</span>
      </div>

      <p v-if="!report" class="empty">Resource estimates are not available until a crisis report is generated.</p>
      <p v-else-if="!resources.length" class="empty">The latest report does not include resource estimates.</p>
      <div v-else class="resource-row-new">
        <article v-for="r in resources" :key="r.key" class="resource-card-new">
          <div class="res-top">
            <span class="res-icon" :class="r.priorityLabel === 'IMMEDIATE' ? 'critical' : 'high'">{{ r.icon }}</span>
            <span class="badge-amber">AI estimated</span>
          </div>
          <span class="res-name">{{ r.label }}</span>
          <strong class="res-qty">{{ r.quantity }} <small v-if="r.unit">{{ r.unit }}</small></strong>
          <span class="res-bottom">
            <span class="res-priority" :class="r.priorityLabel === 'IMMEDIATE' ? 'critical' : 'high'">{{ r.priorityLabel }}</span>
            <template v-if="r.location"> &middot; <span class="res-loc">{{ r.location }}</span></template>
          </span>
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
.block { background: #0f172a; border: 1px solid rgba(56, 189, 248, 0.16); border-radius: 10px; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.block-title { margin: 0; font-size: 18px; color: #f8fafc; font-weight: 700; }
.panel { min-width: 0; }
.two-col { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; align-items: start; }
.kicker { font-size: 12px; letter-spacing: 0.05em; color: #64748b; text-transform: uppercase; font-weight: 700; }
.panel-title { margin: 0; font-size: 18px; color: #f8fafc; font-weight: 700; }
.body-text { margin: 0; line-height: 1.6; color: #cbd5e1; font-size: 15px; }
.empty { margin: 0; color: #94a3b8; font-size: 14px; }

.chip { align-self: flex-start; font-size: 10px; padding: 4px 8px; border-radius: 4px; font-weight: 700; letter-spacing: 0.5px; }
.chip.ai { color: #38bdf8; background: rgba(56, 189, 248, 0.15); border: 1px solid #38bdf8; }
.chip.neutral { color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.4); }

/* Report banner */
.report-banner { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 16px; padding: 16px 20px; border-radius: 10px; border: 1px solid; }
.report-banner.ready { background: rgba(245, 158, 11, 0.05); border-color: rgba(245, 158, 11, 0.4); }
.report-banner.empty { background: #0f172a; border-color: rgba(56, 189, 248, 0.25); }
.report-banner.busy { background: #0f172a; border-color: rgba(34, 211, 238, 0.5); }

.banner-left { display: flex; align-items: center; gap: 16px; }
.warning-circle { width: 40px; height: 40px; background: #f59e0b; color: #0f172a; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.banner-copy { display: flex; flex-direction: column; gap: 4px; max-width: 760px; min-width: 0; }
.banner-kicker { font-size: 14px; font-weight: 800; letter-spacing: 0.04em; }
.report-banner.ready .banner-kicker { color: #fcd34d; }
.report-banner.empty .banner-kicker, .report-banner.busy .banner-kicker { color: #67e8f9; }
.banner-text { margin: 0; font-size: 13px; color: #fbbf24; line-height: 1.5; }
.banner-error { margin: 4px 0 0; font-size: 13px; color: #fca5a5; }
.banner-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.banner-time { font-size: 12px; color: #94a3b8; margin-right: 8px; }

.btn { display: inline-flex; align-items: center; gap: 6px; padding: 9px 16px; border-radius: 6px; font-size: 13px; font-weight: 700; cursor: pointer; border: 1px solid transparent; white-space: nowrap; transition: all 0.2s; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn.primary { background: #38bdf8; color: #0f172a; border: none; }
.btn.primary:hover:not(:disabled) { background: #7dd3fc; }
.btn.outline { background: transparent; color: #e2e8f0; border-color: rgba(255, 255, 255, 0.2); }
.btn.outline:hover:not(:disabled) { border-color: #38bdf8; color: #38bdf8; }
.spin { display: inline-block; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Snapshot Grid */
.snapshot-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.snapshot-tile { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.15); border-radius: 8px; padding: 20px; display: flex; gap: 16px; align-items: flex-start; }
.tile-icon-circle { width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
.threat-icon { background: rgba(239, 68, 68, 0.15); border: 2px solid #ef4444; }
.blue-icon { background: rgba(56, 189, 248, 0.1); border: 2px solid rgba(56, 189, 248, 0.3); }
.green-icon { background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; }
.tile-content { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.metric-label { font-size: 12px; color: #94a3b8; text-transform: none; margin-bottom: 6px; }
.metric-value { font-size: 26px; font-weight: 800; color: #f8fafc; line-height: 1.1; margin-bottom: 6px; }
.metric-value-small { font-size: 16px; font-weight: 700; color: #f8fafc; line-height: 1.3; margin-bottom: 6px; }
.threat-value { color: #ef4444; font-size: 36px; }
.metric-note { font-size: 12px; color: #64748b; line-height: 1.4; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.status-active { color: #4ade80; font-size: 20px; align-self: flex-start; margin-bottom: 6px; }
.bar { height: 4px; border-radius: 2px; background: rgba(255, 255, 255, 0.1); overflow: hidden; margin-top: 4px; margin-bottom: 6px; }
.bar-fill { display: block; height: 100%; background: #ef4444; }

/* Section Headers */
.panel-header-row { display: flex; align-items: center; gap: 12px; margin-bottom: 4px; }
.section-icon { font-size: 24px; }
.section-icon.amber { color: #f59e0b; text-shadow: 0 0 10px rgba(245,158,11,0.5); }

/* Situation summary */
.facts { display: flex; gap: 24px; margin: 24px 0 0; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.05); }
.facts div { display: flex; flex-direction: column; gap: 6px; }
.facts dt { font-size: 12px; color: #64748b; }
.facts dd { margin: 0; font-size: 14px; color: #e2e8f0; font-weight: 600; }

/* AI Recommendations */
.actions-new { display: flex; flex-direction: column; gap: 16px; margin: 20px 0; padding: 0; }
.actions-new li { display: flex; align-items: center; gap: 12px; }
.action-number-circle { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; color: #fff; flex-shrink: 0; }
.action-number-circle.critical { background: #ef4444; }
.action-number-circle.high { background: #f97316; }
.action-number-circle.medium { background: #38bdf8; }
.action-text-new { flex: 1; font-size: 14px; color: #e2e8f0; line-height: 1.5; }
.action-badge-right { padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: 800; border: 1px solid; flex-shrink: 0; }
.action-badge-right.critical { color: #fca5a5; border-color: #ef4444; background: rgba(239,68,68,0.1); }
.action-badge-right.high { color: #fdba74; border-color: #f59e0b; background: rgba(245,158,11,0.1); }
.action-badge-right.medium { color: #7dd3fc; border-color: #38bdf8; background: rgba(56,189,248,0.1); }

.review-row-new { display: flex; flex-direction: column; gap: 12px; margin-top: auto; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.05); }
.btn-ghost-cyan { align-self: flex-start; background: transparent; border: 1px solid var(--accent-cyan); color: var(--accent-cyan); padding: 10px 16px; border-radius: 6px; font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.2s; }
.btn-ghost-cyan:hover:not(:disabled) { background: rgba(56, 189, 248, 0.1); }
.footer-disclaimer { display: flex; align-items: flex-start; gap: 8px; margin-top: 4px; }
.info-icon { color: #94a3b8; font-size: 14px; }
.disclaimer-text { color: #64748b; font-size: 11px; line-height: 1.4; }

/* Resources */
.warning-amber { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 6px; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.4); color: #fbbf24; font-size: 13px; margin-bottom: 24px; }
.info-icon-amber { font-size: 16px; }
.resource-row-new { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.resource-card-new { background: transparent; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 6px; }
.res-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.res-icon { font-size: 24px; }
.badge-amber { color: #f59e0b; border: 1px solid #f59e0b; font-size: 9px; padding: 2px 6px; border-radius: 4px; text-transform: uppercase; font-weight: 700; }
.res-name { font-size: 13px; color: #94a3b8; margin-bottom: 4px; }
.res-qty { font-size: 22px; color: #f8fafc; font-weight: 700; margin-bottom: 16px; }
.res-qty small { font-size: 14px; color: #94a3b8; font-weight: normal; }
.res-bottom { font-size: 12px; color: #64748b; margin-top: 8px; display: flex; align-items: center; gap: 6px; }
.res-priority { font-weight: 600; }
.res-priority.critical { color: #ef4444; }
.res-priority.high { color: #f59e0b; }
.res-loc { color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* Responsive */
@media (max-width: 1100px) {
  .snapshot-grid { grid-template-columns: repeat(2, 1fr); }
  .resource-row-new { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 800px) {
  .two-col { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 520px) {
  .snapshot-grid, .resource-row-new { grid-template-columns: 1fr; }
  .banner-actions { width: 100%; }
}

</style>
