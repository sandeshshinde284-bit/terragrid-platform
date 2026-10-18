<template>
  <main class="incident-detail">
    <div v-if="!incident" class="not-found glass-panel">
      <span class="not-found-icon">⌁</span>
      <h1>Incident not found</h1>
      <p>No incident matching <strong>{{ incidentId }}</strong> exists in the current event feed.</p>
      <button class="primary-button" type="button" @click="goTo('/incidents')">Back to incidents</button>
    </div>

    <template v-else>
      <!-- Tactical Neural Scanner HUD Overlay -->
      <transition name="fade">
        <div v-if="scannerActive" class="neural-scanner-overlay">
          <div class="neural-scanner-modal glass-panel">
            <div class="scanner-header">
              <span class="scanner-radar-icon">📡</span>
              <div class="scanner-titles">
                <h4>Analyzing incident data and generating response plan</h4>
                <small>Gathering data from multiple sources...</small>
              </div>
            </div>

            <div class="scanner-body">
              <div class="radar-scanline-bar">
                <div class="scanline-glow"></div>
              </div>

              <div class="scanner-step-list">
                <div 
                  v-for="(step, sIdx) in analysisSteps" 
                  :key="sIdx" 
                  class="scanner-step-item"
                  :class="{ active: currentStepIndex === sIdx, complete: currentStepIndex > sIdx }"
                >
                  <span class="step-indicator">{{ currentStepIndex > sIdx ? '✓' : (currentStepIndex === sIdx ? '⟳' : '○') }}</span>
                  <span class="step-label">{{ step }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </transition>

      <header class="detail-header sticky-header">
        <div class="header-navigation">
          <span class="phase-indicator-badge">{{ $t('header.phases.response') }}</span>
          <button class="primary-back-btn" type="button" aria-label="Back to incidents" @click="goTo('/incidents')">
            <span class="back-arrow">←</span>
            <span class="back-text">{{ $t('detail.activeIncidents') }}</span>
          </button>
          <span class="breadcrumb-separator">/</span>
          <span class="breadcrumb-current">{{ incident.location }}</span>
        </div>
        <div class="header-actions">
          <button class="ghost-button" type="button" @click="goTo('/')">{{ $t('detail.dashboardBtn') }}</button>
          <button class="ghost-button" type="button" @click="goTo('/map')">{{ $t('detail.liveMapBtn') }}</button>
          <label class="language-selector" for="detail-header-language">
            <span>🌐</span>
            <select
              id="detail-header-language"
              v-model="selectedLanguage"
              @change="handleLanguageChange"
              aria-label="Select language"
            >
              <option value="EN">English</option>
              <option value="DE">Deutsch</option>
              <option value="ES">Español</option>
              <option value="FR">Français</option>
              <option value="IT">Italiano</option>
              <option value="PL">Polski</option>
              <option value="SV">Svenska</option>
            </select>
          </label>
        </div>
      </header>

      <section class="incident-hero">
        <div class="hero-copy">
          <div class="eyebrow"><span class="live-dot"></span> {{ $t('detail.incident') }} {{ displayIncidentId(incident) }}</div>
          <h1>{{ incidentLabel }}</h1>
          <p class="hero-location"><span>⌖</span> {{ incident.location }} · {{ $t('detail.detected') }} {{ formatDate(incident.detectionTime) }}</p>
        </div>
        <div class="hero-status">
          <span class="type-badge" :class="`type-${incident.type}`">{{ formatIncidentType(incident.type) }}</span>
          <span class="severity-badge" :class="`severity-${incident.severity}`">{{ incident.severity.toUpperCase() }} {{ $t('detail.severityLabel') }}</span>
          <span class="status-badge" :class="`status-${incident.status}`">{{ formatStatus(incident.status) }}</span>
        </div>
      </section>

      <nav class="tabs" aria-label="Incident detail sections">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-button"
          :class="{ active: activeTab === tab.id }"
          type="button"
          @click="activeTab = tab.id"
        >
          <span class="tab-icon" aria-hidden="true">{{ tab.icon }}</span>
          <span>{{ tab.label }}</span>
        </button>
      </nav>

      <Transition name="tab-fade" mode="out-in">
        <section :key="activeTab" class="tab-content">
          <!-- OVERVIEW -->
          <!-- OVERVIEW -->
          <TabOverview
            v-if="activeTab === 'overview'"
            :incident="incident"
            :details="incidentDetails"
            :report="deepDossier"
            :isGenerating="isAnalyzingDossier"
            :reportError="aiError"
            :exportingZip="isExportingZip"
            @generate="launchDeepAnalysis"
            @exportZip="exportSitRepZip"
            @reviewRecommendations="activeTab = 'response'"
          />

          <!-- IMPACT ANALYSIS -->
          <TabImpact 
            v-else-if="activeTab === 'impact'" 
            :deepDossier="deepDossier" 
            :isAnalyzingDossier="isAnalyzingDossier" 
            :isBackendMockModeEnabled="appStore.isBackendMockModeEnabled" 
            @launch="launchDeepAnalysis" 
          />

          <!-- MAP & EVIDENCE -->
          <TabMap 
            v-else-if="activeTab === 'map'" 
            :deepDossier="deepDossier" 
            :isAnalyzingDossier="isAnalyzingDossier" 
            :isBackendMockModeEnabled="appStore.isBackendMockModeEnabled" 
            @launch="launchDeepAnalysis" 
            @open-map="goTo('/map')"
          />

          <!-- EMERGENCY RESPONSE -->
          <TabResponse 
            v-else-if="activeTab === 'response'" 
            :deepDossier="deepDossier" 
            :isAnalyzingDossier="isAnalyzingDossier" 
            :isBackendMockModeEnabled="appStore.isBackendMockModeEnabled" 
            :incidentId="incident?.id"
            :incident="incident"
            @launch="launchDeepAnalysis" 
          />

          <!-- INCIDENT HISTORY (PREDICTIVE CASCADE) -->
          <TabHistory 
            v-else-if="activeTab === 'history'" 
            :deepDossier="deepDossier" 
            :isAnalyzingDossier="isAnalyzingDossier" 
            :isBackendMockModeEnabled="appStore.isBackendMockModeEnabled" 
            @launch="launchDeepAnalysis" 
          />

          <!-- SOURCE OF TRUTH -->
          <TabSource 
            v-else-if="activeTab === 'source'" 
            :incident="incident" 
            :deepDossier="deepDossier" 
          />

          <!-- AI INSIGHTS -->
          <TabAiInsights 
            v-else-if="activeTab === 'ai'" 
            :aiLoading="aiLoading" 
            :aiError="aiError" 
            :aiPlan="aiPlan" 
          />

          <!-- ALERTS & COMMUNICATIONS -->
          <TabAlerts 
            v-else-if="activeTab === 'alerts'" 
            :isBackendMockModeEnabled="appStore.isBackendMockModeEnabled" 
            :incident-id="incident.id" 
            @open-alerts="goTo('/alerts')"
          />
        </section>
      </Transition>
    </template>
  </main>
</template>

<script setup lang="ts">
import { displayIncidentId } from '@/utils/incidentId'
import { impactMetricsFrom, fmtFixed, fmtCount, fmtThousands, fmtSigned, sumKnown, DASH } from '@/utils/impactMetrics'
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useEventsStore, useAppStore } from '@/stores'
import type { IncidentLevel1, Event } from '@/types'
import { logWarn, logError } from '@/utils/logger'
import JSZip from 'jszip'
import TabSource from '@/components/molecules/TabSource.vue'
import TabResponse from '@/components/molecules/TabResponse.vue'
import TabHistory from '@/components/molecules/TabHistory.vue'
import TabImpact from '@/components/molecules/TabImpact.vue'
import TabMap from '@/components/molecules/TabMap.vue'
import TabAiInsights from '@/components/molecules/TabAiInsights.vue'
import TabAlerts from '@/components/molecules/TabAlerts.vue'
import TabOverview from '@/components/molecules/TabOverview.vue'

// AI Insights data structure

interface AIInsight {
  id: string
  action: string
}

type TabId = 'overview' | 'impact' | 'map' | 'response' | 'history' | 'source' | 'ai' | 'alerts'
type Status = 'Verified' | 'Pending' | 'Unverified'

interface Tab { id: TabId; label: string; icon: string }

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const selectedLanguage = ref(locale.value.toUpperCase())
const handleLanguageChange = () => {
  locale.value = selectedLanguage.value.toLowerCase()
}
const eventsStore = useEventsStore()
const appStore = useAppStore()
const is3D = computed(() => appStore.viewMode === '3d')
const toggle3D = () => {
  appStore.toggleViewMode()
}
const activeTab = ref<TabId>('overview')
const incidentId = computed(() => String(route.params.id || ''))
const incident = computed<IncidentLevel1 | undefined>(() => eventsStore.allIncidents.find(item => item.id === incidentId.value))

// AI state. The saved crisis report is the single source of recommendations.
// There is no separate plan request, so the overview, AI tab, and export always agree.
const aiError = ref<string | null>(null)

// Tier 2 Deep Tactical AI Dossier State
interface DeepDossier {
  version?: number | null
  generated_at?: string
  immediate_actions?: string[]
  severity_assessment?: string
  situational_assessment: string
  threat_level: string
  predictive_cascade: {
    timeframe: string
    perimeter_delta_km2: number
    spread_direction: string
    primary_risk: string
    secondary_threat: string
  }[]
  critical_infrastructure: {
    facility_name: string
    facility_type: string
    distance_km: number
    risk_level: string
    action_required: string
  }[]
  evacuation_corridors: {
    primary_corridor: string
    alternative_route: string
    choke_points: string[]
    safe_assembly_zones: string[]
    estimated_clearance_time_hours: number
  }
  resource_matrix: {
    resource: string
    quantity: string
    assigned_agency: string
    priority: string
  }[]
  vulnerable_demographics: {
    facilities_at_risk: string[]
    estimated_displaced_citizens: number
    special_needs_assistance_required: string
  }
}

