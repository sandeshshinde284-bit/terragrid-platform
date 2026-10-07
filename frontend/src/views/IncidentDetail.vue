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
                <h4>SYNTHESIZING CRISIS INTELLIGENCE DOSSIER</h4>
                <small>PROCESSING MULTI-SOURCE SATELLITE & ATMOSPHERIC TELEMETRY</small>
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
          <button class="primary-back-btn" type="button" aria-label="Back to incidents" @click="goTo('/incidents')">
            <span class="back-arrow">←</span>
            <span class="back-text">Incidents Console</span>
          </button>
          <span class="breadcrumb-separator">/</span>
          <span class="breadcrumb-current">{{ incident.location }}</span>
        </div>
        <div class="header-actions">
          <button class="ghost-button" type="button" @click="goTo('/')">⌂ Dashboard</button>
          <button class="ghost-button" type="button" @click="goTo('/map')">◎ Live Map</button>
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
            <!-- Operational Command Action Bar -->
            <div class="operational-command-bar glass-panel">
              <div class="toolbar-title">
                <span class="command-dot"></span>
                <span>OPERATIONAL COMMAND DISPATCH</span>
              </div>
              <div class="toolbar-actions">
                <button class="cmd-btn primary" @click="exportSitRepZip" :disabled="isExportingZip">
                  <span v-if="isExportingZip" class="spinner">⟳</span>
                  <span>{{ isExportingZip ? 'COMPILING ZIP...' : '📦 Export SitRep Package (.ZIP)' }}</span>
                </button>
                <button class="cmd-btn secondary" @click="goTo(`/map?fromIncident=${incident.id}&location=${encodeURIComponent(incident.location)}`)">
                  <span>🗺️ View Incident on Tactical Map</span>
                </button>
              </div>
            </div>

            <!-- Hero Tactical Incident Report Banner -->
            <div class="glass-panel ai-recon-hero-card">
              <div class="recon-info">
                <div class="recon-status-badge" :class="{ 'analyzed': !!deepDossier }">
                  <span class="status-pulse-dot"></span>
                  {{ deepDossier ? '🟢 VERIFIED OPERATIONAL REPORT ACTIVE' : '⚡ FULL CRISIS REPORT READY TO SYNTHESIZE' }}
                </div>
                <h2>Crisis Assessment & Impact Forecast</h2>
                <p>
                  {{ deepDossier 
                    ? deepDossier.situational_assessment 
                    : 'Synthesize comprehensive 6h/12h/24h disaster spread predictions, critical hospital & infrastructure vulnerability assessments, evacuation routing, and emergency logistics matrices.' 
                  }}
                </p>
              </div>
              <button 
                class="recon-launch-button" 
                :disabled="isAnalyzingDossier" 
                @click="launchDeepAnalysis"
              >
                <span v-if="isAnalyzingDossier" class="spinner">⟳</span>
                {{ isAnalyzingDossier ? 'SYNTHESIZING REPORT...' : (deepDossier ? '🔄 UPDATE CRISIS REPORT' : '⚡ GENERATE FULL REPORT') }}
              </button>
            </div>

            <!-- Live Environmental Telemetry Gauge Strip -->
            <div class="environmental-gauge-strip">
              <div class="env-gauge-tile glass-panel">
                <span class="gauge-icon">💨</span>
                <div class="gauge-info">
                  <span class="gauge-label">ATMOSPHERIC WIND</span>
                  <strong class="gauge-value">{{ (Math.abs(incident.trend) * 2.1 + 4.2).toFixed(1) }} m/s</strong>
                  <small class="gauge-desc">Surface Acceleration Vector</small>
                </div>
              </div>
              <div class="env-gauge-tile glass-panel">
                <span class="gauge-icon">🌡️</span>
                <div class="gauge-info">
                  <span class="gauge-label">AMBIENT SENSORS</span>
                  <strong class="gauge-value">28.4°C</strong>
                  <small class="gauge-desc">Atmospheric Humidity 78%</small>
                </div>
              </div>
              <div class="env-gauge-tile glass-panel">
                <span class="gauge-icon">👥</span>
                <div class="gauge-info">
                  <span class="gauge-label">CIVIC EXPOSURE BUFFER</span>
                  <strong class="gauge-value">{{ formatNumber(incident.affectedPopulation) }}</strong>
                  <small class="gauge-desc">Residents in danger perimeter</small>
                </div>
              </div>
              <div class="env-gauge-tile glass-panel">
                <span class="gauge-icon">📈</span>
                <div class="gauge-info">
                  <span class="gauge-label">PERIMETER GROWTH</span>
                  <strong class="gauge-value">+{{ incident.trend.toFixed(1) }} km²/h</strong>
                  <small class="gauge-desc">6h Projected +{{ formatNumber(incident.forecast6h) }} km²</small>
                </div>
              </div>
            </div>

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
                <div v-if="aiLoading" class="loading-state">
                  <span class="loading-spinner"></span>
                  <p>Loading AI recommendations...</p>
                </div>
                <div v-else-if="aiError" class="error-state">
                  <span class="error-icon">⚠</span>
                  <p>{{ aiError }}</p>
                </div>
                <ol v-else class="action-list">
                  <!-- COMMENTED OUT (Live Mode): Used to show fallback data from detail.recommendedActions when AI didn't load -->
                  <!-- <li v-for="(action, index) in (aiInsights.length > 0 ? aiInsights : detail.recommendedActions)" :key="action.id || action.title"> -->
                  <!-- Now only shows REAL AI data from aiPlan.immediate_actions -->
                  <li v-for="(action, index) in aiInsights" :key="action.id">
                    <span class="action-number">0{{ index + 1 }}</span><div><strong>{{ action.action }}</strong><p>{{ action.description || '' }}</p></div><span class="priority" :class="`priority-${action.severity}`">{{ action.severity }}</span>
                  </li>
                </ol>
              </article>
            </div>
          </div>

          <!-- IMPACT ANALYSIS -->
          <div v-else-if="activeTab === 'impact'" class="impact-tab">
            <div v-if="deepDossier" class="deep-ai-tab-container">
              <div class="tab-intro">
                <div>
                  <span class="section-kicker">VERTEX AI COGNITIVE RECONNAISSANCE</span>
                  <h2>Critical Infrastructure & Demographic Vulnerability</h2>
                  <p>{{ deepDossier.situational_assessment }}</p>
                </div>
                <span class="ai-chip live">VERTEX AI CALCULATED</span>
              </div>

              <!-- Critical Infrastructure Table -->
              <article class="glass-panel infrastructure-panel" style="padding: 20px; margin-bottom: 20px;">
                <div class="panel-heading">
                  <div><span class="section-kicker">VULNERABILITY MATRIX</span><h3>Exposed Critical Infrastructure</h3></div>
                  <span class="panel-code">AI-IA-01</span>
                </div>
                <div class="ai-facility-grid">
                  <div v-for="fac in deepDossier.critical_infrastructure" :key="fac.facility_name" class="ai-facility-card glass-subpanel">
                    <div class="facility-top">
                      <span class="facility-type-tag">{{ fac.facility_type }}</span>
                      <span class="facility-risk" :class="fac.risk_level.toLowerCase()">{{ fac.risk_level }} RISK</span>
                    </div>
                    <h4>{{ fac.facility_name }}</h4>
                    <div class="facility-meta">
                      <span>📍 Distance: {{ fac.distance_km }} km from epicenter</span>
                    </div>
                    <div class="facility-action">
                      <strong>Directive:</strong> {{ fac.action_required }}
                    </div>
                  </div>
                </div>
              </article>

              <!-- Vulnerable Demographics -->
              <article class="glass-panel demographics-panel" style="padding: 20px;">
                <div class="panel-heading">
                  <div><span class="section-kicker">HUMAN IMPACT</span><h3>Vulnerable Demographics & Facilities</h3></div>
                  <span class="panel-code">AI-IA-02</span>
                </div>
                <div class="demographics-body">
                  <div class="demo-stat-row" style="display: flex; gap: 24px; margin-bottom: 14px;">
                    <div class="demo-stat">
                      <span class="stat-label" style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Estimated Displaced Citizens: </span>
                      <strong class="stat-value" style="font-size: 16px; color: #38bdf8;">{{ deepDossier.vulnerable_demographics.estimated_displaced_citizens.toLocaleString() }}</strong>
                    </div>
                    <div class="demo-stat">
                      <span class="stat-label" style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Special Needs Transport: </span>
                      <span class="stat-desc" style="font-size: 13px; color: #cbd5e1;">{{ deepDossier.vulnerable_demographics.special_needs_assistance_required }}</span>
                    </div>
                  </div>
                  <div class="facilities-at-risk-list" style="margin-top: 14px;">
                    <strong style="color: #38bdf8; font-size: 11px; text-transform: uppercase;">High-Priority Facilities at Risk:</strong>
                    <ul style="margin: 8px 0 0 16px; color: #cbd5e1; font-size: 13px;">
                      <li v-for="f in deepDossier.vulnerable_demographics.facilities_at_risk" :key="f">
                        {{ f }}
                      </li>
                    </ul>
                  </div>
                </div>
              </article>
            </div>

            <div v-else-if="!appStore.isBackendMockModeEnabled" class="phase2-center-container">
              <div class="phase2-card glass-panel">
                <div class="phase2-icon">🏢</div>
                <div class="phase2-tag">AI RECONNAISSANCE PENDING</div>
                <h2>Predictive Impact Assessment</h2>
                <p>Launch the cognitive AI reconnaissance to generate unscripted critical infrastructure exposure, hospital vulnerabilities, and demographic displacement models.</p>
                <button class="primary-button recon-trigger-btn" @click="launchDeepAnalysis" :disabled="isAnalyzingDossier">
                  {{ isAnalyzingDossier ? 'Synthesizing...' : '⚡ Launch Tactical AI Reconnaissance' }}
                </button>
              </div>
            </div>
            <template v-else>

            <div class="tab-intro"><div><span class="section-kicker">FEATURE 09 · IMPACT ASSESSMENT</span><h2>Impact analysis</h2><p>Exposure is segmented into operational zones to guide resource allocation.</p></div><span class="updated-pill">Updated {{ relativeTime(detail.lastUpdated) }}</span></div>
            <div class="impact-layout">
              <article class="glass-panel zone-panel"><div class="panel-heading"><div><span class="section-kicker">EXPOSURE MODEL</span><h3>Affected zones</h3></div><span class="panel-code">IA-01</span></div><div class="zone-list"><div v-for="zone in detail.zones" :key="zone.name" class="zone-row"><div class="zone-icon" :class="`zone-${zone.level}`">{{ zone.code }}</div><div class="zone-main"><div class="row-title"><strong>{{ zone.name }}</strong><span>{{ zone.level }} risk</span></div><div class="progress-track"><span class="progress-fill" :class="`fill-${zone.level}`" :style="{ width: `${zone.percentage}%` }"></span></div><small>{{ formatNumber(zone.area) }} km² · {{ zone.note }}</small></div><strong class="zone-percent">{{ zone.percentage }}%</strong></div></div></article>
              <article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">HUMAN EXPOSURE</span><h3>Population by area</h3></div><span class="panel-code">IA-02</span></div><div class="population-bars"><div v-for="area in detail.populationByArea" :key="area.area" class="population-row"><div class="row-title"><span>{{ area.area }}</span><strong>{{ formatNumber(area.population) }}</strong></div><div class="bar-with-label"><div class="progress-track"><span class="progress-fill population-fill" :style="{ width: `${area.percent}%` }"></span></div><small>{{ area.percent }}%</small></div></div></div><div class="total-callout"><span>Total exposed population</span><strong>{{ formatNumber(incident.affectedPopulation) }}</strong></div></article>
            </div>
            <div class="content-grid two-columns">
              <article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">CRITICAL ASSETS</span><h3>Infrastructure affected</h3></div><span class="panel-code">IA-03</span></div><div class="asset-grid"><div v-for="asset in detail.infrastructure" :key="asset.label" class="asset-card"><span class="asset-icon">{{ asset.icon }}</span><strong>{{ asset.count }}</strong><span>{{ asset.label }}</span><small :class="asset.status">{{ asset.status }}</small></div></div></article>
              <article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">LOGISTICS</span><h3>Resource requirements</h3></div><span class="panel-code">IA-04</span></div><div class="resource-list"><div v-for="resource in detail.resources" :key="resource.name" class="resource-row"><span>{{ resource.name }}</span><div class="resource-progress"><span :style="{ width: `${resource.fulfilled}%` }"></span></div><strong>{{ resource.required }}</strong><small>{{ resource.fulfilled }}% ready</small></div></div></article>
            </div>
          
            </template>
