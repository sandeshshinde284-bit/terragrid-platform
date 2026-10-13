<template>
  <div class="prepare-screen">
    <Header />
    <PreparePlaceholder
      icon="📨"
      title="Agency Alert Templates"
      description="Per-audience pre-event messaging (farmers, hospitals, NGOs, municipal corps) — distinct from RESPONSE's live incident broadcasting on the Alerts tab."
    />
  </div>
</template>

<script setup lang="ts">
import Header from '@/components/organisms/Header.vue'
import PreparePlaceholder from '@/components/molecules/PreparePlaceholder.vue'
</script>
