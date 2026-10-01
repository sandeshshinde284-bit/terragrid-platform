<template>
  <main class="incident-detail">
    <div v-if="!incident" class="not-found glass-panel">
      <span class="not-found-icon">⌁</span>
      <h1>Incident not found</h1>
      <p>No incident matching <strong>{{ incidentId }}</strong> exists in the current event feed.</p>
      <button class="primary-button" type="button" @click="goTo('/incidents')">Back to incidents</button>
    </div>

    <template v-else>
      <header class="detail-header">
        <div class="header-navigation">
          <button class="back-button" type="button" aria-label="Back to incidents" @click="goTo('/incidents')">
            <span aria-hidden="true">←</span> Incidents
          </button>
          <span class="breadcrumb-separator">/</span>
          <span class="breadcrumb-current">{{ incident.location }}</span>
        </div>
        <div class="header-actions">
          <button class="ghost-button" type="button" @click="goTo('/')">⌂ Dashboard</button>
          <button class="ghost-button" type="button" @click="goTo('/analysis')">◈ Analysis</button>
          <button class="ghost-button" type="button" @click="goTo('/map')">◎ Live map</button>
        </div>
      </header>

      <section class="incident-hero">
        <div class="hero-copy">
          <div class="eyebrow"><span class="live-dot"></span> INCIDENT {{ incident.id.toUpperCase() }}</div>
          <h1>{{ incidentLabel }}</h1>
          <p class="hero-location"><span>⌖</span> {{ incident.location }} · Detected {{ formatDate(incident.detectionTime) }}</p>
        </div>
        <div class="hero-status">
          <span class="type-badge" :class="`type-${incident.type}`">{{ formatIncidentType(incident.type) }}</span>
          <span class="severity-badge" :class="`severity-${incident.severity}`">{{ incident.severity.toUpperCase() }} SEVERITY</span>
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
          <div v-if="activeTab === 'overview'" class="overview-tab">
            <div class="metric-grid">
              <article class="metric-card glass-panel threat-card">
                <span class="metric-label">Threat score</span>
                <strong class="metric-value threat-value">{{ threatScore }}<small>/100</small></strong>
                <span class="metric-footnote">{{ threatLevel }} · {{ threatRationale }}</span>
                <div class="progress-track"><span class="progress-fill threat-fill" :style="{ width: `${threatScore}%` }"></span></div>
              </article>
              <article class="metric-card glass-panel">
                <span class="metric-label">Location</span>
                <strong class="metric-value compact-value">{{ incident.location }}</strong>
                <span class="metric-footnote">Affected footprint {{ formatNumber(incident.affectedArea) }} km²</span>
              </article>
              <article class="metric-card glass-panel">
                <span class="metric-label">Population at risk</span>
                <strong class="metric-value">{{ formatNumber(incident.affectedPopulation) }}</strong>
                <span class="metric-footnote">Estimated residents in exposure zone</span>
              </article>
              <article class="metric-card glass-panel">
                <span class="metric-label">Growth trend</span>
                <strong class="metric-value trend-value">{{ getTrendDirection(incident.trend) }} {{ Math.abs(incident.trend).toFixed(1) }}%</strong>
                <span class="metric-footnote">Change in affected area / hour</span>
              </article>
              <article class="metric-card glass-panel">
                <span class="metric-label">6-hour forecast</span>
                <strong class="metric-value">{{ formatNumber(incident.forecast6h) }} <small>km²</small></strong>
                <span class="metric-footnote">Projected maximum footprint</span>
              </article>
              <article class="metric-card glass-panel">
                <span class="metric-label">Current status</span>
                <strong class="metric-value compact-value status-text">{{ formatStatus(incident.status) }}</strong>
                <span class="metric-footnote">Last operational update {{ relativeTime(incident.detectionTime) }}</span>
              </article>
            </div>

            <div class="content-grid two-columns">
              <article class="glass-panel">
                <div class="panel-heading"><div><span class="section-kicker">COMMAND BRIEF</span><h2>Situation summary</h2></div><span class="panel-code">OV-01</span></div>
                <p class="long-copy">{{ summaryText }}</p>
                <div class="summary-facts">
                  <div><span>Incident class</span><strong>{{ formatIncidentType(incident.type) }}</strong></div>
                  <div><span>Operational posture</span><strong>{{ operationalPosture }}</strong></div>
                  <div><span>Data quality</span><strong>{{ detail.dataQuality }}%</strong></div>
                  <div><span>Next review</span><strong>In {{ detail.nextReview }}</strong></div>
                </div>
              </article>
              <article class="glass-panel action-panel">
                <div class="panel-heading"><div><span class="section-kicker">DECISION SUPPORT</span><h2>Recommended actions</h2></div><span class="ai-chip">AI PRIORITIZED</span></div>
                <ol class="action-list">
                  <li v-for="(action, index) in detail.recommendedActions" :key="action.title">
                    <span class="action-number">0{{ index + 1 }}</span><div><strong>{{ action.title }}</strong><p>{{ action.description }}</p></div><span class="priority" :class="`priority-${action.priority}`">{{ action.priority }}</span>
                  </li>
                </ol>
              </article>
            </div>
          </div>

          <!-- IMPACT ANALYSIS -->
          <div v-else-if="activeTab === 'impact'" class="impact-tab">
            <div class="tab-intro"><div><span class="section-kicker">FEATURE 09 · IMPACT ASSESSMENT</span><h2>Impact analysis</h2><p>Exposure is segmented into operational zones to guide resource allocation.</p></div><span class="updated-pill">Updated {{ relativeTime(detail.lastUpdated) }}</span></div>
            <div class="impact-layout">
              <article class="glass-panel zone-panel"><div class="panel-heading"><div><span class="section-kicker">EXPOSURE MODEL</span><h3>Affected zones</h3></div><span class="panel-code">IA-01</span></div><div class="zone-list"><div v-for="zone in detail.zones" :key="zone.name" class="zone-row"><div class="zone-icon" :class="`zone-${zone.level}`">{{ zone.code }}</div><div class="zone-main"><div class="row-title"><strong>{{ zone.name }}</strong><span>{{ zone.level }} risk</span></div><div class="progress-track"><span class="progress-fill" :class="`fill-${zone.level}`" :style="{ width: `${zone.percentage}%` }"></span></div><small>{{ formatNumber(zone.area) }} km² · {{ zone.note }}</small></div><strong class="zone-percent">{{ zone.percentage }}%</strong></div></div></article>
              <article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">HUMAN EXPOSURE</span><h3>Population by area</h3></div><span class="panel-code">IA-02</span></div><div class="population-bars"><div v-for="area in detail.populationByArea" :key="area.area" class="population-row"><div class="row-title"><span>{{ area.area }}</span><strong>{{ formatNumber(area.population) }}</strong></div><div class="bar-with-label"><div class="progress-track"><span class="progress-fill population-fill" :style="{ width: `${area.percent}%` }"></span></div><small>{{ area.percent }}%</small></div></div></div><div class="total-callout"><span>Total exposed population</span><strong>{{ formatNumber(incident.affectedPopulation) }}</strong></div></article>
            </div>
            <div class="content-grid two-columns">
              <article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">CRITICAL ASSETS</span><h3>Infrastructure affected</h3></div><span class="panel-code">IA-03</span></div><div class="asset-grid"><div v-for="asset in detail.infrastructure" :key="asset.label" class="asset-card"><span class="asset-icon">{{ asset.icon }}</span><strong>{{ asset.count }}</strong><span>{{ asset.label }}</span><small :class="asset.status">{{ asset.status }}</small></div></div></article>
              <article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">LOGISTICS</span><h3>Resource requirements</h3></div><span class="panel-code">IA-04</span></div><div class="resource-list"><div v-for="resource in detail.resources" :key="resource.name" class="resource-row"><span>{{ resource.name }}</span><div class="resource-progress"><span :style="{ width: `${resource.fulfilled}%` }"></span></div><strong>{{ resource.required }}</strong><small>{{ resource.fulfilled }}% ready</small></div></div></article>
            </div>
          </div>

          <!-- MAP & EVIDENCE -->
          <div v-else-if="activeTab === 'map'" class="map-tab">
            <div class="tab-intro"><div><span class="section-kicker">FEATURES 03 · 11 · 13</span><h2>Map & evidence</h2><p>Geospatial context and validated media supporting the current incident perimeter.</p></div><button class="primary-button" type="button" @click="goTo('/map')">Open interactive map ↗</button></div>
            <div class="map-evidence-layout">
              <article class="glass-panel map-preview"><div class="map-toolbar"><span class="map-title">SATELLITE REFERENCE · {{ incident.location.toUpperCase() }}</span><span class="map-live"><i></i> LIVE LAYERS</span></div><div class="map-canvas"><div class="map-grid"></div><div v-for="(zone, index) in detail.zones" :key="zone.name" class="map-zone" :class="`map-zone-${index + 1}`"><span>{{ zone.code }}</span></div><div class="map-crosshair">⊕</div><div class="map-scale">N<br><span>━━</span><br>2 km</div><div class="map-legend"><span><i class="legend-dot critical"></i> Critical</span><span><i class="legend-dot watch"></i> Watch</span><span><i class="legend-dot safe"></i> Monitored</span></div></div><div class="map-footer"><span>Imagery: Sentinel-2 · 10m resolution</span><span>Coordinates: {{ detail.coordinates }}</span></div></article>
              <article class="glass-panel evidence-panel"><div class="panel-heading"><div><span class="section-kicker">MEDIA VALIDATION</span><h3>Evidence register</h3></div><span class="verified-chip">{{ verifiedEvidence }}/{{ detail.evidence.length }} VERIFIED</span></div><div class="evidence-list"><div v-for="evidence in detail.evidence" :key="evidence.id" class="evidence-row"><div class="evidence-thumb" :class="`evidence-${evidence.kind}`">{{ evidence.kind === 'satellite' ? '◉' : evidence.kind === 'field' ? '▣' : '◌' }}</div><div class="evidence-main"><strong>{{ evidence.title }}</strong><small>{{ evidence.source }} · {{ evidence.captured }}</small></div><span class="evidence-status" :class="`evidence-${evidence.status.toLowerCase()}`">{{ evidence.status }}</span></div></div><div class="verification-score"><div class="score-ring"><strong>{{ detail.imageVerification }}%</strong><small>confidence</small></div><div><strong>Image verification status</strong><p>Cross-checked against temporal and geospatial signals.</p></div></div></article>
            </div>
          </div>

          <!-- EMERGENCY RESPONSE -->
          <div v-else-if="activeTab === 'response'" class="response-tab">
            <div class="tab-intro"><div><span class="section-kicker">FEATURE 10 · EVACUATION OPERATIONS</span><h2>Emergency response</h2><p>Live route capacity and deployment readiness for the affected population.</p></div><span class="response-state"><i></i> RESPONSE ACTIVE</span></div>
            <div class="response-metrics"><div v-for="metric in detail.responseMetrics" :key="metric.label" class="glass-panel response-metric"><span>{{ metric.label }}</span><strong>{{ metric.value }}</strong><small>{{ metric.note }}</small></div></div>
            <div class="content-grid two-columns"><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">SAFE MOVEMENT</span><h3>Evacuation routes</h3></div><span class="panel-code">ER-01</span></div><div class="route-list"><div v-for="routeItem in detail.routes" :key="routeItem.name" class="route-row"><div class="route-status" :class="`route-${routeItem.status}`"><span></span></div><div class="route-main"><div class="row-title"><strong>{{ routeItem.name }}</strong><span>{{ routeItem.status }}</span></div><small>{{ routeItem.direction }} · {{ routeItem.distance }} · capacity {{ routeItem.capacity }}</small><div class="route-track"><span :style="{ width: `${routeItem.clearance}%` }"></span></div></div><strong class="route-time">{{ routeItem.eta }}</strong></div></div></article><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">FIELD OPERATIONS</span><h3>Resource deployment</h3></div><span class="panel-code">ER-02</span></div><div class="deployment-list"><div v-for="deployment in detail.deployments" :key="deployment.name" class="deployment-row"><span class="deployment-icon">{{ deployment.icon }}</span><div><strong>{{ deployment.name }}</strong><small>{{ deployment.location }}</small></div><span class="deployment-count">{{ deployment.count }}</span><span class="deployment-status" :class="deployment.status">{{ deployment.status }}</span></div></div><div class="eta-callout"><span>Estimated full evacuation</span><strong>{{ detail.evacuationTime }}</strong><small>Based on current route clearance and traffic model</small></div></article></div>
          </div>

          <!-- INCIDENT HISTORY -->
          <div v-else-if="activeTab === 'history'" class="history-tab">
            <div class="tab-intro"><div><span class="section-kicker">FEATURE 05 · HISTORICAL CONTEXT</span><h2>Incident history</h2><p>Comparable events reveal patterns, response outcomes, and reusable lessons.</p></div><span class="panel-code">HISTORY / {{ detail.historicalPattern }}</span></div>
            <div class="content-grid two-columns"><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">COMPARABLE EVENTS</span><h3>Similar past incidents</h3></div><span class="panel-code">IH-01</span></div><div class="history-list"><div v-for="past in detail.pastIncidents" :key="past.name" class="history-row"><div class="history-year">{{ past.year }}</div><div class="history-main"><strong>{{ past.name }}</strong><small>{{ past.location }} · {{ past.duration }}</small></div><div class="history-stat"><strong>{{ past.population }}</strong><small>affected</small></div><span class="similarity">{{ past.similarity }}% match</span></div></div></article><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">BENCHMARK</span><h3>Comparison metrics</h3></div><span class="panel-code">IH-02</span></div><div class="comparison-list"><div v-for="comparison in detail.comparisons" :key="comparison.label" class="comparison-row"><span>{{ comparison.label }}</span><div class="comparison-values"><strong>{{ comparison.current }}</strong><span>vs {{ comparison.baseline }}</span></div><span class="comparison-delta" :class="comparison.direction">{{ comparison.delta }}</span></div></div></article></div>
            <div class="content-grid two-columns"><article class="glass-panel pattern-card"><div class="panel-heading"><div><span class="section-kicker">PATTERN ANALYSIS</span><h3>Historical patterns</h3></div><span class="pattern-confidence">{{ detail.patternConfidence }}% confidence</span></div><ul class="insight-list"><li v-for="pattern in detail.patterns" :key="pattern"><span>↗</span>{{ pattern }}</li></ul></article><article class="glass-panel lessons-card"><div class="panel-heading"><div><span class="section-kicker">AFTER-ACTION LEARNING</span><h3>Lessons learned</h3></div><span class="panel-code">IH-04</span></div><ol class="lessons-list"><li v-for="lesson in detail.lessons" :key="lesson.title"><strong>{{ lesson.title }}</strong><span>{{ lesson.text }}</span></li></ol></article></div>
          </div>

          <!-- SOURCE OF TRUTH -->
          <div v-else-if="activeTab === 'source'" class="source-tab">
            <div class="tab-intro"><div><span class="section-kicker">FEATURE 07 · GOVERNANCE LAYER</span><h2>Source of truth <span class="critical-marker">★</span></h2><p>Every signal is traceable, freshness-scored, and independently verified before it informs decisions.</p></div><div class="quality-score"><span>DATA QUALITY</span><strong>{{ detail.dataQuality }}<small>/100</small></strong></div></div>
            <div class="source-grid"><article class="glass-panel source-overview"><div class="panel-heading"><div><span class="section-kicker">PROVENANCE</span><h3>Data source origin</h3></div><span class="verified-chip">● {{ verifiedSources }} VERIFIED</span></div><div class="source-cards"><div v-for="source in detail.sources" :key="source.name" class="source-card"><div class="source-card-head"><span class="source-icon">{{ source.icon }}</span><span class="source-status" :class="source.status.toLowerCase()">{{ source.status }}</span></div><strong>{{ source.name }}</strong><p>{{ source.description }}</p><div class="source-meta"><span>{{ source.records }} records</span><span>{{ source.confidence }}% confidence</span></div></div></div></article><article class="glass-panel freshness-panel"><div class="panel-heading"><div><span class="section-kicker">FRESHNESS</span><h3>Verification status</h3></div><span class="panel-code">ST-02</span></div><div class="freshness-list"><div><span>Last updated</span><strong>{{ formatDate(detail.lastUpdated) }}</strong></div><div><span>Last verified</span><strong>{{ formatDate(detail.lastVerified) }}</strong></div><div><span>Verification cadence</span><strong>Every 15 minutes</strong></div><div><span>Stale data threshold</span><strong>60 minutes</strong></div></div><div class="freshness-meter"><span>Freshness window</span><div class="progress-track"><span class="progress-fill freshness-fill" style="width: 82%"></span></div><strong>82%</strong></div></article></div>
            <div class="content-grid two-columns"><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">CHAIN OF CUSTODY</span><h3>Data lineage</h3></div><span class="panel-code">ST-03</span></div><div class="lineage-list"><div v-for="lineage in detail.lineage" :key="lineage.label" class="lineage-row"><span class="lineage-marker"></span><div><strong>{{ lineage.label }}</strong><small>{{ lineage.value }}</small></div><span class="confidence-badge">{{ lineage.confidence }}%</span></div></div></article><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">ACCOUNTABILITY</span><h3>Audit trail</h3></div><span class="panel-code">ST-04</span></div><div class="audit-list"><div v-for="audit in detail.auditTrail" :key="audit.time + audit.actor" class="audit-row"><span class="audit-time">{{ audit.time }}</span><div><strong>{{ audit.action }}</strong><small>{{ audit.actor }} · {{ audit.source }}</small></div></div></div></article></div>
          </div>

          <!-- AI INSIGHTS -->
          <div v-else-if="activeTab === 'ai'" class="ai-tab">
            <div class="tab-intro"><div><span class="section-kicker">FEATURE 12 · ASK THE MAP AI</span><h2>AI insights</h2><p>Models combine live telemetry, imagery, terrain, and historical analogues into an explainable forecast.</p></div><button class="primary-button" type="button" @click="goTo('/ask-map')">Ask the Map AI ↗</button></div>
            <div class="ai-grid"><article class="glass-panel prediction-card"><div class="panel-heading"><div><span class="section-kicker">PREDICTION ENGINE</span><h3>Forecast outlook</h3></div><span class="ai-chip">MODEL v4.8</span></div><div class="prediction-head"><div class="forecast-number">{{ detail.aiForecast.probability }}<small>%</small></div><div><strong>{{ detail.aiForecast.headline }}</strong><p>{{ detail.aiForecast.window }}</p></div></div><div class="forecast-timeline"><div v-for="forecast in detail.aiForecast.timeline" :key="forecast.time" class="forecast-point"><span class="forecast-dot" :class="forecast.state"></span><strong>{{ forecast.time }}</strong><small>{{ forecast.value }}</small></div></div></article><article class="glass-panel risk-card"><div class="panel-heading"><div><span class="section-kicker">EXPLAINABILITY</span><h3>Risk score breakdown</h3></div><strong class="risk-total">{{ detail.aiForecast.riskScore }}/100</strong></div><div class="risk-list"><div v-for="risk in detail.aiForecast.riskBreakdown" :key="risk.label" class="risk-row"><div class="row-title"><span>{{ risk.label }}</span><strong>{{ risk.score }}</strong></div><div class="progress-track"><span class="progress-fill risk-fill" :style="{ width: `${risk.score}%` }"></span></div></div></div></article></div>
            <div class="content-grid two-columns"><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">SIGNAL INTERPRETATION</span><h3>Pattern analysis</h3></div><span class="confidence-badge">{{ detail.aiForecast.confidence }}% confidence</span></div><div class="ai-pattern"><div v-for="signal in detail.aiForecast.signals" :key="signal.title" class="signal-row"><span class="signal-icon">{{ signal.icon }}</span><div><strong>{{ signal.title }}</strong><p>{{ signal.detail }}</p></div><span class="signal-impact">{{ signal.impact }}</span></div></div></article><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">AUTOMATED DECISION SUPPORT</span><h3>AI recommended actions</h3></div><span class="ai-chip">LIVE</span></div><ol class="action-list ai-actions"><li v-for="(action, index) in detail.aiForecast.actions" :key="action.title"><span class="action-number">0{{ index + 1 }}</span><div><strong>{{ action.title }}</strong><p>{{ action.reason }}</p></div></li></ol></article></div>
          </div>

          <!-- ALERTS & COMMUNICATIONS -->
          <div v-else-if="activeTab === 'alerts'" class="alerts-tab">
            <div class="tab-intro"><div><span class="section-kicker">FEATURES 06 · 13 · REAL-TIME NOTIFICATIONS</span><h2>Alerts & communications</h2><p>Broadcast reach, delivery health, and community response in one operational view.</p></div><button class="primary-button" type="button" @click="goTo('/alerts')">Open alert center ↗</button></div>
            <div class="response-metrics"><div v-for="metric in detail.communicationMetrics" :key="metric.label" class="glass-panel response-metric"><span>{{ metric.label }}</span><strong>{{ metric.value }}</strong><small>{{ metric.note }}</small></div></div>
            <div class="content-grid two-columns"><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">BROADCAST LOG</span><h3>Alert broadcast history</h3></div><span class="panel-code">AC-01</span></div><div class="alert-history"><div v-for="alert in detail.alertHistory" :key="alert.time + alert.message" class="alert-row"><span class="alert-severity" :class="alert.severity"></span><div><strong>{{ alert.message }}</strong><small>{{ alert.time }} · {{ alert.channel }}</small></div><span class="delivery-status" :class="alert.status">{{ alert.status }}</span></div></div></article><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">REACH & DELIVERY</span><h3>Who was notified</h3></div><span class="panel-code">AC-02</span></div><div class="region-list"><div v-for="region in detail.notifiedRegions" :key="region.name" class="region-row"><span>{{ region.name }}</span><div class="progress-track"><span class="progress-fill region-fill" :style="{ width: `${region.delivery}%` }"></span></div><strong>{{ formatNumber(region.count) }}</strong><small>{{ region.delivery }}% delivered</small></div></div><div class="channel-pills"><span v-for="channel in detail.channels" :key="channel.name" class="channel-pill"><i>{{ channel.icon }}</i>{{ channel.name }} <strong>{{ channel.percent }}%</strong></span></div></article></div>
            <article class="glass-panel response-panel"><div class="panel-heading"><div><span class="section-kicker">OUTCOME MEASUREMENT</span><h3>Response metrics</h3></div><span class="panel-code">AC-03</span></div><div class="outcome-grid"><div v-for="outcome in detail.responseOutcomes" :key="outcome.label"><span>{{ outcome.label }}</span><strong>{{ outcome.value }}</strong><small>{{ outcome.note }}</small></div></div></article>
          </div>
        </section>
      </Transition>
    </template>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEventsStore } from '@/stores'
