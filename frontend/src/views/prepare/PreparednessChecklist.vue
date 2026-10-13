<template>
  <div class="prepare-screen">
    <Header />
    <PreparePlaceholder
      icon="✅"
      title="Preparedness Checklist"
      description="Interactive AI-generated checklist (clear drains, stock supplies, alert hospitals, position boats) with deadline tracking and agency ownership."
    />
  </div>
</template>

<script setup lang="ts">
import Header from '@/components/organisms/Header.vue'
import PreparePlaceholder from '@/components/molecules/PreparePlaceholder.vue'
</script>
