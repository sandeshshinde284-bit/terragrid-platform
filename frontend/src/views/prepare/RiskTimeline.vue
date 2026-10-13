<template>
  <div class="prepare-screen">
    <Header />
    <PreparePlaceholder
      icon="📈"
      title="Risk Escalation Timeline"
      description="Day-by-day escalation view ('Day 5: YELLOW, Day 3: ORANGE, Day 1: RED') built from the 7-Day Forecast Dashboard's real data. Depends on PR1 shipping first."
    />
  </div>
</template>

<script setup lang="ts">
import Header from '@/components/organisms/Header.vue'
import PreparePlaceholder from '@/components/molecules/PreparePlaceholder.vue'
</script>
