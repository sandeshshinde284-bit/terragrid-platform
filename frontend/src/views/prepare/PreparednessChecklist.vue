<template>
  <div class="prepare-screen checklist-screen">
    <Header />

    <div class="checklist-container">
      <!-- Only block the whole page on the true first load (no cities yet) -
           see the matching comment in AgencyAlerts.vue for why. -->
      <div v-if="loading && cities.length === 0" class="empty-state glass-panel tactical-loading-container">
        <div class="radar-ping-ring">
          <span class="radar-dot"></span>
        </div>
        <div class="loading-telemetry-text">
          <strong class="cycling-step-text">{{ $t('prepare.fetchingForecast') }}</strong>
        </div>
        <div class="tactical-progress-track">
          <div class="tactical-scan-laser"></div>
        </div>
      </div>

      <div v-else-if="error && cities.length === 0" class="empty-state glass-panel">
        <div class="empty-icon">⚠️</div>
        <h3>{{ $t('prepare.checklist.loadError') }}</h3>
        <p>{{ error }}</p>
      </div>

      <div v-else-if="cities.length === 0" class="empty-state glass-panel">
        <div class="empty-icon">✅</div>
        <h3>{{ $t('prepare.noForecastData') }}</h3>
        <p>{{ $t('prepare.noForecastDesc') }}</p>
      </div>

      <template v-else>
        <div class="checklist-hero glass-panel">
          <div class="hero-left">
            <h2>{{ $t('prepare.checklist.title') }}</h2>
            <span class="hero-meta">{{ $t('prepare.checklist.subtitle') }}</span>
          </div>
        </div>

        <div class="master-detail">
          <!-- Always-visible, worst-first city list: scan every city's status
               at a glance and jump straight to one with a single click - no
               dropdown to open/scroll/close per city. -->
          <nav class="city-rail glass-panel" aria-label="Cities by risk">
            <button
              v-for="city in sortedCities"
              :key="cityKey(city)"
              type="button"
              class="rail-item"
              :class="[worstRisk(city).toLowerCase(), { active: cityKey(city) === selectedKey }]"
              @click="selectedKey = cityKey(city)"
            >
              <span class="rail-dot"></span>
              <span class="rail-text">
                <span class="rail-name">{{ city.city }}</span>
                <span class="rail-country">{{ countryName(city.country) }}</span>
              </span>
              <span class="rail-risk">{{ worstRisk(city) }}</span>
            </button>
          </nav>

          <div class="detail-panel">
            <div v-if="actionsLoading" class="empty-state glass-panel tactical-loading-container actions-loading">
              <div class="radar-ping-ring small">
                <span class="radar-dot"></span>
              </div>
              <div class="loading-telemetry-text">
                <strong class="cycling-step-text">Generating preparedness checklist for {{ selectedCity?.city }}...</strong>
              </div>
            </div>

            <div v-else-if="actionsError" class="empty-state glass-panel">
              <div class="empty-icon">⚠️</div>
              <h3>Couldn't generate the checklist</h3>
              <p>{{ actionsError }}</p>
            </div>

            <template v-else-if="actionsPlan">
              <div class="risk-context glass-panel" :class="selectedToneClass">
                <span class="context-icon">{{ selectedToneIcon }}</span>
                <span class="context-text">{{ actionsPlan.risk_context }}</span>
                <span class="source-badge" :class="sourceBadgeClass">{{ sourceLabel }}</span>
              </div>

              <div class="progress-bar-row glass-panel" v-if="completionStats.total > 0">
                <span class="progress-label">{{ completionStats.done }} / {{ completionStats.total }} {{ $t('prepare.checklist.complete') }}</span>
                <div class="progress-track">
                  <div class="progress-fill" :style="{ width: completionStats.pct + '%' }"></div>
                </div>
                <span class="progress-pct">{{ completionStats.pct }}%</span>
              </div>

              <!-- Agency ownership filter: "what does Health Dept still owe me" -->
              <div class="agency-filter" v-if="agencyOptions.length > 1">
                <button
                  type="button"
                  class="agency-chip"
                  :class="{ active: selectedAgency === 'ALL' }"
                  @click="selectedAgency = 'ALL'"
                >
                  {{ $t('prepare.checklist.allAgencies') }} <span class="agency-count">{{ actionsPlan.actions.length }}</span>
                </button>
                <button
                  v-for="opt in agencyOptions"
                  :key="opt.agency"
                  type="button"
                  class="agency-chip"
                  :class="{ active: selectedAgency === opt.agency }"
                  @click="selectedAgency = opt.agency"
                >
                  {{ opt.agency }} <span class="agency-count">{{ opt.count }}</span>
                </button>
              </div>

              <div class="priority-section" v-for="tier in priorityTiers" :key="tier.priority" v-show="tier.actions.length > 0">
                <div class="tier-header" :class="tier.className">
                  <span class="tier-dot"></span>
                  <span class="tier-label">{{ tier.label }}</span>
                  <span class="tier-count">{{ tier.actions.length }}</span>
                </div>

                <div class="action-grid">
                  <div
                    v-for="(action, idx) in tier.actions"
                    :key="idx"
                    class="action-card glass-panel"
                    :class="{ completed: isCompleted(action) }"
                  >
                    <div class="action-top">
                      <span class="category-chip" :class="action.category.toLowerCase()">{{ categoryIcon(action.category) }} {{ action.category }}</span>
                      <span class="deadline-chip" :class="deadlineInfo(action).urgency">{{ deadlineInfo(action).label }}</span>
                    </div>
                    <label class="action-check-row">
                      <input
                        type="checkbox"
                        class="action-checkbox"
                        :checked="isCompleted(action)"
                        @change="toggleCompleted(action)"
                      />
                      <p class="action-text">{{ action.action }}</p>
                    </label>
                    <div class="action-agency">
                      <span class="agency-icon">{{ agencyIcon(action.agency) }}</span>
                      <span>{{ action.agency }}</span>
                    </div>
                    <p class="action-rationale">{{ action.rationale }}</p>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import Header from '@/components/organisms/Header.vue'
