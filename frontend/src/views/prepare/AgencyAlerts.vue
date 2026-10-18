<template>
  <div class="prepare-screen alerts-screen">
    <Header />

    <div class="alerts-container">
      <!-- Only block the whole page on the true first load (no cities yet).
           A background refresh (ensureLoaded() re-fetching stale cache -
           see PREPARE_FORECAST_FRESHNESS_MS in stores/index.ts) must not
           nuke an already-good city list just because `loading` flipped
           true again - that was replacing live data with the full tactical
           loader every time someone returned to this tab after 5+ minutes
           elsewhere (e.g. adding a recipient in Settings). -->
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
        <h3>{{ $t('prepare.agencyAlerts.loadError') }}</h3>
        <p>{{ error }}</p>
      </div>

      <div v-else-if="cities.length === 0" class="empty-state glass-panel">
        <div class="empty-icon">📨</div>
        <h3>{{ $t('prepare.noForecastData') }}</h3>
        <p>{{ $t('prepare.noForecastDesc') }}</p>
      </div>

      <template v-else>
        <div class="alerts-hero glass-panel">
          <div class="hero-left">
            <h2>{{ $t('prepare.agencyAlerts.title') }}</h2>
            <span class="hero-meta">{{ $t('prepare.agencyAlerts.subtitle') }}</span>
          </div>
        </div>

        <div
          v-if="!recipientsLoading && whatsappRecipients.length === 0 && emailRecipients.length === 0"
          class="no-recipients-banner glass-panel"
        >
          <span class="no-recipients-icon">⚙️</span>
          <div class="no-recipients-text">
            <strong>{{ $t('prepare.agencyAlerts.noRecipientsTitle') }}</strong>
            <span>{{ $t('prepare.agencyAlerts.noRecipientsDesc') }}</span>
          </div>
          <RouterLink to="/settings" class="no-recipients-cta">{{ $t('prepare.agencyAlerts.goToSettings') }}</RouterLink>
        </div>

        <div class="master-detail">
          <!-- Always-visible, worst-first city list: scan every city's status
               at a glance and jump straight to one with a single click - no
               dropdown to open/scroll/close per city. -->
          <div class="city-rail-wrap glass-panel">
            <input
              v-model="citySearch"
              type="search"
              class="rail-search"
              :placeholder="$t('prepare.cityRail.searchPlaceholder')"
              :aria-label="$t('prepare.cityRail.searchAriaLabel')"
            />
            <nav ref="cityRailEl" class="city-rail" :aria-label="$t('prepare.cityRail.railAriaLabel')">
              <button
                v-for="city in filteredCities"
                :key="cityKey(city)"
                type="button"
                class="rail-item"
                :class="[worstRisk(city).toLowerCase(), { active: cityKey(city) === selectedKey }]"
                @click="selectedKey = cityKey(city)"
              >
                <span class="rail-dot"></span>
                <span class="rail-text">
                  <span class="rail-name">{{ city.city }}</span>
                  <span class="rail-country">{{ getCountryName(city.country) }}</span>
                </span>
                <span class="rail-risk">{{ worstRisk(city) }}</span>
              </button>
              <p v-if="filteredCities.length === 0" class="rail-empty">{{ $t('prepare.cityRail.noMatch') }} "{{ citySearch }}"</p>
            </nav>
          </div>

          <div class="detail-panel">
            <div v-if="alertsLoading" class="empty-state glass-panel tactical-loading-container actions-loading">
              <div class="radar-ping-ring small">
                <span class="radar-dot"></span>
              </div>
              <div class="loading-telemetry-text">
                <strong class="cycling-step-text">{{ $t('prepare.agencyAlerts.drafting') }} {{ selectedCity?.city }}...</strong>
              </div>
            </div>

            <div v-else-if="alertsError" class="empty-state glass-panel">
              <div class="empty-icon">⚠️</div>
              <h3>{{ $t('prepare.agencyAlerts.unableToCreateTitle') }}</h3>
              <p>{{ alertsError }}</p>
            </div>

            <div v-else-if="alertsPlan.is_fallback" class="empty-state glass-panel">

              <div class="empty-icon">⚠️</div>

              <p>AI analysis is unavailable right now. No alerts are shown.</p>

            </div>

            <template v-else-if="alertsPlan">
              <div class="risk-context glass-panel" :class="selectedToneClass">
                <span class="context-icon">{{ selectedToneIcon }}</span>
                <span class="context-text">{{ alertsPlan.risk_context }}</span>
                <button
                  v-if="worstDayConfidence"
                  type="button"
                  class="confidence-badge"
                  :class="confidenceClass(worstDayConfidence.confidence_pct)"
                  :aria-expanded="confidenceDetailExpanded"
                  @click="confidenceDetailExpanded = !confidenceDetailExpanded"
                >{{ worstDayConfidence.confidence_pct.toFixed(0) }}% {{ $t('prepare.timeline.agreement') }} <span class="info-hint" aria-hidden="true">{{ confidenceDetailExpanded ? '▲' : 'ⓘ' }}</span></button>
                <span class="source-badge" :class="sourceBadgeClass" :title="sourceLabel">{{ sourceLabelSimple }}</span>
              </div>

              <p v-if="worstDayConfidence && confidenceDetailExpanded" class="confidence-detail glass-panel">{{ confidenceTooltip }}</p>

              <div v-if="showLowConfidenceWarning" class="low-confidence-warning glass-panel">
                {{ $t('prepare.agencyAlerts.lowConfidenceWarning') }}
              </div>

              <!-- Audience tabs: switch which single audience's template is shown,
                   since each is written in a different voice for a different reader. -->
              <div class="audience-tabs">
                <div class="helper-text-above-tabs">{{ $t('prepare.agencyAlerts.selectRecipientGroup') }}</div>
                <button
                  v-for="aud in alertsPlan.alerts"
                  :key="aud.audience"
                  type="button"
                  class="audience-tab"
                  :class="{ active: selectedAudience === aud.audience }"
                  @click="selectedAudience = aud.audience"
                >
                  <span class="audience-icon">{{ audienceIcon(aud.audience) }}</span>
                  {{ audienceLabel(aud.audience) }}
                </button>
              </div>

              <div v-if="selectedAlert" class="alert-card glass-panel">
                <div class="alert-top">
                  <span class="channel-chip">{{ selectedAlert.channel }}</span>
                  <div class="alert-top-actions">
                    <button type="button" class="copy-btn" :class="{ copied: justCopied }" @click="copyMessage(selectedAlert)">
                      {{ justCopied ? '✓' : $t('prepare.agencyAlerts.copyMessage') }}
                    </button>
                    <template v-if="isWhatsAppEnabled">
                      <template v-if="whatsappRecipients.length > 0">
                        <div class="helper-text-recipient">{{ $t('prepare.agencyAlerts.chooseRecipient') }}</div>
                        <select v-model="selectedRecipientPhone" class="recipient-select" :aria-label="$t('prepare.agencyAlerts.whatsappRecipientAriaLabel')">
                          <option value="" disabled selected>{{ $t('prepare.agencyAlerts.selectRecipient') }}</option>
                          <option v-for="r in whatsappRecipients" :key="r.phone_number" :value="r.phone_number">
                            {{ r.label }}
                          </option>
                        </select>
                        <button
                          type="button"
                          class="send-whatsapp-btn"
                          :disabled="sendingWhatsApp"
                          @click="sendViaWhatsApp(selectedAlert)"
                        >
                          {{ sendingWhatsApp ? $t('prepare.agencyAlerts.sending') : $t('prepare.agencyAlerts.sendWhatsApp') }}
                        </button>
                      </template>
                      <RouterLink v-else-if="!recipientsLoading" to="/settings" class="configure-recipients-link">
                        {{ $t('prepare.agencyAlerts.addWhatsAppSettings') }}
                      </RouterLink>
                    </template>
                    <template v-if="emailRecipients.length > 0">
                      <div class="helper-text-recipient">{{ $t('prepare.agencyAlerts.chooseRecipient') }}</div>
                      <select v-model="selectedRecipientEmail" class="recipient-select" :aria-label="$t('prepare.agencyAlerts.emailRecipientAriaLabel')">
                        <option value="" disabled selected>{{ $t('prepare.agencyAlerts.selectRecipient') }}</option>
                        <option v-for="r in emailRecipients" :key="r.email" :value="r.email">
                          {{ r.label }}
                        </option>
                      </select>
                      <button
                        type="button"
                        class="send-email-btn"
                        :disabled="sendingEmail"
                        @click="sendViaEmail(selectedAlert)"
                      >
                        {{ sendingEmail ? $t('prepare.agencyAlerts.sending') : $t('prepare.agencyAlerts.sendEmail') }}
                      </button>
                    </template>
                    <RouterLink v-else-if="!recipientsLoading" to="/settings" class="configure-recipients-link">
                      {{ $t('prepare.agencyAlerts.addEmailSettings') }}
                    </RouterLink>
                  </div>
                </div>
                <h3 class="alert-headline">{{ selectedAlert.headline }}</h3>
                <p class="alert-message">{{ selectedAlert.message }}</p>
                <p class="alert-tone-rationale">
                  <span class="rationale-label">Why this message style was chosen:</span> {{ selectedAlert.tone_rationale }}
                </p>
                <p v-if="sendResult" class="send-result" :class="sendResult.success ? 'success' : 'error'">
                  <span v-if="sendResult.success && sendResult.detail === 'copy'">✓ Message copied to clipboard</span>
                  <span v-else-if="sendResult.success">✅ {{ sendResult.detail }}</span>
                  <span v-else>⚠️ {{ sendResult.detail }}</span>
                </p>
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
import { RouterLink, useRoute } from 'vue-router'
import Header from '@/components/organisms/Header.vue'
import { useMockMode } from '@/composables/useMockMode'
import { useWhatsApp } from '@/composables/useWhatsApp'
import { usePrepareForecastStore, type PrepareCityForecast } from '@/stores'
import { getCountryName } from '@/utils/countries'
// Shared with every other PREPARE screen - see usePrepareLookups.ts for why
// that moved to one shared copy.
import { RISK_RANK, cityKey, useCityRailFilter, worstRisk } from '@/composables/usePrepareLookups'

