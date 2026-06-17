/**
 * Vue Router configuration with OIDC navigation guard.
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { userManager } from '../auth/oidc'
import { useOnboarding } from '../composables/useOnboarding'

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
    path: '/confirm-email',
    component: () => import('../views/ConfirmEmailView.vue'),
    meta: { title: 'Confirm email' },
  },
  {
    path: '/welcome',
    component: () => import('../views/WelcomeView.vue'),
    meta: { requiresAuth: true, title: 'Welcome' },
  },
  {
    path: '/circles',
    component: () => import('../views/CirclesView.vue'),
    meta: { requiresAuth: true, title: 'Circles' },
  },
  {
    // Full-page create form. Declared before /circles/:id so the static
    // `new` segment is never captured as a circle id.
    path: '/circles/new',
    component: () => import('../views/CircleFormView.vue'),
    meta: { requiresAuth: true, title: 'New circle' },
  },
  {
    // Full-page edit form, outside the tabbed shell.
    path: '/circles/:id/edit',
    component: () => import('../views/CircleFormView.vue'),
    meta: { requiresAuth: true, title: 'Edit circle' },
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
  // Legal pages are public (reachable pre-login) and currently stubs.
  {
    path: '/legal/terms',
    component: () => import('../views/LegalTermsView.vue'),
    meta: { title: 'Terms of Service' },
  },
  {
    path: '/legal/privacy',
    component: () => import('../views/LegalPrivacyView.vue'),
    meta: { title: 'Privacy Policy' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Authed routes that must never be bounced to the welcome intro:
// /welcome itself (avoids a redirect loop) and the invite flow
// (/join/:token), so a freshly-authenticated invitee can complete the
// join first and only then sees /welcome on the next navigation.
const ONBOARDING_EXEMPT = new Set(['/welcome'])

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
  // Authenticated: gate brand-new users into the welcome intro. This
  // lives in the guard — not App.vue's one-shot onMounted — so it fires
  // on every authed landing, including the client-side redirect out of
  // /auth/callback, which does not remount the root component. Loading
  // is idempotent and non-throwing; an unknown state never redirects.
  if (!ONBOARDING_EXEMPT.has(to.path) && !to.path.startsWith('/join/')) {
    const onboarding = useOnboarding()
    await onboarding.ensureLoaded()
    if (onboarding.loaded.value && !onboarding.welcomeSeen.value) {
      return { path: '/welcome' }
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