import { useMockMode } from '@/composables/useMockMode'
import { usePrepareForecastStore, type PrepareCityForecast } from '@/stores'

const { t } = useI18n()

type CityForecast = PrepareCityForecast

interface PreparednessAction {
  action: string
  agency: string
  category: string
  priority: 1 | 2 | 3
  deadline_day: number
  rationale: string
}

interface ActionsPlan {
  risk_context: string
  actions: PreparednessAction[]
  ai_available?: boolean
  is_fallback?: boolean
  is_mock_demo?: boolean
}

const { fetchWithMockMode } = useMockMode()

// Shared across all 4 PREPARE pages - fetched once, reused on tab switches
// instead of each page re-fetching all ~40 cities independently (see
// stores/index.ts for why this used to make every page load take minutes).
const prepareForecastStore = usePrepareForecastStore()
const { cities, loading, error } = storeToRefs(prepareForecastStore)
const selectedKey = ref('')

const actionsPlan = ref<ActionsPlan | null>(null)
const actionsLoading = ref(false)
const actionsError = ref('')
const actionsSource = ref('')

const RISK_RANK: Record<string, number> = { GREEN: 0, YELLOW: 1, ORANGE: 2, RED: 3 }

const COUNTRY_NAMES: Record<string, string> = {
  IN: 'India', NP: 'Nepal', CN: 'China', HK: 'Hong Kong', BD: 'Bangladesh',
  PK: 'Pakistan', TH: 'Thailand', VN: 'Vietnam', SG: 'Singapore', MY: 'Malaysia',
  IQ: 'Iraq', AE: 'UAE', ET: 'Ethiopia', KE: 'Kenya', RW: 'Rwanda', US: 'United States',
}
const countryName = (code: string) => COUNTRY_NAMES[code] || code

const CATEGORY_ICONS: Record<string, string> = {
  DRAINAGE: '🌊', MEDICAL: '🏥', EVACUATION: '🚤', SUPPLIES: '📦',
  COMMUNICATION: '📢', INFRASTRUCTURE: '🏗️',
}
const categoryIcon = (category: string) => CATEGORY_ICONS[(category || '').toUpperCase()] || '📋'