type CityForecast = PrepareCityForecast

interface AgencyAlert {
  audience: string
  channel: string
  headline: string
  message: string
  tone_rationale: string
}

interface AlertsPlan {
  risk_context: string
  alerts: AgencyAlert[]
  ai_available?: boolean
  is_fallback?: boolean
  is_mock_demo?: boolean
}

const { fetchWithMockMode } = useMockMode()
const { isWhatsAppEnabled } = useWhatsApp()

// Shared across all 4 PREPARE pages - fetched once, reused on tab switches
// instead of each page re-fetching all ~40 cities independently (see
// stores/index.ts for why this used to make every page load take minutes).
const prepareForecastStore = usePrepareForecastStore()
const { cities, loading, error } = storeToRefs(prepareForecastStore)
const selectedKey = ref('')
const route = useRoute()

const alertsPlan = ref<AlertsPlan | null>(null)
const alertsLoading = ref(false)
const alertsError = ref('')
const alertsSource = ref('')
const selectedAudience = ref('')
const justCopied = ref(false)

const AUDIENCE_META: Record<string, { label: string; icon: string }> = {
  FARMERS: { label: 'Farmers', icon: '🌾' },
  HOSPITALS: { label: 'Hospitals', icon: '🏥' },
  NGOS: { label: 'NGOs', icon: '🤝' },
  MUNICIPAL_CORPS: { label: 'Municipal Corps', icon: '🏛️' },
}
const audienceLabel = (aud: string) => AUDIENCE_META[aud]?.label || aud
const audienceIcon = (aud: string) => AUDIENCE_META[aud]?.icon || '📨'