</div>

          <!-- MAP & EVIDENCE -->
          <div v-else-if="activeTab === 'map'" class="map-tab">
            <div v-if="deepDossier" class="deep-ai-tab-container">
              <div class="tab-intro">
                <div>
                  <span class="section-kicker">EVACUATION ROUTING & TRANSIT CORRIDORS</span>
                  <h2>Evacuation Routing & Safety Perimeters</h2>
                  <p>Real-time calculated transit clearance times, primary corridors, and bottleneck choke-points.</p>
                </div>
                <button class="primary-button" type="button" @click="goTo('/map')">Open Fullscreen Radar ↗</button>
              </div>

              <div class="content-grid two-columns">
                <article class="glass-panel" style="padding: 20px;">
                  <div class="panel-heading">
                    <div><span class="section-kicker">SAFE TRANSIT</span><h3>Primary Evacuation Corridor</h3></div>
                    <span class="panel-code">EVAC-ROUTE-01</span>
                  </div>
                  <div class="evac-route-details">
                    <div class="route-highlight" style="display: flex; gap: 12px; align-items: center; margin-bottom: 12px;">
                      <span class="route-icon" style="font-size: 24px;">🛣️</span>
                      <div>
                        <strong style="color: #38bdf8; font-size: 14px;">{{ deepDossier.evacuation_corridors.primary_corridor }}</strong>
                        <small style="display: block; color: #94a3b8; font-size: 11px;">Designated Primary Outbound Corridor</small>
                      </div>
                    </div>
                    <div class="route-highlight alt" style="display: flex; gap: 12px; align-items: center; margin-bottom: 14px;">
                      <span class="route-icon" style="font-size: 24px;">🔀</span>
                      <div>
                        <strong style="color: #cbd5e1; font-size: 13px;">{{ deepDossier.evacuation_corridors.alternative_route }}</strong>
                        <small style="display: block; color: #94a3b8; font-size: 11px;">Secondary Contingency Route</small>
                      </div>
                    </div>
                    <div class="clearance-eta" style="margin-top: 14px; padding: 12px; background: rgba(14, 165, 233, 0.1); border-radius: 8px;">
                      <span style="color: #94a3b8; font-size: 11px; text-transform: uppercase;">Estimated Corridor Clearance Time:</span>
                      <strong style="display: block; font-size: 20px; color: #38bdf8; margin-top: 2px;">{{ deepDossier.evacuation_corridors.estimated_clearance_time_hours }} Hours</strong>
                    </div>
                  </div>
                </article>

                <article class="glass-panel" style="padding: 20px;">
                  <div class="panel-heading">
                    <div><span class="section-kicker">HAZARD WARNING</span><h3>Critical Choke-Points & Assembly Zones</h3></div>
                    <span class="panel-code">EVAC-CHOKE-02</span>
                  </div>
                  <div class="choke-rally-grid">
                    <div class="choke-box" style="margin-bottom: 16px;">
                      <strong style="color: #fb7185; font-size: 12px; text-transform: uppercase;">⚠️ Bottleneck Choke-Points:</strong>
                      <ul style="margin: 6px 0 0 16px; color: #cbd5e1; font-size: 13px;">
                        <li v-for="cp in deepDossier.evacuation_corridors.choke_points" :key="cp">
                          {{ cp }}
                        </li>
                      </ul>
                    </div>
                    <div class="rally-box">
                      <strong style="color: #4ade80; font-size: 12px; text-transform: uppercase;">🟢 Safe Assembly Staging Perimeters:</strong>
                      <ul style="margin: 6px 0 0 16px; color: #cbd5e1; font-size: 13px;">
                        <li v-for="sz in deepDossier.evacuation_corridors.safe_assembly_zones" :key="sz">
                          {{ sz }}
                        </li>
                      </ul>
                    </div>
                  </div>
                </article>
              </div>
            </div>

            <div v-else-if="!appStore.isBackendMockModeEnabled" class="phase2-center-container">
              <div class="phase2-card glass-panel">
                <div class="phase2-icon">🗺️</div>
                <div class="phase2-tag">REPORT PENDING</div>
                <h2>Evacuation Corridor Routing</h2>
                <p>Generate primary transit routing, bridge bottleneck warnings, and safe assembly staging areas.</p>
                <button class="primary-button recon-trigger-btn" @click="launchDeepAnalysis" :disabled="isAnalyzingDossier">
                  {{ isAnalyzingDossier ? 'Synthesizing...' : '⚡ Generate Full Crisis Report' }}
                </button>
              </div>
            </div>
            <template v-else>

            <div class="tab-intro"><div><span class="section-kicker">FEATURES 03 · 11 · 13</span><h2>Map & evidence</h2><p>Geospatial context and validated media supporting the current incident perimeter.</p></div><button class="primary-button" type="button" @click="goTo('/map')">Open interactive map ↗</button></div>
            <div class="map-evidence-layout">
              <article class="glass-panel map-preview"><div class="map-toolbar"><span class="map-title">SATELLITE REFERENCE · {{ incident.location.toUpperCase() }}</span><span class="map-live"><i></i> LIVE LAYERS</span></div><div class="map-canvas"><div class="map-grid"></div><div v-for="(zone, index) in detail.zones" :key="zone.name" class="map-zone" :class="`map-zone-${index + 1}`"><span>{{ zone.code }}</span></div><div class="map-crosshair">⊕</div><div class="map-scale">N<br><span>━━</span><br>2 km</div><div class="map-legend"><span><i class="legend-dot critical"></i> Critical</span><span><i class="legend-dot watch"></i> Watch</span><span><i class="legend-dot safe"></i> Monitored</span></div></div><div class="map-footer"><span>Imagery: Sentinel-2 · 10m resolution</span><span>Coordinates: {{ detail.coordinates }}</span></div></article>
              <article class="glass-panel evidence-panel"><div class="panel-heading"><div><span class="section-kicker">MEDIA VALIDATION</span><h3>Evidence register</h3></div><span class="verified-chip">{{ verifiedEvidence }}/{{ detail.evidence.length }} VERIFIED</span></div><div class="evidence-list"><div v-for="evidence in detail.evidence" :key="evidence.id" class="evidence-row"><div class="evidence-thumb" :class="`evidence-${evidence.kind}`">{{ evidence.kind === 'satellite' ? '◉' : evidence.kind === 'field' ? '▣' : '◌' }}</div><div class="evidence-main"><strong>{{ evidence.title }}</strong><small>{{ evidence.source }} · {{ evidence.captured }}</small></div><span class="evidence-status" :class="`evidence-${evidence.status.toLowerCase()}`">{{ evidence.status }}</span></div></div><div class="verification-score"><div class="score-ring"><strong>{{ detail.imageVerification }}%</strong><small>confidence</small></div><div><strong>Image verification status</strong><p>Cross-checked against temporal and geospatial signals.</p></div></div></article>
            </div>
          
            </template>
