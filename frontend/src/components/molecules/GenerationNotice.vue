<template>
  <div class="generation-notice" :class="{ full: variant === 'full' }" role="status" aria-live="polite">
    <span class="spin" aria-hidden="true">⟳</span>
    <div class="notice-copy">
      <strong class="notice-title">{{ $t('generation.generating', { seconds: elapsed }) }}</strong>
      <ol v-if="variant === 'full'" class="notice-steps">
        <li
          v-for="(_, i) in STEP_COUNT"
          :key="i"
          :class="{ done: i < currentStep, active: i === currentStep }"
        >
          <span class="step-mark" aria-hidden="true">{{ i < currentStep ? '✓' : (i === currentStep ? '⟳' : '○') }}</span>
          <span>{{ $t(`generation.step${i + 1}`) }}</span>
        </li>
      </ol>
      <span class="notice-text">{{ $t('generation.background') }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

// Full variant: a step list that advances on a timer. The steps describe what
// the pipeline does; they are not measured progress from the backend.
const STEP_COUNT = 4
const SECONDS_PER_STEP = 8

const props = withDefaults(defineProps<{
  startedAt: number | null
  variant?: 'compact' | 'full'
}>(), { variant: 'compact' })

const now = ref(Date.now())
let timer: number | undefined

const elapsed = computed(() => {
  const start = props.startedAt ?? now.value
  return Math.max(0, Math.floor((now.value - start) / 1000))
})

// The last step stays active until the report arrives.
const currentStep = computed(() => Math.min(Math.floor(elapsed.value / SECONDS_PER_STEP), STEP_COUNT - 1))

onMounted(() => {
  timer = window.setInterval(() => { now.value = Date.now() }, 1000)
})
onUnmounted(() => {
  if (timer !== undefined) window.clearInterval(timer)
})
</script>

<style scoped>
.generation-notice {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid rgba(34, 211, 238, 0.35);
  background: rgba(8, 47, 73, 0.35);
}
.generation-notice.full { padding: 18px 20px; gap: 14px; }
.spin {
  display: inline-block;
  color: #22d3ee;
  font-size: 16px;
  line-height: 1.2;
  animation: notice-spin 1s linear infinite;
}
.notice-copy { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.notice-title { font-size: 13px; color: #e0f2fe; font-weight: 600; }
.full .notice-title { font-size: 15px; }
.notice-text { font-size: 12px; color: #94a3b8; line-height: 1.5; }
.notice-steps {
  list-style: none;
  margin: 6px 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.notice-steps li { display: flex; gap: 10px; font-size: 14px; color: #64748b; line-height: 1.4; }
.notice-steps li.done { color: #94a3b8; }
.notice-steps li.active { color: #e0f2fe; font-weight: 600; }
.step-mark { width: 16px; flex: 0 0 16px; color: #22d3ee; }
@keyframes notice-spin { to { transform: rotate(360deg); } }
</style>