const sortedCities = computed(() => {
  return [...cities.value].sort((a, b) => RISK_RANK[worstRisk(b)] - RISK_RANK[worstRisk(a)])
})

const { citySearch, cityRailEl, filteredCities, scrollActiveIntoView } = useCityRailFilter(sortedCities)

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

// the city's worst forecast day. If multiple days tie for worst risk_level,
// surface the one with the LOWEST agreement - the most conservative read,
// since that's the one most likely to be a brief spike rather than a
// sustained risk worth alerting agencies over.
const worstDayConfidence = computed(() => {
  const city = selectedCity.value
  if (!city || city.daily.length === 0) return null
  const worstRank = city.daily.reduce((max, day) => Math.max(max, RISK_RANK[day.risk_level] ?? 0), 0)
  const worstDays = city.daily.filter(day => (RISK_RANK[day.risk_level] ?? 0) === worstRank)
  if (worstRank === 0 || worstDays.length === 0) return null
  return worstDays.reduce((lowest, day) => (day.confidence_pct < lowest.confidence_pct ? day : lowest), worstDays[0])
})

const confidenceClass = (pct: number): string => {
  if (pct >= 70) return 'confidence-high'
  if (pct >= 40) return 'confidence-medium'
  return 'confidence-low'
}

// Whether the confidence-badge explanation is expanded. A hover-only
// `:title` doesn't show on touch devices or in a recording, and the old
// "i" icon was marked aria-hidden so assistive tech skipped it entirely -
// this makes the full explanation a real, persistent, keyboard/touch-
// reachable toggle instead (same fix already applied in RiskTimeline).
const confidenceDetailExpanded = ref(false)

