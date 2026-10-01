<template>
  <div class="not-found">
    <h1>404</h1>
    <h2>Page Not Found</h2>
    <p>The page you're looking for doesn't exist.</p>
    <RouterLink to="/">Back to Dashboard</RouterLink>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  padding: 20px;
  text-align: center;
}

.not-found h1 {
  font-size: 72px;
  margin-bottom: 20px;
  color: var(--accent-cyan);
}

.not-found a {
  margin-top: 20px;
  padding: 10px 20px;
  background-color: var(--accent-cyan);
  color: var(--bg-dark);
  border-radius: 4px;
  text-decoration: none;
}
</style>
