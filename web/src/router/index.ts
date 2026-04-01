import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/views/MainLayout.vue'),
      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/HomePage.vue'),
        },
        {
          path: 'multi',
          name: 'multi',
          component: () => import('@/views/MultiImageView.vue'),
        },
        {
          path: 'gallery',
          name: 'gallery',
          component: () => import('@/views/GalleryView.vue'),
        },
        {
          path: 'scenes',
          name: 'scenes',
          component: () => import('@/views/SceneLibraryView.vue'),
        },
        {
          path: 'pricing',
          name: 'pricing',
          component: () => import('@/views/PricingView.vue'),
        },
      ],
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
    },
    {
      path: '/user-center',
      name: 'user-center',
      component: () => import('@/views/UserCenter.vue'),
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('@/views/AdminPanel.vue'),
    },
  ],
})

export default router