const confidenceTooltip = computed(() => {
  const day = worstDayConfidence.value
  if (!day) return ''
  return `Reliability of this risk level: ${day.confidence_pct.toFixed(0)}% of forecast data agreed on this risk level.`
})

const showLowConfidenceWarning = computed(() => {
  const day = worstDayConfidence.value
  return !!day && !day.alert_recommended
})

const sourceLabel = computed(() => alertsSource.value || '')
const sourceBadgeClass = computed(() => {
  if (alertsPlan.value?.is_mock_demo) return 'mock'
  if (alertsPlan.value?.is_fallback) return 'fallback'
  return 'live'
})

// The backend's own source string ("Gemini 2.5 Flash via Vertex AI") is
// accurate but reads as engineering detail to someone who isn't - this
// keeps that full string available on hover/title while the badge itself
// says something anyone can read at a glance.
const sourceLabelSimple = computed(() => {
  switch (sourceBadgeClass.value) {
    case 'mock': return 'Demo data'
    case 'fallback': return 'AI unavailable'
    default: return 'AI-drafted'
  }
})

const selectedAlert = computed<AgencyAlert | null>(() => {
  return alertsPlan.value?.alerts.find(a => a.audience === selectedAudience.value) || alertsPlan.value?.alerts[0] || null
})

// Deterministic location/date header prepended to every outgoing send
// (WhatsApp and email, below) - independent of whatever the AI-drafted
// message text says, so a recipient always gets the place and date even
// if the model's prose happens to omit it. Built from the same city/day
// data already on screen, not a second guess.
const locationLine = computed(() => {
  const city = selectedCity.value
  const day = worstDayConfidence.value
  if (!city) return ''
  const place = `📍 ${city.city}, ${getCountryName(city.country)}`
  const when = day?.date ? ` — ${day.date}` : ''
  return `${place}${when}\n\n`
})

const copyMessage = async (alert: AgencyAlert) => {
  try {
    await navigator.clipboard.writeText(alert.message)
    justCopied.value = true
    sendResult.value = { success: true, detail: 'copy' }
    setTimeout(() => { 
      justCopied.value = false
      sendResult.value = null
    }, 1800)
  } catch {
    // Clipboard API can be unavailable (older browsers, insecure context) -
    // fail silently rather than block the user; the message is still on screen to select manually.
  }
}

const apiHost = () => import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)

// WhatsApp send (via WAHA, backend/services/whatsapp.py) - manual only: the
// operator reviews the AI-drafted text on screen, picks one of a small,
// pre-approved demo recipient list, and clicks Send. Deliberately not a
// free-text phone number field - the backend only accepts the same
// pre-approved list (see WhatsAppService's docstring for why).
interface WhatsAppRecipient {
  label: string
  phone_number: string
}

const whatsappRecipients = ref<WhatsAppRecipient[]>([])
const selectedRecipientPhone = ref('')
const sendingWhatsApp = ref(false)
const sendResult = ref<{ success: boolean; detail: string } | null>(null)

const fetchWhatsAppRecipients = async () => {
  if (!isWhatsAppEnabled.value) return
  try {
    const host = apiHost()
    const response = await fetchWithMockMode(`${host}/api/v1/prepare/alerts/recipients`)
    if (!response.ok) return
    const json = await response.json()
    whatsappRecipients.value = json.recipients || []
    if (whatsappRecipients.value.length > 0) {
      selectedRecipientPhone.value = whatsappRecipients.value[0].phone_number
    }
  } catch {
    // Non-critical - WhatsApp send controls just stay hidden if this fails.
  }
}