// Agency names are free-text, AI-generated owning bodies (e.g. "NDRF / Fire
// Department", "Municipal Corporation - Drainage Dept") - not a fixed enum,
// so this can't be an exact-match lookup like CATEGORY_ICONS. Keyword match
// instead, checked in a specific-to-general order so e.g. "Municipal
// Corporation - Drainage Dept" hits drainage before falling to the generic
// municipal icon. Every agency card was previously showing the same 🏛️
// regardless of which agency it actually was.
const AGENCY_ICON_KEYWORDS: Array<[string, string]> = [
  ['drainage', '🌊'], ['water', '🌊'], ['flood', '🌊'],
  ['health', '🏥'], ['medical', '🏥'], ['hospital', '🏥'],
  ['fire', '🚒'], ['ndrf', '🚒'], ['rescue', '🚒'],
  ['police', '🚓'], ['traffic', '🚓'],
  ['relief', '🆘'], ['disaster management', '🆘'], ['emergency management', '🆘'],
  ['supply', '📦'], ['supplies', '📦'],
  ['communication', '📢'],
  ['municipal', '🏛️'],
]
const agencyIcon = (agency: string): string => {
  const lower = (agency || '').toLowerCase()
  for (const [keyword, icon] of AGENCY_ICON_KEYWORDS) {
    if (lower.includes(keyword)) return icon
  }
  return '🏛️'
}

const cityKey = (city: CityForecast) => `${city.city}-${city.country}`

const worstRisk = (city: CityForecast): string => {
  return city.daily.reduce((worst, day) => (RISK_RANK[day.risk_level] > RISK_RANK[worst] ? day.risk_level : worst), 'GREEN')
}

const sortedCities = computed(() => {
  return [...cities.value].sort((a, b) => RISK_RANK[worstRisk(b)] - RISK_RANK[worstRisk(a)])
})

const selectedCity = computed<CityForecast | null>(() => {
  return cities.value.find(c => cityKey(c) === selectedKey.value) || null
})

const selectedToneClass = computed(() => {
  if (!selectedCity.value) return 'green'
  return worstRisk(selectedCity.value).toLowerCase()
})

const selectedToneIcon = computed(() => {
  const tone = selectedToneClass.value
  return tone === 'red' ? '🔴' : tone === 'orange' ? '🟠' : tone === 'yellow' ? '🟡' : '✅'
})

const sourceLabel = computed(() => actionsSource.value || '')
const sourceBadgeClass = computed(() => {
  if (actionsPlan.value?.is_mock_demo) return 'mock'
  if (actionsPlan.value?.is_fallback) return 'fallback'
  return 'live'
})

// --- Completion tracking (PR6: interactive checklist) -----------------------
// Persisted to localStorage, per-browser. Actions have no stable backend ID,
// so completion is keyed by city + agency + action text. This persists
// reliably for mock mode (the fixture text never changes) and for live mode
// as long as the checklist isn't regenerated with different wording - an
// inherent limitation until actions carry stable IDs from the backend
// (would need DB-backed task identity, deferred - see PREPARE_PHASE_NOTES.md).
const COMPLETED_STORAGE_KEY = 'terragrid_checklist_completed_v1'

const loadCompletedFromStorage = (): Set<string> => {
  try {
    const raw = localStorage.getItem(COMPLETED_STORAGE_KEY)
    if (!raw) return new Set()
    const arr = JSON.parse(raw)
    return new Set(Array.isArray(arr) ? arr : [])
  } catch {
    return new Set()
  }
}

const saveCompletedToStorage = (keys: Set<string>) => {
  try {
    localStorage.setItem(COMPLETED_STORAGE_KEY, JSON.stringify([...keys]))
  } catch {
    // Best-effort only (private browsing, storage quota, etc.) - never block the UI on this.
  }
}

const completedKeys = ref<Set<string>>(loadCompletedFromStorage())

const actionKey = (action: PreparednessAction): string => {
  const city = selectedCity.value
  return `${city ? cityKey(city) : ''}::${action.agency}::${action.action}`
}

const isCompleted = (action: PreparednessAction) => completedKeys.value.has(actionKey(action))

const toggleCompleted = (action: PreparednessAction) => {
  const key = actionKey(action)
  const next = new Set(completedKeys.value)
  if (next.has(key)) next.delete(key)
  else next.add(key)
  completedKeys.value = next
  saveCompletedToStorage(next)
}

