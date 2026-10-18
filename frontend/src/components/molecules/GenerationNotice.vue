<template>
  <div class="generation-notice" role="status" aria-live="polite">
    <span class="spin" aria-hidden="true">⟳</span>
    <div class="notice-copy">
      <strong class="notice-title">{{ $t('generation.generating', { seconds: elapsed }) }}</strong>
      <span class="notice-text">{{ $t('generation.background') }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps<{ startedAt: number | null }>()

const now = ref(Date.now())
let timer: number | undefined

const elapsed = computed(() => {
  const start = props.startedAt ?? now.value
  return Math.max(0, Math.floor((now.value - start) / 1000))
})

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
.spin {
  display: inline-block;
  color: #22d3ee;
  font-size: 16px;
  line-height: 1.2;
  animation: notice-spin 1s linear infinite;
}
.notice-copy { display: flex; flex-direction: column; gap: 4px; }
.notice-title { font-size: 13px; color: #e0f2fe; font-weight: 600; }
.notice-text { font-size: 12px; color: #94a3b8; line-height: 1.5; }
@keyframes notice-spin { to { transform: rotate(360deg); } }
</style>
