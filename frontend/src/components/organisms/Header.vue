<template>
  <header class="header glass-panel">
    <div class="header-left">
      <div class="logo" @click="goHome" style="cursor: pointer;">
        <span class="logo-icon">🌍</span>
        <h1>TERRAGRID INTELLIGENCE</h1>
      </div>
      <nav class="nav-menu">
        <RouterLink to="/" :class="{ active: isActive('/') }">📊 Dashboard</RouterLink>
        <RouterLink to="/incidents" :class="{ active: isActive('/incidents') }">📋 Incidents</RouterLink>
        <RouterLink to="/map" :class="{ active: isActive('/map') }">🗺️ Map</RouterLink>
        <RouterLink to="/analysis" :class="{ active: isActive('/analysis') }">📈 Analysis</RouterLink>
        <RouterLink to="/ask-map" :class="{ active: isActive('/ask-map') }">🤖 Ask Map</RouterLink>
        <RouterLink to="/alerts" :class="{ active: isActive('/alerts') }">🚨 Alerts</RouterLink>
      </nav>
    </div>

    <!-- Mobile Menu Button -->
    <button class="mobile-menu-btn" @click="toggleMobileMenu" aria-label="Toggle menu">
      <span class="hamburger" :class="{ open: mobileMenuOpen }">
        <span></span>
        <span></span>
        <span></span>
      </span>
    </button>

    <div class="header-center"></div>

    <div class="header-right">
      <!-- Mock/Live Data Toggle (Disabled for Strict Live Mode) -->
      <!--
      <button 
        class="header-btn mock-toggle"
        @click="toggleMockMode"
        :class="{ active: mockModeEnabled }"
        :title="mockModeEnabled ? 'Using Mock Data (Testing Mode)' : 'Using Live APIs (Production)'"
      >
        <span v-if="mockModeEnabled">🧪 MOCK</span>
        <span v-else>🌐 LIVE</span>
      </button>
      -->

      <button 
        class="header-btn"
        @click="refreshData"
        :disabled="appStore.isLoading"
        title="Refresh data"
      >
        <span v-if="appStore.isLoading">⟳</span>
        <span v-else>⟳</span>
      </button>

      <button 
        class="header-btn"
        @click="toggle3D"
        :class="{ active: is3D }"
        title="Toggle 2D/3D view"
      >
        {{ is3D ? '3D' : '2D' }}
      </button>

      <label class="language-selector" for="header-language">
        <span>🌐</span>
        <select 
          id="header-language" 
          v-model="selectedLanguage" 
          @change="handleLanguageChange"
          aria-label="Select language"
        >
          <option value="EN">English</option>
          <option value="DE">Deutsch</option>
          <option value="ES">Español</option>
          <option value="FR">Français</option>
          <option value="IT">Italiano</option>
          <option value="PL">Polski</option>
          <option value="SV">Svenska</option>
        </select>
      </label>
    </div>
  </header>

  <!-- Mobile Navigation Drawer -->
  <Transition name="slide-left">
    <nav v-if="mobileMenuOpen" class="mobile-nav-drawer">
      <RouterLink 
        to="/" 
        :class="{ active: isActive('/') }"
        @click="closeMobileMenu"
      >
        📊 Dashboard
      </RouterLink>
      <RouterLink 
        to="/incidents" 
        :class="{ active: isActive('/incidents') }"
        @click="closeMobileMenu"
      >
        📋 Incidents
      </RouterLink>
      <RouterLink 
        to="/map" 
        :class="{ active: isActive('/map') }"
        @click="closeMobileMenu"
      >
        🗺️ Map
      </RouterLink>
      <RouterLink 
        to="/analysis" 
        :class="{ active: isActive('/analysis') }"
        @click="closeMobileMenu"
      >
        📈 Analysis
      </RouterLink>
      <RouterLink 
        to="/ask-map" 
        :class="{ active: isActive('/ask-map') }"
        @click="closeMobileMenu"
      >
        🤖 Ask Map
      </RouterLink>
      <RouterLink 
        to="/alerts" 
        :class="{ active: isActive('/alerts') }"
        @click="closeMobileMenu"
      >
        🚨 Alerts
      </RouterLink>

      <!-- Settings Section Divider -->
      <div class="menu-divider"></div>

      <!-- Settings -->
      <div class="settings-section">
        <div class="settings-title">⚙️ Settings</div>
        
        <!-- Dark/Light Mode Toggle -->
        <button 
          class="settings-item"
          @click="toggleTheme"
          title="Toggle dark/light mode"
        >
          <span>{{ appStore.isDarkMode ? '☀️' : '🌙' }}</span>
          <span>{{ appStore.isDarkMode ? 'Light Mode' : 'Dark Mode' }}</span>
        </button>
      </div>
    </nav>
  </Transition>

  <!-- Mobile Menu Overlay -->
  <Transition name="fade">
    <div v-if="mobileMenuOpen" class="mobile-overlay" @click="closeMobileMenu"></div>
  </Transition>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import { useAppStore } from '@/stores'
