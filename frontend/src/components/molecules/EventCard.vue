<template>
  <div class="event-card">
    <div class="card-header">
      <h3>{{ event.name }}</h3>
      <Badge :variant="severityVariant">{{ event.severity }}</Badge>
    </div>
    <div class="card-body">
      <p><strong>Type:</strong> {{ event.type }}</p>
      <p><strong>Location:</strong> {{ event.latitude }}, {{ event.longitude }}</p>
      <p><strong>Time:</strong> {{ formattedTime }}</p>
    </div>
    <div class="card-footer">
      <Button @click="handleView" variant="primary" size="sm">
        View Details
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import Button from '../atoms/Button.vue'
import Badge from '../atoms/Badge.vue'
import { logger } from '@/config/logger'
import type { Event } from '@/types'

interface Props {
  event: Event
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'view-details': [id: string]
}>()

const severityVariant = computed(() => {
  const severity = props.event.severity.toLowerCase()
  const map: Record<string, 'danger' | 'warning' | 'success' | 'info'> = {
    high: 'danger',
    medium: 'warning',
    low: 'success',
  }
  return map[severity] || 'info'
})

const formattedTime = computed(() => {
  return formatDistanceToNow(new Date(props.event.created_at), { addSuffix: true })
})

const handleView = (): void => {
  logger.debug('Viewing event details', { eventId: props.event.id })
  emit('view-details', props.event.id)
}
</script>

<style scoped>
.event-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 16px;
  margin-bottom: 12px;
  transition: all 0.3s;
}

.event-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
}

.card-body {
  margin-bottom: 12px;
}

.card-body p {
  margin: 6px 0;
  font-size: 14px;
  color: #666;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
}
</style>