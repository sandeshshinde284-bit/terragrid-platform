<template>
  <div class="prepare-placeholder glass-panel">
    <div class="placeholder-icon">{{ icon }}</div>
    <h2>{{ title }}</h2>
    <p class="placeholder-status">🛠️ Building — not yet live</p>
    <p class="placeholder-desc">{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon: string
  title: string
  description: string
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
