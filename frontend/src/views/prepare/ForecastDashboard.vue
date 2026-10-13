<template>
  <div class="prepare-screen">
    <Header />
    <PreparePlaceholder
      icon="🌦️"
      title="7-Day Forecast Dashboard"
      description="Weather forecast, threat timeline, and risk escalation (YELLOW → ORANGE → RED) for the next 5-7 days. Real OpenWeatherMap + CHIRPS-GEFS data — no mock numbers shown until this is live."
    />
  </div>
</template>

<script setup lang="ts">
import Header from '@/components/organisms/Header.vue'
import PreparePlaceholder from '@/components/molecules/PreparePlaceholder.vue'
</script>
