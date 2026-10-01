<template>
  <div class="ai-insights">
    <h3>🤖 AI RECOMMENDED ACTIONS</h3>
    
    <div class="insights-list">
      <!-- Critical Actions -->
      <template v-if="criticalInsights.length">
        <div class="insight-section">
          <h4 class="section-title critical">🚨 CRITICAL (Immediate)</h4>
          <div v-for="insight in criticalInsights" :key="insight.id" class="insight-item">
            <div class="insight-action">{{ insight.action }}</div>
            <div class="insight-meta">
              {{ insight.estimatedAffected.toLocaleString() }} people
              {{ insight.timeUrgent }}
            </div>
            <button class="why-btn">
              [WHY?]
            </button>
          </div>
        </div>
      </template>

      <!-- Secondary Actions -->
      <template v-if="secondaryInsights.length">
        <div class="insight-section">
          <h4 class="section-title secondary">⚠️ SECONDARY (Monitor)</h4>
          <div v-for="insight in secondaryInsights" :key="insight.id" class="insight-item">
            <div class="insight-action">{{ insight.action }}</div>
            <button class="why-btn">
              [WHY?]
            </button>
          </div>
        </div>
      </template>
    </div>

    <!-- Last Updated -->
    <div class="updated-info">
      Last Updated: {{ lastUpdated }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { AIInsight } from '@/types'

interface Props {
  insights: AIInsight[]
  lastUpdated: string
}

const props = withDefaults(defineProps<Props>(), {
  lastUpdated: 'now',
})

const criticalInsights = computed(() =>
  props.insights.filter(i => i.severity === 'critical')
)

const secondaryInsights = computed(() =>
  props.insights.filter(i => i.severity === 'secondary')
)
</script>

<style scoped>
.ai-insights {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-insights h3 {
  margin: 0;
  font-size: 16px;
}

.insights-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.insight-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-title {
  font-size: 12px;
  text-transform: uppercase;
  margin: 0;
}

.section-title.critical {
  color: var(--accent-cyan);
}

.section-title.secondary {
  color: var(--accent-green);
}

.insight-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.insight-action {
  font-size: 12px;
  font-weight: 600;
}

.insight-meta {
  font-size: 11px;
  color: var(--text-secondary);
}

.why-btn {
  align-self: flex-start;
  background: transparent;
  border: none;
  color: var(--accent-cyan);
  cursor: pointer;
  font-size: 11px;
  text-decoration: underline;
  padding: 0;
  margin-top: 4px;
}

.why-btn:hover {
  color: var(--accent-green);
}

.updated-info {
  font-size: 11px;
  color: var(--text-secondary);
  text-align: right;
}
</style>
