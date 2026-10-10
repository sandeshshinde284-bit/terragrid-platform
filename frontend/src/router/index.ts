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