<template>
  <div class="preparedness-handoff glass-panel">
    <h3 class="panel-title">🔗 Link to Response</h3>
    
    <div v-if="!selectedCity" class="empty-state">
      <p>Select a city in Risk Timeline to initiate response review.</p>
    </div>

    <template v-else>
      <!-- City Summary -->
      <div class="city-summary">
        <span class="summary-item">
          <strong>{{ selectedCity }}</strong>, {{ selectedCountry }}
        </span>
        <span v-if="hazardType" class="summary-item">{{ hazardType }}</span>
        <span v-if="riskLevel" class="summary-item risk-badge" :class="riskLevel.toLowerCase()">
          {{ riskLevel }}
        </span>
      </div>

      <!-- Incident Selector -->
      <div class="form-group">
        <label for="incident-select">Select Incident</label>
        <select
          id="incident-select"
          v-model="selectedIncidentId"
          class="form-input"
          :disabled="loadingIncidents || loading"
        >
          <option value="">-- Choose an incident --</option>
          <option v-for="inc in incidents" :key="inc.id" :value="inc.id">
            {{ inc.event_type }} @ {{ inc.location_name || `(${inc.latitude}, ${inc.longitude})` }}
          </option>
        </select>
        <p v-if="incidents.length === 0 && !loadingIncidents" class="hint">No active incidents found.</p>
      </div>

      <!-- Officer Name -->
      <div class="form-group">
        <label for="officer-name">Officer Name</label>
        <input
          id="officer-name"
          v-model="officerName"
          type="text"
          class="form-input"
          placeholder="Your name"
          :disabled="loading"
        />
      </div>

      <!-- Compatibility Warning -->
      <div v-if="selectedIncident && hazardMismatch" class="warning-box">
        ⚠️ Hazard mismatch: Forecast is {{ hazardType }} but incident is {{ selectedIncident.event_type }}.
        <label class="checkbox">
          <input v-model="confirmMismatch" type="checkbox" />
          I confirm this is the correct incident
        </label>
      </div>

      <!-- Submit Button -->
      <button
        class="handoff-button"
        :disabled="!canSubmit || loading"
        @click="submitHandoff"
      >
        <span v-if="loading">⏳ Linking...</span>
        <span v-else>→ Link to Incident & Open Response</span>
      </button>

      <!-- Messages -->
      <p v-if="error" class="error-msg">{{ error }}</p>
      <p v-if="success" class="success-msg">✅ Context linked! Opening Response...</p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const props = defineProps<{
  city?: string
  country?: string
  hazard?: string
  risk?: string
}>()

const router = useRouter()

// State
const selectedIncidentId = ref<number | ''>('')
const officerName = ref('')
const loading = ref(false)
const loadingIncidents = ref(false)
const error = ref('')
const success = ref(false)
const confirmMismatch = ref(false)
const incidents = ref<any[]>([])

const selectedCity = computed(() => props.city)
const selectedCountry = computed(() => props.country)
const hazardType = computed(() => props.hazard)
const riskLevel = computed(() => props.risk)

const selectedIncident = computed(() =>
  incidents.value.find(i => i.id === selectedIncidentId.value)
)

const hazardMismatch = computed(() => {
  if (!selectedIncident.value || !hazardType.value) return false
  return selectedIncident.value.event_type !== hazardType.value
})

const canSubmit = computed(() => {
  if (!selectedIncidentId.value || !officerName.value) return false
  if (hazardMismatch.value && !confirmMismatch.value) return false
  return true
})

// Load incidents
const loadIncidents = async () => {
  loadingIncidents.value = true
  try {
    const res = await axios.get('/api/v1/incidents', { params: { status: 'confirmed,detected' } })
    incidents.value = res.data.incidents || []
  } catch (e) {
    console.error('Failed to load incidents:', e)
    incidents.value = []
  } finally {
    loadingIncidents.value = false
  }
}

// Submit handoff
const submitHandoff = async () => {
  if (!selectedIncidentId.value) return

  loading.value = true
  error.value = ''
  success.value = false

  try {
    await axios.post(
      `/api/v1/incidents/${selectedIncidentId.value}/preparedness-context`,
      {
        city: selectedCity.value,
        country: selectedCountry.value,
        hazard_type: hazardType.value,
        risk_level: riskLevel.value,
        assessment_at: new Date().toISOString(),
        snapshot_json: { /* checklist snapshot */ },
        source_metadata_json: { /* source info */ },
        initiated_by: officerName.value,
        compatibility_override_reason: hazardMismatch.value ? 'User confirmed mismatch' : null,
      }
    )

    success.value = true
    setTimeout(() => {
      router.push({
        name: 'IncidentDetail',
        params: { incidentId: selectedIncidentId.value },
        query: { tab: 'response' },
      })
    }, 500)
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Failed to link preparedness context'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadIncidents()
})

watch(() => props.city, () => {
  selectedIncidentId.value = ''
  confirmMismatch.value = false
})
</script>

<style scoped>
.preparedness-handoff {
  padding: 1.5rem;
  border-radius: var(--radius-lg);
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  margin-top: 1rem;
}

.panel-title {
  margin-top: 0;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.empty-state {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.city-summary {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.summary-item {
  padding: 0.5rem 0.75rem;
  background: rgba(34, 211, 238, 0.1);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  color: var(--text-primary);
}

.risk-badge {
  background: rgba(34, 211, 238, 0.2) !important;
  font-weight: 600;
}

.risk-badge.critical {
  background: rgba(255, 107, 107, 0.2) !important;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-primary);
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  background: var(--bg-panel);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: 0.875rem;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.1);
}

.warning-box {
  padding: 0.75rem;
  background: rgba(245, 158, 11, 0.1);
  border-left: 3px solid rgb(245, 158, 11);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
  cursor: pointer;
}

.checkbox input {
  cursor: pointer;
}

.handoff-button {
  width: 100%;
  padding: 0.75rem;
  background: var(--color-primary);
  color: var(--bg-primary);
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  cursor: pointer;
  transition: opacity 250ms;
}

.handoff-button:hover:not(:disabled) {
  opacity: 0.9;
}

.handoff-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-msg,
.success-msg {
  margin-top: 1rem;
  font-size: 0.875rem;
}

.error-msg {
  color: rgb(255, 107, 107);
}

.success-msg {
  color: rgb(46, 204, 113);
}

.hint {
  margin: 0;
  font-size: 0.8rem;
  color: var(--text-muted);
}
</style>