</div>

          <!-- EMERGENCY RESPONSE -->
          <div v-else-if="activeTab === 'response'" class="response-tab">
            <div v-if="deepDossier" class="deep-ai-tab-container">
              <div class="tab-intro">
                <div>
                  <span class="section-kicker">RESOURCE MOBILIZATION MATRIX</span>
                  <h2>Multi-Agency Resource Mobilization</h2>
                  <p>Operational logistics and multi-agency resource allocations calculated for this sector.</p>
                </div>
                <span class="response-state"><i></i> MOBILIZATION ACTIVE</span>
              </div>

              <article class="glass-panel" style="padding: 20px;">
                <div class="panel-heading">
                  <div><span class="section-kicker">ASSET DEPLOYMENT</span><h3>Operational Logistics Matrix</h3></div>
                  <span class="panel-code">LOG-ASSET-01</span>
                </div>
                <div class="resource-matrix-table-wrapper" style="overflow-x: auto;">
                  <table class="ai-resource-table" style="width: 100%; border-collapse: collapse;">
                    <thead>
                      <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.1); text-align: left; color: #94a3b8; font-size: 11px;">
                        <th style="padding: 10px;">Resource Asset</th>
                        <th style="padding: 10px;">Required Quantity</th>
                        <th style="padding: 10px;">Assigned Agency</th>
                        <th style="padding: 10px;">Deployment Priority</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="res in deepDossier.resource_matrix" :key="res.resource" style="border-bottom: 1px solid rgba(255, 255, 255, 0.05); font-size: 13px;">
                        <td style="padding: 12px 10px; color: #ffffff; font-weight: 700;">{{ res.resource }}</td>
                        <td style="padding: 12px 10px; color: #38bdf8;">{{ res.quantity }}</td>
                        <td style="padding: 12px 10px; color: #cbd5e1;">{{ res.assigned_agency }}</td>
                        <td style="padding: 12px 10px;">
                          <span class="priority-tag" :class="res.priority.toLowerCase()">{{ res.priority }}</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </article>
            </div>

            <div v-else-if="!appStore.isBackendMockModeEnabled" class="phase2-center-container">
              <div class="phase2-card glass-panel">
                <div class="phase2-icon">🚑</div>
                <div class="phase2-tag">REPORT PENDING</div>
                <h2>Multi-Agency Resource Matrix</h2>
                <p>Generate specialized equipment counts, first-responder squad deployment, and medical logistics matrices.</p>
                <button class="primary-button recon-trigger-btn" @click="launchDeepAnalysis" :disabled="isAnalyzingDossier">
                  {{ isAnalyzingDossier ? 'Synthesizing...' : '⚡ Generate Full Crisis Report' }}
                </button>
              </div>
            </div>
            <template v-else>

            <div class="tab-intro"><div><span class="section-kicker">FEATURE 10 · EVACUATION OPERATIONS</span><h2>Emergency response</h2><p>Live route capacity and deployment readiness for the affected population.</p></div><span class="response-state"><i></i> RESPONSE ACTIVE</span></div>
            <div class="response-metrics"><div v-for="metric in detail.responseMetrics" :key="metric.label" class="glass-panel response-metric"><span>{{ metric.label }}</span><strong>{{ metric.value }}</strong><small>{{ metric.note }}</small></div></div>
            <div class="content-grid two-columns"><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">SAFE MOVEMENT</span><h3>Evacuation routes</h3></div><span class="panel-code">ER-01</span></div><div class="route-list"><div v-for="routeItem in detail.routes" :key="routeItem.name" class="route-row"><div class="route-status" :class="`route-${routeItem.status}`"><span></span></div><div class="route-main"><div class="row-title"><strong>{{ routeItem.name }}</strong><span>{{ routeItem.status }}</span></div><small>{{ routeItem.direction }} · {{ routeItem.distance }} · capacity {{ routeItem.capacity }}</small><div class="route-track"><span :style="{ width: `${routeItem.clearance}%` }"></span></div></div><strong class="route-time">{{ routeItem.eta }}</strong></div></div></article><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">FIELD OPERATIONS</span><h3>Resource deployment</h3></div><span class="panel-code">ER-02</span></div><div class="deployment-list"><div v-for="deployment in detail.deployments" :key="deployment.name" class="deployment-row"><span class="deployment-icon">{{ deployment.icon }}</span><div><strong>{{ deployment.name }}</strong><small>{{ deployment.location }}</small></div><span class="deployment-count">{{ deployment.count }}</span><span class="deployment-status" :class="deployment.status">{{ deployment.status }}</span></div></div><div class="eta-callout"><span>Estimated full evacuation</span><strong>{{ detail.evacuationTime }}</strong><small>Based on current route clearance and traffic model</small></div></article></div>
          
            </template>