const completionStats = computed(() => {
  const actions = actionsPlan.value?.actions || []
  const total = actions.length
  const done = actions.filter(a => isCompleted(a)).length
  return { total, done, pct: total > 0 ? Math.round((done / total) * 100) : 0 }
})

// --- Agency ownership filter (PR6) -------------------------------------------
const selectedAgency = ref('ALL')

const agencyOptions = computed(() => {
  const actions = actionsPlan.value?.actions || []
  const counts = new Map<string, number>()
  for (const a of actions) counts.set(a.agency, (counts.get(a.agency) || 0) + 1)
  return Array.from(counts.entries()).map(([agency, count]) => ({ agency, count }))
})

// --- Deadline tracking (PR6): resolve the relative "Day N" into an actual
// forecast date and flag urgency against today's date. ----------------------
const formatDay = (dateStr: string): string => {
  const d = new Date(dateStr)
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

type Urgency = 'overdue' | 'today' | 'soon' | 'normal'

const deadlineInfo = (action: PreparednessAction): { label: string; urgency: Urgency } => {
  const day = selectedCity.value?.daily?.[action.deadline_day - 1]
  if (!day) return { label: `Before Day ${action.deadline_day}`, urgency: 'normal' }

  const deadlineDate = new Date(`${day.date}T00:00:00`)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diffDays = Math.round((deadlineDate.getTime() - today.getTime()) / 86400000)

  let urgency: Urgency = 'normal'
  if (diffDays < 0) urgency = 'overdue'
  else if (diffDays === 0) urgency = 'today'
  else if (diffDays === 1) urgency = 'soon'

  const label = urgency === 'overdue'
    ? `Overdue - was due ${formatDay(day.date)}`
    : urgency === 'today'
      ? `Due today (${formatDay(day.date)})`
      : `Due ${formatDay(day.date)}`

  return { label, urgency }
}

// Group the generated actions into IMMEDIATE / HIGH / STAGED tiers so the most
// urgent work is always first, regardless of the order the model returned them in.
// Also respects the agency ownership filter above.
const priorityTiers = computed(() => {
  const all = actionsPlan.value?.actions || []
  const actions = selectedAgency.value === 'ALL' ? all : all.filter(a => a.agency === selectedAgency.value)
  return [
    { priority: 1, label: t('prepare.checklist.tierImmediate'), className: 'immediate', actions: actions.filter(a => a.priority === 1) },
    { priority: 2, label: t('prepare.checklist.tierHigh'), className: 'high', actions: actions.filter(a => a.priority === 2) },
    { priority: 3, label: t('prepare.checklist.tierStaged'), className: 'staged', actions: actions.filter(a => a.priority === 3) },
  ]
})

const apiHost = () => import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)

const fetchActionsForSelectedCity = async () => {
  const city = selectedCity.value
  if (!city) return

  actionsLoading.value = true
  actionsError.value = ''
  actionsPlan.value = null

  try {
    const host = apiHost()
    const params = new URLSearchParams({ city: city.city, country: city.country })
    const response = await fetchWithMockMode(`${host}/api/v1/prepare/actions?${params.toString()}`)

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const json = await response.json()
    actionsPlan.value = json.data
    actionsSource.value = json.source || ''
  } catch (e) {
    actionsError.value = e instanceof Error ? e.message : 'Unknown error generating checklist'
  } finally {
    actionsLoading.value = false
  }
}

onMounted(async () => {
  // If another PREPARE page already loaded fresh forecast data, this
  // resolves immediately and the watch(cities, ...) below picks the
  // default selection from what's already there.
  await prepareForecastStore.ensureLoaded(fetchWithMockMode)
  if (cities.value.length > 0 && !selectedCity.value) {
    selectedKey.value = cityKey(sortedCities.value[0])
  }
})

watch(cities, (newCities) => {
  if (newCities.length > 0 && !selectedCity.value) {
    selectedKey.value = cityKey(sortedCities.value[0])
  }
})

watch(selectedKey, () => {
  selectedAgency.value = 'ALL'
  if (selectedCity.value) fetchActionsForSelectedCity()
})
</script>

<style scoped>
.checklist-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.checklist-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 4px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 48px 24px;
  text-align: center;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 32px;
}