const deepDossier = ref<DeepDossier | null>(null)
const incidentDetails = ref<any | null>(null)
const isAnalyzingDossier = ref(false)

// Everything that shows recommendations reads from the saved report.
const aiPlan = computed<DeepDossier | null>(() => deepDossier.value)
const aiLoading = computed(() => isAnalyzingDossier.value)
const aiInsights = computed<AIInsight[]>(() =>
  (deepDossier.value?.immediate_actions || []).map((action, idx) => ({ id: `ai-action-${idx}`, action }))
)
const scannerActive = ref(false)
const currentStepIndex = ref(0)
const analysisSteps = [
  'Loading satellite imagery & weather data from multiple sources...',
  'Identifying critical facilities within impact zone...',
  'Forecasting event progression for 6, 12, and 24 hours ahead...',
  'Generating evacuation strategy & resource allocation plan...'
]

async function launchDeepAnalysis() {
  if (!incidentId.value) return
  isAnalyzingDossier.value = true
  scannerActive.value = true
  currentStepIndex.value = 0
  const stepInterval = setInterval(() => {
    if (currentStepIndex.value < analysisSteps.length - 1) {
      currentStepIndex.value++
    }
  }, 1100)

  try {
    const host = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)
    const res = await fetch(`${host}/api/v1/incidents/${incidentId.value}/deep-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    if (data.status === 'fallback') {
      // AI is offline: nothing was saved. Keep the last saved report on screen.
      aiError.value = 'AI analysis is unavailable right now. The last saved report is still shown.'
    } else if (data.dossier) {
      aiError.value = null
      deepDossier.value = { ...data.dossier, version: data.version ?? null, generated_at: new Date().toISOString() }
    }
  } catch (err) {
    logError('Could not generate the deep AI dossier for this incident', err)
  } finally {
    clearInterval(stepInterval)
    currentStepIndex.value = analysisSteps.length
    setTimeout(() => {
      isAnalyzingDossier.value = false
      scannerActive.value = false
    }, 600)
  }
}

async function loadIncidentDetails() {
  if (!incidentId.value) return
  try {
    const host = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)
    const res = await fetch(`${host}/api/v1/incidents/${incidentId.value}`)
    if (res.ok) incidentDetails.value = await res.json()
  } catch (err) {
    logWarn('Could not load raw incident details', err)
  }
}

async function checkExistingDossier() {
  if (!incidentId.value) return
  try {
    const host = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)
    const res = await fetch(`${host}/api/v1/incidents/${incidentId.value}/deep-dossier`)
    if (res.ok) {
      const data = await res.json()
      if (data.dossier) {
        deepDossier.value = { ...data.dossier, version: data.version ?? null, generated_at: data.generated_at }
      }
    }
  } catch (e) {
    // Ignore if not yet generated
  }
}

const tabs = computed<Tab[]>(() => [
  { id: 'overview', label: t('detail.innerTabs.overview'), icon: '◈' }, 
  { id: 'impact', label: t('detail.innerTabs.impact'), icon: '▦' },
  { id: 'map', label: t('detail.innerTabs.map'), icon: '◎' }, 
  { id: 'response', label: t('detail.innerTabs.response'), icon: '⚑' },
  { id: 'history', label: t('detail.innerTabs.history'), icon: '◷' }, 
  { id: 'source', label: t('detail.innerTabs.source'), icon: '✦' },
  { id: 'ai', label: t('detail.innerTabs.insights'), icon: '⌁' }, 
  { id: 'alerts', label: t('detail.innerTabs.alerts'), icon: '⌁' },
])

const incidentLabel = computed(() => incident.value ? `${formatIncidentType(incident.value.type)} event` : 'Incident')
// Real backend risk score only. The old formula (severity + trend) produced a
// number that looked measured but was invented.
const threatScore = computed<number | null>(() => incident.value?.threatScore ?? null)
const threatLevel = computed(() => {
  const s = threatScore.value
  if (s === null) return t('overviewTab.notScored')
  return s >= 80 ? 'Critical exposure' : s >= 60 ? 'Elevated exposure' : 'Moderate exposure'
})
const summaryText = computed(() => {
  const inc = incident.value
  if (!inc) return ''
  const footprint = inc.affectedArea === null ? 'an area that has not been measured yet' : `${inc.affectedArea.toFixed(0)} km²`
  const exposed = inc.affectedPopulation === null ? 'an exposed population that has not been estimated yet' : `an estimated ${inc.affectedPopulation.toLocaleString()} residents`
  const projection = inc.trend === null
    ? ''
    : ` Impact analysis shows ${inc.trend > 0 ? 'growth' : 'no growth'} of ${inc.trend.toFixed(1)} km²/h.`
  return `A ${formatIncidentType(inc.type).toLowerCase()} incident is affecting ${inc.location}. The current footprint covers ${footprint} and includes ${exposed}.${projection} Field response and continuous verification remain required.`
})

function goTo(path: string) { router.push(path) }
function formatDate(value: Date) { return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value)) }
function relativeTime(value: Date) { const minutes = Math.max(1, Math.round((Date.now() - new Date(value).getTime()) / 60000)); return minutes < 60 ? `${minutes}m ago` : `${Math.round(minutes / 60)}h ago` }
function formatIncidentType(type: Event['type']) { return type.charAt(0).toUpperCase() + type.slice(1) }
function formatStatus(status: IncidentLevel1['status']) { return status.charAt(0).toUpperCase() + status.slice(1) }

const isExportingZip = ref(false)

async function exportSitRepZip() {
  if (!incident.value) return
  isExportingZip.value = true
  const inc = incident.value
  const dossier = deepDossier.value
  const zip = new JSZip()

  try {
    // 1. ICS-201 Incident Command Briefing
    const ics201 = [
      '=================================================================',
      '  TERRAGRID COMMAND CENTER // ICS-201 INCIDENT BRIEFING REPORT  ',
      '=================================================================',
      `INCIDENT ID:        ${inc.id.toUpperCase()}`,
      `CLASSIFICATION:     ${formatIncidentType(inc.type).toUpperCase()}`,
      `LOCATION SECTOR:    ${inc.location}`,
      `GPS COORDINATES:    ${inc.coordinates ? `${inc.coordinates[0]?.toFixed(4)}° N, ${inc.coordinates[1]?.toFixed(4)}° E` : 'N/A'}`,
      `DETECTION TIME:     ${formatDate(inc.detectionTime)}`,
      `OPERATIONAL STATUS: ${inc.status.toUpperCase()}`,
      `THREAT SCORE:       ${threatScore.value === null ? 'NOT SCORED' : `${threatScore.value}/100`} (${threatLevel.value})`,
      '-----------------------------------------------------------------',
      '  PHYSICAL EXPOSURE & EXPANSION METRICS (MODEL ESTIMATES)        ',
      '-----------------------------------------------------------------',
      `AFFECTED FOOTPRINT:    ${fmtFixed(inc.affectedArea, 0, ' km²')}`,
      `POPULATION IN DANGER:  ${fmtCount(inc.affectedPopulation)} citizens`,
      `GROWTH VELOCITY:       ${fmtSigned(inc.trend, 1, ' km²/h')}`,
      `6-HOUR MAXIMUM BUFFER: ${fmtSigned(inc.forecast6h, 0, ' km²')}`,
      '-----------------------------------------------------------------',
      '  EVIDENCE STATUS                                                ',
      '-----------------------------------------------------------------',
      'VERIFIED SOURCE DATA:  hazard type, location, coordinates, source, detection time (from the feed)',
      'MODEL ESTIMATES:       affected area, people exposed, risk score, expansion, 6h forecast',
      `UNKNOWN / NOT MODELLED: ${[
        inc.affectedArea == null && 'affected area',
        inc.affectedPopulation == null && 'people exposed',
        inc.threatScore == null && 'risk score',
        inc.trend == null && 'expansion rate',
        inc.forecast6h == null && '6h forecast',
      ].filter(Boolean).join(', ') || 'none'}`,
      'AI RECOMMENDATIONS:    generated by Gemini; NOT verified and NOT authorized',
      '-----------------------------------------------------------------',
      '  TACTICAL SITUATIONAL BRIEFING (AI-GENERATED, NOT VERIFIED)     ',
      '-----------------------------------------------------------------',
      dossier ? dossier.situational_assessment : summaryText.value,
      '',
      '=================================================================',
      `GENERATED AT: ${new Date().toISOString()}                       `,
      '================================================================='
    ].join('\n')
    zip.file('01_ICS-201_Incident_Command_Briefing.txt', ics201)

    // 2. Tactical Action Plan
    const actionPlan = [
      '=================================================================',
      '  TERRAGRID COMMAND CENTER // TACTICAL CRISIS ACTION DIRECTIVES  ',
      '=================================================================',
      `INCIDENT: ${inc.location} [${inc.id.toUpperCase()}]`,
      '-----------------------------------------------------------------',
      'AI-RECOMMENDED DIRECTIVES (NOT AUTHORIZED UNTIL APPROVED BY AN OFFICER):',
      ...(aiInsights.value && aiInsights.value.length
        ? aiInsights.value.map((a: any, idx: number) => `[RECOMMENDATION 0${idx + 1}] Status: AI proposal, NOT AUTHORIZED UNTIL APPROVED BY AN OFFICER\nAction: ${a.action}\n`)
        : ['[DIRECTIVE 01] Maintain active perimeter surveillance and deploy local emergency responders.\n']),
      '-----------------------------------------------------------------',
      `SECTOR JURISDICTION CONTEXT:\n${aiPlan.value?.country_context || 'FEMA / UN-OCHA Operational Standard Protocol'}`,
      '================================================================='
    ].join('\n')
    zip.file('02_Tactical_Response_Plan.txt', actionPlan)

    // 3. Evacuation Corridors & Shelters
    if (dossier?.evacuation_corridors) {
      const evac = dossier.evacuation_corridors
      const evacDoc = [
        '=================================================================',
        '  TERRAGRID EMERGENCY TRANSIT // EVACUATION CORRIDOR DIRECTIVE   ',
        '=================================================================',
        `TARGET SECTOR: ${inc.location}`,
        'ROAD STATUS: UNVERIFIED. Not checked for flooding, blockages or closures. Field confirmation required.',
        `ESTIMATED CLEARANCE TIME: ${evac.estimated_clearance_time_hours} Hours (estimate)`,
        '-----------------------------------------------------------------',
        `PRIMARY OUTBOUND CORRIDOR:\n>> ${evac.primary_corridor}\n`,
        `CONTINGENCY ALTERNATIVE ROUTE:\n>> ${evac.alternative_route}\n`,
        '-----------------------------------------------------------------',
        'BOTTLENECK CHOKE-POINTS & ROAD HAZARDS:',
        ...evac.choke_points.map((cp: string) => `  [!] ${cp}`),
        '',
        'DESIGNATED SAFE ASSEMBLY STAGING PERIMETERS:',
        ...evac.safe_assembly_zones.map((sz: string) => `  [*] ${sz}`),
        '================================================================='
      ].join('\n')
      zip.file('03_Evacuation_Corridor_Routing.txt', evacDoc)
    }

    // 4. Critical Infrastructure Vulnerability
    if (dossier?.critical_infrastructure) {
      const infra = dossier.critical_infrastructure
      const infraDoc = [
        '=================================================================',
        '  TERRAGRID GIS INTELLIGENCE // CRITICAL INFRASTRUCTURE AT RISK  ',
        '=================================================================',
        `SECTOR: ${inc.location}`,
        '-----------------------------------------------------------------',
        ...infra.map((fac: any, idx: number) => 
          `[ASSET 0${idx + 1}] ${fac.facility_name.toUpperCase()}\n` +
          `  Type:     ${fac.facility_type}\n` +
          `  Distance: ${fac.distance_km} km from epicenter\n` +
          `  Threat:   ${fac.risk_level.toUpperCase()} RISK\n` +
          `  Action:   ${fac.action_required}\n`
        ),
        '================================================================='
      ].join('\n')
      zip.file('04_Critical_Infrastructure_Vulnerability.txt', infraDoc)
    }

    // 5. Predictive Cascade Simulation
    if (dossier?.predictive_cascade) {
      const cascade = dossier.predictive_cascade
      const cascadeDoc = [
        '=================================================================',
        '  TERRAGRID FUSION ENGINE // 24-HOUR PREDICTIVE CASCADE MODEL    ',
        '=================================================================',
        `DISASTER VECTOR: ${inc.location}`,
        '-----------------------------------------------------------------',
        ...cascade.map((c: any) => 
          `[TIMEFRAME: ${c.timeframe.toUpperCase()}]\n` +
          `  Perimeter Expansion: +${c.perimeter_delta_km2} km²\n` +
          `  Spread Trajectory:   ${c.spread_direction}\n` +
          `  Primary Hazard:      ${c.primary_risk}\n` +
          `  Cascading Danger:    ${c.secondary_threat}\n`
        ),
        '================================================================='
      ].join('\n')
      zip.file('05_Predictive_Cascade_Simulation.txt', cascadeDoc)
    }

    // 6. Complete Machine-Readable JSON Telemetry
    const jsonExport = JSON.stringify({
      incident: inc,
      ai_plan: aiPlan.value,
      deep_dossier: dossier,
      exported_at: new Date().toISOString()
    }, null, 2)
    zip.file('06_Crisis_Telemetry_Metadata.json', jsonExport)

    // 7. Response action log: who acknowledged, what was assigned, what was sent
    try {
      const host = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)
      const res = await fetch(`${host}/api/v1/incidents/${inc.id}/response`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const state = await res.json()
      const lines = [
        '=================================================================',
        '  TERRAGRID // RESPONSE ACTION LOG (OPERATOR-DECLARED NAMES)     ',
        '=================================================================',
        `INCIDENT: ${inc.location} [${inc.id.toUpperCase()}]`,
        `ACKNOWLEDGED: ${state.acknowledged ? `${state.acknowledged_by} at ${state.acknowledged_at}` : 'No'}`,
        `CURRENT STATUS: ${state.status}`,
        '-----------------------------------------------------------------',
        'TASKS:',
        ...(state.tasks.length
          ? state.tasks.map((t: any) => `  [${String(t.priority || 'medium').toUpperCase()}] [${t.status}] ${t.title} -> ${t.assignee}${t.due_at ? ` | deadline ${t.due_at} (UTC)` : ' | no deadline'}${t.note ? ` | blocked: ${t.note}` : ''} | added by ${t.created_by}`)
          : ['  None recorded']),
        '-----------------------------------------------------------------',
        'ALERTS (sent only after approval):',
        ...(state.alerts.length
          ? state.alerts.flatMap((a: any) => [
              `  [${a.status}] ${a.subject}${a.task_id ? ` (linked to task #${a.task_id})` : ''}`,
              `    To: ${a.recipients.join(', ')}`,
              `    Drafted by ${a.created_by}; decided by ${a.decided_by || 'n/a'}`,
              ...(a.delivery_results || []).map((d: any) => `    - ${d.recipient}: ${d.success ? 'delivered' : 'NOT delivered'}${d.detail ? ` (${d.detail})` : ''}`),
            ])
          : ['  None recorded']),
        '-----------------------------------------------------------------',
        'FULL LOG:',
        ...(state.log.length
          ? state.log.map((e: any) => `  ${e.at} | ${e.actor} | ${e.action}`)
          : ['  No actions recorded']),
        '================================================================='
      ].join('\n')
      zip.file('07_Response_Action_Log.txt', lines)
    } catch {
      zip.file('07_Response_Action_Log.txt', 'The response action log could not be loaded when this export was made.\n')
    }

    // Generate and download ZIP package!
    const blob = await zip.generateAsync({ type: 'blob' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `TERRAGRID-CRISIS-PACKAGE-${inc.id.toUpperCase()}-${Date.now()}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (err) {
    logError('Could not generate the SitRep zip package', err)
  } finally {
    isExportingZip.value = false
  }
}

onMounted(async () => {
  if (eventsStore.allIncidents.length === 0) {
    try {
      // Mirrors Dashboard.vue's own db_hydration mapping exactly (same endpoint,
      // same id-field priority, same response unwrapping) - this used to use a
      // different, simplified mapping that (a) never unwrapped the endpoint's
      // real { data: [...], pagination: ... } shape, so raw.length was always
      // undefined and setIncidents() never ran, and (b) built a different id
      // than Dashboard.vue does (e.id only, vs Dashboard's data?.id priority).
      // Either bug alone was enough to make a direct page refresh show
      // "Incident not found" even though the incident still exists - the store
      // either never repopulated, or repopulated with an id that didn't match
      // the one in the URL.
      const host = import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)
      const res = await fetch(`${host}/api/v1/incidents?limit=100&offset=0`)
      if (res.ok) {
        const apiResponse = await res.json()
        const rawIncidents = apiResponse.data || apiResponse
        if (rawIncidents && Array.isArray(rawIncidents) && rawIncidents.length > 0) {
          const mapped = rawIncidents.map((event: any, index: number) => {
            const impact = event.impact || {}
            const severity = (event.severity || 'medium').toLowerCase()
            const locationName = event.location_name || 'Unknown'
            const source = event.source || event.data?.source || 'unknown'

            return {
              id: event.data?.id || event.data?.nasa_id || event.data?.gdacs_id || event.id || `event-${index}-${Date.now()}`,
              type: event.event_type || 'fire',
              location: locationName,
              location_name: locationName,
              countryCode: event.countryCode || 'UN',
              severity: (severity === 'critical' ? 'high' : severity) as 'low' | 'medium' | 'high',
              status: event.status === 'detected' || event.status === 'active' ? 'active' : (event.status || 'active'),
              ...impactMetricsFrom(event),
              detectionTime: new Date(event.event_timestamp || Date.now()),
              coordinates: [event.latitude, event.longitude] as [number, number],
              source: source,
              confidence: event.confidence ?? event.data?.confidence ?? 0,
              event_timestamp: event.event_timestamp || event.created_at || Date.now(),
              data: event.data || {},
            }
          })
          eventsStore.setIncidents(mapped)
        }
      }
    } catch (err) {
      logWarn('Could not hydrate incidents on the incident detail page', err)
    }
  }

  if (incidentId.value) {
    checkExistingDossier()
    loadIncidentDetails()
  }

  // Handle query parameter to switch to AI Insights tab
  const tabQuery = route.query.tab as string | undefined
  if (tabQuery === 'ai-insights') {
    activeTab.value = 'ai'
  }
})

