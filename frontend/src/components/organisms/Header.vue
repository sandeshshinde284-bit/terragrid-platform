<template>
    <div 
      v-if="appStore.isBackendMockModeEnabled" 
      class="header-simulation-banner"
      style="background: rgba(56, 189, 248, 0.15); border-bottom: 1px solid rgba(56, 189, 248, 0.4); color: #bae6fd; padding: 6px 16px; font-size: 13px; display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; text-align: center;"
    >
      <span>ℹ️</span>
      <span><strong>{{ $t('header.simulationModeActive') }}</strong>: {{ $t('header.simulationModeDesc') }}</span>
    </div>

    <header class="header glass-panel">
    <div class="header-left">
      <div class="logo" @click="goHome" style="cursor: pointer;">
        <span class="logo-icon">🌍</span>
        <h1>{{ $t('app.title') }}</h1>
      </div>
      <nav class="nav-menu">
        <!-- PHASE SELECTOR - the only thing left in the main header bar now.
             Feature tabs moved to their own strip below (.tools-bar) so the
             header stays a single compact row instead of growing tall with
             a second row stacked inside the same glass-panel box. -->
        <div class="phase-selector">
          <button
            class="phase-btn"
            :class="{ active: activePhase === 'prepare' }"
            @click="router.push('/prepare/forecast')"
          >
            {{ $t('header.phases.prepare') }}
          </button>
          <button
            class="phase-btn"
            :class="{ active: activePhase === 'response' }"
            @click="router.push('/')"
          >
            {{ $t('header.phases.response') }}
          </button>
          <button
            class="phase-btn roadmap"
            :class="{ active: activePhase === 'roadmap' }"
            @click="router.push('/roadmap')"
            :title="$t('header.phases.predictRecoverTooltip')"
          >
            {{ $t('header.phases.predictRecover') }}
            <span class="soon-badge">{{ $t('header.soon') }}</span>
          </button>
        </div>
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

      <button
        class="header-btn"
        @click="toggle3D"
        :class="{ active: is3D }"
        title="Toggle 2D/3D view"
      >
        {{ is3D ? $t('header.3d') : $t('header.2d') }}
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

  <!-- ACTIVE TOOLS - a totally separate strip from the header above, not
       nested in the same glass-panel box. Mirrors the mobile drawer's
       existing section labels (see mobile-nav-section-title below) so a
       first-time viewer has an explicit word for what this row is. -->
  <div class="tools-bar">
    <span class="tools-label">{{ $t('header.activeTools') }}</span>

    <div class="nav-row" v-if="activePhase === 'prepare'">
      <div class="nav-group">
        <RouterLink to="/prepare/forecast" :class="{ active: isActive('/prepare/forecast') }">🌦️ {{ $t('header.tools.forecast') }}</RouterLink>
        <RouterLink to="/prepare/risk-timeline" :class="{ active: isActive('/prepare/risk-timeline') }">📈 {{ $t('header.tools.riskTimeline') }}</RouterLink>
        <RouterLink to="/prepare/checklist" :class="{ active: isActive('/prepare/checklist') }">✅ {{ $t('header.tools.checklist') }}</RouterLink>
        <RouterLink to="/prepare/agency-alerts" :class="{ active: isActive('/prepare/agency-alerts') }">📨 {{ $t('header.tools.agencyAlerts') }}</RouterLink>
      </div>
    </div>

    <div class="nav-row" v-if="activePhase === 'response'">
      <div class="nav-group">
        <RouterLink to="/" :class="{ active: isActive('/') }">📊 {{ $t('header.tools.dashboard') }}</RouterLink>
        <RouterLink to="/incidents" :class="{ active: isActive('/incidents') }">📋 {{ $t('header.tools.incidents') }}</RouterLink>
        <RouterLink to="/map" :class="{ active: isActive('/map') }">🗺️ {{ $t('header.tools.map') }}</RouterLink>
        <RouterLink to="/analysis" :class="{ active: isActive('/analysis') }">📈 {{ $t('header.tools.analysis') }}</RouterLink>
        <RouterLink to="/alerts" :class="{ active: isActive('/alerts') }">📢 {{ $t('header.tools.alerts') }}</RouterLink>
      </div>
    </div>

    <div class="nav-row nav-row-roadmap" v-if="activePhase === 'roadmap'">
      <div class="nav-group nav-group-disabled">
        <span class="nav-roadmap-badge">{{ $t('header.roadmap.predictSoon') }}</span>
        <span class="nav-roadmap-badge">{{ $t('header.roadmap.recoverSoon') }}</span>
      </div>
    </div>
  </div>

  <!-- Mobile Navigation Drawer -->
  <Transition name="slide-left">
    <nav v-if="mobileMenuOpen" class="mobile-nav-drawer">
      <!-- Mobile Nav Section with Phase Switcher -->
      <div class="mobile-phase-selector">
        <button
          :class="{ active: activePhase === 'prepare' }"
          @click="router.push('/prepare/forecast')"
        >
          {{ $t('header.phases.prepare') }}
        </button>
        <button
          :class="{ active: activePhase === 'response' }"
          @click="router.push('/')"
        >
          {{ $t('header.phases.response') }}
        </button>
        <button
          :class="{ active: activePhase === 'roadmap' }"
          @click="router.push('/roadmap'); closeMobileMenu()"
        >
          {{ $t('header.phases.predictRecover') }}
          <span class="soon-badge">{{ $t('header.soon') }}</span>
        </button>
      </div>

      <div class="menu-divider"></div>

      <!-- Prepare Section -->
      <div class="mobile-nav-section" v-if="activePhase === 'prepare'">
        <div class="mobile-nav-section-title">{{ $t('header.phases.prepare') }}</div>
        <RouterLink
          to="/prepare/forecast"
          :class="{ active: isActive('/prepare/forecast') }"
          @click="closeMobileMenu"
        >
          🌦️ {{ $t('header.tools.forecast') }}
        </RouterLink>
        <RouterLink
          to="/prepare/risk-timeline"
          :class="{ active: isActive('/prepare/risk-timeline') }"
          @click="closeMobileMenu"
        >
          📈 {{ $t('header.tools.riskTimeline') }}
        </RouterLink>
        <RouterLink
          to="/prepare/checklist"
          :class="{ active: isActive('/prepare/checklist') }"
          @click="closeMobileMenu"
        >
          ✅ {{ $t('header.tools.checklist') }}
        </RouterLink>
        <RouterLink
          to="/prepare/agency-alerts"
          :class="{ active: isActive('/prepare/agency-alerts') }"
          @click="closeMobileMenu"
        >
          📨 {{ $t('header.tools.agencyAlerts') }}
        </RouterLink>
      </div>

      <!-- Response Section -->
      <div class="mobile-nav-section" v-if="activePhase === 'response'">
        <div class="mobile-nav-section-title">{{ $t('header.phases.response') }}</div>
        <RouterLink
          to="/"
          :class="{ active: isActive('/') }"
          @click="closeMobileMenu"
        >
          📊 {{ $t('header.tools.dashboard') }}
        </RouterLink>
        <RouterLink
          to="/incidents"
          :class="{ active: isActive('/incidents') }"
          @click="closeMobileMenu"
        >
          📋 {{ $t('header.tools.incidents') }}
        </RouterLink>
        <RouterLink
          to="/map"
          :class="{ active: isActive('/map') }"
          @click="closeMobileMenu"
        >
          🗺️ {{ $t('header.tools.mapShort') }}
        </RouterLink>
        <RouterLink
          to="/analysis"
          :class="{ active: isActive('/analysis') }"
          @click="closeMobileMenu"
        >
          📈 {{ $t('header.tools.analysisShort') }}
        </RouterLink>
        <RouterLink
          to="/alerts"
          :class="{ active: isActive('/alerts') }"
          @click="closeMobileMenu"
        >
          🚨 {{ $t('header.tools.alerts') }}
        </RouterLink>
      </div>

      <!-- Settings Section Divider -->
      <div class="menu-divider"></div>

      <!-- Settings -->
      <div class="settings-section">
        <div class="settings-title">⚙️ {{ $t('header.settings') }}</div>
        
        <!-- Dark/Light Mode Toggle -->
        <button 
          class="settings-item"
          @click="toggleTheme"
          title="Toggle dark/light mode"
        >
          <span>{{ appStore.isDarkMode ? '☀️' : '🌙' }}</span>
          <span>{{ appStore.isDarkMode ? $t('header.lightMode') : $t('header.darkMode') }}</span>
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
import { computed, ref, watch } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'
import { useAppStore } from '@/stores'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const { locale } = useI18n()
const selectedLanguage = ref(locale.value.toUpperCase())
const is3D = computed(() => appStore.viewMode === '3d')
const mobileMenuOpen = ref(false)