import { useI18n } from 'vue-i18n'
import { useMockMode } from '@/composables/useMockMode'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const { locale } = useI18n()
const selectedLanguage = ref(locale.value.toUpperCase())
const is3D = computed(() => appStore.viewMode === '3d')
const mobileMenuOpen = ref(false)

// Mock mode toggle (shared composable - keeps Header and Dashboard in sync)
const { isMockMode: mockModeEnabled, toggleMockMode } = useMockMode()

const goHome = () => {
  router.push('/')
}

const isActive = (path: string) => {
  return route.path === path
}

const refreshData = async () => {
  appStore.setLoading(true)
  // Refresh incidents data
  setTimeout(() => {
    appStore.setLoading(false)
  }, 1000)
}

const toggle3D = () => {
  appStore.toggleViewMode()
}

const toggleTheme = () => {
  appStore.toggleTheme()
}

const handleLanguageChange = () => {
  locale.value = selectedLanguage.value.toLowerCase()
}

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

const closeMobileMenu = () => {
  mobileMenuOpen.value = false
}
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(90deg, var(--header-bg-start), var(--header-bg-end));
  border-bottom: 1px solid var(--header-border);
  gap: 12px;
  height: auto;
  flex-shrink: 0;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: fit-content;
}

.logo-icon {
  font-size: 24px;
}

.logo h1 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--accent-cyan);
}

.nav-menu {
  display: flex;
  gap: 8px;
  align-items: center;
}

.nav-menu :deep(a) {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 10px;
  border-radius: 4px;
  transition: all 0.2s ease;
  border: 2px solid transparent;
  white-space: nowrap;
  position: relative;
}

.nav-menu :deep(a:hover) {
  color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.15);
  border-color: var(--accent-cyan);
}

