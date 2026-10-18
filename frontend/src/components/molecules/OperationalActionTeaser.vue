<template>
  <div class="operational-teaser">
    <!-- Loading State -->
    <div v-if="isLoading" class="teaser-loading">
      <div class="loading-header">
        <span class="teaser-pulse-dot"></span>
        <label class="teaser-title">⚡ AI Processing</label>
      </div>
      <div class="loading-content">
        <div class="radar-mini">
          <span class="radar-dot"></span>
        </div>
        <div class="loading-messages">
          <span class="loading-text">Analyzing incident data...</span>
          <span class="loading-subtext">Generating response plan</span>
        </div>
      </div>
      <div class="loading-bar">
        <div class="loading-progress"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="teaser-error">
      <span class="error-icon">⚠</span>
      <span class="error-text">Unable to load AI insights</span>
    </div>

    <!-- AI unavailable: the backend returned its generic offline plan. Say so,
         instead of presenting its generic line as a Critical Action. -->
    <div v-else-if="aiPlan && aiPlan.is_fallback" class="teaser-empty">
      <span class="empty-icon">⚠</span>
      <span class="empty-text">AI analysis unavailable. Use standard protocols.</span>
    </div>
    <!-- Content State -->
    <div v-else-if="aiPlan && topAction" class="teaser-content">
      <!-- Header -->
      <div class="teaser-header">
        <span class="teaser-pulse-dot"></span>
        <label class="teaser-title">AI-recommended next step</label>
        <span class="review-tag">Evidence + review required</span>
      </div>

      <!-- Top Action Only -->
      <div class="teaser-action-card">
        <span class="action-num">01</span>
        <span class="action-text">{{ expanded ? topAction : shortAction }}</span>
        <button v-if="topAction.length > shortAction.length" class="show-more" @click="expanded = !expanded">{{ expanded ? 'Show less' : 'Show full reasoning' }}</button>
      </div>

      <!-- Each recommendation with the input that supports it, when the reasoning is expanded -->
      <div v-if="expanded && allActions.length" class="all-actions">
        <div v-for="(act, i) in allActions" :key="i" class="action-basis">
          <strong>{{ i + 1 }}. {{ act.text }}</strong>
          <span class="basis-line">Basis: {{ act.basis }}</span>
        </div>
      </div>

      <!-- Evidence behind the recommendation, shown with it -->
      <div v-if="evidence && evidence.length" class="evidence-box">
        <span class="evidence-title">Evidence</span>
        <ul class="evidence-list">
          <li v-for="(line, i) in evidence" :key="i">{{ line }}</li>
        </ul>
      </div>

      <!-- Show count of remaining actions if > 1 -->
      <div v-if="remainingCount > 0" class="remaining-badge">
        +{{ remainingCount }} more action{{ remainingCount !== 1 ? 's' : '' }}
      </div>

      <!-- Link to Full AI Insights -->
      <button class="view-full-btn" @click="navigateToInsights">
        Open incident brief →
      </button>
    </div>

    <!-- Empty State -->
    <div v-else class="teaser-empty">
      <span class="empty-icon">📋</span>
      <span class="empty-text">No AI analysis yet</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps<{
  aiPlan: any | null
  isLoading: boolean
  error: string | null | undefined
  incidentId: string
  evidence?: string[]
}>()

const emit = defineEmits<{
  navigateToInsights: []
}>()

const router = useRouter()

// Extract top action (first immediate action)
const topAction = computed(() => {
  return props.aiPlan?.immediate_actions?.[0] || null
})

// Count remaining actions
const expanded = ref(false)

// Every recommendation paired with the input the model cited for it.
const allActions = computed(() => {
  const actions: string[] = props.aiPlan?.immediate_actions || []
  const basis: string[] = props.aiPlan?.immediate_action_evidence || []
  return actions.map((text, i) => ({
    text,
    basis: basis[i] && !/no supporting input/i.test(basis[i]) ? basis[i] : 'not cited by the model. Check before acting.',
  }))
})
// Short summary for the panel; the full reasoning sits behind "Show full reasoning".
const shortAction = computed(() => {
  const t = topAction.value || ''
  if (t.length <= 140) return t
  return t.slice(0, 140).replace(/\s+\S*$/, '') + '…'
})

const remainingCount = computed(() => {
  const actions = props.aiPlan?.immediate_actions || []
  return Math.max(0, actions.length - 1)
})

