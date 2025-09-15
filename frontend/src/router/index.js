import { createRouter, createWebHistory } from 'vue-router'
import FileUpload from '@/components/FileUpload.vue'
import Home from '@/components/Home.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/upload',
      name: 'file-upload',
      component: FileUpload
    }
  ],
})

export default router