.checklist-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 20px;
}

.hero-left h2 {
  margin: 0 0 4px 0;
  color: var(--accent-cyan);
}

.hero-meta {
  font-size: 13px;
  color: var(--text-secondary);
}

/* Master-detail layout: an always-visible, worst-first city list beside the
   detail panel, so every city's status is scannable at once - no dropdown
   to open/scroll/close per city. */
.master-detail {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
  align-items: flex-start;
}

.city-rail {
  flex: 0 0 260px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  max-height: 70vh;
  overflow-y: auto;
  /* Themed scrollbar instead of the browser's default light-gray one, which
     clashes against this panel's dark background. The mobile media query
     below already themes this for horizontal scrolling; this covers the
     vertical desktop case the same way. */
  scrollbar-width: thin;
  scrollbar-color: var(--accent-primary, #22d3ee) transparent;
}

.city-rail::-webkit-scrollbar {
  width: 6px;
}

.city-rail::-webkit-scrollbar-button {
  display: none;
  width: 0;
  height: 0;
}

.city-rail::-webkit-scrollbar-track {
  background: transparent;
}

.city-rail::-webkit-scrollbar-thumb {
  background: var(--accent-primary, #22d3ee);
  border-radius: 3px;
}

.rail-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.rail-item:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateX(4px);
}

.rail-item.active {
  background: rgba(56, 189, 248, 0.2);
  border-color: rgba(56, 189, 248, 0.5);
  box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.3), inset 0 0 8px rgba(56, 189, 248, 0.1);
}

.rail-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
}

