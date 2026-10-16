<template>
  <div class="settings-screen">
    <Header />

    <div class="settings-container">
      <div class="settings-hero glass-panel">
        <div class="hero-left">
          <h2>{{ $t('settings.title') }}</h2>
          <span class="hero-meta">{{ $t('settings.subtitle') }}</span>
        </div>
      </div>

      <div class="recipient-grid">
        <!-- WhatsApp recipients -->
        <section class="glass-panel recipient-card">
          <div class="card-heading">
            <span class="card-icon">💬</span>
            <h3>{{ $t('settings.whatsappTitle') }}</h3>
          </div>
          <p class="card-desc">
            {{ $t('settings.whatsappDesc') }}
          </p>
          <p class="card-note">
            ℹ️ {{ $t('settings.whatsappNote') }}
          </p>

          <div v-if="whatsappLoading" class="recipient-status">{{ $t('settings.loading') }}</div>
          <div v-else-if="whatsappRecipients.length === 0" class="recipient-status empty">
            {{ $t('settings.noWhatsapp') }}
          </div>
          <ul v-else class="recipient-list">
            <li v-for="r in whatsappRecipients" :key="r.id" class="recipient-row">
              <div class="recipient-info">
                <strong>{{ r.label }}</strong>
                <span class="recipient-value">{{ r.value }}</span>
              </div>
              <button
                type="button"
                class="remove-btn"
                :disabled="removingId === r.id"
                @click="removeRecipient('whatsapp', r.id)"
                aria-label="Remove recipient"
              >
                {{ removingId === r.id ? '…' : '✕' }}
              </button>
            </li>
          </ul>

          <form class="add-form" @submit.prevent="addRecipient('whatsapp')">
            <input
              v-model="whatsappForm.label"
              type="text"
              :placeholder="$t('settings.labelPlaceholder')"
              class="form-input"
            />
            <input
              v-model="whatsappForm.value"
              type="text"
              :placeholder="$t('settings.phonePlaceholder')"
              class="form-input"
            />
            <button type="submit" class="add-btn" :disabled="addingWhatsapp">
              {{ addingWhatsapp ? $t('settings.adding') : $t('settings.addBtn') }}
            </button>
          </form>
          <p v-if="whatsappFormError" class="form-error">{{ whatsappFormError }}</p>
        </section>

        <!-- Email recipients -->
        <section class="glass-panel recipient-card">
          <div class="card-heading">
            <span class="card-icon">✉️</span>
            <h3>{{ $t('settings.emailTitle') }}</h3>
          </div>
          <p class="card-desc">
            {{ $t('settings.emailDesc') }}
          </p>

          <div v-if="emailLoading" class="recipient-status">{{ $t('settings.loading') }}</div>
          <div v-else-if="emailRecipients.length === 0" class="recipient-status empty">
            {{ $t('settings.noEmail') }}
          </div>
          <ul v-else class="recipient-list">
            <li v-for="r in emailRecipients" :key="r.id" class="recipient-row">
              <div class="recipient-info">
                <strong>{{ r.label }}</strong>
                <span class="recipient-value">{{ r.value }}</span>
              </div>
              <button
                type="button"
                class="remove-btn"
                :disabled="removingId === r.id"
                @click="removeRecipient('email', r.id)"
                aria-label="Remove recipient"
              >
                {{ removingId === r.id ? '…' : '✕' }}
              </button>
            </li>
          </ul>

          <form class="add-form" @submit.prevent="addRecipient('email')">
            <input
              v-model="emailForm.label"
              type="text"
              :placeholder="$t('settings.labelPlaceholder')"
              class="form-input"
            />
            <input
              v-model="emailForm.value"
              type="email"
              :placeholder="$t('settings.emailPlaceholder')"
              class="form-input"
            />
            <button type="submit" class="add-btn" :disabled="addingEmail">
              {{ addingEmail ? $t('settings.adding') : $t('settings.addBtn') }}
            </button>
          </form>
          <p v-if="emailFormError" class="form-error">{{ emailFormError }}</p>
        </section>

        <!-- Critical Alert recipients (RESPONSE phase) -->
        <section class="glass-panel recipient-card">
          <div class="card-heading">
            <span class="card-icon">🚨</span>
            <h3>{{ $t('settings.criticalTitle') }}</h3>
          </div>
          <p class="card-desc">
            {{ $t('settings.criticalDesc') }}
          </p>

          <div v-if="criticalLoading" class="recipient-status">{{ $t('settings.loading') }}</div>
          <div v-else-if="criticalRecipients.length === 0" class="recipient-status empty">
            {{ $t('settings.noCritical') }}
          </div>
          <ul v-else class="recipient-list">
            <li v-for="r in criticalRecipients" :key="r.id" class="recipient-row">
              <div class="recipient-info">
                <strong>{{ r.label }}</strong>
                <span class="recipient-value">{{ r.value }}</span>
              </div>
              <button
                type="button"
                class="remove-btn"
                :disabled="removingId === r.id"
                @click="removeRecipient('critical_email', r.id)"
                aria-label="Remove recipient"
              >
                {{ removingId === r.id ? '…' : '✕' }}
              </button>
            </li>
          </ul>

          <form class="add-form" @submit.prevent="addRecipient('critical_email')">
            <input
              v-model="criticalForm.label"
              type="text"
              :placeholder="$t('settings.labelPlaceholder')"
              class="form-input"
            />
            <input
              v-model="criticalForm.value"
              type="email"
              :placeholder="$t('settings.emailPlaceholder')"
              class="form-input"
            />
            <button type="submit" class="add-btn" :disabled="addingCritical">
              {{ addingCritical ? $t('settings.adding') : $t('settings.addBtn') }}
            </button>
          </form>
          <p v-if="criticalFormError" class="form-error">{{ criticalFormError }}</p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import Header from '@/components/organisms/Header.vue'

