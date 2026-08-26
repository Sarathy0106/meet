import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import LoginView from '@/views/LoginView.vue'
import SignupView from '@/views/SignupView.vue'
import PreJoinView from '@/views/PreJoinView.vue'
import MeetingRoomView from '@/views/MeetingRoomView.vue'
import LobbyWaitingView from '@/views/LobbyWaitingView.vue'
import PostMeetingView from '@/views/PostMeetingView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: DashboardView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/signup',
      name: 'signup',
      component: SignupView,
    },
    {
      path: '/meet/:code',
      name: 'prejoin',
      component: PreJoinView,
    },
    {
      path: '/meet/:code/room',
      name: 'room',
      component: MeetingRoomView,
    },
    {
      path: '/meet/:code/waiting',
      name: 'waiting',
      component: LobbyWaitingView,
    },
    {
      path: '/meet/:code/post',
      name: 'post-meeting',
      component: PostMeetingView,
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

export default router