import type { IncidentLevel1, Event } from '@/types'

type TabId = 'overview' | 'impact' | 'map' | 'response' | 'history' | 'source' | 'ai' | 'alerts'
type Status = 'Verified' | 'Pending' | 'Unverified'

interface Tab { id: TabId; label: string; icon: string }
interface DetailData {
  dataQuality: number; nextReview: string; lastUpdated: Date; lastVerified: Date; coordinates: string; imageVerification: number
  recommendedActions: { title: string; description: string; priority: string }[]
  zones: { name: string; code: string; level: string; percentage: number; area: number; note: string }[]
  populationByArea: { area: string; population: number; percent: number }[]
  infrastructure: { label: string; icon: string; count: number; status: string }[]
  resources: { name: string; required: string; fulfilled: number }[]
  evidence: { id: string; title: string; source: string; captured: string; kind: string; status: Status }[]
  responseMetrics: { label: string; value: string; note: string }[]
  routes: { name: string; status: string; direction: string; distance: string; capacity: string; clearance: number; eta: string }[]
  deployments: { name: string; location: string; count: string; icon: string; status: string }[]
  evacuationTime: string
  historicalPattern: string; pastIncidents: { year: string; name: string; location: string; duration: string; population: string; similarity: number }[]
  comparisons: { label: string; current: string; baseline: string; delta: string; direction: string }[]
  patterns: string[]; patternConfidence: number; lessons: { title: string; text: string }[]
  sources: { name: string; icon: string; status: Status; description: string; records: number; confidence: number }[]
  lineage: { label: string; value: string; confidence: number }[]
  auditTrail: { time: string; action: string; actor: string; source: string }[]
  aiForecast: { probability: number; headline: string; window: string; riskScore: number; confidence: number; timeline: { time: string; value: string; state: string }[]; riskBreakdown: { label: string; score: number }[]; signals: { title: string; detail: string; icon: string; impact: string }[]; actions: { title: string; reason: string }[] }
  communicationMetrics: { label: string; value: string; note: string }[]
  alertHistory: { time: string; message: string; channel: string; severity: string; status: string }[]
  notifiedRegions: { name: string; count: number; delivery: number }[]
  channels: { name: string; icon: string; percent: number }[]
  responseOutcomes: { label: string; value: string; note: string }[]
}

