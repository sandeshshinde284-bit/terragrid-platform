<template>
  <div class="prepare-screen">
    <Header />
    <div class="roadmap-grid">
      <PreparePlaceholder
        icon="🔮"
        title="Predict"
        description="Early-warning forecasting ahead of the current 7-day window. Feature scope not yet finalized."
      />
      <PreparePlaceholder
        icon="♻️"
        title="Recover"
        description="Post-event recovery and resource reallocation tracking. Feature scope not yet finalized."
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import Header from '@/components/organisms/Header.vue'
import PreparePlaceholder from '@/components/molecules/PreparePlaceholder.vue'
</script>

<style scoped>
.roadmap-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16px;
}
</style>
