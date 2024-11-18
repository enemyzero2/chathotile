import { createRouter, createWebHashHistory } from 'vue-router'
import Chat from '../views/Chat.vue'
import UserSettings from '../views/usersettings.vue'

const routes = [
  {
    path: '/',
    name: 'Chat',
    component: Chat
  },
  {
    path: '/settings',
    name: 'Settings',
    component: UserSettings
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
});

export default router