// Navigate to Incident Detail and scroll to AI Insights tab
const navigateToInsights = () => {
  // Go straight to the incident's overview: that is where the recommended
  // actions and the report are. The separate AI tab repeated the same plan.
  router.push({
    name: 'IncidentDetail',
    params: { id: props.incidentId }
  })
  emit('navigateToInsights')
}
</script>

<style scoped>
.operational-teaser {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

/* Loading State */
.teaser-loading {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  background: linear-gradient(135deg, rgba(30, 58, 138, 0.4), var(--bg-overlay));
  border: 1px solid rgba(59, 130, 246, 0.4);
  border-radius: 8px;
  animation: loadingGlow 2s ease-in-out infinite;
}

@keyframes loadingGlow {
  0%, 100% {
    border-color: rgba(59, 130, 246, 0.3);
    background: linear-gradient(135deg, rgba(30, 58, 138, 0.3), var(--bg-overlay));
  }
  50% {
    border-color: rgba(59, 130, 246, 0.6);
    background: linear-gradient(135deg, rgba(30, 58, 138, 0.5), rgba(15, 23, 42, 0.9));
  }
}

.loading-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(59, 130, 246, 0.2);
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.radar-mini {
  position: relative;
  width: 24px;
  height: 24px;
  border: 2px solid rgba(59, 130, 246, 0.7);
  border-radius: 50%;
  flex-shrink: 0;
  animation: radarSpin 2s linear infinite;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}

.radar-dot {
  position: absolute;
  width: 6px;
  height: 6px;
  background: #3b82f6;
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.8);
}

.loading-messages {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.loading-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-cyan);
  letter-spacing: 0.5px;
}

.loading-subtext {
  font-size: 11px;
  color: var(--text-muted);
  font-style: italic;
}

.loading-bar {
  height: 3px;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 4px;
}

.loading-progress {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #0ea5e9, #3b82f6);
  background-size: 200% 100%;
  border-radius: 2px;
  animation: loadingBar 1.5s ease-in-out infinite;
}

@keyframes loadingBar {
  0% {
    transform: translateX(-100%);
  }
  50% {
    transform: translateX(100%);
  }
  100% {
    transform: translateX(-100%);
  }
}

@keyframes radarSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Error State */
.teaser-error {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  color: #f87171;
  font-size: 13px;
}

.error-icon {
  font-size: 16px;
}

/* Content State */
.teaser-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.teaser-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.teaser-pulse-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.teaser-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

/* Action Card */
.teaser-action-card {
  display: flex;
  gap: 8px;
  padding: 10px;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 6px;
  align-items: flex-start;
}

.action-num {
  font-family: ui-monospace, monospace;
  font-weight: 700;
  font-size: 13px;
  color: #ef4444;
  flex-shrink: 0;
  padding-top: 2px;
}

.evidence-box { display: flex; flex-direction: column; gap: 4px; padding: 8px 10px; border-radius: 6px; background: rgba(15,23,42,0.5); }
.evidence-title { font-size: 11px; font-weight: 700; letter-spacing: 0.04em; color: #94a3b8; text-transform: uppercase; }
.evidence-list { margin: 0; padding-left: 16px; font-size: 12px; color: #cbd5e1; display: flex; flex-direction: column; gap: 2px; }

.all-actions { display: flex; flex-direction: column; gap: 8px; }
.action-basis { display: flex; flex-direction: column; gap: 2px; font-size: 12px; color: #e2e8f0; }
.basis-line { color: #94a3b8; font-size: 11px; }

.show-more {
  margin-top: 4px;
  background: none;
  border: none;
  padding: 0;
  color: #7dd3fc;
  font-size: 12px;
  cursor: pointer;
}

.review-tag {
  display: inline-block;
  margin-left: 6px;
  font-size: 11px;
  color: #fde68a;
}

.action-text {
  font-size: 14px;
  line-height: 1.4;
  color: var(--text-secondary);
  word-break: break-word;
}

/* Remaining Badge */
.remaining-badge {
  display: inline-block;
  font-size: 11px;
  color: var(--text-secondary);
  background: rgba(71, 85, 105, 0.2);
  padding: 4px 8px;
  border-radius: 4px;
  text-align: center;
}

/* View Full Button */
.view-full-btn {
  padding: 8px 12px;
  background: var(--accent-cyan);
  border: none;
  border-radius: 6px;
  color: #04141a;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.view-full-btn:hover {
  background: #26c6da;
  transform: translateY(-1px);
}

.view-full-btn:active {
  transform: translateY(0);
}

/* Empty State */
.teaser-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 12px;
  color: var(--text-muted);
  text-align: center;
}

.empty-icon {
  font-size: 20px;
}

.empty-text {
  font-size: 12px;
}
</style>