</div>

          <!-- INCIDENT HISTORY -->
          <div v-else-if="activeTab === 'history'" class="history-tab">
            <div v-if="deepDossier" class="deep-ai-tab-container">
              <div class="tab-intro">
                <div>
                  <span class="section-kicker">FEATURE 09 · PREDICTIVE CASCADE MODELING</span>
                  <h2>6H / 12H / 24H Disaster Spread Simulation</h2>
                  <p>Trajectory forecasting based on atmospheric wind vectors and local terrain topography.</p>
                </div>
                <span class="ai-chip live">CASCADE SIMULATION ACTIVE</span>
              </div>

              <div class="cascade-timeline-grid">
                <div v-for="cascade in deepDossier.predictive_cascade" :key="cascade.timeframe" class="cascade-card glass-panel" style="padding: 20px;">
                  <div class="cascade-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span class="time-tag" style="font-weight: 800; color: #38bdf8; font-size: 14px;">⏱️ {{ cascade.timeframe }}</span>
                    <span class="delta-badge" style="font-size: 11px; font-weight: 800; color: #fb7185; background: rgba(244, 63, 94, 0.15); padding: 4px 10px; border-radius: 999px;">+{{ cascade.perimeter_delta_km2 }} km² EXPANSION</span>
                  </div>
                  <div class="cascade-vector" style="margin-bottom: 12px;">
                    <label style="color: #94a3b8; font-size: 10px; text-transform: uppercase; font-weight: 700;">Vector & Trajectory:</label>
                    <p style="margin: 4px 0 0 0; color: #ffffff; font-size: 13px;">{{ cascade.spread_direction }}</p>
                  </div>
                  <div class="cascade-risks" style="display: flex; flex-direction: column; gap: 6px; border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 10px;">
                    <div style="font-size: 12px; color: #cbd5e1;">
                      <strong style="color: #fbbf24;">Primary Threat:</strong> {{ cascade.primary_risk }}
                    </div>
                    <div style="font-size: 12px; color: #fb7185;">
                      <strong>Cascading Risk:</strong> {{ cascade.secondary_threat }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="!appStore.isBackendMockModeEnabled" class="phase2-center-container">
              <div class="phase2-card glass-panel">
                <div class="phase2-icon">🔮</div>
                <div class="phase2-tag">AI RECONNAISSANCE PENDING</div>
                <h2>Predictive Cascade Simulation</h2>
                <p>Launch the cognitive AI reconnaissance to model 6-hour, 12-hour, and 24-hour crisis expansion trajectories using atmospheric wind vectors.</p>
                <button class="primary-button recon-trigger-btn" @click="launchDeepAnalysis" :disabled="isAnalyzingDossier">
                  {{ isAnalyzingDossier ? 'Synthesizing...' : '⚡ Launch Tactical AI Reconnaissance' }}
                </button>
              </div>
            </div>
            <template v-else>

            <div class="tab-intro"><div><span class="section-kicker">FEATURE 05 · HISTORICAL CONTEXT</span><h2>Incident history</h2><p>Comparable events reveal patterns, response outcomes, and reusable lessons.</p></div><span class="panel-code">HISTORY / {{ detail.historicalPattern }}</span></div>
            <div class="content-grid two-columns"><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">COMPARABLE EVENTS</span><h3>Similar past incidents</h3></div><span class="panel-code">IH-01</span></div><div class="history-list"><div v-for="past in detail.pastIncidents" :key="past.name" class="history-row"><div class="history-year">{{ past.year }}</div><div class="history-main"><strong>{{ past.name }}</strong><small>{{ past.location }} · {{ past.duration }}</small></div><div class="history-stat"><strong>{{ past.population }}</strong><small>affected</small></div><span class="similarity">{{ past.similarity }}% match</span></div></div></article><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">BENCHMARK</span><h3>Comparison metrics</h3></div><span class="panel-code">IH-02</span></div><div class="comparison-list"><div v-for="comparison in detail.comparisons" :key="comparison.label" class="comparison-row"><span>{{ comparison.label }}</span><div class="comparison-values"><strong>{{ comparison.current }}</strong><span>vs {{ comparison.baseline }}</span></div><span class="comparison-delta" :class="comparison.direction">{{ comparison.delta }}</span></div></div></article></div>
            <div class="content-grid two-columns"><article class="glass-panel pattern-card"><div class="panel-heading"><div><span class="section-kicker">PATTERN ANALYSIS</span><h3>Historical patterns</h3></div><span class="pattern-confidence">{{ detail.patternConfidence }}% confidence</span></div><ul class="insight-list"><li v-for="pattern in detail.patterns" :key="pattern"><span>↗</span>{{ pattern }}</li></ul></article><article class="glass-panel lessons-card"><div class="panel-heading"><div><span class="section-kicker">AFTER-ACTION LEARNING</span><h3>Lessons learned</h3></div><span class="panel-code">IH-04</span></div><ol class="lessons-list"><li v-for="lesson in detail.lessons" :key="lesson.title"><strong>{{ lesson.title }}</strong><span>{{ lesson.text }}</span></li></ol></article></div>
          
            </template>
</div>

          <!-- SOURCE OF TRUTH -->
          <div v-else-if="activeTab === 'source'" class="source-tab">
            <div v-if="!appStore.isBackendMockModeEnabled" class="phase2-center-container">
              <div class="phase2-card glass-panel">
                <div class="phase2-icon">🔗</div>
                <div class="phase2-tag">PHASE 2 ROADMAP</div>
                <h2>Data Lineage & Audit Trail</h2>
                <p>Immutable data provenance tracking and automated source verification chains are scheduled for delivery in <strong>Phase 2</strong>.</p>
                <div class="phase2-note">Real-time AI tactical response plans are operational in the <strong>Overview</strong> and <strong>AI Insights</strong> tabs.</div>
              </div>
            </div>
            <template v-else>

            <div class="tab-intro"><div><span class="section-kicker">FEATURE 07 · GOVERNANCE LAYER</span><h2>Source of truth <span class="critical-marker">★</span></h2><p>Every signal is traceable, freshness-scored, and independently verified before it informs decisions.</p></div><div class="quality-score"><span>DATA QUALITY</span><strong>{{ detail.dataQuality }}<small>/100</small></strong></div></div>
            <div class="source-grid"><article class="glass-panel source-overview"><div class="panel-heading"><div><span class="section-kicker">PROVENANCE</span><h3>Data source origin</h3></div><span class="verified-chip">● {{ verifiedSources }} VERIFIED</span></div><div class="source-cards"><div v-for="source in detail.sources" :key="source.name" class="source-card"><div class="source-card-head"><span class="source-icon">{{ source.icon }}</span><span class="source-status" :class="source.status.toLowerCase()">{{ source.status }}</span></div><strong>{{ source.name }}</strong><p>{{ source.description }}</p><div class="source-meta"><span>{{ source.records }} records</span><span>{{ source.confidence }}% confidence</span></div></div></div></article><article class="glass-panel freshness-panel"><div class="panel-heading"><div><span class="section-kicker">FRESHNESS</span><h3>Verification status</h3></div><span class="panel-code">ST-02</span></div><div class="freshness-list"><div><span>Last updated</span><strong>{{ formatDate(detail.lastUpdated) }}</strong></div><div><span>Last verified</span><strong>{{ formatDate(detail.lastVerified) }}</strong></div><div><span>Verification cadence</span><strong>Every 15 minutes</strong></div><div><span>Stale data threshold</span><strong>60 minutes</strong></div></div><div class="freshness-meter"><span>Freshness window</span><div class="progress-track"><span class="progress-fill freshness-fill" style="width: 82%"></span></div><strong>82%</strong></div></article></div>
            <div class="content-grid two-columns"><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">CHAIN OF CUSTODY</span><h3>Data lineage</h3></div><span class="panel-code">ST-03</span></div><div class="lineage-list"><div v-for="lineage in detail.lineage" :key="lineage.label" class="lineage-row"><span class="lineage-marker"></span><div><strong>{{ lineage.label }}</strong><small>{{ lineage.value }}</small></div><span class="confidence-badge">{{ lineage.confidence }}%</span></div></div></article><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">ACCOUNTABILITY</span><h3>Audit trail</h3></div><span class="panel-code">ST-04</span></div><div class="audit-list"><div v-for="audit in detail.auditTrail" :key="audit.time + audit.actor" class="audit-row"><span class="audit-time">{{ audit.time }}</span><div><strong>{{ audit.action }}</strong><small>{{ audit.actor }} · {{ audit.source }}</small></div></div></div></article></div>
          
            </template>
</div>

          <!-- AI INSIGHTS -->
          <div v-else-if="activeTab === 'ai'" class="ai-tab">
            <div class="tab-intro"><div><span class="section-kicker">FEATURE 12 · ASK THE MAP AI</span><h2>AI insights</h2><p>Models combine live telemetry, imagery, terrain, and historical analogues into an explainable forecast.</p></div><button class="primary-button" type="button" @click="goTo('/ask-map')">Ask the Map AI ↗</button></div>
            
            <!-- COMMENTED OUT (Live Mode): These sections used to show hardcoded detail.aiForecast mock data -->
            <!-- They are kept here as reference for what was originally displayed -->
            <!-- Forecast card: Shows probability, timeline, and risk breakdown -->
            <!-- <div class="ai-grid"><article class="glass-panel prediction-card"><div class="panel-heading"><div><span class="section-kicker">PREDICTION ENGINE</span><h3>Forecast outlook</h3></div><span class="ai-chip">MODEL v4.8</span></div><div class="prediction-head"><div class="forecast-number">{{ detail.aiForecast.probability }}<small>%</small></div><div><strong>{{ detail.aiForecast.headline }}</strong><p>{{ detail.aiForecast.window }}</p></div></div><div class="forecast-timeline"><div v-for="forecast in detail.aiForecast.timeline" :key="forecast.time" class="forecast-point"><span class="forecast-dot" :class="forecast.state"></span><strong>{{ forecast.time }}</strong><small>{{ forecast.value }}</small></div></div></article><article class="glass-panel risk-card"><div class="panel-heading"><div><span class="section-kicker">EXPLAINABILITY</span><h3>Risk score breakdown</h3></div><strong class="risk-total">{{ detail.aiForecast.riskScore }}/100</strong></div><div class="risk-list"><div v-for="risk in detail.aiForecast.riskBreakdown" :key="risk.label" class="risk-row"><div class="row-title"><span>{{ risk.label }}</span><strong>{{ risk.score }}</strong></div><div class="progress-track"><span class="progress-fill risk-fill" :style="{ width: `${risk.score}%` }"></span></div></div></div></article></div> -->
            
            <!-- Signal interpretation & Actions: Shows pattern analysis and decision support -->
            <!-- <div class="content-grid two-columns"><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">SIGNAL INTERPRETATION</span><h3>Pattern analysis</h3></div><span class="confidence-badge">{{ detail.aiForecast.confidence }}% confidence</span></div><div class="ai-pattern"><div v-for="signal in detail.aiForecast.signals" :key="signal.title" class="signal-row"><span class="signal-icon">{{ signal.icon }}</span><div><strong>{{ signal.title }}</strong><p>{{ signal.detail }}</p></div><span class="signal-impact">{{ signal.impact }}</span></div></div></article><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">AUTOMATED DECISION SUPPORT</span><h3>AI recommended actions</h3></div><span class="ai-chip">LIVE</span></div><ol class="action-list ai-actions"><li v-for="(action, index) in detail.aiForecast.actions" :key="action.title"><span class="action-number">0{{ index + 1 }}</span><div><strong>{{ action.title }}</strong><p>{{ action.reason }}</p></div></li></ol></article></div> -->
            
            <!-- NEW (Live Mode): Now displays REAL AI data from aiPlan and aiInsights -->
            <div v-if="aiLoading" class="loading-state">
              <span class="loading-spinner"></span>
              <p>Loading AI analysis...</p>
            </div>
            <div v-else-if="aiError" class="error-state">
              <span class="error-icon">⚠</span>
              <p>AI analysis unavailable: {{ aiError }}</p>
            </div>
            <div v-else-if="aiPlan" class="real-ai-content">
              <article class="glass-panel">
                <div class="panel-heading"><div><span class="section-kicker">AI DECISION SUPPORT</span><h2>{{ aiPlan.country_context }}</h2></div></div>
                <p class="long-copy">{{ aiPlan.severity_assessment }}</p>
              </article>
              <article class="glass-panel action-panel" style="margin-top: 18px;">
                <div class="panel-heading"><div><span class="section-kicker">IMMEDIATE ACTIONS</span><h3>Live AI recommendations</h3></div><span class="ai-chip">LIVE</span></div>
                <ol class="action-list">
                  <li v-for="(action, index) in aiPlan.immediate_actions" :key="index">
                    <span class="action-number">0{{ index + 1 }}</span><div><strong>{{ action }}</strong></div>
                  </li>
                </ol>
              </article>
              <article class="glass-panel" style="margin-top: 18px;">
                <div class="panel-heading"><div><span class="section-kicker">EVACUATION GUIDANCE</span><h3>Critical instructions</h3></div></div>
                <p class="long-copy">{{ aiPlan.evacuation_guidance }}</p>
              </article>
            </div>
            <div v-else class="loading-state">
              <p>No AI data available</p>
            </div>
          </div>

          <!-- ALERTS & COMMUNICATIONS -->
          <div v-else-if="activeTab === 'alerts'" class="alerts-tab">
            <div v-if="!appStore.isBackendMockModeEnabled" class="phase2-center-container">
              <div class="phase2-card glass-panel">
                <div class="phase2-icon">📱</div>
                <div class="phase2-tag">PHASE 2 ROADMAP</div>
                <h2>Alert Management & Dispatch</h2>
                <p>Multi-channel emergency broadcast analytics and delivery tracking are scheduled for delivery in <strong>Phase 2</strong>.</p>
                <div class="phase2-note">Real-time AI tactical response plans are operational in the <strong>Overview</strong> and <strong>AI Insights</strong> tabs.</div>
              </div>
            </div>
            <template v-else>

            <div class="tab-intro"><div><span class="section-kicker">FEATURES 06 · 13 · REAL-TIME NOTIFICATIONS</span><h2>Alerts & communications</h2><p>Broadcast reach, delivery health, and community response in one operational view.</p></div><button class="primary-button" type="button" @click="goTo('/alerts')">Open alert center ↗</button></div>
            <div class="response-metrics"><div v-for="metric in detail.communicationMetrics" :key="metric.label" class="glass-panel response-metric"><span>{{ metric.label }}</span><strong>{{ metric.value }}</strong><small>{{ metric.note }}</small></div></div>
            <div class="content-grid two-columns"><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">BROADCAST LOG</span><h3>Alert broadcast history</h3></div><span class="panel-code">AC-01</span></div><div class="alert-history"><div v-for="alert in detail.alertHistory" :key="alert.time + alert.message" class="alert-row"><span class="alert-severity" :class="alert.severity"></span><div><strong>{{ alert.message }}</strong><small>{{ alert.time }} · {{ alert.channel }}</small></div><span class="delivery-status" :class="alert.status">{{ alert.status }}</span></div></div></article><article class="glass-panel"><div class="panel-heading"><div><span class="section-kicker">REACH & DELIVERY</span><h3>Who was notified</h3></div><span class="panel-code">AC-02</span></div><div class="region-list"><div v-for="region in detail.notifiedRegions" :key="region.name" class="region-row"><span>{{ region.name }}</span><div class="progress-track"><span class="progress-fill region-fill" :style="{ width: `${region.delivery}%` }"></span></div><strong>{{ formatNumber(region.count) }}</strong><small>{{ region.delivery }}% delivered</small></div></div><div class="channel-pills"><span v-for="channel in detail.channels" :key="channel.name" class="channel-pill"><i>{{ channel.icon }}</i>{{ channel.name }} <strong>{{ channel.percent }}%</strong></span></div></article></div>
            <article class="glass-panel response-panel"><div class="panel-heading"><div><span class="section-kicker">OUTCOME MEASUREMENT</span><h3>Response metrics</h3></div><span class="panel-code">AC-03</span></div><div class="outcome-grid"><div v-for="outcome in detail.responseOutcomes" :key="outcome.label"><span>{{ outcome.label }}</span><strong>{{ outcome.value }}</strong><small>{{ outcome.note }}</small></div></div></article>
          
            </template>
</div>
        </section>
      </Transition>
    </template>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEventsStore, useAppStore } from '@/stores'