interface Recipient {
  id: number
  label: string
  value: string
}

type Channel = 'whatsapp' | 'email' | 'critical_email'

const apiHost = () => import.meta.env.VITE_API_URL || (window.location.hostname === 'localhost' ? 'http://localhost:8000' : window.location.origin)

const whatsappRecipients = ref<Recipient[]>([])
const emailRecipients = ref<Recipient[]>([])
const criticalRecipients = ref<Recipient[]>([])
const whatsappLoading = ref(true)
const emailLoading = ref(true)
const criticalLoading = ref(true)
const addingWhatsapp = ref(false)
const addingEmail = ref(false)
const addingCritical = ref(false)
const removingId = ref<number | null>(null)
const whatsappFormError = ref('')
const emailFormError = ref('')
const criticalFormError = ref('')

const whatsappForm = reactive({ label: '', value: '' })
const emailForm = reactive({ label: '', value: '' })
const criticalForm = reactive({ label: '', value: '' })

// Per-channel wiring so add/remove/load below stay one small function each
// instead of a three-way branch repeated in every one of them.
const channelState: Record<Channel, {
  list: typeof whatsappRecipients
  loading: typeof whatsappLoading
  adding: typeof addingWhatsapp
  form: typeof whatsappForm
  formError: typeof whatsappFormError
}> = {
  whatsapp: { list: whatsappRecipients, loading: whatsappLoading, adding: addingWhatsapp, form: whatsappForm, formError: whatsappFormError },
  email: { list: emailRecipients, loading: emailLoading, adding: addingEmail, form: emailForm, formError: emailFormError },
  critical_email: { list: criticalRecipients, loading: criticalLoading, adding: addingCritical, form: criticalForm, formError: criticalFormError },
}

const fetchRecipients = async (channel: Channel) => {
  const host = apiHost()
  const response = await fetch(`${host}/api/v1/prepare/settings/recipients/${channel}`)
  if (!response.ok) throw new Error(`Backend returned ${response.status}`)
  const json = await response.json()
  return (json.recipients || []) as Recipient[]
}

const loadChannel = async (channel: Channel) => {
  const state = channelState[channel]
  state.loading.value = true
  try {
    state.list.value = await fetchRecipients(channel)
  } catch {
    // Non-critical - list just stays empty if this fails.
  } finally {
    state.loading.value = false
  }
}

const loadWhatsapp = () => loadChannel('whatsapp')
const loadEmail = () => loadChannel('email')
const loadCritical = () => loadChannel('critical_email')