// Detect active phase based on current route. All three phases (prepare,
// response, roadmap) are now real routes with meta.phase set, so this is
// the single source of truth - no local toggle state needed.
const activePhase = computed(() => {
  const phaseMeta = route.meta.phase as string | undefined
  if (phaseMeta === 'prepare' || phaseMeta === 'roadmap') {
    return phaseMeta
  }
  // Default to 'response' for all other routes (/, /incidents, /map, etc.)
  return 'response'
})

const goHome = () => {
  router.push('/')
}

const isActive = (path: string) => {
  return route.path === path
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
  align-items: center;
}

.phase-selector {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 0;
}

.phase-btn {
  padding: 8px 16px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  border: 2px solid var(--glass-border);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.phase-btn:hover:not(:disabled) {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.1);
}

.phase-btn.active {
  /* Flat accent fill instead of a blue gradient + colored shadow - matches
     every other "active" control in the app (filter chips, sort toggles),
     so the phase switch doesn't stand out as a one-off style. */
  background: var(--accent-cyan);
  border-color: var(--accent-cyan);
  color: #04141a;
  font-weight: 700;
}

.phase-btn.roadmap {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.phase-btn.roadmap.active {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--glass-border);
  color: var(--text-primary);
  box-shadow: none;
}

.soon-badge {
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.3px;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(168, 85, 247, 0.18);
  color: #c084fc;
  white-space: nowrap;
}

