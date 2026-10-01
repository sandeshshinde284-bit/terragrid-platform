<template>
  <span :class="['badge', `badge-${severity}`]">
    {{ severity.toUpperCase() }}
  </span>
</template>

<script setup lang="ts">
import type { Event } from '@/types'

defineProps<{
  severity: Event['severity']
}>()
</script>

<style scoped>
.badge {
  display: inline-block;
  padding: 6px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  white-space: nowrap;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.badge-high {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
  border: 1px solid rgba(255, 107, 107, 0.5);
}

.badge-medium {
  background: rgba(243, 156, 18, 0.2);
  color: #f39c12;
  border: 1px solid rgba(243, 156, 18, 0.5);
}

.badge-low {
  background: rgba(46, 204, 113, 0.2);
  color: #2ecc71;
  border: 1px solid rgba(46, 204, 113, 0.5);
}
</style>