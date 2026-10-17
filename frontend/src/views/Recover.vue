<template>
  <div class="recover-screen">
    <Header />
    <div class="roadmap-grid">
      <PreparePlaceholder
        icon="♻️"
        :title="$t('header.phases.recover')"
        description="Post-event recovery and resource reallocation tracking. Feature scope not yet finalized."
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
.recover-screen {
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
