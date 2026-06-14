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
    meta: { title: 'Sign in' },
  },
  {
    path: '/auth/callback',
    component: () => import('../views/AuthCallbackView.vue'),
  },
  {
    path: '/circles',
    component: () => import('../views/CirclesView.vue'),
    meta: { requiresAuth: true, title: 'Circles' },
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
        meta: { title: 'Calendar' },
      },
      {
        path: 'list',
        component: () => import('../views/CircleListView.vue'),
        meta: { title: 'List' },
      },
    ],
  },
  {
    // Day detail is full-screen, outside the tabbed shell.
    path: '/circles/:id/day/:date',
    component: () => import('../views/DayDetailView.vue'),
    meta: { requiresAuth: true, title: 'Day' },
  },
  {
    path: '/join/:token',
    component: () => import('../views/JoinView.vue'),
    meta: { requiresAuth: true, title: 'Join circle' },
  },
  {
    path: '/profile',
    component: () => import('../views/ProfileSettingsView.vue'),
    meta: { requiresAuth: true, title: 'Profile' },
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

// Keep the browser tab title in sync with the active route. The leaf
// child's title wins over the parent shell (reverse-scan `matched`);
// circle pages later refine this to the circle name once it loads.
router.afterEach((to) => {
  const match = [...to.matched].reverse().find((r) => r.meta.title)
  const title = match?.meta.title as string | undefined
  document.title = title ? `${title} · MeepleTime` : 'MeepleTime'
})

export default router
