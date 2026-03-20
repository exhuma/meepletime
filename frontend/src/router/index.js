import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: () => {
    const token = localStorage.getItem('meepletime_token')
    return token ? '/circles' : '/login'
  }},
  { path: '/login', component: () => import('../views/LoginView.vue') },
  { path: '/register', component: () => import('../views/RegisterView.vue') },
  { path: '/circles', component: () => import('../views/CirclesView.vue'), meta: { requiresAuth: true } },
  { path: '/circles/:id', component: () => import('../views/CircleCalendarView.vue'), meta: { requiresAuth: true } },
  { path: '/circles/:id/day/:date', component: () => import('../views/DayDetailView.vue'), meta: { requiresAuth: true } },
  { path: '/join/:token', component: () => import('../views/JoinView.vue'), meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  if (to.meta.requiresAuth && !localStorage.getItem('meepletime_token')) {
    next('/login')
  } else {
    next()
  }
})

export default router