const route = useRoute()
const router = useRouter()
const eventsStore = useEventsStore()
const activeTab = ref<TabId>('overview')
const incidentId = computed(() => String(route.params.id || ''))
const incident = computed<IncidentLevel1 | undefined>(() => eventsStore.allIncidents.find(item => item.id === incidentId.value))

const tabs: Tab[] = [
  { id: 'overview', label: 'Overview', icon: '◈' }, 
  { id: 'impact', label: 'Impact', icon: '▦' },
  { id: 'map', label: 'Map', icon: '◎' }, 
  { id: 'response', label: 'Response', icon: '⚑' },
  { id: 'history', label: 'History', icon: '◷' }, 
  { id: 'source', label: 'Source', icon: '✦' },
  { id: 'ai', label: 'Insights', icon: '⌁' }, 
  { id: 'alerts', label: 'Alerts', icon: '⌁' },
];

const detail = computed<DetailData>(() => makeDetail(incident.value))
const incidentLabel = computed(() => incident.value ? `${formatIncidentType(incident.value.type)} event` : 'Incident')
const threatScore = computed(() => incident.value ? Math.min(99, Math.round(incident.value.severity === 'high' ? 78 + Math.abs(incident.value.trend) : incident.value.severity === 'medium' ? 55 + incident.value.trend : 32 + incident.value.trend)) : 0)
const threatLevel = computed(() => threatScore.value >= 80 ? 'Critical exposure' : threatScore.value >= 60 ? 'Elevated exposure' : 'Moderate exposure')
const threatRationale = computed(() => incident.value?.trend && incident.value.trend > 10 ? 'rapid expansion detected' : 'stable monitoring posture')
const operationalPosture = computed(() => incident.value?.status === 'active' ? 'Full response' : incident.value?.status === 'monitoring' ? 'Enhanced monitoring' : 'Recovery')
const summaryText = computed(() => incident.value ? `A ${formatIncidentType(incident.value.type).toLowerCase()} incident is affecting ${incident.value.location}. The current footprint covers ${formatNumber(incident.value.affectedArea)} km² and includes an estimated ${formatNumber(incident.value.affectedPopulation)} residents. Models indicate ${incident.value.trend > 0 ? 'continued expansion' : 'contraction'} over the next six hours, requiring coordinated field response and continuous verification.` : '')
const verifiedEvidence = computed(() => detail.value.evidence.filter(item => item.status === 'Verified').length)
const verifiedSources = computed(() => detail.value.sources.filter(item => item.status === 'Verified').length)