const sendViaWhatsApp = async (alert: AgencyAlert) => {
  if (!isWhatsAppEnabled.value || !selectedRecipientPhone.value || sendingWhatsApp.value) return

  sendingWhatsApp.value = true
  sendResult.value = null

  try {
    const host = apiHost()
    const response = await fetchWithMockMode(`${host}/api/v1/prepare/alerts/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        phone_number: selectedRecipientPhone.value,
        // Headline + body, exactly as shown on screen - this route sends
        // verbatim what the operator reviewed, never regenerates it. The
        // location line is prepended deterministically here rather than
        // trusting the AI-drafted text to always restate the city - the
        // prompt now directs it to, but a recipient must never get an
        // alert with no place name just because the model's prose skipped it.
        message: `${locationLine.value}${alert.headline}\n\n${alert.message}`,
      }),
    })

    const json = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new Error(json.detail || `Backend returned ${response.status}`)
    }

    sendResult.value = { success: true, detail: json.detail || 'Sent.' }
  } catch (e) {
    sendResult.value = {
      success: false,
      detail: e instanceof Error ? e.message : 'Unknown error sending WhatsApp message',
    }
  } finally {
    sendingWhatsApp.value = false
  }
}

// Email send (via Resend, backend/services/notifications.py) - same
// manual, pre-approved-recipient-only pattern as WhatsApp above, just a
// separate EMAIL_ALERT_RECIPIENTS list so testing this can never
// accidentally email RESPONSE phase's real incident recipient list.
interface EmailRecipient {
  label: string
  email: string
}

const emailRecipients = ref<EmailRecipient[]>([])
const selectedRecipientEmail = ref('')
const sendingEmail = ref(false)

const fetchEmailRecipients = async () => {
  try {
    const host = apiHost()
    const response = await fetchWithMockMode(`${host}/api/v1/prepare/alerts/email-recipients`)
    if (!response.ok) return
    const json = await response.json()
    emailRecipients.value = json.recipients || []
    if (emailRecipients.value.length > 0) {
      selectedRecipientEmail.value = emailRecipients.value[0].email
    }
  } catch {
    // Non-critical - email send controls just stay hidden if this fails.
  }
}

const sendViaEmail = async (alert: AgencyAlert) => {
  if (!selectedRecipientEmail.value || sendingEmail.value) return

  sendingEmail.value = true
  sendResult.value = null

  try {
    const host = apiHost()
    const response = await fetchWithMockMode(`${host}/api/v1/prepare/alerts/send-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: selectedRecipientEmail.value,
        subject: alert.headline,
        // Exactly as shown on screen - this route sends verbatim what the
        // operator reviewed, never regenerates it. Same deterministic
        // location header as the WhatsApp send above.
        message: `${locationLine.value}${alert.message}`,
      }),
    })

    const json = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new Error(json.detail || `Backend returned ${response.status}`)
    }

    sendResult.value = { success: true, detail: json.detail || 'Sent.' }
  } catch (e) {
    sendResult.value = {
      success: false,
      detail: e instanceof Error ? e.message : 'Unknown error sending email',
    }
  } finally {
    sendingEmail.value = false
  }
}

// Clear a stale send result when switching to a different alert - a "Sent
// to X" banner from the Farmers alert shouldn't linger once the operator
// has moved on to Hospitals.
watch([selectedAudience, selectedKey], () => {
  sendResult.value = null
})

const fetchAlertsForSelectedCity = async () => {
  const city = selectedCity.value
  if (!city) return

  alertsLoading.value = true
  alertsError.value = ''
  alertsPlan.value = null

  try {
    const host = apiHost()
    const params = new URLSearchParams({ city: city.city, country: city.country })
    const response = await fetchWithMockMode(`${host}/api/v1/prepare/alerts?${params.toString()}`)

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }

    const json = await response.json()
    alertsPlan.value = json.data
    alertsSource.value = json.source || ''
    if (alertsPlan.value?.alerts?.length) {
      selectedAudience.value = alertsPlan.value.alerts[0].audience
    }
  } catch (e) {
    alertsError.value = e instanceof Error ? e.message : 'Unknown error generating alert templates'
  } finally {
    alertsLoading.value = false
  }
}

