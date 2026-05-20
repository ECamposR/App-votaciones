import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import LoginView from '../views/LoginView.vue'
import SetupView from '../views/SetupView.vue'
import { AppShell } from '../shell'
import DashboardView from '../views/admin/DashboardView.vue'
import PollDetailView from '../views/admin/PollDetailView.vue'
import ImportView from '../views/admin/ImportView.vue'
import UsersView from '../views/admin/UsersView.vue'

export function createAppRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
      { path: '/setup', name: 'setup', component: SetupView, meta: { public: true } },
      {
        path: '/',
        component: AppShell,
        children: [
          { path: '', redirect: { name: 'dashboard' } },
          { path: 'admin', redirect: { name: 'dashboard' } },
          { path: 'admin/dashboard', name: 'dashboard', component: DashboardView },
          { path: 'admin/polls/:id', name: 'poll-detail', component: PollDetailView, props: true },
          { path: 'admin/import', name: 'import', component: ImportView },
          { path: 'admin/users', name: 'users', component: UsersView },
        ],
      },
    ],
  })
}

export function installRouteGuards(router, pinia) {
  router.beforeEach(async (to) => {
    const authStore = useAuthStore(pinia)

    if ((to.name === 'login' || to.name === 'setup') && authStore.user) {
      return { name: 'dashboard' }
    }

    if (to.name === 'setup' && authStore.hasSetup === true) {
      return { name: 'login' }
    }

    if (authStore.hasSetup === false && to.name !== 'setup') {
      return { name: 'setup' }
    }

    if (to.meta.public) {
      return true
    }

    if (!authStore.user) {
      return { name: 'login' }
    }

    return true
  })
}
