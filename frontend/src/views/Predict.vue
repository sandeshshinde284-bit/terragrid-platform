<template>
  <div class="predict-screen">
    <Header />
    <div class="roadmap-grid">
      <PreparePlaceholder
        icon="📊"
        :title="$t('header.phases.predict')"
        description="Early-warning forecasting ahead of the current 7-day window. Feature scope not yet finalized."
        :showComingSoon="true"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import Header from '@/components/organisms/Header.vue'
import PreparePlaceholder from '@/components/molecules/PreparePlaceholder.vue'
</script>

<style scoped>
.predict-screen {
  width: 100%;
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
  min-height: 100vh;
  overflow-y: auto;
}

.roadmap-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16px;
  padding: 24px;
}
</style>