function goTo(path: string) { router.push(path) }
function formatNumber(value: number) { return new Intl.NumberFormat('en-US').format(value) }
function formatDate(value: Date) { return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(value)) }
function relativeTime(value: Date) { const minutes = Math.max(1, Math.round((Date.now() - new Date(value).getTime()) / 60000)); return minutes < 60 ? `${minutes}m ago` : `${Math.round(minutes / 60)}h ago` }
function formatIncidentType(type: Event['type']) { return type.charAt(0).toUpperCase() + type.slice(1) }
function formatStatus(status: IncidentLevel1['status']) { return status.charAt(0).toUpperCase() + status.slice(1) }
function getTrendDirection(value: number) { return value >= 0 ? '↗' : '↘' }

function makeDetail(item?: IncidentLevel1): DetailData {
  const now = new Date()
  const population = item?.affectedPopulation || 85000
  const area = item?.affectedArea || 1250
  const type = item?.type || 'fire'
  return {
    dataQuality: 94, nextReview: '12 minutes', lastUpdated: new Date(now.getTime() - 8 * 60000), lastVerified: new Date(now.getTime() - 14 * 60000), coordinates: '34.2286° N, 117.8610° W', imageVerification: 96,
    recommendedActions: [{ title: 'Evacuate critical exposure zone', description: 'Issue a mandatory evacuation order for Zone A and open receiving shelters.', priority: 'urgent' }, { title: 'Stage mobile medical teams', description: 'Position two teams near the eastern access corridor before peak movement.', priority: 'high' }, { title: 'Protect utility corridor', description: 'Coordinate with utilities to isolate vulnerable substations and maintain continuity.', priority: 'medium' }],
    zones: [{ name: 'Zone A · Primary impact', code: 'A', level: 'critical', percentage: 38, area: Math.round(area * .38), note: 'Direct exposure' }, { name: 'Zone B · Expansion edge', code: 'B', level: 'high', percentage: 34, area: Math.round(area * .34), note: 'Wind / water flow' }, { name: 'Zone C · Monitoring ring', code: 'C', level: 'watch', percentage: 28, area: Math.round(area * .28), note: 'Potential spread' }],
    populationByArea: [{ area: 'North corridor', population: Math.round(population * .31), percent: 31 }, { area: 'East foothills', population: Math.round(population * .27), percent: 27 }, { area: 'Central valley', population: Math.round(population * .24), percent: 24 }, { area: 'South communities', population: Math.round(population * .18), percent: 18 }],
    infrastructure: [{ label: 'Hospitals', icon: '✚', count: type === 'flood' ? 3 : 2, status: 'operational' }, { label: 'Road segments', icon: '╱', count: 14, status: 'restricted' }, { label: 'Bridges', icon: '⌁', count: 4, status: 'inspect now' }, { label: 'Shelters', icon: '⌂', count: 8, status: 'available' }],
    resources: [{ name: 'Shelter beds', required: '12,400', fulfilled: 78 }, { name: 'Emergency vehicles', required: '46 units', fulfilled: 64 }, { name: 'Medical kits', required: '1,860', fulfilled: 91 }, { name: 'Water supply', required: '84,000 L', fulfilled: 56 }],
    evidence: [{ id: 'ev-1', title: 'Perimeter mosaic · 10m', source: 'Sentinel-2 satellite', captured: '8 min ago', kind: 'satellite', status: 'Verified' }, { id: 'ev-2', title: 'Eastern access corridor', source: 'Field unit 07', captured: '22 min ago', kind: 'field', status: 'Verified' }, { id: 'ev-3', title: 'Community report cluster', source: 'Civic signal network', captured: '31 min ago', kind: 'social', status: 'Pending' }, { id: 'ev-4', title: 'Thermal anomaly frame', source: 'NOAA GOES-West', captured: '42 min ago', kind: 'satellite', status: 'Verified' }],
    responseMetrics: [{ label: 'Routes open', value: '7 / 9', note: '2 under clearance' }, { label: 'Units deployed', value: '38', note: 'of 51 assigned' }, { label: 'Shelters active', value: '8', note: '2,940 beds free' }, { label: 'Evacuation progress', value: '42%', note: '12,860 residents moved' }],
    routes: [{ name: 'Route 01 · Sierra Highway', status: 'open', direction: 'Southbound', distance: '18.4 km', capacity: 'high', clearance: 92, eta: '24 min' }, { name: 'Route 02 · Valley Connector', status: 'limited', direction: 'Westbound', distance: '12.1 km', capacity: 'medium', clearance: 61, eta: '38 min' }, { name: 'Route 03 · Foothill Bypass', status: 'clearing', direction: 'Northwest', distance: '22.7 km', capacity: 'low', clearance: 34, eta: '55 min' }],
    deployments: [{ name: 'Fire & rescue', location: 'Zone A staging', count: '14 units', icon: '✚', status: 'active' }, { name: 'Medical response', location: 'Civic shelter', count: '8 teams', icon: '✚', status: 'active' }, { name: 'Traffic control', location: 'Route 01', count: '12 officers', icon: '⚑', status: 'moving' }, { name: 'Utility crew', location: 'East substation', count: '4 crews', icon: 'ϟ', status: 'standby' }],
    evacuationTime: '2h 18m', historicalPattern: 'wind-driven expansion', pastIncidents: [{ year: '2024', name: 'Canyon Ridge event', location: 'San Bernardino, CA', duration: '2d 14h', population: '61,200', similarity: 87 }, { year: '2022', name: 'Pine Creek incident', location: 'Riverside, CA', duration: '1d 08h', population: '43,800', similarity: 73 }, { year: '2021', name: 'North Pass event', location: 'Los Angeles, CA', duration: '3d 02h', population: '102,400', similarity: 68 }],
    comparisons: [{ label: 'Expansion rate', current: `${Math.abs(item?.trend || 18.4).toFixed(1)}% / h`, baseline: '12.4% / h', delta: '+48%', direction: 'bad' }, { label: 'Population exposure', current: formatNumber(population), baseline: '68,000', delta: '+25%', direction: 'bad' }, { label: 'Detection to response', current: '11 min', baseline: '24 min', delta: '−54%', direction: 'good' }, { label: 'Data confidence', current: '94%', baseline: '81%', delta: '+13%', direction: 'good' }],
    patterns: ['Expansion follows a north-east wind corridor observed in 4 of 5 comparable events.', 'Peak population exposure typically occurs 90–120 minutes after the first perimeter breach.', 'Early shelter activation correlates with a 31% reduction in secondary injuries.'], patternConfidence: 89,
    lessons: [{ title: 'Pre-position shelter transport', text: 'Deploy accessible transport before route restrictions begin.' }, { title: 'Verify social signals faster', text: 'Pair community reports with thermal imagery within 15 minutes.' }, { title: 'Protect the east corridor', text: 'The eastern approach has been the most reliable evacuation route.' }],
    sources: [{ name: 'Satellite telemetry', icon: '◉', status: 'Verified', description: 'Sentinel-2, GOES-West and thermal composites', records: 248, confidence: 98 }, { name: 'Field reports', icon: '▣', status: 'Verified', description: 'Responder observations and perimeter GPS', records: 67, confidence: 95 }, { name: 'Sensor network', icon: '⌁', status: 'Verified', description: 'Weather, air quality and water-level sensors', records: 1842, confidence: 93 }, { name: 'Social media signals', icon: '◌', status: 'Pending', description: 'Geolocated public reports and call center triage', records: 412, confidence: 76 }],
    lineage: [{ label: 'Reported by', value: 'Regional Operations Center · Unit 07', confidence: 96 }, { label: 'Sensor inputs', value: '18 weather · 6 thermal · 42 air quality nodes', confidence: 93 }, { label: 'Processing pipeline', value: 'TerraGrid fusion engine · v4.8.2', confidence: 99 }, { label: 'Human verification', value: 'M. Ortega · Duty analyst · 14:26 UTC', confidence: 100 }],
    auditTrail: [{ time: '14:26 UTC', action: 'Perimeter verified', actor: 'M. Ortega', source: 'Field report #07' }, { time: '14:18 UTC', action: 'Forecast refreshed', actor: 'Fusion engine', source: 'Satellite + weather' }, { time: '14:04 UTC', action: 'Incident severity raised', actor: 'A. Chen', source: 'Operations console' }, { time: '13:51 UTC', action: 'Incident created', actor: 'Automated detection', source: 'GOES-West' }],
    aiForecast: { probability: 82, headline: 'Expansion likely toward east corridor', window: 'Next 90 minutes · high confidence', riskScore: 84, confidence: 91, timeline: [{ time: 'Now', value: `${formatNumber(area)} km²`, state: 'current' }, { time: '+2h', value: `${formatNumber(Math.round(area * 1.18))} km²`, state: 'forecast' }, { time: '+6h', value: `${formatNumber(item?.forecast6h || Math.round(area * 1.35))} km²`, state: 'forecast' }, { time: '+12h', value: `${formatNumber(Math.round(area * 1.52))} km²`, state: 'forecast' }], riskBreakdown: [{ label: 'Rate of expansion', score: 88 }, { label: 'Population exposure', score: 82 }, { label: 'Infrastructure fragility', score: 76 }, { label: 'Response readiness', score: 64 }], signals: [{ title: 'Wind corridor alignment', detail: 'Sustained 24 km/h winds align with the historic north-east spread vector.', icon: '≋', impact: 'HIGH' }, { title: 'Thermal intensity rising', detail: 'Three consecutive satellite frames show a 12% increase in thermal signature.', icon: '◉', impact: 'HIGH' }, { title: 'Route congestion building', detail: 'Eastbound travel speed is 18% below the evacuation model baseline.', icon: '⇢', impact: 'MEDIUM' }], actions: [{ title: 'Prioritize east corridor evacuation', reason: 'Model projects the fastest exposure growth in this direction.' }, { title: 'Keep Route 01 one-way southbound', reason: 'Maximizes throughput and reduces opposing traffic conflicts.' }, { title: 'Re-run forecast after next imagery pass', reason: 'Next satellite pass will resolve the current 76% signal ambiguity.' }] },
    communicationMetrics: [{ label: 'Residents reached', value: '91,284', note: 'of 96,400 target' }, { label: 'Delivery rate', value: '94.7%', note: 'across all channels' }, { label: 'Acknowledged', value: '68.2%', note: '12,860 responses' }, { label: 'Response time', value: '4m 12s', note: 'median acknowledgement' }],
    alertHistory: [{ time: '14:22 UTC', message: 'Mandatory evacuation · Zone A', channel: 'SMS + sirens + app', severity: 'critical', status: 'delivered' }, { time: '14:08 UTC', message: 'Shelter activation notice', channel: 'SMS + web + radio', severity: 'warning', status: 'delivered' }, { time: '13:55 UTC', message: 'Route restriction · Highway 18', channel: 'DOT feed + app', severity: 'warning', status: 'delivered' }, { time: '13:42 UTC', message: 'Prepare-to-evacuate advisory', channel: 'SMS + social', severity: 'info', status: 'partial' }],
    notifiedRegions: [{ name: 'San Gabriel foothills', count: 38240, delivery: 98 }, { name: 'East corridor', count: 24680, delivery: 95 }, { name: 'Central valley', count: 18420, delivery: 92 }, { name: 'South communities', count: 9944, delivery: 88 }],
    channels: [{ name: 'SMS', icon: '▣', percent: 99 }, { name: 'Mobile app', icon: '⌁', percent: 94 }, { name: 'Sirens', icon: '◉', percent: 100 }, { name: 'Radio', icon: '◌', percent: 87 }],
    responseOutcomes: [{ label: 'Evacuation compliance', value: '78%', note: '+12% since last alert' }, { label: 'Shelter check-ins', value: '2,940', note: '84% of projected arrivals' }, { label: 'Help requests resolved', value: '93%', note: 'within 15 minutes' }, { label: 'False-positive reports', value: '2.1%', note: 'below 5% threshold' }],
  }
}
</script>

