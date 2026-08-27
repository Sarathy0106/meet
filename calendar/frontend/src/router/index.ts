import { createRouter, createWebHistory } from 'vue-router'
import MonthView from '@/views/MonthView.vue'
import WeekView from '@/views/WeekView.vue'
import DayView from '@/views/DayView.vue'
import PublicRsvpView from '@/views/PublicRsvpView.vue'
import LoginView from '@/views/LoginView.vue'

const routes = [
  {
    path: '/',
    name: 'calendar',
    redirect: '/month',
  },
  {
    path: '/month',
    name: 'month',
    component: MonthView,
  },
  {
    path: '/week',
    name: 'week',
    component: WeekView,
  },
  {
    path: '/day',
    name: 'day',
    component: DayView,
  },
  {
    path: '/rsvp/:token',
    name: 'public-rsvp',
    component: PublicRsvpView,
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
})
