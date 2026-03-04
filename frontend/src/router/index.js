import { createRouter, createWebHistory } from 'vue-router'
import ScenesPage from '../views/Scenes.vue'
import ChatPage from '../views/ChatPage.vue'

const routes = [
  {
    path: '/',
    name: 'Scenes',
    component: ScenesPage
  },
  {
    path: '/chat',
    name: 'Chat',
    component: ChatPage
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router