<style scoped>
:global(body) { background: #0f0f0f; }
.incident-detail { min-height: 100%; padding: 24px clamp(16px, 4vw, 56px) 64px; color: #f8fafc; background: radial-gradient(circle at 85% 0%, rgba(14,165,233,.09), transparent 28%), #0f0f0f; }
.glass-panel { background: rgba(22, 29, 39, .72); border: 1px solid rgba(148,163,184,.17); border-radius: 14px; backdrop-filter: blur(14px); box-shadow: 0 14px 40px rgba(0,0,0,.2); }
.glass-panel:hover { border-color: rgba(14,165,233,.48); box-shadow: 0 0 24px rgba(14,165,233,.12); transition: box-shadow .25s ease, border-color .25s ease; }
.detail-header, .header-navigation, .header-actions, .hero-status, .panel-heading, .row-title, .tab-intro, .map-toolbar, .map-footer { display: flex; align-items: center; }
.detail-header { justify-content: space-between; gap: 20px; margin-bottom: 28px; }
.header-navigation, .header-actions { gap: 11px; flex-wrap: wrap; }
.back-button, .ghost-button, .primary-button { border: 1px solid rgba(148,163,184,.25); color: #e2e8f0; background: transparent; border-radius: 8px; padding: 9px 13px; cursor: pointer; font: inherit; transition: .2s ease; }
.back-button:hover, .ghost-button:hover { border-color: #0ea5e9; color: #7dd3fc; box-shadow: 0 0 16px rgba(14,165,233,.2); }
.breadcrumb-separator { color: #475569; }.breadcrumb-current { color: #94a3b8; font-size: 13px; }
.primary-button { background: #0ea5e9; border-color: #38bdf8; color: #03111b; font-weight: 700; }.primary-button:hover { background: #38bdf8; box-shadow: 0 0 22px rgba(14,165,233,.45); }
.incident-hero { display: flex; justify-content: space-between; align-items: flex-end; gap: 20px; margin-bottom: 26px; }.eyebrow, .section-kicker { color: #38bdf8; font-size: 10px; font-weight: 800; letter-spacing: .16em; }.live-dot, .response-state i, .map-live i { display: inline-block; width: 7px; height: 7px; margin-right: 7px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 10px #22c55e; }.hero-copy h1 { margin: 8px 0 4px; font-size: clamp(28px, 4vw, 42px); letter-spacing: -.04em; }.hero-location { margin: 0; color: #94a3b8; }.hero-location span { color: #38bdf8; }.hero-status { gap: 8px; flex-wrap: wrap; justify-content: flex-end; }.type-badge, .severity-badge, .status-badge, .ai-chip, .verified-chip, .updated-pill, .response-state, .pattern-confidence { padding: 6px 9px; border-radius: 6px; font-size: 10px; font-weight: 800; letter-spacing: .06em; }.type-badge { background: rgba(168,85,247,.16); color: #d8b4fe; }.type-fire { color: #fb923c; background: rgba(249,115,22,.15); }.type-flood { color: #38bdf8; background: rgba(14,165,233,.15); }.type-landslide { color: #fbbf24; background: rgba(245,158,11,.15); }.severity-high { color: #fb7185; background: rgba(244,63,94,.15); }.severity-medium { color: #fbbf24; background: rgba(245,158,11,.15); }.severity-low { color: #4ade80; background: rgba(34,197,94,.15); }.status-active { color: #4ade80; }.status-monitoring { color: #fbbf24; }.status-resolved { color: #94a3b8; }.status-badge { border: 1px solid currentColor; }
.tabs { display: flex; gap: 3px; overflow-x: auto; border-bottom: 1px solid rgba(148,163,184,.18); scrollbar-width: thin; scrollbar-color: rgba(14,165,233,.4) transparent; padding-bottom: 2px; }.tab-button { white-space: nowrap; display: flex; align-items: center; gap: 5px; border: 1px solid transparent; border-bottom: 2px solid transparent; padding: 11px 13px; background: transparent; color: #a0aec0; cursor: pointer; font: inherit; font-size: 12px; font-weight: 600; transition: .2s ease; border-radius: 6px 6px 0 0; flex-shrink: 0; min-width: fit-content; }.tab-button:hover { color: #67e8f9; border-color: rgba(14,165,233,.35); background: rgba(14,165,233,.08); border-bottom-color: #0ea5e9; }.tab-button.active { color: #0ea5e9; border: 1px solid rgba(14,165,233,.48); border-bottom: 2px solid #0ea5e9; background: linear-gradient(180deg, rgba(14,165,233,.15), rgba(14,165,233,.05)); box-shadow: inset 0 0 12px rgba(14,165,233,.1); }.tab-icon { font-size: 16px; color: inherit; flex-shrink: 0; }.tab-button:hover .tab-icon { color: #38bdf8; }.tab-button.active .tab-icon { color: #0ea5e9; }.critical-marker { color: #fbbf24; margin-left: 2px; }
.tab-content { padding-top: 26px; }.tab-fade-enter-active, .tab-fade-leave-active { transition: opacity .2s ease, transform .2s ease; }.tab-fade-enter-from, .tab-fade-leave-to { opacity: 0; transform: translateY(5px); }
.metric-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 18px; }.metric-card { min-height: 136px; padding: 18px; }.metric-label, .metric-footnote, .metric-card small { display: block; color: #94a3b8; font-size: 11px; }.metric-value { display: block; margin: 15px 0 6px; color: #67e8f9; font-size: 27px; line-height: 1.1; }.metric-value small { display: inline; font-size: 12px; color: #94a3b8; }.compact-value { font-size: 17px; color: #f8fafc; line-height: 1.25; }.threat-value { color: #fb7185; }.trend-value { color: #4ade80; }.status-text { color: #fbbf24; }.progress-track { height: 5px; margin-top: 12px; overflow: hidden; background: rgba(100,116,139,.2); border-radius: 99px; }.progress-fill { display: block; height: 100%; border-radius: inherit; background: #0ea5e9; box-shadow: 0 0 10px rgba(14,165,233,.55); }.threat-fill { background: #fb7185; }.content-grid { display: grid; gap: 18px; margin-top: 18px; }.two-columns { grid-template-columns: repeat(2, minmax(0, 1fr)); }.content-grid > .glass-panel, .impact-layout > .glass-panel, .source-grid > .glass-panel, .ai-grid > .glass-panel { padding: 22px; }.panel-heading { justify-content: space-between; gap: 12px; margin-bottom: 20px; }.panel-heading h2, .panel-heading h3 { margin-top: 4px; color: #f8fafc; }.panel-code { color: #475569; font: 700 10px ui-monospace, monospace; }.long-copy { color: #cbd5e1; line-height: 1.75; }.summary-facts { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 22px; }.summary-facts span, .summary-facts strong { display: block; }.summary-facts span { color: #64748b; font-size: 11px; }.summary-facts strong { margin-top: 3px; color: #e2e8f0; font-size: 13px; }.ai-chip, .verified-chip { color: #67e8f9; background: rgba(14,165,233,.12); }.action-list, .lessons-list { display: grid; gap: 15px; padding: 0; margin: 0; list-style: none; }.action-list li { display: flex; align-items: flex-start; gap: 12px; }.action-number { color: #0ea5e9; font: 700 12px ui-monospace, monospace; }.action-list strong { color: #f8fafc; font-size: 13px; }.action-list p { margin: 4px 0 0; color: #94a3b8; font-size: 12px; }.priority { margin-left: auto; color: #fbbf24; font-size: 9px; font-weight: 800; text-transform: uppercase; }.priority-urgent { color: #fb7185; }
.tab-intro { justify-content: space-between; gap: 20px; margin-bottom: 20px; }.tab-intro h2 { margin: 5px 0 4px; font-size: 25px; }.tab-intro p { margin: 0; color: #94a3b8; }.updated-pill, .pattern-confidence { color: #94a3b8; background: rgba(100,116,139,.13); }.impact-layout, .source-grid, .ai-grid, .map-evidence-layout { display: grid; grid-template-columns: 1.1fr .9fr; gap: 18px; }.zone-list, .population-bars, .resource-list, .freshness-list, .lineage-list, .audit-list, .route-list, .deployment-list, .history-list, .comparison-list, .evidence-list, .region-list, .alert-history { display: grid; gap: 15px; }.zone-row, .route-row, .history-row, .alert-row, .deployment-row, .lineage-row, .audit-row, .region-row { display: flex; align-items: center; gap: 12px; }.zone-icon { display: grid; place-items: center; width: 33px; height: 33px; border-radius: 8px; font-weight: 800; }.zone-critical { color: #fb7185; background: rgba(244,63,94,.18); }.zone-high { color: #fb923c; background: rgba(249,115,22,.18); }.zone-watch { color: #fbbf24; background: rgba(245,158,11,.18); }.zone-main, .route-main, .history-main, .region-row > span:first-child { flex: 1; min-width: 0; }.row-title { justify-content: space-between; gap: 10px; }.row-title strong, .row-title span, .zone-main small { font-size: 12px; }.row-title span, .zone-main small, .route-main small, .history-main small, .deployment-row small, .audit-row small { color: #64748b; }.zone-percent { color: #67e8f9; font-size: 13px; }.fill-critical { background: #fb7185; }.fill-high { background: #fb923c; }.fill-watch { background: #fbbf24; }.population-row .row-title strong { color: #67e8f9; }.population-fill, .region-fill { background: #22d3ee; }.bar-with-label { display: flex; align-items: center; gap: 9px; }.bar-with-label .progress-track { flex: 1; }.bar-with-label small { color: #64748b; }.total-callout, .eta-callout { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-top: 20px; padding: 13px; border: 1px solid rgba(14,165,233,.25); border-radius: 8px; background: rgba(14,165,233,.08); }.total-callout span, .eta-callout span { color: #94a3b8; font-size: 12px; }.total-callout strong, .eta-callout strong { color: #67e8f9; }.asset-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }.asset-card { padding: 13px 8px; text-align: center; border-radius: 9px; background: rgba(15,23,42,.65); }.asset-icon { display: block; color: #38bdf8; font-size: 22px; }.asset-card strong, .asset-card span, .asset-card small { display: block; }.asset-card strong { margin-top: 4px; font-size: 21px; }.asset-card span { color: #cbd5e1; font-size: 10px; }.asset-card small { margin-top: 8px; color: #4ade80; font-size: 9px; }.asset-card small.restricted, .asset-card small.inspect { color: #fbbf24; }.resource-row { display: grid; grid-template-columns: 1.2fr 1fr auto; align-items: center; gap: 10px; color: #cbd5e1; font-size: 12px; }.resource-progress { height: 6px; overflow: hidden; background: rgba(100,116,139,.18); border-radius: 99px; }.resource-progress span { display: block; height: 100%; background: #22d3ee; border-radius: inherit; }.resource-row strong { color: #f8fafc; font-size: 12px; }.resource-row small { grid-column: 2 / 4; color: #64748b; font-size: 10px; }
.map-preview { overflow: hidden; padding: 0 !important; }.map-toolbar, .map-footer { justify-content: space-between; gap: 10px; padding: 14px 18px; }.map-title, .map-live { color: #94a3b8; font: 700 10px ui-monospace, monospace; }.map-live { color: #4ade80; }.map-canvas { position: relative; height: 400px; overflow: hidden; background: linear-gradient(135deg, #112c2e 0%, #173d41 35%, #263c32 68%, #172f2d 100%); }.map-grid { position: absolute; inset: 0; opacity: .28; background-image: linear-gradient(rgba(125,211,252,.2) 1px, transparent 1px), linear-gradient(90deg, rgba(125,211,252,.2) 1px, transparent 1px); background-size: 45px 45px; transform: rotate(-12deg) scale(1.2); }.map-zone { position: absolute; width: 145px; height: 110px; display: grid; place-items: center; border: 2px solid; border-radius: 45% 55% 50% 40%; font: 800 18px ui-monospace, monospace; transform: rotate(-20deg); }.map-zone-1 { top: 25%; left: 27%; color: #fb7185; border-color: rgba(251,113,133,.8); background: rgba(244,63,94,.2); box-shadow: 0 0 30px rgba(244,63,94,.35); }.map-zone-2 { top: 42%; left: 48%; color: #fb923c; border-color: rgba(251,146,60,.7); background: rgba(249,115,22,.16); }.map-zone-3 { top: 51%; left: 16%; color: #fbbf24; border-color: rgba(251,191,36,.6); background: rgba(245,158,11,.12); }.map-crosshair { position: absolute; top: 48%; left: 51%; color: #fff; font-size: 30px; text-shadow: 0 0 12px #0ea5e9; }.map-scale { position: absolute; right: 17px; top: 18px; color: #e2e8f0; text-align: center; font-weight: 800; }.map-scale span { color: #38bdf8; }.map-legend { position: absolute; bottom: 14px; left: 15px; display: flex; gap: 12px; padding: 8px 10px; color: #cbd5e1; font-size: 10px; background: rgba(15,23,42,.8); border-radius: 6px; }.legend-dot { display: inline-block; width: 7px; height: 7px; margin-right: 3px; border-radius: 50%; }.legend-dot.critical { background: #fb7185; }.legend-dot.watch { background: #fbbf24; }.legend-dot.safe { background: #4ade80; }.map-footer { border-top: 1px solid rgba(148,163,184,.12); color: #64748b; font-size: 10px; }.evidence-row { display: flex; align-items: center; gap: 10px; }.evidence-thumb { display: grid; place-items: center; width: 42px; height: 38px; color: #67e8f9; border-radius: 6px; background: linear-gradient(135deg, rgba(14,165,233,.3), rgba(34,197,94,.2)); font-size: 21px; }.evidence-main { flex: 1; }.evidence-main strong, .evidence-main small { display: block; }.evidence-main strong { font-size: 12px; }.evidence-main small { margin-top: 3px; color: #64748b; font-size: 10px; }.evidence-status, .delivery-status { font-size: 9px; font-weight: 800; text-transform: uppercase; }.evidence-verified, .delivered { color: #4ade80; }.evidence-pending, .partial { color: #fbbf24; }.verification-score { display: flex; align-items: center; gap: 13px; margin-top: 22px; padding-top: 18px; border-top: 1px solid rgba(148,163,184,.14); }.verification-score p { margin: 3px 0 0; font-size: 11px; }.score-ring { display: grid; place-items: center; width: 67px; height: 67px; border: 4px solid #22d3ee; border-left-color: rgba(34,211,238,.2); border-radius: 50%; }.score-ring strong { color: #67e8f9; font-size: 16px; }.score-ring small { color: #64748b; font-size: 8px; }
.response-state { color: #4ade80; }.response-metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }.response-metric { padding: 18px; }.response-metric span, .response-metric small { display: block; color: #94a3b8; font-size: 11px; }.response-metric strong { display: block; margin: 10px 0 4px; color: #67e8f9; font-size: 25px; }.route-status { width: 10px; align-self: stretch; position: relative; }.route-status span { position: absolute; top: 6px; width: 8px; height: 8px; border-radius: 50%; }.route-open span { background: #4ade80; box-shadow: 0 0 8px #4ade80; }.route-limited span { background: #fbbf24; }.route-clearing span { background: #fb923c; }.route-time { color: #67e8f9; font-size: 12px; }.route-track { height: 4px; margin-top: 8px; background: rgba(100,116,139,.2); border-radius: 99px; }.route-track span { display: block; height: 100%; background: #4ade80; border-radius: inherit; }.route-limited + .route-main .route-track span { background: #fbbf24; }.deployment-icon { display: grid; place-items: center; width: 30px; height: 30px; color: #38bdf8; border-radius: 7px; background: rgba(14,165,233,.13); }.deployment-row div { flex: 1; }.deployment-row strong, .deployment-row small { display: block; }.deployment-row strong { font-size: 12px; }.deployment-row small { margin-top: 2px; font-size: 10px; }.deployment-count { color: #cbd5e1; font-size: 11px; }.deployment-status { font-size: 9px; text-transform: uppercase; }.deployment-status.active { color: #4ade80; }.deployment-status.moving { color: #38bdf8; }.deployment-status.standby { color: #fbbf24; }.eta-callout { flex-wrap: wrap; }.eta-callout small { width: 100%; color: #64748b; font-size: 10px; }.history-year { color: #38bdf8; font: 700 12px ui-monospace, monospace; }.history-stat { text-align: right; }.history-stat strong, .history-stat small { display: block; }.history-stat strong { color: #67e8f9; font-size: 12px; }.history-stat small { color: #64748b; font-size: 9px; }.similarity { color: #a78bfa; font-size: 10px; }.comparison-row { display: flex; align-items: center; gap: 12px; }.comparison-row > span:first-child { flex: 1; color: #cbd5e1; font-size: 12px; }.comparison-values { text-align: right; }.comparison-values strong, .comparison-values span { display: block; }.comparison-values strong { color: #f8fafc; font-size: 12px; }.comparison-values span { color: #64748b; font-size: 10px; }.comparison-delta { min-width: 42px; text-align: right; font-size: 11px; }.comparison-delta.good { color: #4ade80; }.comparison-delta.bad { color: #fb7185; }.insight-list { display: grid; gap: 13px; padding: 0; margin: 0; list-style: none; }.insight-list li { color: #cbd5e1; font-size: 12px; }.insight-list span { margin-right: 10px; color: #38bdf8; }.lessons-list { list-style: decimal; padding-left: 22px; }.lessons-list li { padding-left: 5px; color: #94a3b8; }.lessons-list strong, .lessons-list span { display: block; }.lessons-list strong { color: #f8fafc; font-size: 12px; }.lessons-list span { margin-top: 3px; font-size: 11px; }
.quality-score { text-align: right; }.quality-score span, .quality-score strong { display: block; }.quality-score span { color: #64748b; font-size: 9px; letter-spacing: .12em; }.quality-score strong { color: #4ade80; font-size: 28px; }.quality-score small { color: #64748b; font-size: 11px; }.source-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }.source-card { padding: 14px; border: 1px solid rgba(148,163,184,.14); border-radius: 9px; background: rgba(15,23,42,.55); }.source-card-head { display: flex; justify-content: space-between; }.source-icon { color: #38bdf8; font-size: 22px; }.source-status { font-size: 9px; text-transform: uppercase; }.source-status.verified { color: #4ade80; }.source-status.pending { color: #fbbf24; }.source-card strong { display: block; margin-top: 9px; font-size: 12px; }.source-card p { min-height: 33px; margin: 5px 0 12px; font-size: 10px; }.source-meta { display: flex; justify-content: space-between; color: #64748b; font-size: 9px; }.freshness-list div { display: flex; justify-content: space-between; gap: 12px; }.freshness-list span { color: #64748b; font-size: 11px; }.freshness-list strong { color: #cbd5e1; font-size: 11px; text-align: right; }.freshness-meter { margin-top: 24px; }.freshness-meter > span, .freshness-meter > strong { color: #94a3b8; font-size: 10px; }.freshness-meter > strong { float: right; color: #4ade80; }.freshness-fill { background: #4ade80; }.lineage-marker { width: 9px; height: 9px; border: 2px solid #0ea5e9; border-radius: 50%; box-shadow: 0 0 8px rgba(14,165,233,.6); }.lineage-row div { flex: 1; }.lineage-row strong, .lineage-row small, .audit-row strong, .audit-row small { display: block; }.lineage-row strong, .audit-row strong { font-size: 12px; }.lineage-row small, .audit-row small { margin-top: 3px; font-size: 10px; }.confidence-badge { color: #67e8f9; font: 700 10px ui-monospace, monospace; }.audit-time { min-width: 68px; color: #38bdf8; font: 10px ui-monospace, monospace; }.audit-row div { flex: 1; }
.ai-grid { grid-template-columns: 1.2fr .8fr; }.prediction-head { display: flex; align-items: center; gap: 18px; }.forecast-number { color: #67e8f9; font-size: 55px; font-weight: 800; line-height: 1; }.forecast-number small { font-size: 21px; }.prediction-head strong { font-size: 14px; }.prediction-head p { margin: 4px 0 0; font-size: 11px; }.forecast-timeline { display: grid; grid-template-columns: repeat(4, 1fr); margin-top: 30px; }.forecast-point { position: relative; padding-top: 14px; border-top: 1px solid rgba(148,163,184,.2); }.forecast-point:not(:last-child):after { content: ''; position: absolute; top: -2px; right: 0; width: 5px; height: 5px; border-radius: 50%; background: #38bdf8; }.forecast-dot { position: absolute; top: -4px; left: 0; width: 7px; height: 7px; border-radius: 50%; background: #38bdf8; }.forecast-dot.current { background: #4ade80; box-shadow: 0 0 8px #4ade80; }.forecast-point strong, .forecast-point small { display: block; }.forecast-point strong { font-size: 11px; }.forecast-point small { margin-top: 3px; color: #67e8f9; font-size: 10px; }.risk-total { color: #fb7185; font-size: 22px; }.risk-list { display: grid; gap: 17px; }.risk-fill { background: linear-gradient(90deg, #fbbf24, #fb7185); }.signal-row { display: flex; align-items: flex-start; gap: 12px; padding: 12px 0; border-bottom: 1px solid rgba(148,163,184,.12); }.signal-row:last-child { border-bottom: 0; }.signal-icon { color: #38bdf8; font-size: 19px; }.signal-row div { flex: 1; }.signal-row strong { font-size: 12px; }.signal-row p { margin: 4px 0 0; font-size: 11px; }.signal-impact { color: #fbbf24; font-size: 9px; font-weight: 800; }.ai-actions li { padding-bottom: 14px; border-bottom: 1px solid rgba(148,163,184,.12); }
.communication-metrics {}.alert-row { align-items: flex-start; }.alert-severity { width: 4px; min-height: 35px; border-radius: 99px; background: #38bdf8; }.alert-severity.critical { background: #fb7185; }.alert-severity.warning { background: #fbbf24; }.alert-row div { flex: 1; }.alert-row strong, .alert-row small { display: block; }.alert-row strong { font-size: 12px; }.alert-row small { margin-top: 4px; color: #64748b; font-size: 10px; }.region-row { flex-wrap: wrap; }.region-row > span:first-child { font-size: 12px; }.region-row .progress-track { flex: 1; min-width: 100px; margin-top: 0; }.region-row strong { color: #67e8f9; font-size: 11px; }.region-row small { width: 100%; margin-left: calc(30% + 12px); color: #64748b; font-size: 10px; }.channel-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }.channel-pill { padding: 7px 9px; color: #cbd5e1; border: 1px solid rgba(148,163,184,.15); border-radius: 6px; font-size: 10px; }.channel-pill i { margin-right: 5px; color: #38bdf8; font-style: normal; }.channel-pill strong { margin-left: 5px; color: #4ade80; }.response-panel { padding: 22px; margin-top: 18px; }.outcome-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }.outcome-grid span, .outcome-grid strong, .outcome-grid small { display: block; }.outcome-grid span { color: #94a3b8; font-size: 11px; }.outcome-grid strong { margin: 7px 0 3px; color: #67e8f9; font-size: 23px; }.outcome-grid small { color: #64748b; font-size: 10px; }
.not-found { max-width: 560px; margin: 90px auto; padding: 48px; text-align: center; }.not-found-icon { display: block; color: #38bdf8; font-size: 50px; }.not-found h1 { margin: 12px 0 8px; }.not-found p { margin-bottom: 25px; }.not-found strong { color: #67e8f9; }
@media (max-width: 1100px) { .metric-grid { grid-template-columns: repeat(3, 1fr); }.tabs { margin-inline: -16px; padding-inline: 16px; }.asset-grid { grid-template-columns: repeat(2, 1fr); }.tab-button { padding: 10px 11px; font-size: 11px; } }
@media (max-width: 780px) { .incident-detail { padding: 16px 12px 40px; }.detail-header, .incident-hero, .tab-intro { align-items: flex-start; flex-direction: column; }.header-actions { width: 100%; }.hero-status { justify-content: flex-start; }.metric-grid, .response-metrics, .outcome-grid { grid-template-columns: repeat(2, 1fr); }.two-columns, .impact-layout, .source-grid, .ai-grid, .map-evidence-layout { grid-template-columns: 1fr; }.map-canvas { height: 300px; }.source-cards { grid-template-columns: 1fr 1fr; }.tab-button { padding: 10px 11px; font-size: 11px; } }
@media (max-width: 450px) { .metric-grid, .response-metrics, .source-cards, .outcome-grid { grid-template-columns: 1fr; }.summary-facts { grid-template-columns: 1fr; }.tabs { gap: 0; }.tab-button { padding: 9px 8px; font-size: 10px; }.tab-button span:not(.tab-icon):not(.critical-marker) { display: inline; margin-left: 3px; font-size: 9px; text-transform: uppercase; letter-spacing: .05em; }.forecast-number { font-size: 44px; }.map-footer { align-items: flex-start; flex-direction: column; }.resource-row { grid-template-columns: 1fr auto; }.resource-progress { grid-column: 1 / 3; grid-row: 2; }.resource-row small { grid-column: 1 / 3; }.region-row small { margin-left: 0; }.not-found { margin: 40px auto; padding: 30px 18px; } }

/* Design-system refinement: responsive glassmorphism, contrast and interaction states */
:root {
  --detail-bg: #0f0f0f;
  --detail-panel: rgba(22, 29, 39, .72);
  --detail-border: rgba(148, 163, 184, .17);
  --detail-accent: #0ea5e9;
  --detail-cyan: #67e8f9;
  --detail-primary: #ffffff;
  --detail-secondary: #94a3b8;
  --detail-muted: #64748b;
  --detail-body: #cbd5e1;
  --detail-glow: 0 0 24px rgba(14, 165, 233, .12);
}

.incident-detail {
  background: radial-gradient(circle at 85% 0%, rgba(14, 165, 233, .09), transparent 30%), var(--detail-bg);
  color: var(--detail-primary);
  font-size: 13px;
}

.glass-panel,
.metric-card,
.response-metric,
.source-card,
.asset-card,
.channel-pill {
  background: var(--detail-panel);
  border: 1px solid var(--detail-border);
  backdrop-filter: blur(14px);
  transition: border-color .25s ease, box-shadow .25s ease, transform .25s ease;
}

.glass-panel:hover,
.metric-card:hover,
.response-metric:hover,
.source-card:hover,
.asset-card:hover,
.channel-pill:hover {
  border-color: var(--detail-accent);
  box-shadow: var(--detail-glow);
}

.detail-header {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--detail-border);
}

.back-button,
.ghost-button,
.primary-button {
  min-height: 38px;
  transition: color .2s ease, background .2s ease, border-color .2s ease, box-shadow .2s ease, transform .2s ease;
}

.back-button:hover,
.ghost-button:hover,
.primary-button:hover,
.tab-button:hover,
.tab-button.active {
  border-color: var(--detail-accent);
  box-shadow: var(--detail-glow);
}

.ghost-button:hover,
.back-button:hover { transform: translateY(-1px); }

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
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .08em;
  text-transform: uppercase;
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
  box-shadow: 0 0 18px rgba(14, 165, 233, .1);
}
.action-panel:hover {
  border-color: #38bdf8 !important;
  box-shadow: 0 0 28px rgba(14, 165, 233, .28);
}

.panel-heading { margin-bottom: 20px; }
.panel-heading h2, .panel-heading h3 { font-size: clamp(16px, 1.5vw, 20px); }
.long-copy, .signal-row p, .source-card p, .not-found p { font-size: 13px; line-height: 1.65; }

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
  .header-actions .ghost-button { padding: 8px 9px; font-size: 11px; }
  .hero-copy h1 { font-size: clamp(25px, 8vw, 34px); }
  .metric-grid,
  .response-metrics,
  .source-cards,
  .outcome-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .metric-card { min-height: 132px; padding: 16px 14px; }
  .metric-value { margin-top: 12px; font-size: clamp(16px, 6vw, 22px); }
  .compact-value { font-size: 15px; }
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
  .metric-label, .metric-footnote { font-size: 10px; }
  .metric-value { font-size: 16px; }
  .tab-button { padding-inline: 11px; font-size: 11px; }
  .tab-button span:not(.tab-icon):not(.critical-marker) { display: inline; }
}
</style>