const addRecipient = async (channel: Channel) => {
  const { form, formError: errorRef, adding: addingRef } = channelState[channel]

  errorRef.value = ''
  if (!form.label.trim() || !form.value.trim()) {
    errorRef.value = 'Both label and value are required.'
    return
  }

  addingRef.value = true
  try {
    const host = apiHost()
    const response = await fetch(`${host}/api/v1/prepare/settings/recipients/${channel}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ label: form.label.trim(), value: form.value.trim() }),
    })
    const json = await response.json().catch(() => ({}))
    if (!response.ok) {
      throw new Error(json.detail || `Backend returned ${response.status}`)
    }
    form.label = ''
    form.value = ''
    await loadChannel(channel)
  } catch (e) {
    errorRef.value = e instanceof Error ? e.message : 'Unknown error adding recipient'
  } finally {
    addingRef.value = false
  }
}

const removeRecipient = async (channel: Channel, id: number) => {
  removingId.value = id
  try {
    const host = apiHost()
    const response = await fetch(`${host}/api/v1/prepare/settings/recipients/${channel}/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error(`Backend returned ${response.status}`)
    channelState[channel].list.value = channelState[channel].list.value.filter(r => r.id !== id)
  } catch {
    // Leave the row in place - the operator can retry the remove.
  } finally {
    removingId.value = null
  }
}

onMounted(() => {
  loadWhatsapp()
  loadCritical()
  loadEmail()
})
</script>

<style scoped>
.settings-screen {
  min-height: 100vh;
  background: var(--bg-dark);
}

.settings-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px 20px 60px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.glass-panel {
  background: rgba(26, 31, 46, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.settings-hero {
  padding: 20px 24px;
  background: var(--accent-cyan-soft);
}

.hero-left h2 {
  margin: 0 0 4px;
  color: var(--accent-cyan);
  font-size: 22px;
}

.hero-meta {
  color: var(--text-secondary);
  font-size: 13px;
}

.recipient-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 20px;
}

.recipient-card {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.card-heading {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-heading h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 16px;
}

.card-icon {
  font-size: 18px;
}

.card-desc {
  margin: 0;
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
  line-height: 1.5;
}

.card-note {
  margin: 0;
  padding: 8px 10px;
  border-radius: 6px;
  background: rgba(56, 189, 248, 0.08);
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  line-height: 1.5;
}

.recipient-status {
  /* Was var(--text-muted) (#666666 in dark mode) - ~2.8:1 contrast against
     this panel's background, unreadable. Matched to the rgba(255,255,255,…)
     scale the rest of this file already uses (card-desc 0.75, card-note
     0.7, recipient-value 0.65) - this one got missed in that pass. */
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  padding: 8px 0;
}

.recipient-status.empty {
  font-style: italic;
}

.recipient-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recipient-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  background: var(--bg-subtle);
}

.recipient-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.recipient-info strong {
  color: rgba(255, 255, 255, 0.95);
  font-size: 13px;
}

.recipient-value {
  color: rgba(255, 255, 255, 0.65);
  font-size: 12px;
  overflow-wrap: anywhere;
}

.remove-btn {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  border: 1px solid var(--glass-border);
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
  cursor: pointer;
  font-size: 13px;
  line-height: 1;
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.remove-btn:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.22);
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.2);
}

.remove-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.remove-btn:disabled {
  opacity: 0.6;
  cursor: default;
}

.add-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--glass-border);
}

.form-input {
  flex: 1 1 140px;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-primary);
  font-size: 13px;
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
  opacity: 1;
}

.form-input:focus {
  outline: none;
  border-color: rgba(56, 189, 248, 0.8);
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
  background: rgba(255, 255, 255, 0.05);
}

.add-btn {
  padding: 8px 14px;
  border-radius: 6px;
  border: 1px solid rgba(56, 189, 248, 0.5);
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
}

.add-btn:hover:not(:disabled) {
  background: rgba(56, 189, 248, 0.3);
  box-shadow: 0 4px 12px rgba(56, 189, 248, 0.3);
  transform: translateY(-1px);
}

.add-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.add-btn:disabled {
  opacity: 0.6;
  cursor: default;
}

.form-error {
  margin: 0;
  color: #ef4444;
  font-size: 12px;
}
</style>
