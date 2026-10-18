<template>
  <div v-if="context" class="preparedness-context glass-panel">
    <div class="context-header">
      <h4>📋 Preparedness Context</h4>
      <span class="source-badge">From PREPARE</span>
    </div>

    <div class="context-grid">
      <div class="context-item">
        <span class="label">Location</span>
        <span class="value">{{ context.city }}, {{ context.country }}</span>
      </div>
      <div v-if="context.hazard_type" class="context-item">
        <span class="label">Hazard</span>
        <span class="value">{{ context.hazard_type }}</span>
      </div>
      <div v-if="context.risk_level" class="context-item">
        <span class="label">Risk Level</span>
        <span class="value risk" :class="context.risk_level.toLowerCase()">{{ context.risk_level }}</span>
      </div>
      <div class="context-item">
        <span class="label">Assessed At</span>
        <span class="value">{{ formatTime(context.assessment_at) }}</span>
      </div>
    </div>

    <div v-if="context.snapshot_json?.actions?.length" class="context-actions">
      <p class="actions-label">{{ context.snapshot_json.actions.length }} Preparedness Actions</p>
      <ul class="actions-list">
        <li v-for="(action, idx) in context.snapshot_json.actions.slice(0, 3)" :key="idx">
          ✓ {{ action }}
        </li>
        <li v-if="context.snapshot_json.actions.length > 3" class="more-actions">
          +{{ context.snapshot_json.actions.length - 3 }} more
        </li>
      </ul>
    </div>

    <div v-if="context.initiated_by" class="context-meta">
      <span class="meta-label">Initiated by</span>
      <span class="meta-value">{{ context.initiated_by }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const context = ref<any>(null)
const loading = ref(false)

const formatTime = (time: string) => {
  return new Date(time).toLocaleString()
}

const loadContext = async () => {
  const incidentId = route.params.incidentId
  if (!incidentId) return

  loading.value = true
  try {
    const res = await axios.get(`/api/v1/incidents/${incidentId}/preparedness-context`)
    context.value = res.data
  } catch (e) {
    console.error('Failed to load preparedness context:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadContext()
})
</script>

<style scoped>
.preparedness-context {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border-radius: var(--radius-lg);
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
}

.context-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--glass-border);
}

.context-header h4 {
  margin: 0;
  color: var(--text-primary);
}

.source-badge {
  padding: 0.25rem 0.75rem;
  background: rgba(34, 211, 238, 0.15);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  color: var(--color-primary);
  font-weight: 600;
}

.context-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}

.context-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.value {
  font-size: 0.95rem;
  color: var(--text-primary);
  font-weight: 500;
}

.risk {
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm);
  background: rgba(34, 211, 238, 0.1);
  display: inline-block;
  width: fit-content;
}

.risk.critical {
  background: rgba(255, 107, 107, 0.1);
}

.context-actions {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--glass-border);
}

.actions-label {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.actions-list {
  margin: 0;
  padding-left: 1.5rem;
  list-style: none;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.actions-list li {
  padding: 0.25rem 0;
}

.more-actions {
  font-style: italic;
  color: var(--text-muted);
}

.context-meta {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--glass-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
}

.meta-label {
  color: var(--text-secondary);
  font-weight: 500;
}

.meta-value {
  color: var(--text-primary);
}
</style>
