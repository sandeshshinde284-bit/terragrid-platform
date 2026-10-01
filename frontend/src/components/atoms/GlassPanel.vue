<template>
  <div 
    :class="['glass-panel', `severity-${severity}`]"
    @click="handleClick"
  >
    <div class="glass-blur"></div>
    <div class="content">
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Event } from '@/types'

withDefaults(
  defineProps<{
    severity?: Event['severity']
    clickable?: boolean
  }>(),
  {
    severity: 'medium',
    clickable: false,
  }
)

const emit = defineEmits<{
  click: []
}>()

const handleClick = () => {
  emit('click')
}
</script>

<style scoped>
.glass-panel {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid var(--glass-border);
  transition: all 0.3s ease;
}

.glass-blur {
  position: absolute;
  inset: 0;
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.content {
  position: relative;
  z-index: 1;
  padding: 16px;
}

.glass-panel.severity-high {
  border-color: rgba(255, 107, 107, 0.5);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 0 20px rgba(255, 107, 107, 0.5);
}

.glass-panel.severity-medium {
  border-color: rgba(243, 156, 18, 0.4);
}

.glass-panel.severity-low {
  border-color: rgba(46, 204, 113, 0.4);
}

.glass-panel:hover {
  transform: translateY(-2px);
  background: var(--bg-overlay);
}
</style>
