<template>
  <div class="prepare-placeholder glass-panel">
    <div class="placeholder-icon">{{ icon }}</div>
    <h2>
      {{ title }}
      <span class="coming-soon-badge" v-if="showComingSoon">COMING SOON</span>
    </h2>
    <p class="placeholder-status">🛠️ Building — not yet live</p>
    <p class="placeholder-desc">{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon: string
  title: string
  description: string
  showComingSoon?: boolean
}>()
</script>

<style scoped>
.prepare-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 24px;
  margin: 24px auto;
  max-width: 520px;
  gap: 10px;
}

.placeholder-icon {
  font-size: 40px;
  margin-bottom: 4px;
}

.prepare-placeholder h2 {
  margin: 0;
  color: var(--accent-cyan);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.coming-soon-badge {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.4);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 700;
  color: #3b82f6;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.placeholder-status {
  font-weight: 700;
  font-size: 13px;
  letter-spacing: 0.3px;
  color: #f59e0b;
  margin: 4px 0;
}

.placeholder-desc {
  color: var(--text-secondary);
  font-size: 13px;
  max-width: 400px;
}
</style>
