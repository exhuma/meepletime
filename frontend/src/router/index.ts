/**
 * Vue Router configuration with OIDC navigation guard.
 */
import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from 'vue-router'
import { userManager } from '../auth/oidc'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/circles',
  },
  {
    path: '/auth/callback',
    component: () =>
      import('../views/AuthCallbackView.vue'),
  },
  {
    path: '/circles',
    component: () => import('../views/CirclesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/circles/:id',
    component: () =>
      import('../views/CircleCalendarView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/circles/:id/day/:date',
    component: () =>
      import('../views/DayDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/join/:token',
    component: () => import('../views/JoinView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true
  const user = await userManager.getUser()
  if (!user || user.expired) {
    await userManager.signinRedirect({
      state: to.fullPath,
    })
    return false
  }
  return true
})

export default router