const recipientsLoading = ref(true)

// Arriving with ?city=Chennai&country=IN (e.g. the "Draft agency alert"
// link on Risk Timeline) selects that exact city instead of always falling
// back to the globally-worst one - mirrors RiskTimeline's own
// selectFromQuery so every PREPARE screen honors the same deep link.
const selectFromQuery = (): boolean => {
  const qCity = route.query.city
  const qCountry = route.query.country
  if (typeof qCity !== 'string' || typeof qCountry !== 'string') return false
  const match = cities.value.find(c => c.city === qCity && c.country === qCountry)
  if (!match) return false
  selectedKey.value = cityKey(match)
  return true
}

// Falls back to whatever city/country the operator last looked at on any
// PREPARE screen - used when there's no query string to go on, e.g.
// arriving via the Header's plain tab strip rather than an in-page link
// that forwards ?city=&country=.
const selectFromStore = (): boolean => {
  const { selectedCity: storedCity, selectedCountry: storedCountry } = prepareForecastStore
  if (!storedCity || !storedCountry) return false
  const match = cities.value.find(c => c.city === storedCity && c.country === storedCountry)
  if (!match) return false
  selectedKey.value = cityKey(match)
  return true
}

onMounted(async () => {
  Promise.allSettled([fetchWhatsAppRecipients(), fetchEmailRecipients()]).finally(() => {
    recipientsLoading.value = false
  })

  // If another PREPARE page already loaded fresh forecast data, this
  // resolves immediately and the watch(cities, ...) below picks the
  // default selection from what's already there.
  await prepareForecastStore.ensureLoaded(fetchWithMockMode)
  if (cities.value.length > 0 && !selectedCity.value) {
    if (!selectFromQuery() && !selectFromStore()) {
      selectedKey.value = cityKey(sortedCities.value[0])
    }
  }
  scrollActiveIntoView()
})

watch(cities, (newCities) => {
  if (newCities.length > 0 && !selectedCity.value) {
    if (!selectFromQuery() && !selectFromStore()) {
      selectedKey.value = cityKey(sortedCities.value[0])
    }
  }
})

watch(selectedKey, () => {
  if (selectedCity.value) fetchAlertsForSelectedCity()
  confidenceDetailExpanded.value = false
  scrollActiveIntoView()
})

// Keep the shared store in sync so the next PREPARE screen the operator
// opens (via the Header tabs) sees the same city, not its own default.
watch(selectedCity, (city) => {
  if (city) prepareForecastStore.setSelectedCity(city.city, city.country)
})
</script>

<style scoped>
.alerts-screen {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  padding: 16px;
  gap: 16px;
  overflow: hidden;
}

.alerts-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
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

.alerts-hero {
  padding: 18px 24px;
  background: var(--accent-cyan-soft);
}

.hero-left h2 {
  margin: 0 0 4px 0;
  font-size: 20px;
  color: var(--accent-cyan);
}

