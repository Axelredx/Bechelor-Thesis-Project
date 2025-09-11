import { createRouter, createWebHistory } from 'vue-router'
import FileUpload from '@/components/FileUpload.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: FileUpload,
    }
  ],
})

export default router