// Watch for query parameter changes
watch(() => route.query.tab, (newTab) => {
  if (newTab === 'ai-insights') {
    activeTab.value = 'ai'
  }
}, { immediate: true })

// Priority helper functions for resource matrix display
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

// Cascade color styling helper
function getDeltaBadgeStyle(colorCode?: string): Record<string, string> {
  const code = (colorCode || 'RED').toUpperCase()
  switch (code) {
    case 'RED':
      return { color: '#fb7185', background: 'rgba(244, 63, 94, 0.15)' }
    case 'ORANGE':
      return { color: '#fb923c', background: 'rgba(249, 115, 22, 0.15)' }
    case 'YELLOW':
      return { color: '#fbbf24', background: 'rgba(245, 158, 11, 0.15)' }
    case 'GREEN':
      return { color: '#4ade80', background: 'rgba(34, 197, 94, 0.15)' }
    default:
      return { color: '#fb7185', background: 'rgba(244, 63, 94, 0.15)' }
  }
}

function getCascadeColorHex(colorCode?: string): string {
  const code = (colorCode || 'RED').toUpperCase()
  switch (code) {
    case 'RED': return '#ef4444'
    case 'ORANGE': return '#f97316'
    case 'YELLOW': return '#eab308'
    case 'GREEN': return '#22c55e'
    default: return '#ef4444'
  }
}
</script>

