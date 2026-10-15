<template>
  <div class="prepare-screen">
    <Header />
    <div class="roadmap-grid">
      <PreparePlaceholder
        icon="🔮"
        :title="$t('roadmap.predictTitle')"
        :description="$t('roadmap.predictDesc')"
      />
      <PreparePlaceholder
        icon="♻️"
        :title="$t('roadmap.recoverTitle')"
        :description="$t('roadmap.recoverDesc')"
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