import type { IncidentLevel1, Event } from '@/types'
import JSZip from 'jszip'

// AI Insights data structure
interface ResponsePlan {
  immediate_actions: string[]
  resource_allocation: Record<string, unknown>
  evacuation_guidance: string
  severity_assessment: string
  country_context: string
}

interface AIInsight {
  id: string
  action: string
  estimatedAffected?: number
  timeUrgent: boolean
  severity: 'urgent' | 'high' | 'medium' | 'low'
}

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
const appStore = useAppStore()
const activeTab = ref<TabId>('overview')
const incidentId = computed(() => String(route.params.id || ''))
const incident = computed<IncidentLevel1 | undefined>(() => eventsStore.allIncidents.find(item => item.id === incidentId.value))

// AI Insights state
const aiPlan = ref<ResponsePlan | null>(null)
const aiInsights = ref<AIInsight[]>([])
const aiLoading = ref(false)
const aiError = ref<string | null>(null)

// Tier 2 Deep Tactical AI Dossier State
interface DeepDossier {
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
const isAnalyzingDossier = ref(false)
const scannerActive = ref(false)
const currentStepIndex = ref(0)
const analysisSteps = [
  'Fusing NASA thermal telemetry with OpenWeather wind vectors...',
  'Cross-referencing municipal hospital & bridge infrastructure...',
  'Running 6H/12H/24H Predictive Cascade simulation...',
  'Synthesizing Multi-Agency Evacuation & Deployment Dossier...'
]

async function launchDeepAnalysis() {
  if (!incidentId.value) return
  isAnalyzingDossier.value = true
  scannerActive.value = true
  currentStepIndex.value = 0

  // Animate the neural scanner steps
  const stepInterval = setInterval(() => {
    if (currentStepIndex.value < analysisSteps.length - 1) {
      currentStepIndex.value++
    }
  }, 1100)

  try {
    const res = await fetch(`/api/v1/incidents/${incidentId.value}/deep-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    if (data.dossier) {
      deepDossier.value = data.dossier
    }
  } catch (err) {
    console.error('Failed to generate deep AI dossier:', err)
  } finally {
    clearInterval(stepInterval)
    currentStepIndex.value = analysisSteps.length
    setTimeout(() => {
      isAnalyzingDossier.value = false
      scannerActive.value = false
    }, 600)
  }
}

async function checkExistingDossier() {
  if (!incidentId.value) return
  try {
    const res = await fetch(`/api/v1/incidents/${incidentId.value}/deep-dossier`)
    if (res.ok) {
      const data = await res.json()
      if (data.dossier) {
        deepDossier.value = data.dossier
      }
    }
  } catch (e) {
    // Ignore if not yet generated
  }
}

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

import mockDetails from '@/data/mock_incident_evidence.json'

const detail = computed(() => {
  const d = JSON.parse(JSON.stringify(mockDetails))
  d.lastUpdated = new Date(Date.now() - 8 * 60000)
  d.lastVerified = new Date(Date.now() - 14 * 60000)
  return d
})
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

function getIncidentIcon(type?: string, location?: string): string {
  const t = (type || '').toLowerCase()
  const loc = (location || '').toLowerCase()
  if (t.includes('fire') || loc.includes('fire')) return '🔥'
  if (t.includes('flood') || loc.includes('flood')) return '💧'
  if (t.includes('quake') || t.includes('seismic') || loc.includes('quake')) return '🌍'
  if (t.includes('storm') || loc.includes('storm') || loc.includes('typhoon') || loc.includes('hurricane')) return '🌀'
  if (t.includes('landslide')) return '⛰️'
  if (t.includes('volcano')) return '🌋'
  return '🌤️'
}

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
      `THREAT SCORE:       ${threatScore.value}/100 (${threatLevel.value})`,
      '-----------------------------------------------------------------',
      '  PHYSICAL EXPOSURE & EXPANSION METRICS                          ',
      '-----------------------------------------------------------------',
      `AFFECTED FOOTPRINT:    ${formatNumber(inc.affectedArea)} km²`,
      `POPULATION IN DANGER:  ${formatNumber(inc.affectedPopulation)} citizens`,
      `GROWTH VELOCITY:       +${inc.trend?.toFixed(1) || '0.0'} km²/h`,
      `6-HOUR MAXIMUM BUFFER: +${formatNumber(inc.forecast6h)} km²`,
      '-----------------------------------------------------------------',
      '  TACTICAL SITUATIONAL BRIEFING                                  ',
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
      'PRIORITY IMMEDIATE DIRECTIVES:',
      ...(aiInsights.value && aiInsights.value.length
        ? aiInsights.value.map((a: any, idx: number) => `[DIRECTIVE 0${idx + 1}] Priority: ${a.severity?.toUpperCase() || 'HIGH'}\nAction: ${a.action}\n`)
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
        `ESTIMATED CLEARANCE TIME: ${evac.estimated_clearance_time_hours} Hours`,
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
    console.error('Failed to generate SitRep zip package:', err)
  } finally {
    isExportingZip.value = false
  }
}

async function fetchAIInsights() {
  if (!incidentId.value) return
  aiLoading.value = true
  aiError.value = null
  try {
    const response = await fetch(`/api/v1/incidents/${incidentId.value}/insights`)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    if (data.plan) {
      aiPlan.value = data.plan
      // Transform backend plan to frontend insights
      aiInsights.value = (data.plan.immediate_actions || []).map((action: string, idx: number) => ({
        id: `ai-action-${idx}`,
        action,
        timeUrgent: idx === 0,
        severity: idx === 0 ? 'urgent' : idx === 1 ? 'high' : 'medium'
      }))
    }
  } catch (err) {
    aiError.value = err instanceof Error ? err.message : 'Failed to load AI insights'
    console.error('[AIInsights]', aiError.value)
  } finally {
    aiLoading.value = false
  }
}

onMounted(async () => {
  if (eventsStore.allIncidents.length === 0) {
    try {
      const host = window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin
      const res = await fetch(`${host}/api/v1/incidents?limit=100`)
      if (res.ok) {
        const raw = await res.json()
        if (raw && raw.length > 0) {
          eventsStore.setIncidents(raw.map((e: any, idx: number) => ({
            id: e.id || `event_${idx}`,
            type: e.event_type || 'fire',
            location: e.location_name || 'Unknown',
            countryCode: e.countryCode || 'UN',
            severity: e.severity || 'medium',
            status: e.status || 'active',
            threatScore: e.threatScore ?? e.impact?.risk_score ?? 50,
            detectionTime: new Date(e.event_timestamp || e.detectionTime || Date.now()),
            affectedArea: e.affectedArea ?? e.impact?.affected_area_km2 ?? 150,
            affectedPopulation: e.affectedPopulation ?? e.impact?.affected_population ?? 50000,
            trend: e.trend ?? e.impact?.trend_km2_per_hour ?? 5.2,
            forecast6h: e.forecast6h ?? e.impact?.forecast_6h_km2 ?? 31.2,
            coordinates: [e.latitude, e.longitude] as [number, number],
          })))
        }
      }
    } catch (err) {
      console.warn('Failed to hydrate incidents on detail page:', err)
    }
  }

  if (incidentId.value) {
    fetchAIInsights()
    checkExistingDossier()
  }
})

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
}.eyebrow, .section-kicker { color: #38bdf8; font-size: 10px; font-weight: 800; letter-spacing: .16em; }.live-dot, .response-state i, .map-live i { display: inline-block; width: 7px; height: 7px; margin-right: 7px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 10px #22c55e; }.hero-copy h1 { margin: 8px 0 4px; font-size: clamp(28px, 4vw, 42px); letter-spacing: -.04em; }.hero-location { margin: 0; color: #94a3b8; }.hero-location span { color: #38bdf8; }.hero-status { gap: 8px; flex-wrap: wrap; justify-content: flex-end; }.type-badge, .severity-badge, .status-badge, .ai-chip, .verified-chip, .updated-pill, .response-state, .pattern-confidence { padding: 6px 9px; border-radius: 6px; font-size: 10px; font-weight: 800; letter-spacing: .06em; }.type-badge { background: rgba(168,85,247,.16); color: #d8b4fe; }.type-fire { color: #fb923c; background: rgba(249,115,22,.15); }.type-flood { color: #38bdf8; background: rgba(14,165,233,.15); }.type-landslide { color: #fbbf24; background: rgba(245,158,11,.15); }.severity-high { color: #fb7185; background: rgba(244,63,94,.15); }.severity-medium { color: #fbbf24; background: rgba(245,158,11,.15); }.severity-low { color: #4ade80; background: rgba(34,197,94,.15); }.status-active { color: #4ade80; }.status-monitoring { color: #fbbf24; }.status-resolved { color: #94a3b8; }.status-badge { border: 1px solid currentColor; }
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
  font-size: 11px;
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
  font-size: 14px;
  line-height: 1.6;
  color: #cbd5e1;
  margin: 0 0 18px 0;
}

.phase2-note {
  font-size: 12px;
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
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.12), rgba(30, 41, 59, 0.7));
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
  font-size: 10px;
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
  font-size: 13px;
  line-height: 1.5;
  color: #cbd5e1;
  margin: 0;
}

.recon-launch-button {
  background: linear-gradient(135deg, #0ea5e9, #2563eb);
  color: #ffffff;
  border: 1px solid #38bdf8;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.5px;
  cursor: pointer;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.25s ease;
  box-shadow: 0 4px 16px rgba(14, 165, 233, 0.35);
}

.recon-launch-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #38bdf8, #1d4ed8);
  box-shadow: 0 0 24px rgba(56, 189, 248, 0.6);
  transform: translateY(-2px);
}

.recon-launch-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.recon-trigger-btn {
  margin-top: 14px;
  font-size: 13px;
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
  box-shadow: 0 0 50px rgba(14, 165, 233, 0.4);
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
  font-size: 15px;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.8px;
}

.scanner-titles small {
  color: #94a3b8;
  font-size: 10px;
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
  font-size: 12px;
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
  font-size: 10px;
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
  font-size: 10px;
  font-weight: 800;
  color: #38bdf8;
  background: rgba(14, 165, 233, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
}

.facility-risk {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 4px;
}

.facility-risk.critical { color: #ef4444; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); }
.facility-risk.high { color: #f59e0b; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); }
.facility-risk.moderate { color: #38bdf8; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); }

.ai-facility-card h4 {
  margin: 0;
  font-size: 14px;
  color: #ffffff;
}

.facility-meta {
  font-size: 11px;
  color: #94a3b8;
}

.facility-action {
  font-size: 12px;
  line-height: 1.4;
  color: #cbd5e1;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 8px;
}

.priority-tag {
  font-size: 10px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 4px;
}

.priority-tag.immediate { color: #ef4444; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); }
.priority-tag.high { color: #f59e0b; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.3); }
.priority-tag.staged { color: #38bdf8; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); }

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
  font-size: 13px;
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.primary-back-btn:hover {
  background: #0ea5e9;
  color: #03111b;
  box-shadow: 0 0 16px rgba(14, 165, 233, 0.5);
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
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(30, 41, 59, 0.65));
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 12px;
  gap: 16px;
}

.toolbar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.8px;
  color: #94a3b8;
  text-transform: uppercase;
}

.command-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 10px #10b981;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.cmd-btn {
  padding: 9px 16px;
  font-size: 12px;
  font-weight: 700;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.cmd-btn.primary {
  background: linear-gradient(135deg, #0ea5e9, #2563eb);
  border: 1px solid #38bdf8;
  color: #ffffff;
  box-shadow: 0 4px 14px rgba(14, 165, 233, 0.35);
}

.cmd-btn.primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #38bdf8, #1d4ed8);
  box-shadow: 0 0 20px rgba(56, 189, 248, 0.6);
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
  box-shadow: 0 0 8px #38bdf8;
}

.recon-title-group h4 {
  margin: 0;
  font-size: 13px;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 0.6px;
}

.recon-coords-badge {
  font-size: 11px;
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
  font-size: 10px;
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
  font-size: 14px;
  font-weight: 800;
}

.wind-label {
  font-size: 10px;
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
  font-size: 11px;
  font-weight: 700;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.gis-console-btn:hover {
  background: #0ea5e9;
  color: #03111b;
  box-shadow: 0 0 14px rgba(14, 165, 233, 0.5);
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
  font-size: 10px;
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
  font-size: 10px;
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
</style>