.nav-menu :deep(a.active) {
  color: #ffffff;
  background: linear-gradient(135deg, #1e40af, #0ea5e9);
  border-color: var(--accent-cyan);
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(30, 64, 175, 0.3);
}

.header-center {
  flex: 1;
  min-width: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.header-btn {
  background: transparent;
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
  padding: 6px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  transition: all 0.2s ease;
  white-space: nowrap;
  flex-shrink: 0;
}

.header-btn:hover:not(:disabled) {
  background: var(--accent-cyan-soft);
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.header-btn.active {
  background: var(--accent-cyan-soft);
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.header-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Mock/Live Toggle Special Styling */
.mock-toggle {
  font-weight: 700;
  font-size: 10px;
  padding: 6px 12px;
  letter-spacing: 0.5px;
}

.mock-toggle.active {
  background: rgba(255, 193, 7, 0.2);
  border-color: #ffc107;
  color: #ffc107;
  box-shadow: 0 0 8px rgba(255, 193, 7, 0.3);
}

.mock-toggle:not(.active) {
  background: rgba(16, 185, 129, 0.15);
  border-color: #10b981;
  color: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.2);
}

.settings-btn {
  display: flex;
  align-items: center;
  gap: 4px;
}

.language-selector {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 2px solid var(--accent-cyan);
  border-radius: 4px;
  background: rgba(30, 144, 255, 0.1);
  color: var(--accent-cyan);
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s ease;
  cursor: pointer;
  flex-shrink: 0;
}

.language-selector:hover {
  background: rgba(30, 144, 255, 0.2);
  box-shadow: 0 0 12px rgba(30, 144, 255, 0.3);
}

.language-selector select {
  border: none;
  background: transparent;
  color: var(--accent-cyan);
  font: inherit;
  font-weight: 600;
  outline: none;
  cursor: pointer;
  min-width: 80px;
  padding: 2px 4px;
  font-size: 11px;
}

.language-selector select option {
  background: var(--bg-dark);
  color: var(--accent-cyan);
  font-weight: 600;
  padding: 4px;
  font-size: 11px;
}

.language-selector select option:checked {
  background: rgba(30, 144, 255, 0.3);
  color: var(--accent-cyan);
}

.language-selector option {
  color: #111827;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .header {
    padding: 10px 12px;
    gap: 8px;
  }

  .header-left {
    gap: 12px;
  }

  .logo h1 {
    font-size: 14px;
  }

  .logo-icon {
    font-size: 20px;
  }

  .nav-menu {
    gap: 4px;
  }

  .nav-menu :deep(a) {
    font-size: 10px;
    padding: 4px 8px;
  }

  .header-btn {
    font-size: 10px;
    padding: 4px 8px;
  }

  .language-selector {
    padding: 4px 8px;
  }

  .language-selector select {
    min-width: 60px;
    font-size: 10px;
  }
}

@media (max-width: 480px) {
  .header {
    padding: 8px 10px;
    gap: 4px;
    order: -1;
  }

  .header-left {
    flex: 1;
    gap: 8px;
  }

  .logo {
    gap: 4px;
  }

  .logo h1 {
    font-size: 12px;
  }

  .logo-icon {
    font-size: 18px;
  }

  .nav-menu {
    display: none;
  }

  .mobile-menu-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: 1px solid var(--glass-border);
    width: 32px;
    height: 32px;
    padding: 0;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s ease;
  }

  .mobile-menu-btn:hover {
    background: rgba(30, 144, 255, 0.1);
    border-color: var(--accent-cyan);
  }

  .hamburger {
    display: flex;
    flex-direction: column;
    gap: 4px;
    width: 18px;
    height: 14px;
    position: relative;
  }

  .hamburger span {
    width: 100%;
    height: 2px;
    background: var(--accent-cyan);
    border-radius: 1px;
    transition: all 0.3s ease;
  }

  .hamburger.open span:nth-child(1) {
    transform: rotate(45deg) translateY(8px);
  }

  .hamburger.open span:nth-child(2) {
    opacity: 0;
  }

  .hamburger.open span:nth-child(3) {
    transform: rotate(-45deg) translateY(-8px);
  }

  .header-center {
    display: none;
  }

  .header-right {
    gap: 4px;
    order: 3;
  }

  .header-btn {
    font-size: 9px;
    padding: 3px 6px;
    display: none;
  }

  .language-selector {
    display: none;
  }

  /* Mobile Navigation Drawer */
  .mobile-nav-drawer {
    position: fixed;
    top: 50px;
    left: 0;
    width: 100%;
    max-width: 300px;
    max-height: calc(100vh - 50px);
    background: linear-gradient(180deg, var(--header-bg-start), var(--header-bg-end));
    backdrop-filter: blur(20px);
    border-right: 1px solid var(--glass-border);
    border-bottom: 1px solid var(--glass-border);
    padding: 8px 0;
    display: flex;
    flex-direction: column;
    gap: 0;
    z-index: 999;
    overflow-y: auto;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }

  .mobile-nav-drawer :deep(a) {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 13px;
    font-weight: 600;
    padding: 12px 16px;
    border-left: 3px solid transparent;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    box-sizing: border-box;
  }

  .mobile-nav-drawer :deep(a:hover) {
    background: rgba(30, 144, 255, 0.15);
    color: var(--accent-cyan);
    border-left-color: var(--accent-cyan);
  }

  .mobile-nav-drawer :deep(a.active) {
    background: linear-gradient(90deg, rgba(30, 144, 255, 0.3), transparent);
    color: #ffffff;
    border-left-color: var(--accent-cyan);
    font-weight: 700;
  }

  /* Menu Divider */
  .menu-divider {
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
    margin: 8px 0;
  }

  /* Settings Section */
  .settings-section {
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .settings-title {
    color: var(--text-secondary);
    font-size: 11px;
    font-weight: 700;
    padding: 8px 16px 4px 16px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    opacity: 0.8;
  }

  .settings-item {
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--text-secondary);
    background: transparent;
    border: none;
    font-size: 13px;
    font-weight: 600;
    padding: 12px 16px;
    border-left: 3px solid transparent;
    cursor: pointer;
    transition: all 0.2s ease;
    width: 100%;
    box-sizing: border-box;
    text-align: left;
  }

  .settings-item:hover {
    background: rgba(30, 144, 255, 0.15);
    color: var(--accent-cyan);
    border-left-color: var(--accent-cyan);
  }

  .settings-item:active {
    background: linear-gradient(90deg, rgba(30, 144, 255, 0.3), transparent);
    color: #ffffff;
    border-left-color: var(--accent-cyan);
  }

  /* Mobile Overlay */
  .mobile-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    z-index: 998;
  }

  /* Animations */
  .slide-left-enter-active,
  .slide-left-leave-active {
    transition: all 0.3s ease;
  }

  .slide-left-enter-from {
    transform: translateX(-100%);
    opacity: 0;
  }

  .slide-left-leave-to {
    transform: translateX(-100%);
    opacity: 0;
  }

  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.3s ease;
  }

  .fade-enter-from,
  .fade-leave-to {
    opacity: 0;
  }
}
</style>