.rail-item.green .rail-dot { background: #22c55e; }
.rail-item.yellow .rail-dot { background: #eab308; box-shadow: 0 0 4px rgba(234, 179, 8, 0.35); }
.rail-item.orange .rail-dot { background: #f97316; box-shadow: 0 0 6px rgba(249, 115, 22, 0.45); }
.rail-item.red .rail-dot { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.55); }

.rail-text {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.rail-name {
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rail-country {
  font-size: 11px;
  color: var(--text-secondary);
}

.rail-risk {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.rail-risk {
  font-size: 11px;
  font-weight: 900;
  letter-spacing: 0.06em;
  flex-shrink: 0;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
}

.rail-item.green .rail-risk {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.15);
  text-shadow: 0 0 4px rgba(34, 197, 94, 0.3);
}

.rail-item.yellow .rail-risk {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.15);
  text-shadow: 0 0 4px rgba(251, 191, 36, 0.3);
}

.rail-item.orange .rail-risk {
  color: #fb923c;
  background: rgba(251, 147, 60, 0.2);
  text-shadow: 0 0 4px rgba(251, 147, 60, 0.4);
}

.rail-item.red .rail-risk {
  color: #fca5a5;
  background: rgba(252, 165, 165, 0.15);
  text-shadow: 0 0 4px rgba(252, 165, 165, 0.3);
}

.detail-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.actions-loading {
  padding: 32px 20px;
}

.risk-context {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-left: 3px solid var(--text-secondary);
  flex-wrap: wrap;
}

.risk-context.green { border-left-color: #22c55e; }
.risk-context.yellow { border-left-color: #eab308; }
.risk-context.orange { border-left-color: #f97316; }
.risk-context.red { border-left-color: #ef4444; }

.context-icon {
  font-size: 16px;
}

.context-text {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  flex: 1;
}

.source-badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 4px;
  white-space: nowrap;
}

.source-badge.mock {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.source-badge.live {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.source-badge.fallback {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
  border: 1px solid rgba(234, 179, 8, 0.3);
}

.progress-bar-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 18px;
}

.progress-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
}

.progress-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #38bdf8, #22c55e);
  border-radius: 3px;
  transition: width 0.25s ease;
}

.progress-pct {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  width: 36px;
  text-align: right;
}

.agency-filter {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.agency-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.agency-chip.active {
  border-color: rgba(56, 189, 248, 0.4);
  background: rgba(56, 189, 248, 0.12);
  color: #38bdf8;
}

.agency-count {
  font-size: 10px;
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 6px;
  border-radius: 10px;
}

.priority-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tier-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 2px;
}

.tier-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.tier-header.immediate .tier-dot { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.55); }
.tier-header.high .tier-dot { background: #f97316; box-shadow: 0 0 6px rgba(249, 115, 22, 0.4); }
.tier-header.staged .tier-dot { background: #38bdf8; }

.tier-label {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-primary);
}

.tier-count {
  font-size: 11px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.06);
  padding: 1px 7px;
  border-radius: 10px;
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.action-card {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
}

.action-card:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.action-card.completed {
  opacity: 0.6;
}

.action-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 6px;
}

.category-chip {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  white-space: nowrap;
}

.deadline-chip {
  font-size: 11px;
  font-weight: 600;
  color: #38bdf8;
  white-space: nowrap;
}

.deadline-chip.today {
  color: #eab308;
}

.deadline-chip.overdue {
  color: #ef4444;
  font-weight: 800;
}

.action-check-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
}

.action-checkbox {
  margin-top: 3px;
  width: 15px;
  height: 15px;
  flex-shrink: 0;
  accent-color: #38bdf8;
  cursor: pointer;
}

.action-text {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  line-height: 1.4;
}

.action-card.completed .action-text {
  text-decoration: line-through;
  color: var(--text-secondary);
}

.action-agency {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.action-rationale {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.4;
  padding-top: 6px;
  border-top: 1px dashed rgba(255, 255, 255, 0.08);
}

/* Tactical Loading Animation (matches ForecastDashboard.vue / RiskTimeline.vue) */
.tactical-loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 60px 20px;
}
.radar-ping-ring {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  border: 2px solid rgba(14, 165, 233, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.radar-ping-ring.small {
  width: 36px;
  height: 36px;
}
.radar-ping-ring::before {
  content: '';
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  border: 1px solid rgba(14, 165, 233, 0.5);
  animation: radar-ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
}
.radar-dot {
  width: 12px;
  height: 12px;
  background-color: #0ea5e9;
  border-radius: 50%;
  box-shadow: 0 0 15px 4px rgba(14, 165, 233, 0.6);
}
.radar-ping-ring.small .radar-dot {
  width: 8px;
  height: 8px;
}
.loading-telemetry-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
}
.cycling-step-text {
  font-size: 14px;
  color: #94a3b8;
  font-family: monospace;
  animation: pulse-text 1.5s ease-in-out infinite;
}
.tactical-progress-track {
  width: 250px;
  height: 2px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}
.tactical-scan-laser {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 40%;
  background: linear-gradient(90deg, transparent, #0ea5e9, transparent);
  animation: scan-laser 2s linear infinite;
}
@keyframes radar-ping {
  0% { transform: scale(0.5); opacity: 1; }
  100% { transform: scale(2); opacity: 0; }
}
@keyframes pulse-text {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
@keyframes scan-laser {
  0% { left: -40%; }
  100% { left: 100%; }
}

@media (max-width: 480px) {
  .checklist-screen {
    padding: 8px;
    gap: 8px;
  }

  .checklist-hero {
    padding: 14px 16px;
  }

  /* Stack the city rail above the detail panel, and lay it out as a
     horizontally scrollable row of compact chips rather than a tall
     vertical list eating the screen before the checklist even shows. */
  .master-detail {
    flex-direction: column;
  }

  .city-rail {
    flex: 0 0 auto;
    flex-direction: row;
    max-height: none;
    overflow-x: auto;
    overflow-y: hidden;
    width: 100%;
    position: relative;
    scrollbar-width: thin;
    scrollbar-color: var(--accent-primary, #22d3ee) transparent;
  }

  .city-rail::-webkit-scrollbar {
    height: 6px;
  }

  .city-rail::-webkit-scrollbar-button {
    display: none;
    width: 0;
    height: 0;
  }

  .city-rail::-webkit-scrollbar-track {
    background: transparent;
  }

  .city-rail::-webkit-scrollbar-thumb {
    background: var(--accent-primary, #22d3ee);
    border-radius: 3px;
  }

  .city-rail::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    bottom: 6px;
    width: 24px;
    background: linear-gradient(to right, transparent, rgba(10, 14, 22, 0.85));
    pointer-events: none;
  }

  .rail-item {
    flex: 0 0 auto;
    min-width: 150px;
  }
}
</style>