.hero-meta {
  font-size: 12px;
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

.city-rail-wrap {
  flex: 0 0 260px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
}

.rail-search {
  flex-shrink: 0;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  font-size: 13px;
  outline: none;
}

.rail-search::placeholder {
  color: var(--text-secondary);
}

.rail-search:focus {
  border-color: var(--accent-cyan, #22d3ee);
}

.rail-empty {
  font-size: 12px;
  color: var(--text-secondary);
  padding: 8px 4px;
  margin: 0;
}

.city-rail {
  display: flex;
  flex-direction: column;
  gap: 4px;
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

/* Now a real <button> (was a plain <span> with a hover-only :title) so the
   full confidence explanation is reachable on touch, in a recording, and
   by keyboard/screen-reader users - not just on mouse hover. */
.confidence-badge {
  font: inherit;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 3px 8px;
  border: none;
  border-radius: 999px;
  white-space: nowrap;
  cursor: pointer;
}

.confidence-badge:focus-visible {
  outline: 2px solid var(--accent-cyan, #22d3ee);
  outline-offset: 2px;
}

.confidence-badge .info-hint {
  font-size: 9px;
  opacity: 0.75;
}

.confidence-detail {
  margin: -4px 0 0;
  padding: 10px 14px;
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-secondary);
}

.confidence-badge.confidence-high {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.12);
}

.confidence-badge.confidence-medium {
  color: #eab308;
  background: rgba(234, 179, 8, 0.12);
}

.confidence-badge.confidence-low {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.12);
}

.low-confidence-warning {
  padding: 10px 16px;
  font-size: 12px;
  line-height: 1.5;
  color: #eab308;
  background: rgba(234, 179, 8, 0.08);
  border-left: 3px solid #eab308;
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

.audience-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  flex-direction: column;
}

.helper-text-above-tabs {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: -4px;
}

.audience-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.audience-tab.active {
  border-color: rgba(56, 189, 248, 0.4);
  background: rgba(56, 189, 248, 0.12);
  color: #38bdf8;
}

.audience-icon {
  font-size: 14px;
}

.alert-card {
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.alert-top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.channel-chip {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 3px 9px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
}

.copy-btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 200ms ease;
}

.copy-btn:hover {
  background: rgba(255, 255, 255, 0.14);
}

.copy-btn.copied {
  border-color: rgba(34, 197, 94, 0.5);
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.recipient-select {
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.helper-text-recipient {
  font-size: 12px;
  color: var(--text-secondary);
}

.no-recipients-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  margin-bottom: 16px;
  border: 1px solid var(--accent-cyan);
  background: var(--accent-cyan-soft);
}

.no-recipients-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.no-recipients-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.no-recipients-text strong {
  color: var(--text-primary);
  font-size: 13px;
}

.no-recipients-text span {
  color: var(--text-secondary);
  font-size: 12px;
}

.no-recipients-cta {
  flex-shrink: 0;
  padding: 8px 14px;
  border-radius: 6px;
  border: 1px solid var(--accent-cyan);
  color: var(--accent-cyan);
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

.no-recipients-cta:hover {
  background: var(--accent-cyan-soft);
}

.configure-recipients-link {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px dashed var(--glass-border);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

.configure-recipients-link:hover {
  color: var(--accent-cyan);
  border-color: var(--accent-cyan);
}

.send-whatsapp-btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(37, 211, 102, 0.4);
  background: rgba(37, 211, 102, 0.12);
  color: #25d366;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.send-whatsapp-btn:hover:not(:disabled) {
  background: rgba(37, 211, 102, 0.2);
}

.send-whatsapp-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

.send-email-btn {
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid rgba(96, 165, 250, 0.4);
  background: rgba(96, 165, 250, 0.12);
  color: #60a5fa;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.send-email-btn:hover:not(:disabled) {
  background: rgba(96, 165, 250, 0.2);
}

.send-email-btn:disabled {
  opacity: 0.6;
  cursor: wait;
}

.send-result {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  padding: 8px 12px;
  border-radius: 6px;
}

.send-result.success {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.send-result.error {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.alert-headline {
  margin: 0;
  font-size: 17px;
  font-weight: 700;
}

.alert-message {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-line;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 14px;
}

.alert-tone-rationale {
  margin: 0;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.rationale-label {
  font-weight: 600;
  color: var(--text-primary);
}

/* Tactical Loading Animation (matches ForecastDashboard.vue / RiskTimeline.vue / PreparednessChecklist.vue) */
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

@media (max-width: 768px) {
  .master-detail {
    flex-direction: column;
  }

  .city-rail-wrap {
    flex: 0 0 auto;
    width: 100%;
  }

  .rail-search {
    width: 100%;
  }

  .city-rail {
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

  .alert-top-actions {
    flex-direction: column;
    width: 100%;
  }

  .recipient-select,
  .copy-btn,
  .send-whatsapp-btn,
  .send-email-btn,
  .configure-recipients-link {
    width: 100%;
  }

  .audience-tabs {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .helper-text-above-tabs {
    width: 100%;
  }

  .alert-card {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .alerts-screen {
    padding: 8px;
    gap: 8px;
  }

  .alerts-hero {
    padding: 14px 16px;
  }

  .alert-top-actions {
    flex-direction: column;
    width: 100%;
  }

  .recipient-select,
  .copy-btn,
  .send-whatsapp-btn,
  .send-email-btn,
  .configure-recipients-link {
    width: 100%;
  }
}
</style>
