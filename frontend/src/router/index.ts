import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: {
      title: 'TerraGrid - Disaster Intelligence',
      requiresAuth: false,
    },
  },
  {
    path: '/incidents',
    name: 'Incidents',
    component: () => import('@/views/IncidentsScreen.vue'),
    meta: {
      title: 'Incidents - TerraGrid',
      requiresAuth: false,
    },
  },
  {
    path: '/map',
    name: 'MapFullScreen',
    component: () => import('@/views/MapFullScreen.vue'),
    meta: {
      title: 'Strategic Map - TerraGrid',
      requiresAuth: false,
    },
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('@/views/AnalysisScreen.vue'),
    meta: {
      title: 'Analysis - TerraGrid',
      requiresAuth: false
    }
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/AlertsScreen.vue'),
    meta: {
      title: 'Alerts & Broadcasts - TerraGrid',
      requiresAuth: false,
    },
  },
  {
    path: '/incident/:id',
    name: 'IncidentDetail',
    component: () => import('@/views/IncidentDetail.vue'),
    meta: {
      title: 'Incident Details',
      requiresAuth: false,
    },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: {
      title: 'Settings',
      requiresAuth: false,
      phase: 'settings',
    },
  },
  // ---- PREPARE phase routes (added for Phase 2) ----
  {
    path: '/prepare/forecast',
    name: 'PrepareForecast',
    component: () => import('@/views/prepare/ForecastDashboard.vue'),
    meta: {
      title: '7-Day Forecast - TerraGrid',
      requiresAuth: false,
      phase: 'prepare',
    },
  },
  {
    path: '/prepare/risk-timeline',
    name: 'PrepareRiskTimeline',
    component: () => import('@/views/prepare/RiskTimeline.vue'),
    meta: {
      title: 'Risk Escalation Timeline - TerraGrid',
      requiresAuth: false,
      phase: 'prepare',
    },
  },
  {
    path: '/prepare/checklist',
    name: 'PrepareChecklist',
    component: () => import('@/views/prepare/PreparednessChecklist.vue'),
    meta: {
      title: 'Preparedness Checklist - TerraGrid',
      requiresAuth: false,
      phase: 'prepare',
    },
  },
  {
    path: '/prepare/agency-alerts',
    name: 'PrepareAgencyAlerts',
    component: () => import('@/views/prepare/AgencyAlerts.vue'),
    meta: {
      title: 'Agency Alert Templates - TerraGrid',
      requiresAuth: false,
      phase: 'prepare',
    },
  },
  {
    path: '/roadmap',
    name: 'RoadmapPreview',
    component: () => import('@/views/RoadmapPreview.vue'),
    meta: {
      title: 'Predict & Recover Roadmap - TerraGrid',
      requiresAuth: false,
      phase: 'roadmap',
    },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '404 Not Found',
    },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to, from, next) => {
  const title = to.meta.title as string
  if (title) {
    document.title = title
  }
  next()
})

export default router