/* The feature tabs now live in .tools-bar, a separate strip entirely
   outside the header's glass-panel box (see below) - that strip already
   carries its own background/border, so .nav-row itself goes back to a
   plain flex row instead of being its own nested boxed-within-a-box. */
.nav-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  row-gap: 4px;
  min-height: 32px;
}

.nav-row-roadmap {
  height: auto;
}

/* ---- Active Tools strip - sibling of <header>, not nested inside it.
   Keeping the phase selector and the feature tabs in two visually
   separate elements (own background/border each) is what actually fixes
   "the header is so big" - previously both lived inside the same
   <header class="header glass-panel"> box, stacked as two rows, so the
   whole thing grew tall and read as one dense block. This strip is its
   own section, labelled, full width, so RESPONSE's 5 tabs never crowd a
   box sized for the 3 phase buttons above it. */
.tools-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  padding: 8px 16px;
  background: rgba(10, 14, 20, 0.55);
  border-bottom: 1px solid var(--header-border, rgba(255, 255, 255, 0.08));
  flex-shrink: 0;
}

.tools-label {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--text-secondary);
  white-space: nowrap;
  opacity: 0.75;
}

.tools-bar :deep(a) {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 10px;
  border-radius: 6px;
  transition: all 0.2s ease;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--glass-border);
  white-space: nowrap;
  position: relative;
}

.tools-bar :deep(a:hover) {
  color: var(--accent-cyan);
  background: rgba(30, 144, 255, 0.15);
  border-color: var(--accent-cyan);
}

/* Deliberately NOT the same vibrant gradient fill as .phase-btn.active -
   now that the tools strip is a physically separate element from the
   header (not just a visually-boxed row within it), a softer active
   tint still reads clearly without needing the bold fill the phase
   button uses one section up. */
.tools-bar :deep(a.active) {
  color: var(--accent-cyan, #22d3ee);
  background: rgba(34, 211, 238, 0.14);
  border-color: var(--accent-cyan, #22d3ee);
  font-weight: 700;
  box-shadow: none;
}

.nav-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-group-disabled {
  opacity: 0.85;
}

.nav-roadmap-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px dashed var(--glass-border);
  color: var(--text-secondary);
  white-space: nowrap;
}

.header-center {
  flex: 1;
  min-width: 0;
}

/* Hidden by default - only meant to appear below the 480px mobile
   breakpoint (see @media (max-width: 480px) below, which sets
   display: flex and gives .hamburger its actual icon styling). With no
   default display rule here, this <button> had no explicit display at
   all on desktop, so it rendered as a native, empty, un-styled browser
   button - the .hamburger icon inside it only gets sized/styled inside
   that same mobile media query, so outside of it this button collapsed
   to a tiny default button nub sitting between the nav tabs and the
   right-side controls. That's the stray dot that kept showing up there. */
.mobile-menu-btn {
  display: none;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.header-btn {
  background: rgba(255, 255, 255, 0.03);
  border: 2px solid var(--glass-border);
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
  background: rgba(255, 193, 7, 0.15);
  border-color: #ffc107;
  color: #ffc107;
}

.mock-toggle:not(.active) {
  background: rgba(16, 185, 129, 0.12);
  border-color: #10b981;
  color: #10b981;
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

  .tools-bar {
    padding: 6px 12px;
    gap: 10px;
  }

  .tools-label {
    font-size: 9px;
  }

  .logo h1 {
    font-size: 14px;
  }

  .logo-icon {
    font-size: 20px;
  }

  .tools-bar :deep(a) {
    font-size: 10px;
    padding: 4px 8px;
  }

  .nav-roadmap-badge {
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

  .tools-bar {
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

  .mobile-phase-selector {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 8px 12px;
  }

  .mobile-phase-selector button {
    padding: 10px 12px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    border: 2px solid var(--glass-border);
    border-radius: 6px;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
    text-transform: uppercase;
  }

  .mobile-phase-selector button:hover:not(:disabled) {
    border-color: var(--accent-cyan);
    color: var(--accent-cyan);
    background: rgba(30, 144, 255, 0.1);
  }

  .mobile-phase-selector button.active {
    background: var(--accent-cyan);
    border-color: var(--accent-cyan);
    color: #04141a;
    font-weight: 700;
  }

  .mobile-phase-selector button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
    border-style: dashed;
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

  /* Mobile Nav Sections (Prepare / Response / Roadmap groups) */
  .mobile-nav-section {
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .mobile-nav-section-title {
    color: var(--text-secondary);
    font-size: 11px;
    font-weight: 700;
    padding: 8px 16px 4px 16px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
    opacity: 0.8;
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
