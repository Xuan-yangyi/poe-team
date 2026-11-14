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
        // Work orders
        {
          path: 'work-orders',
          name: 'work-orders',
          component: () => import('@/views/WorkOrderList.vue'),
        },
        {
          path: 'work-orders/:id',
          name: 'work-order-detail',
          component: () => import('@/views/WorkOrderDetail.vue'),
        },
        // Shipments
        {
          path: 'shipments',
          name: 'shipments',
          component: () => import('@/views/ShipmentList.vue'),
        },
        {
          path: 'shipments/:id',
          name: 'shipment-detail',
          component: () => import('@/views/ShipmentDetail.vue'),
        },
        // Inventory
        {
          path: 'inventory',
          name: 'inventory',
          component: () => import('@/views/InventoryStock.vue'),
        },
        // Production
        {
          path: 'production',
          name: 'production',
          component: () => import('@/views/ProductionPage.vue'),
        },
        // Reconciliation
        {
          path: 'reconciliation',
          name: 'reconciliation',
          component: () => import('@/views/ReconciliationPage.vue'),
        },
        // Conversations
        {
          path: 'conversations',
          name: 'conversations',
          component: () => import('@/views/ConversationPage.vue'),
        },
        // Alerts
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