<style scoped>
:global(body) { background: #0f0f0f; }
.incident-detail { min-height: 100%; padding: 24px clamp(16px, 4vw, 56px) 64px; color: #f8fafc; background: radial-gradient(circle at 85% 0%, rgba(14,165,233,.09), transparent 28%), #0f0f0f; }
.glass-panel { background: rgba(22, 29, 39, .72); border: 1px solid rgba(148,163,184,.17); border-radius: 14px; backdrop-filter: blur(14px); box-shadow: 0 14px 40px rgba(0,0,0,.2); }
.glass-panel:hover { border-color: rgba(14,165,233,.4); transition: border-color .25s ease; }
.detail-header, .header-navigation, .header-actions, .hero-status, .panel-heading, .row-title, .tab-intro, .map-toolbar, .map-footer { display: flex; align-items: center; }
.detail-header { justify-content: space-between; gap: 20px; margin-bottom: 28px; }
.header-navigation, .header-actions { gap: 11px; flex-wrap: wrap; }
.back-button, .ghost-button, .primary-button { border: 1px solid rgba(148,163,184,.25); color: #e2e8f0; background: transparent; border-radius: 8px; padding: 9px 13px; cursor: pointer; font: inherit; transition: .2s ease; }
.back-button:hover, .ghost-button:hover { border-color: #0ea5e9; color: #7dd3fc; }

.language-selector {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid rgba(56, 189, 248, 0.4);
  border-radius: 6px;
  background: rgba(14, 165, 233, 0.1);
  color: var(--accent-cyan);
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
  cursor: pointer;
  flex-shrink: 0;
}

.language-selector:hover {
  background: rgba(14, 165, 233, 0.2);
  border-color: #38bdf8;
}

.language-selector select {
  border: none;
  background: transparent;
  color: #38bdf8;
  font: inherit;
  font-weight: 600;
  outline: none;
  cursor: pointer;
  min-width: 80px;
  padding: 2px 4px;
  font-size: 13px;
}

.language-selector select option {
  background: #0f172a;
  color: #38bdf8;
  font-weight: 600;
  padding: 4px;
  font-size: 13px;
}

.breadcrumb-separator { color: #475569; }.breadcrumb-current { color: #94a3b8; font-size: 18px; }
.primary-button { background: #0ea5e9; border-color: #38bdf8; color: #03111b; font-weight: 700; }.primary-button:hover { background: #38bdf8; }
.phase-indicator-badge {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.8px;
  color: #38bdf8;
  background: rgba(14, 165, 233, 0.12);
  border: 1px solid rgba(14, 165, 233, 0.35);
  border-radius: 5px;
  padding: 4px 9px;
  white-space: nowrap;
}
.incident-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
  margin-top: 36px !important; /* Generous breathing room below sticky header */
  margin-bottom: 28px !important;
}
.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
}.eyebrow, .section-kicker {
  color: #38bdf8;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: .16em;
  text-transform: none;
}.live-dot, .response-state i, .map-live i { display: inline-block; width: 7px; height: 7px; margin-right: 7px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,.6); }.hero-copy h1 { margin: 8px 0 4px; font-size: clamp(28px, 4vw, 42px); letter-spacing: -.04em; }.hero-location { margin: 0; color: #94a3b8; }.hero-location span { color: #38bdf8; }.hero-status { gap: 8px; flex-wrap: wrap; justify-content: flex-end; }.type-badge, .severity-badge, .status-badge, .ai-chip, .verified-chip, .updated-pill, .response-state, .pattern-confidence { padding: 6px 9px; border-radius: 6px; font-size: 16px; font-weight: 800; letter-spacing: .06em; }.type-badge { background: rgba(168,85,247,.16); color: #d8b4fe; }.type-fire { color: #fb923c; background: rgba(249,115,22,.15); }.type-flood { color: #38bdf8; background: rgba(14,165,233,.15); }.type-landslide { color: #fbbf24; background: rgba(245,158,11,.15); }.severity-high { color: #fb7185; background: rgba(244,63,94,.15); }.severity-medium { color: #fbbf24; background: rgba(245,158,11,.15); }.severity-low { color: #4ade80; background: rgba(34,197,94,.15); }.status-active { color: #4ade80; }.status-monitoring { color: #fbbf24; }.status-resolved { color: #94a3b8; }.status-badge { border: 1px solid currentColor; }
.tabs { display: flex; gap: 3px; overflow-x: auto; border-bottom: 1px solid rgba(148,163,184,.18); scrollbar-width: thin; scrollbar-color: rgba(14,165,233,.4) transparent; padding-bottom: 2px; }.tab-button { white-space: nowrap; display: flex; align-items: center; gap: 5px; border: 1px solid transparent; border-bottom: 2px solid transparent; padding: 11px 13px; background: transparent; color: #a0aec0; cursor: pointer; font: inherit; font-size: 16px; font-weight: 600; transition: .2s ease; border-radius: 6px 6px 0 0; flex-shrink: 0; min-width: fit-content; }.tab-button:hover { color: #67e8f9; border-color: rgba(14,165,233,.35); background: rgba(14,165,233,.08); border-bottom-color: #0ea5e9; }.tab-button.active { color: #0ea5e9; border: 1px solid rgba(14,165,233,.48); border-bottom: 2px solid #0ea5e9; background: rgba(14,165,233,.1); }.tab-icon { font-size: 16px; color: inherit; flex-shrink: 0; }.tab-button:hover .tab-icon { color: #38bdf8; }.tab-button.active .tab-icon { color: #0ea5e9; }.critical-marker { color: #fbbf24; margin-left: 2px; }
.tab-content { padding-top: 26px; }.tab-fade-enter-active, .tab-fade-leave-active { transition: opacity .2s ease, transform .2s ease; }.tab-fade-enter-from, .tab-fade-leave-to { opacity: 0; transform: translateY(5px); }
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 18px; }.metric-card { min-height: 136px; padding: 18px; }.metric-label, .metric-footnote, .metric-card small { display: block; color: #94a3b8; font-size: 18px; }.metric-value { display: block; margin: 15px 0 6px; color: #67e8f9; font-size: 27px; line-height: 1.1; }.metric-value small { display: inline; font-size: 16px; color: #94a3b8; }.compact-value { font-size: 17px; color: #f8fafc; line-height: 1.25; }.threat-value { color: #fb7185; }.trend-value { color: #4ade80; }.status-text { color: #fbbf24; }.progress-track { height: 5px; margin-top: 12px; overflow: hidden; background: rgba(100,116,139,.2); border-radius: 99px; }.progress-fill { display: block; height: 100%; border-radius: inherit; background: #0ea5e9; }.threat-fill { background: #fb7185; }.content-grid { display: grid; gap: 18px; margin-top: 18px; }.two-columns { grid-template-columns: repeat(2, minmax(0, 1fr)); }.content-grid > .glass-panel, .impact-layout > .glass-panel, .source-grid > .glass-panel, .ai-grid > .glass-panel { padding: 22px; }.panel-heading { justify-content: space-between; gap: 12px; margin-bottom: 20px; }.panel-heading h2, .panel-heading h3 { margin-top: 4px; color: #f8fafc; }.panel-code { color: #475569; font: 700 10px ui-monospace, monospace; }.long-copy { color: #cbd5e1; line-height: 1.75; }.summary-facts { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 22px; }.summary-facts span, .summary-facts strong { display: block; }.summary-facts span { color: #64748b; font-size: 18px; }.summary-facts strong { margin-top: 3px; color: #e2e8f0; font-size: 18px; }.ai-chip, .verified-chip { color: #67e8f9; background: rgba(14,165,233,.12); }.action-list, .lessons-list { display: grid; gap: 15px; padding: 0; margin: 0; list-style: none; }.action-list li { display: flex; align-items: flex-start; gap: 12px; }.action-number { color: #0ea5e9; font: 700 12px ui-monospace, monospace; }.action-list strong { color: #f8fafc; font-size: 18px; }.action-list p { margin: 4px 0 0; color: #94a3b8; font-size: 16px; }.priority { margin-left: auto; color: #fbbf24; font-size: 18px; font-weight: 800; text-transform: uppercase; }.priority-urgent { color: #fb7185; }
.tab-intro { justify-content: space-between; gap: 20px; margin-bottom: 20px; }.tab-intro h2 { margin: 5px 0 4px; font-size: 25px; }.tab-intro p { margin: 0; color: #94a3b8; }.updated-pill, .pattern-confidence { color: #94a3b8; background: rgba(100,116,139,.13); }.impact-layout, .source-grid, .ai-grid, .map-evidence-layout { display: grid; grid-template-columns: 1.1fr .9fr; gap: 18px; }.zone-list, .population-bars, .resource-list, .freshness-list, .lineage-list, .audit-list, .route-list, .deployment-list, .history-list, .comparison-list, .evidence-list, .region-list, .alert-history { display: grid; gap: 15px; }.zone-row, .route-row, .history-row, .alert-row, .deployment-row, .lineage-row, .audit-row, .region-row { display: flex; align-items: center; gap: 12px; }.zone-icon { display: grid; place-items: center; width: 33px; height: 33px; border-radius: 8px; font-weight: 800; }.zone-critical { color: #fb7185; background: rgba(244,63,94,.18); }.zone-high { color: #fb923c; background: rgba(249,115,22,.18); }.zone-watch { color: #fbbf24; background: rgba(245,158,11,.18); }.zone-main, .route-main, .history-main, .region-row > span:first-child { flex: 1; min-width: 0; }.row-title { justify-content: space-between; gap: 10px; }.row-title strong, .row-title span, .zone-main small { font-size: 16px; }.row-title span, .zone-main small, .route-main small, .history-main small, .deployment-row small, .audit-row small { color: #64748b; }.zone-percent { color: #67e8f9; font-size: 18px; }.fill-critical { background: #fb7185; }.fill-high { background: #fb923c; }.fill-watch { background: #fbbf24; }.population-row .row-title strong { color: #67e8f9; }.population-fill, .region-fill { background: #22d3ee; }.bar-with-label { display: flex; align-items: center; gap: 9px; }.bar-with-label .progress-track { flex: 1; }.bar-with-label small { color: #64748b; }.total-callout, .eta-callout { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-top: 20px; padding: 13px; border: 1px solid rgba(14,165,233,.25); border-radius: 8px; background: rgba(14,165,233,.08); }.total-callout span, .eta-callout span { color: #94a3b8; font-size: 16px; }.total-callout strong, .eta-callout strong { color: #67e8f9; }.asset-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }.asset-card { padding: 13px 8px; text-align: center; border-radius: 9px; background: rgba(15,23,42,.65); }.asset-icon { display: block; color: #38bdf8; font-size: 22px; }.asset-card strong, .asset-card span, .asset-card small { display: block; }.asset-card strong { margin-top: 4px; font-size: 21px; }.asset-card span { color: #cbd5e1; font-size: 16px; }.asset-card small { margin-top: 8px; color: #4ade80; font-size: 18px; }.asset-card small.restricted, .asset-card small.inspect { color: #fbbf24; }.resource-row { display: grid; grid-template-columns: 1.2fr 1fr auto; align-items: center; gap: 10px; color: #cbd5e1; font-size: 16px; }.resource-progress { height: 6px; overflow: hidden; background: rgba(100,116,139,.18); border-radius: 99px; }.resource-progress span { display: block; height: 100%; background: #22d3ee; border-radius: inherit; }.resource-row strong { color: #f8fafc; font-size: 16px; }.resource-row small { grid-column: 2 / 4; color: #64748b; font-size: 16px; }
.map-preview { overflow: hidden; padding: 0 !important; }.map-toolbar, .map-footer { justify-content: space-between; gap: 10px; padding: 14px 18px; }.map-title, .map-live { color: #94a3b8; font: 700 10px ui-monospace, monospace; }.map-live { color: #4ade80; }.map-canvas { position: relative; height: 400px; overflow: hidden; background: linear-gradient(135deg, #112c2e 0%, #173d41 35%, #263c32 68%, #172f2d 100%); }.map-grid { position: absolute; inset: 0; opacity: .28; background-image: linear-gradient(rgba(125,211,252,.2) 1px, transparent 1px), linear-gradient(90deg, rgba(125,211,252,.2) 1px, transparent 1px); background-size: 45px 45px; transform: rotate(-12deg) scale(1.2); }.map-zone { position: absolute; width: 145px; height: 110px; display: grid; place-items: center; border: 2px solid; border-radius: 45% 55% 50% 40%; font: 800 18px ui-monospace, monospace; transform: rotate(-20deg); }.map-zone-1 { top: 25%; left: 27%; color: #fb7185; border-color: rgba(251,113,133,.8); background: rgba(244,63,94,.2); }.map-zone-2 { top: 42%; left: 48%; color: #fb923c; border-color: rgba(251,146,60,.7); background: rgba(249,115,22,.16); }.map-zone-3 { top: 51%; left: 16%; color: #fbbf24; border-color: rgba(251,191,36,.6); background: rgba(245,158,11,.12); }.map-crosshair { position: absolute; top: 48%; left: 51%; color: #fff; font-size: 30px; text-shadow: 0 0 12px #0ea5e9; }.map-scale { position: absolute; right: 17px; top: 18px; color: #e2e8f0; text-align: center; font-weight: 800; }.map-scale span { color: #38bdf8; }.map-legend { position: absolute; bottom: 14px; left: 15px; display: flex; gap: 12px; padding: 8px 10px; color: #cbd5e1; font-size: 16px; background: rgba(15,23,42,.8); border-radius: 6px; }.legend-dot { display: inline-block; width: 7px; height: 7px; margin-right: 3px; border-radius: 50%; }.legend-dot.critical { background: #fb7185; }.legend-dot.watch { background: #fbbf24; }.legend-dot.safe { background: #4ade80; }.map-footer { border-top: 1px solid rgba(148,163,184,.12); color: #64748b; font-size: 16px; }.evidence-row { display: flex; align-items: center; gap: 10px; }.evidence-thumb { display: grid; place-items: center; width: 42px; height: 38px; color: #67e8f9; border-radius: 6px; background: linear-gradient(135deg, rgba(14,165,233,.3), rgba(34,197,94,.2)); font-size: 21px; }.evidence-main { flex: 1; }.evidence-main strong, .evidence-main small { display: block; }.evidence-main strong { font-size: 16px; }.evidence-main small { margin-top: 3px; color: #64748b; font-size: 16px; }.evidence-status, .delivery-status { font-size: 18px; font-weight: 800; text-transform: uppercase; }.evidence-verified, .delivered { color: #4ade80; }.evidence-pending, .partial { color: #fbbf24; }.verification-score { display: flex; align-items: center; gap: 13px; margin-top: 22px; padding-top: 18px; border-top: 1px solid rgba(148,163,184,.14); }.verification-score p { margin: 3px 0 0; font-size: 18px; }.score-ring { display: grid; place-items: center; width: 67px; height: 67px; border: 4px solid #22d3ee; border-left-color: rgba(34,211,238,.2); border-radius: 50%; }.score-ring strong { color: #67e8f9; font-size: 16px; }.score-ring small { color: #64748b; font-size: 8px; }
.response-state { color: #4ade80; }.response-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }.response-metric { padding: 18px; }.response-metric span, .response-metric small { display: block; color: #94a3b8; font-size: 18px; }.response-metric strong { display: block; margin: 10px 0 4px; color: #67e8f9; font-size: 25px; }.route-status { width: 10px; align-self: stretch; position: relative; }.route-status span { position: absolute; top: 6px; width: 8px; height: 8px; border-radius: 50%; }.route-open span { background: #4ade80; box-shadow: 0 0 8px #4ade80; }.route-limited span { background: #fbbf24; }.route-clearing span { background: #fb923c; }.route-time { color: #67e8f9; font-size: 16px; }.route-track { height: 4px; margin-top: 8px; background: rgba(100,116,139,.2); border-radius: 99px; }.route-track span { display: block; height: 100%; background: #4ade80; border-radius: inherit; }.route-limited + .route-main .route-track span { background: #fbbf24; }.deployment-icon { display: grid; place-items: center; width: 30px; height: 30px; color: #38bdf8; border-radius: 7px; background: rgba(14,165,233,.13); }.deployment-row div { flex: 1; }.deployment-row strong, .deployment-row small { display: block; }.deployment-row strong { font-size: 16px; }.deployment-row small { margin-top: 2px; font-size: 16px; }.deployment-count { color: #cbd5e1; font-size: 18px; }.deployment-status { font-size: 18px; text-transform: uppercase; }.deployment-status.active { color: #4ade80; }.deployment-status.moving { color: #38bdf8; }.deployment-status.standby { color: #fbbf24; }.eta-callout { flex-wrap: wrap; }.eta-callout small { width: 100%; color: #64748b; font-size: 16px; }.history-year { color: #38bdf8; font: 700 12px ui-monospace, monospace; }.history-stat { text-align: right; }.history-stat strong, .history-stat small { display: block; }.history-stat strong { color: #67e8f9; font-size: 16px; }.history-stat small { color: #64748b; font-size: 18px; }.similarity { color: #a78bfa; font-size: 16px; }.comparison-row { display: flex; align-items: center; gap: 12px; }.comparison-row > span:first-child { flex: 1; color: #cbd5e1; font-size: 16px; }.comparison-values { text-align: right; }.comparison-values strong, .comparison-values span { display: block; }.comparison-values strong { color: #f8fafc; font-size: 16px; }.comparison-values span { color: #64748b; font-size: 16px; }.comparison-delta { min-width: 42px; text-align: right; font-size: 18px; }.comparison-delta.good { color: #4ade80; }.comparison-delta.bad { color: #fb7185; }.insight-list { display: grid; gap: 13px; padding: 0; margin: 0; list-style: none; }.insight-list li { color: #cbd5e1; font-size: 16px; }.insight-list span { margin-right: 10px; color: #38bdf8; }.lessons-list { list-style: decimal; padding-left: 22px; }.lessons-list li { padding-left: 5px; color: #94a3b8; }.lessons-list strong, .lessons-list span { display: block; }.lessons-list strong { color: #f8fafc; font-size: 16px; }.lessons-list span { margin-top: 3px; font-size: 18px; }
.quality-score { text-align: right; }.quality-score span, .quality-score strong { display: block; }.quality-score span { color: #64748b; font-size: 18px; letter-spacing: .12em; }.quality-score strong { color: #4ade80; font-size: 28px; }.quality-score small { color: #64748b; font-size: 18px; }.source-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }.source-card { padding: 14px; border: 1px solid rgba(148,163,184,.14); border-radius: 9px; background: rgba(15,23,42,.55); }.source-card-head { display: flex; justify-content: space-between; }.source-icon { color: #38bdf8; font-size: 22px; }.source-status { font-size: 18px; text-transform: uppercase; }.source-status.verified { color: #4ade80; }.source-status.pending { color: #fbbf24; }.source-card strong { display: block; margin-top: 9px; font-size: 16px; }.source-card p { min-height: 33px; margin: 5px 0 12px; font-size: 16px; }.source-meta { display: flex; justify-content: space-between; color: #64748b; font-size: 18px; }.freshness-list div { display: flex; justify-content: space-between; gap: 12px; }.freshness-list span { color: #64748b; font-size: 18px; }.freshness-list strong { color: #cbd5e1; font-size: 18px; text-align: right; }.freshness-meter { margin-top: 24px; }.freshness-meter > span, .freshness-meter > strong { color: #94a3b8; font-size: 16px; }.freshness-meter > strong { float: right; color: #4ade80; }.freshness-fill { background: #4ade80; }.lineage-marker { width: 9px; height: 9px; border: 2px solid #0ea5e9; border-radius: 50%; box-shadow: 0 0 8px rgba(14,165,233,.6); }.lineage-row div { flex: 1; }.lineage-row strong, .lineage-row small, .audit-row strong, .audit-row small { display: block; }.lineage-row strong, .audit-row strong { font-size: 16px; }.lineage-row small, .audit-row small { margin-top: 3px; font-size: 16px; }.confidence-badge { color: #67e8f9; font: 700 10px ui-monospace, monospace; }.audit-time { min-width: 68px; color: #38bdf8; font: 10px ui-monospace, monospace; }.audit-row div { flex: 1; }
.ai-grid { grid-template-columns: 1.2fr .8fr; }.prediction-head { display: flex; align-items: center; gap: 18px; }.forecast-number { color: #67e8f9; font-size: 55px; font-weight: 800; line-height: 1; }.forecast-number small { font-size: 21px; }.prediction-head strong { font-size: 16px; }.prediction-head p { margin: 4px 0 0; font-size: 18px; }.forecast-timeline { display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 30px; }.forecast-point { position: relative; padding-top: 14px; border-top: 1px solid rgba(148,163,184,.2); }.forecast-point:not(:last-child):after { content: ''; position: absolute; top: -2px; right: 0; width: 5px; height: 5px; border-radius: 50%; background: #38bdf8; }.forecast-dot { position: absolute; top: -4px; left: 0; width: 7px; height: 7px; border-radius: 50%; background: #38bdf8; }.forecast-dot.current { background: #4ade80; box-shadow: 0 0 8px #4ade80; }.forecast-point strong, .forecast-point small { display: block; }.forecast-point strong { font-size: 18px; }.forecast-point small { margin-top: 3px; color: #67e8f9; font-size: 16px; }.risk-total { color: #fb7185; font-size: 22px; }.risk-list { display: grid; gap: 17px; }.risk-fill { background: linear-gradient(90deg, #fbbf24, #fb7185); }.signal-row { display: flex; align-items: flex-start; gap: 12px; padding: 12px 0; border-bottom: 1px solid rgba(148,163,184,.12); }.signal-row:last-child { border-bottom: 0; }.signal-icon { color: #38bdf8; font-size: 19px; }.signal-row div { flex: 1; }.signal-row strong { font-size: 16px; }.signal-row p { margin: 4px 0 0; font-size: 18px; }.signal-impact { color: #fbbf24; font-size: 18px; font-weight: 800; }.ai-actions li { padding-bottom: 14px; border-bottom: 1px solid rgba(148,163,184,.12); }
.communication-metrics {}.alert-row { align-items: flex-start; }.alert-severity { width: 4px; min-height: 35px; border-radius: 99px; background: #38bdf8; }.alert-severity.critical { background: #fb7185; }.alert-severity.warning { background: #fbbf24; }.alert-row div { flex: 1; }.alert-row strong, .alert-row small { display: block; }.alert-row strong { font-size: 16px; }.alert-row small { margin-top: 4px; color: #64748b; font-size: 16px; }.region-row { flex-wrap: wrap; }.region-row > span:first-child { font-size: 16px; }.region-row .progress-track { flex: 1; min-width: 100px; margin-top: 0; }.region-row strong { color: #67e8f9; font-size: 18px; }.region-row small { width: 100%; margin-left: calc(30% + 12px); color: #64748b; font-size: 16px; }.channel-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }.channel-pill { padding: 7px 9px; color: #cbd5e1; border: 1px solid rgba(148,163,184,.15); border-radius: 6px; font-size: 16px; }.channel-pill i { margin-right: 5px; color: #38bdf8; font-style: normal; }.channel-pill strong { margin-left: 5px; color: #4ade80; }.response-panel { padding: 22px; margin-top: 18px; }.outcome-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }.outcome-grid span, .outcome-grid strong, .outcome-grid small { display: block; }.outcome-grid span { color: #94a3b8; font-size: 18px; }.outcome-grid strong { margin: 7px 0 3px; color: #67e8f9; font-size: 23px; }.outcome-grid small { color: #64748b; font-size: 16px; }
.not-found { max-width: 560px; margin: 90px auto; padding: 48px; text-align: center; }.not-found-icon { display: block; color: #38bdf8; font-size: 50px; }.not-found h1 { margin: 12px 0 8px; }.not-found p { margin-bottom: 25px; }.not-found strong { color: #67e8f9; }
@media (max-width: 1100px) { .metric-grid { grid-template-columns: repeat(3, 1fr); }.tabs { margin-inline: -16px; padding-inline: 16px; }.asset-grid { grid-template-columns: repeat(2, 1fr); }.tab-button { padding: 10px 11px; font-size: 18px; } }
@media (max-width: 780px) { .incident-detail { padding: 16px 12px 40px; }.detail-header, .incident-hero, .tab-intro { align-items: flex-start; flex-direction: column; }.header-actions { width: 100%; }.hero-status { justify-content: flex-start; }.metric-grid, .response-metrics, .outcome-grid { grid-template-columns: repeat(2, 1fr); }.two-columns, .impact-layout, .source-grid, .ai-grid, .map-evidence-layout { grid-template-columns: 1fr; }.map-canvas { height: 300px; }.source-cards { grid-template-columns: 1fr 1fr; }.tab-button { padding: 10px 11px; font-size: 18px; } }
@media (max-width: 450px) { .metric-grid, .response-metrics, .source-cards, .outcome-grid { grid-template-columns: 1fr; }.summary-facts { grid-template-columns: 1fr; }.tabs { gap: 0; }.tab-button { padding: 9px 8px; font-size: 16px; }.tab-button span:not(.tab-icon):not(.critical-marker) { display: inline; margin-left: 3px; font-size: 18px; text-transform: uppercase; letter-spacing: .05em; }.forecast-number { font-size: 44px; }.map-footer { align-items: flex-start; flex-direction: column; }.resource-row { grid-template-columns: 1fr auto; }.resource-progress { grid-column: 1 / 3; grid-row: 2; }.resource-row small { grid-column: 1 / 3; }.region-row small { margin-left: 0; }.not-found { margin: 40px auto; padding: 30px 18px; } }

:root {
  --detail-bg: #0b0f19;
  --detail-panel: #0f172a;
  --detail-border: #1e293b;
  --detail-accent: #38bdf8;
  --detail-cyan: #38bdf8;
  --detail-primary: #f8fafc;
  --detail-secondary: #94a3b8;
  --detail-muted: #64748b;
  --detail-body: #cbd5e1;
  --detail-glow: none; /* Removed gamer glows */
}

/* Base structural styles */
body { background: var(--detail-bg) !important; }

.incident-detail { 
  min-height: 100%; 
  padding: 24px clamp(16px, 4vw, 56px) 64px; 
  color: var(--detail-primary); 
  background: var(--detail-bg);
  
 
}

/* Strict Monospace for Telemetry & Scientific Data */
.metric-value, .recon-coords-badge, .gauge-value, .panel-code, .forecast-number, .threat-value, .action-number {
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace !important;
  letter-spacing: -0.02em;
}

/* Matte, High-Contrast Structuring (Zero Gimmicks) */
.glass-panel,
.metric-card,
.response-metric,
.source-card,
.asset-card,
.channel-pill,
.env-gauge-tile {
  background: var(--detail-panel);
  border: 1px solid var(--detail-border);
  border-radius: 8px; /* Sharper corners for enterprise feel */
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  transition: border-color .15s ease, transform .15s ease;
  backdrop-filter: none; /* Removed heavy blurs for crispness */
}

/* Scientific Icon Styling */
.mono-icon {
  font-family: ui-monospace, monospace;
  color: #64748b; /* Neutral slate */
  font-size: 20px;
  filter: grayscale(100%);
}

.env-gauge-tile:hover .mono-icon {
  color: #38bdf8; /* Brand cyan on hover */
}

/* Strict interactive states without neon glows */
.glass-panel:hover,
.metric-card:hover,
.env-gauge-tile:hover { 
  border-color: #334155; 
  transform: translateY(-1px);
}

.metric-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 24px; }
.metric-card { min-height: 120px; padding: 16px; border-top: 3px solid #1e293b; }
.metric-card:hover { border-top: 3px solid var(--detail-accent); }

.threat-card { border-top: 3px solid #dc2626 !important; }
.threat-value { color: #ef4444 !important; font-weight: 700; }

.status-badge { border: 1px solid currentColor; }
.status-badge.active { background: #065f46; color: #34d399; border: none; }
.status-badge.monitoring { background: #1e3a8a; color: #60a5fa; border: none; }
.status-badge.resolved { background: #334155; color: #94a3b8; border: none; }

.ai-resource-table th {
  border-bottom: 2px solid #334155;
  color: #94a3b8;
  font-size: 18px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 12px 10px;
}

.ai-resource-table td {
  border-bottom: 1px solid #1e293b;
  padding: 12px 10px;

}

.priority-tag { font-family: ui-monospace, monospace; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 18px; }
.priority-tag.immediate { background: #7f1d1d; color: #fca5a5; }
.priority-tag.high { background: #78350f; color: #fdba74; }
.priority-tag.staged { background: #1e3a8a; color: #93c5fd; }

/* Scientific Data Provenance Watermarks */
.provenance-tag {
  display: block;
  font-family: ui-monospace, monospace;
  font-size: 16px;
  color: #475569;
  text-transform: uppercase;
  margin-top: 12px;
  text-align: right;
}

.forecast-timeline { 
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 24px; 
}

.forecast-point {
  display: grid;
  grid-template-columns: 80px 1fr;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #0f172a;
  border-left: 4px solid #38bdf8;
  border-radius: 0 6px 6px 0;
}

.forecast-point.critical { border-left-color: #dc2626; }
.forecast-point.warning { border-left-color: #d97706; }

.forecast-point strong { font-family: ui-monospace, monospace; font-size: 16px; color: #e2e8f0; }
.forecast-point p { margin: 0; color: #94a3b8; line-height: 1.5; }

.detail-header, .header-navigation, .header-actions, .hero-status, .panel-heading, .row-title, .tab-intro, .map-toolbar, .map-footer { display: flex; align-items: center; }
.detail-header { justify-content: space-between; gap: 20px; margin-bottom: 28px; }
.header-navigation, .header-actions { gap: 11px; flex-wrap: wrap; }
.back-button, .ghost-button, .primary-button { border: 1px solid rgba(148,163,184,.25); color: #e2e8f0; background: transparent; border-radius: 6px; padding: 8px 12px; cursor: pointer; font-size: 16px; font-weight: 600; transition: .15s ease; }
.back-button:hover, .ghost-button:hover { border-color: #38bdf8; color: #ffffff; background: rgba(56, 189, 248, 0.1); }
.breadcrumb-separator { color: #475569; }.breadcrumb-current { color: #94a3b8; font-size: 18px; }
.primary-button { background: #0284c7; border-color: #0284c7; color: #ffffff; }.primary-button:hover { background: #0369a1; border-color: #0369a1; }

.hero-copy h1,
.tab-intro h2,
.panel-heading h2,
.panel-heading h3 {
  color: var(--detail-primary);
  font-weight: 700;
  letter-spacing: -.02em;
}

.hero-location,
.tab-intro p,
.long-copy,
.summary-facts strong,
.action-list p,
.signal-row p,
.source-card p,
.not-found p { color: var(--detail-body); }

.metric-label,
.metric-footnote,
.metric-card small,
.response-metric span,
.response-metric small,
.summary-facts span,
.section-kicker,
.panel-code,
.tab-intro .section-kicker,
.freshness-list span,
.freshness-meter > span,
.outcome-grid span,
.outcome-grid small {
  color: var(--detail-secondary);
  font-size: 13px;
  font-weight: 600;
  letter-spacing: .05em;
  text-transform: none;
  line-height: 1.5;
}

.metric-value,
.response-metric strong,
.outcome-grid strong,
.zone-percent,
.population-row .row-title strong,
.total-callout strong,
.eta-callout strong,
.forecast-number,
.quality-score strong,
.risk-total {
  color: var(--detail-cyan);
  font-weight: 700;
  font-size: 1.4em;
  display: block;
  margin-top: 8px;
}

.metric-grid {
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.metric-card {
  min-width: 0;
  padding: clamp(18px, 1.4vw, 22px);
}

.metric-value { font-size: clamp(16px, 2vw, 27px); }
.metric-label { line-height: 1.35; }
.metric-footnote { line-height: 1.45; letter-spacing: 0; text-transform: none; }

.tabs {
  overflow-x: auto;
  overflow-y: hidden;
  flex-wrap: nowrap;
  scrollbar-width: thin;
  scrollbar-color: rgba(14, 165, 233, .55) transparent;
}
.tabs::-webkit-scrollbar { height: 5px; }
.tabs::-webkit-scrollbar-thumb { background: rgba(14, 165, 233, .55); border-radius: 999px; }
.tab-button { flex: 0 0 auto; white-space: nowrap; min-height: 48px; }

.tab-content { min-width: 0; }
.content-grid > .glass-panel,
.impact-layout > .glass-panel,
.source-grid > .glass-panel,
.ai-grid > .glass-panel,
.map-evidence-layout > .glass-panel {
  border-color: var(--detail-border);
  transition: border-color .25s ease, box-shadow .25s ease, transform .25s ease;
}

.action-panel {
  border: 2px solid var(--detail-accent) !important;
}
.action-panel:hover {
  border-color: #38bdf8 !important;
}

.loading-state, .error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  text-align: center;
  color: #94a3b8;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(14,165,233,.3);
  border-top-color: #0ea5e9;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  background: rgba(244,63,94,.1);
  border: 1px solid rgba(244,63,94,.3);
  border-radius: 8px;
  color: #fb7185;
}

.error-icon {
  font-size: 18px;
}

.ai-action-item {
  background: rgba(14,165,233,.08);
  border-left: 3px solid #0ea5e9;
  padding-left: 12px;
}

.panel-heading { margin-bottom: 20px; }
.panel-heading h2, .panel-heading h3 { font-size: clamp(16px, 1.5vw, 20px); }
.long-copy, .signal-row p, .source-card p, .not-found p { font-size: 18px; line-height: 1.65; }

@media (min-width: 1200px) {
  .metric-grid { grid-template-columns: repeat(6, minmax(0, 1fr)); }
}

@media (max-width: 1199px) {
  .metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (max-width: 767px) {
  .incident-detail { padding: 16px 12px 40px; }
  .detail-header, .incident-hero, .tab-intro { align-items: flex-start; }
  .header-actions { width: 100%; }
  .header-actions .ghost-button { flex: 1 1 auto; }
  .hero-status { justify-content: flex-start; }
  .metric-grid,
  .response-metrics,
  .outcome-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .metric-card { min-height: 128px; padding: 18px; }
  .two-columns, .impact-layout, .source-grid, .ai-grid, .map-evidence-layout { grid-template-columns: 1fr; }
  .map-canvas { height: 300px; }
  .source-cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .tab-content { padding-top: 20px; }
}

@media (max-width: 480px) {
  .incident-detail { padding: 12px 10px 32px; }
  .detail-header { gap: 12px; margin-bottom: 20px; }
  .header-actions { gap: 8px; }
  .header-actions .ghost-button { padding: 8px 9px; font-size: 18px; }
  .hero-copy h1 { font-size: clamp(25px, 8vw, 34px); }
  .metric-grid,
  .response-metrics,
  .source-cards,
  .outcome-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .metric-card { min-height: 132px; padding: 16px 14px; }
  .metric-value { margin-top: 12px; font-size: clamp(16px, 6vw, 22px); }
  .compact-value { font-size: 18px; }
  .content-grid > .glass-panel,
  .impact-layout > .glass-panel,
  .source-grid > .glass-panel,
  .ai-grid > .glass-panel { padding: 18px; }
  .asset-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .map-footer { align-items: flex-start; flex-direction: column; }
  .row-title { align-items: flex-start; }
}

@media (max-width: 360px) {
  .incident-detail { padding-inline: 8px; }
  .metric-grid,
  .response-metrics,
  .outcome-grid { gap: 8px; }
  .metric-card { padding: 14px 12px; }
  .metric-label, .metric-footnote { font-size: 16px; }
  .metric-value { font-size: 16px; }
  .tab-button { padding-inline: 11px; font-size: 18px; }
  .tab-button span:not(.tab-icon):not(.critical-marker) { display: inline; }
}

/* ===== PHASE 2 ROADMAP STYLES ===== */
.phase2-center-container {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
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
  background: rgba(15, 23, 42, 0.75);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 16px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}

.phase2-icon {
  font-size: 48px;
  margin-bottom: 16px;
  filter: drop-shadow(0 0 12px rgba(14, 165, 233, 0.4));
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

.phase2-card h2 {
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 12px 0;
}

.phase2-card p {
  font-size: 16px;
  line-height: 1.6;
  color: #cbd5e1;
  margin: 0 0 18px 0;
}

.phase2-note {
  font-size: 16px;
  line-height: 1.5;
  color: #94a3b8;
  background: rgba(30, 41, 59, 0.6);
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

/* ===== TACTICAL RECONNAISSANCE HERO CARD ===== */
.ai-recon-hero-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 20px 24px;
  margin-bottom: 22px;
  background: rgba(22, 29, 39, 0.72);
  border: 1px solid rgba(14, 165, 233, 0.35);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.recon-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.recon-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 800;
  color: #fbbf24;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}

.recon-status-badge.analyzed {
  color: #10b981;
}

.recon-info h2 {
  font-size: 18px;
  font-weight: 800;
  color: #ffffff;
  margin: 0;
}

.recon-info p {

  line-height: 1.5;
  color: #cbd5e1;
  margin: 0;
}

.recon-launch-button {
  background: var(--accent-cyan);
  color: #04141a;
  border: 1px solid #38bdf8;
  padding: 12px 24px;
  border-radius: 8px;

  font-weight: 800;
  letter-spacing: 0.5px;
  cursor: pointer;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.25s ease;
}

.recon-launch-button:hover:not(:disabled) {
  background: #38bdf8;
  transform: translateY(-2px);
}

.recon-launch-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.recon-trigger-btn {
  margin-top: 14px;

  padding: 10px 20px;
}

/* ===== TACTICAL NEURAL SCANNER HUD ===== */
.neural-scanner-overlay {
  position: fixed;
  inset: 0;
  background: rgba(11, 15, 25, 0.88);
  backdrop-filter: blur(14px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.neural-scanner-modal {
  max-width: 560px;
  width: 100%;
  padding: 32px 28px;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid #38bdf8;
  border-radius: 14px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.scanner-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 20px;
}

.scanner-radar-icon {
  font-size: 34px;
  animation: radarPulse 2s infinite;
}

@keyframes radarPulse {
  0% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.15); opacity: 1; }
  100% { transform: scale(1); opacity: 0.8; }
}

.scanner-titles h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.8px;
}

.scanner-titles small {
  color: #94a3b8;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.radar-scanline-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 99px;
  overflow: hidden;
  position: relative;
  margin-bottom: 24px;
}

.scanline-glow {
  width: 40%;
  height: 100%;
  background: #38bdf8;
  box-shadow: 0 0 14px #38bdf8;
  position: absolute;
  animation: scanSweep 1.5s infinite ease-in-out;
}

@keyframes scanSweep {
  0% { left: -40%; }
  100% { left: 100%; }
}

.scanner-step-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.scanner-step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #64748b;
  font-size: 16px;
  transition: all 0.3s ease;
}

.scanner-step-item.active {
  color: #38bdf8;
  font-weight: 700;
}

.scanner-step-item.complete {
  color: #10b981;
}

.step-indicator {
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid currentColor;
  font-size: 16px;
  font-weight: 800;
  flex-shrink: 0;
}

/* ===== DEEP AI TABS STYLING ===== */
.deep-ai-tab-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ai-facility-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
  margin-top: 14px;
}

.ai-facility-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.facility-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.facility-type-tag {
  font-size: 16px;
  font-weight: 800;
  color: #38bdf8;
  background: rgba(14, 165, 233, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
}

.facility-risk {
  font-size: 16px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 4px;
}

.facility-risk.critical { color: #ef4444; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); }
.facility-risk.high { color: #f59e0b; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); }
.facility-risk.moderate { color: #38bdf8; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); }

.ai-facility-card h4 {
  margin: 0;
  font-size: 16px;
  color: #ffffff;
}

.facility-meta {
  font-size: 18px;
  color: #94a3b8;
}

.facility-action {
  font-size: 16px;
  line-height: 1.4;
  color: #cbd5e1;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 8px;
}

.priority-tag {
  font-size: 16px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 4px;
}

.priority-tag.immediate { color: #ef4444; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); }
.priority-tag.high { color: #f59e0b; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); }
.priority-tag.staged { color: #38bdf8; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); }

/* Cascade card color coding */
.cascade-red { border-left: 4px solid #fb7185; }
.cascade-orange { border-left: 4px solid #fb923c; }
.cascade-yellow { border-left: 4px solid #fbbf24; }
.cascade-green { border-left: 4px solid #4ade80; }

.cascade-timeline-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

@media (max-width: 900px) {
  .cascade-timeline-grid { grid-template-columns: 1fr; }
  .ai-recon-hero-card { flex-direction: column; align-items: flex-start; }
  .recon-launch-button { width: 100%; justify-content: center; }
}

/* ===== STICKY HEADER & HANDY BACK BUTTON ===== */
.sticky-header {
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(20px);
  background: rgba(10, 15, 26, 0.92);
  border-bottom: 1px solid rgba(56, 189, 248, 0.25);
  padding: 12px 18px;
  margin: -24px -16px 20px -16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.primary-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(14, 165, 233, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.4);
  color: #38bdf8;
  font-weight: 700;

  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.primary-back-btn:hover {
  background: #0ea5e9;
  color: #03111b;
  transform: translateX(-2px);
}

.back-arrow {
  font-size: 16px;
}

/* ===== OPERATIONAL COMMAND DISPATCH BAR ===== */
.operational-command-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  margin-bottom: 18px;
  background: rgba(20, 30, 48, 0.75);
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 12px;
  gap: 16px;
}

.toolbar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: rgba(255, 255, 255, 0.9);
  text-transform: none;
}

.command-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.6);
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.cmd-btn {
  padding: 9px 16px;
  font-size: 16px;
  font-weight: 700;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.cmd-btn.primary {
  background: var(--accent-cyan);
  border: 1px solid #38bdf8;
  color: #04141a;
}

.cmd-btn.primary:hover:not(:disabled) {
  background: #38bdf8;
  transform: translateY(-1px);
}

.cmd-btn.secondary {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e2e8f0;
}

.cmd-btn.secondary:hover {
  background: rgba(30, 41, 59, 0.95);
  border-color: #38bdf8;
  color: #38bdf8;
}

/* ===== TACTICAL GIS RECONNAISSANCE MAP CARD ===== */
.recon-map-card {
  padding: 18px 20px;
  margin-bottom: 20px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(14, 165, 233, 0.3);
  border-radius: 12px;
}

.recon-map-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.recon-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.radar-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 5px rgba(56, 189, 248, 0.6);
}

.recon-title-group h4 {
  margin: 0;

  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.6px;
}

.recon-coords-badge {
  font-size: 18px;
  font-family: monospace;
  font-weight: 700;
  color: #94a3b8;
  background: rgba(30, 41, 59, 0.7);
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.recon-radar-canvas {
  position: relative;
  height: 220px;
  border-radius: 10px;
  overflow: hidden;
  background: radial-gradient(circle at center, rgba(14, 165, 233, 0.15), rgba(11, 15, 25, 0.95) 75%);
  border: 1px solid rgba(56, 189, 248, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}

.radar-grid-lines {
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle, transparent 20%, rgba(56, 189, 248, 0.08) 20%, transparent 22%),
    radial-gradient(circle, transparent 40%, rgba(56, 189, 248, 0.08) 40%, transparent 42%),
    radial-gradient(circle, transparent 65%, rgba(56, 189, 248, 0.08) 65%, transparent 67%),
    linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px);
  background-size: 100% 100%, 100% 100%, 100% 100%, 30px 30px, 30px 30px;
}

.radar-scan-sweep {
  position: absolute;
  inset: -50%;
  background: conic-gradient(from 0deg, transparent 75%, rgba(14, 165, 233, 0.25) 100%);
  animation: radarRotate 4s linear infinite;
  pointer-events: none;
}

@keyframes radarRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.ground-zero-marker {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
}

.epicenter-core {
  font-size: 28px;
  filter: drop-shadow(0 0 10px rgba(14, 165, 233, 0.8));
  z-index: 3;
}

.epicenter-ping {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 90px;
  height: 90px;
  margin-top: -45px;
  margin-left: -45px;
  border-radius: 50%;
  border: 2px solid #ef4444;
  background: rgba(239, 68, 68, 0.12);
  animation: bufferPulse 2.2s infinite ease-out;
  pointer-events: none;
}

@keyframes bufferPulse {
  0% { transform: scale(0.6); opacity: 1; }
  100% { transform: scale(1.6); opacity: 0; }
}

.danger-buffer-label {
  margin-top: 8px;
  font-size: 16px;
  font-weight: 800;
  color: #ffffff;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(239, 68, 68, 0.4);
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.wind-vector-indicator {
  position: absolute;
  top: 14px;
  left: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(56, 189, 248, 0.25);
  padding: 4px 10px;
  border-radius: 6px;
  z-index: 3;
}

.wind-arrow {
  color: #38bdf8;
  font-size: 16px;
  font-weight: 800;
}

.wind-label {
  font-size: 16px;
  font-weight: 700;
  color: #cbd5e1;
}

.recon-overlay-actions {
  position: absolute;
  bottom: 12px;
  right: 14px;
  z-index: 3;
}

.gis-console-btn {
  background: rgba(14, 165, 233, 0.2);
  border: 1px solid #0ea5e9;
  color: #38bdf8;
  font-size: 18px;
  font-weight: 700;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.gis-console-btn:hover {
  background: #0ea5e9;
  color: #03111b;
}

/* ===== ENVIRONMENTAL SENSOR GAUGES STRIP ===== */
.environmental-gauge-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.env-gauge-tile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
}

.gauge-icon {
  font-size: 24px;
}

.gauge-info {
  display: flex;
  flex-direction: column;
}

.gauge-label {
  font-size: 16px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.gauge-value {
  font-size: 16px;
  font-weight: 800;
  color: #f1f5f9;
  margin: 1px 0;
}

.gauge-desc {
  font-size: 16px;
  color: #64748b;
}

/* ===== MOBILE RESPONSIVE TWEAKS FOR INCIDENT DETAIL ===== */
@media (max-width: 900px) {
  .environmental-gauge-strip {
    grid-template-columns: repeat(2, 1fr);
  }
  .operational-command-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .toolbar-actions {
    flex-direction: column;
    width: 100%;
  }
  .cmd-btn {
    width: 100%;
    justify-content: center;
  }
  .cascade-timeline-grid {
    grid-template-columns: 1fr;
  }
  .ai-recon-hero-card {
    flex-direction: column;
    align-items: flex-start;
  }
  .recon-launch-button {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 600px) {
  .environmental-gauge-strip {
    grid-template-columns: 1fr;
  }
  .recon-map-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .recon-radar-canvas {
    height: 180px;
  }
}

.incident-id {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: #cbd5e1;
  background: rgba(148, 163, 184, 0.15);
  vertical-align: middle;
}
</style>

