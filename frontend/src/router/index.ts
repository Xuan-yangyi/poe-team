import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import MainLayout from '@/layouts/MainLayout.vue'
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/DashboardView.vue'),
        },
        {
          path: 'work-orders',
          name: 'work-orders',
          component: () => import('@/views/WorkOrderList.vue'),
        },
        {
          path: 'shipments',
          name: 'shipments',
          component: () => import('@/views/ShipmentList.vue'),
        },
        {
          path: 'inventory',
          name: 'inventory',
          component: () => import('@/views/InventoryStock.vue'),
        },
        {
          path: 'alerts',
          name: 'alerts',
          component: () => import('@/views/AlertList.vue'),
        },
      ],
    },
  ],
})

// Navigation guard
router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    next()
  } else if (!auth.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router