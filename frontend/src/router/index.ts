/**
 * Vue Router configuration with OIDC navigation guard.
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { userManager } from '../auth/oidc'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/circles',
  },
  // LoginView initiates the OIDC redirect from onMounted.
  // Keeping login as a proper route avoids calling
  // signinRedirect() inside the navigation guard, which
  // can race with Vue Router's history restoration and
  // cause an infinite redirect loop.
  {
    path: '/login',
    component: () => import('../views/LoginView.vue'),
  },
  {
    path: '/auth/callback',
    component: () => import('../views/AuthCallbackView.vue'),
  },
  {
    path: '/circles',
    component: () => import('../views/CirclesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    // Tabbed circle shell: calendar and list share a header strip.
    path: '/circles/:id',
    component: () => import('../views/CircleView.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        component: () => import('../views/CircleCalendarView.vue'),
      },
      {
        path: 'list',
        component: () => import('../views/CircleListView.vue'),
      },
    ],
  },
  {
    // Day detail is full-screen, outside the tabbed shell.
    path: '/circles/:id/day/:date',
    component: () => import('../views/DayDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/join/:token',
    component: () => import('../views/JoinView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    component: () => import('../views/ProfileSettingsView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Redirect unauthenticated users to /login rather than
// calling signinRedirect() directly from the guard.
// Calling signinRedirect (which sets window.location.href)
// and then returning false causes Vue Router to call
// history.go(-1), which races with the browser navigation
// and produces an infinite redirect loop.
router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true
  const user = await userManager.getUser()
  if (!user || user.expired) {
    return {
      path: '/login',
      query: { returnTo: to.fullPath },
    }
  }
  return true
})

export default router
