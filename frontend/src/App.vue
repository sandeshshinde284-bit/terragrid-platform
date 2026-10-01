<template>
  <div :class="{ 'dark-mode': appStore.isDarkMode }" class="app">
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useAppStore } from '@/stores'

const appStore = useAppStore()
</script>

<style>
@import './style.css';

.app {
  --bg-dark: #ffffff;
  --bg-panel: #f9fafb;
  --bg-overlay: rgba(255, 255, 255, 0.85);
  --glass-bg: rgba(255, 255, 255, 0.72);
  --glass-border: rgba(15, 23, 42, 0.12);
  --text-primary: #111827;
  --text-secondary: #4b5563;
  --text-muted: #6b7280;
  --accent-cyan: #1e40af;
  --accent-green: #047857;
  --accent-purple: #7c3aed;
  --accent-cyan-soft: rgba(30, 64, 175, 0.1);
  --critical: #b91c1c;
  --critical-surface: rgba(220, 38, 38, 0.08);
  --critical-border: rgba(220, 38, 38, 0.25);
  --header-bg-start: rgba(255, 255, 255, 0.94);
  --header-bg-end: rgba(241, 245, 249, 0.94);
  --header-border: rgba(30, 64, 175, 0.2);
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-dark);
  color: var(--text-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.app.dark-mode {
  --bg-dark: #0f1419;
  --bg-panel: #1a1f2e;
  --bg-overlay: rgba(26, 31, 46, 0.85);
  --glass-bg: rgba(26, 31, 46, 0.7);
  --glass-border: rgba(255, 255, 255, 0.15);
  --text-primary: #e0e0e0;
  --text-secondary: #9e9e9e;
  --text-muted: #666666;
  --accent-cyan: #00bcd4;
  --accent-green: #1dd1a1;
  --accent-purple: #9c27b0;
  --accent-cyan-soft: rgba(0, 188, 212, 0.1);
  --critical: #ff6b6b;
  --critical-surface: rgba(255, 107, 107, 0.1);
  --critical-border: rgba(255, 107, 107, 0.3);
  --header-bg-start: rgba(26, 31, 46, 0.9);
  --header-bg-end: rgba(15, 20, 25, 0.9);
  --header-border: rgba(0, 188, 212, 0.2);
}
</style>
