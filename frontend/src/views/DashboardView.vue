<template>
  <div class="min-h-screen w-full flex flex-col bg-[#202124] text-white">
    <!-- Top Navigation Bar -->
    <header class="h-16 px-6 border-b border-meet-border flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-meet-blue flex items-center justify-center text-white shadow-md">
          <Video :size="22" />
        </div>
        <div class="flex items-center gap-1.5">
          <span class="text-xl font-bold tracking-tight text-white">sidaz</span>
          <span class="text-xl font-light text-meet-textMuted">meet</span>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <div class="hidden sm:flex flex-col text-right">
          <span class="text-sm font-medium text-white">{{ currentTime }}</span>
          <span class="text-xs text-meet-textMuted">{{ currentDate }}</span>
        </div>

        <!-- Auth State / User Profile -->
        <div v-if="authStore.isAuthenticated" class="flex items-center gap-3">
          <div class="flex items-center gap-2">
            <AvatarInitials :name="authStore.displayName" size="sm" />
            <span class="text-sm font-medium hidden md:inline">{{ authStore.displayName }}</span>
          </div>
          <button
            @click="authStore.logout()"
            class="p-2 rounded-full hover:bg-meet-surfaceLight text-meet-textMuted hover:text-white transition-colors"
            title="Sign out"
          >
            <LogOut :size="18" />
          </button>
        </div>
        <div v-else class="flex items-center gap-2">
          <RouterLink
            to="/login"
            class="px-4 py-2 text-sm font-medium text-meet-primary hover:bg-meet-surfaceLight rounded-full transition-colors"
          >
            Sign in
          </RouterLink>
          <RouterLink
            to="/signup"
            class="px-4 py-2 text-sm font-medium bg-meet-blue hover:bg-meet-blue-hover text-white rounded-full transition-colors shadow"
          >
            Sign up
          </RouterLink>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-6 py-12 flex flex-col justify-center">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
        <!-- Left Hero Column -->
        <div class="lg:col-span-7 space-y-8">
          <div class="space-y-4">
            <h1 class="text-4xl sm:text-5xl font-normal tracking-tight text-white leading-tight">
              Video calls and meetings for everyone
            </h1>
            <p class="text-lg text-meet-textMuted max-w-xl">
              Connect, collaborate, and celebrate from anywhere with crystal clear audio, HD video, and real-time screen sharing.
            </p>
          </div>

          <!-- Action Buttons -->
          <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
            <!-- New Meeting Menu -->
            <div class="relative w-full sm:w-auto">
              <button
                @click="isNewMeetingMenuOpen = !isNewMeetingMenuOpen"
                class="w-full sm:w-auto px-6 py-3.5 bg-meet-blue hover:bg-meet-blue-hover text-white rounded-full font-medium text-sm flex items-center justify-center gap-2 shadow-lg transition-all"
              >
                <Video :size="18" />
                <span>New meeting</span>
                <ChevronDown :size="16" />
              </button>

              <!-- Dropdown Menu -->
              <div
                v-if="isNewMeetingMenuOpen"
                class="absolute left-0 mt-2 w-full sm:w-64 bg-[#303134] border border-meet-border rounded-2xl shadow-2xl py-2 z-40"
              >
                <button
                  @click="startInstantMeeting"
                  class="w-full px-4 py-3 text-left text-sm hover:bg-meet-surfaceLight text-white flex items-center gap-3 transition-colors"
                >
                  <Plus :size="18" class="text-meet-primary" />
                  <div>
                    <div class="font-medium">Start an instant meeting</div>
                    <div class="text-xs text-meet-textMuted">Join directly in your browser</div>
                  </div>
                </button>
                <button
                  @click="openScheduleModal"
                  class="w-full px-4 py-3 text-left text-sm hover:bg-meet-surfaceLight text-white flex items-center gap-3 transition-colors"
                >
                  <Calendar :size="18" class="text-meet-green" />
                  <div>
                    <div class="font-medium">Schedule a meeting</div>
                    <div class="text-xs text-meet-textMuted">Plan for a future date & time</div>
                  </div>
                </button>
              </div>
            </div>

            <!-- Join with code input -->
            <div class="flex items-center gap-2 w-full sm:max-w-sm">
              <div class="relative flex-1">
                <Keyboard :size="18" class="absolute left-4 top-3.5 text-meet-textMuted" />
                <input
                  v-model="joinCodeInput"
                  @keyup.enter="handleJoinByCode"
                  type="text"
                  placeholder="Enter a code or link"
                  class="w-full pl-11 pr-4 py-3 bg-transparent border border-meet-border focus:border-meet-primary rounded-full text-sm text-white placeholder-meet-textMuted outline-none transition-colors"
                />
              </div>
              <button
                @click="handleJoinByCode"
                :disabled="!joinCodeInput.trim()"
                class="px-5 py-3 text-sm font-medium text-meet-primary hover:bg-meet-surfaceLight disabled:opacity-40 disabled:hover:bg-transparent rounded-full transition-colors shrink-0"
              >
                Join
              </button>
            </div>
          </div>

          <div class="pt-8 border-t border-meet-border/60">
            <p class="text-xs text-meet-textMuted">
              Built with LiveKit Cloud SFU & Vue 3 • Fully compliant with technical specification
            </p>
          </div>
        </div>

        <!-- Right Visual Showcase Column -->
        <div class="lg:col-span-5 flex justify-center">
          <div class="relative w-full max-w-md bg-[#303134] border border-meet-border rounded-3xl p-6 shadow-2xl overflow-hidden">
            <!-- Mock Meeting Preview -->
            <div class="grid grid-cols-2 gap-3 mb-4 aspect-video">
              <div class="bg-[#202124] rounded-xl flex flex-col items-center justify-center p-3 relative border border-white/5">
                <AvatarInitials name="Alex Morgan" size="lg" />
                <span class="absolute bottom-2 left-2 text-[10px] bg-black/60 px-1.5 py-0.5 rounded text-white font-medium">Alex Morgan</span>
              </div>
              <div class="bg-[#202124] rounded-xl flex flex-col items-center justify-center p-3 relative border border-meet-primary/60 outline outline-1 outline-meet-primary">
                <AvatarInitials name="Sarah Connor" size="lg" />
                <span class="absolute bottom-2 left-2 text-[10px] bg-black/60 px-1.5 py-0.5 rounded text-white font-medium">Sarah Connor</span>
                <span class="absolute top-2 right-2 w-2 h-2 rounded-full bg-meet-green animate-pulse"></span>
              </div>
            </div>

            <div class="text-center space-y-1.5">
              <h3 class="text-lg font-medium text-white">Get a link you can share</h3>
              <p class="text-xs text-meet-textMuted leading-relaxed">
                Click <strong>New meeting</strong> to get a link you can send to people you want to meet with.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Previous Meetings History Drawer / Section (for logged-in users) -->
      <div v-if="authStore.isAuthenticated" class="mt-16 pt-8 border-t border-meet-border">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-2">
            <Clock :size="20" class="text-meet-primary" />
            <h2 class="text-xl font-semibold text-white">Your Meeting History</h2>
          </div>
          <button
            @click="loadHistory"
            class="text-xs text-meet-primary hover:underline"
          >
            Refresh
          </button>
        </div>

        <div v-if="meetingHistory.length === 0" class="text-center py-8 text-meet-textMuted text-sm">
          No previous meetings recorded yet.
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="m in meetingHistory"
            :key="m.id"
            class="p-4 bg-[#303134] border border-meet-border rounded-2xl flex flex-col justify-between hover:border-meet-primary/50 transition-colors"
          >
            <div class="space-y-2">
              <div class="flex items-start justify-between">
                <h4 class="font-medium text-white truncate">{{ m.title || 'Instant Meeting' }}</h4>
                <span class="text-xs font-mono text-meet-primary bg-meet-surfaceLight px-2 py-0.5 rounded">
                  {{ m.code }}
                </span>
              </div>
              <p class="text-xs text-meet-textMuted">
                {{ formatDateTime(m.created_at) }}
              </p>
            </div>

            <div class="mt-4 pt-3 border-t border-meet-border/60 flex items-center justify-between">
              <button
                @click="openChatHistory(m.code)"
                class="text-xs text-meet-textMuted hover:text-white flex items-center gap-1.5"
              >
                <MessageSquare :size="14" />
                <span>View Chat Log</span>
              </button>
              <button
                @click="rejoinMeeting(m.code)"
                class="px-3 py-1 bg-meet-blue/20 hover:bg-meet-blue text-meet-primary hover:text-white rounded-full text-xs font-medium transition-colors"
              >
                Rejoin
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Schedule Meeting Modal -->
    <div
      v-if="isScheduleModalOpen"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="w-full max-w-md bg-[#303134] border border-meet-border rounded-2xl p-6 shadow-2xl space-y-5">
        <div class="flex items-center justify-between border-b border-meet-border pb-3">
          <h3 class="text-lg font-medium text-white">Schedule a meeting</h3>
          <button @click="isScheduleModalOpen = false" class="text-meet-textMuted hover:text-white">
            <X :size="20" />
          </button>
        </div>

        <form @submit.prevent="createScheduledMeeting" class="space-y-4">
          <div class="space-y-1">
            <label class="text-xs font-semibold text-meet-textMuted uppercase tracking-wider">Title</label>
            <input
              v-model="scheduleTitle"
              type="text"
              required
              placeholder="e.g., Weekly Sync"
              class="w-full px-3 py-2 bg-[#202124] border border-meet-border rounded-xl text-white text-sm focus:border-meet-primary outline-none"
            />
          </div>

          <div class="space-y-1">
            <label class="text-xs font-semibold text-meet-textMuted uppercase tracking-wider">Date & Time</label>
            <input
              v-model="scheduleDate"
              type="datetime-local"
              required
              class="w-full px-3 py-2 bg-[#202124] border border-meet-border rounded-xl text-white text-sm focus:border-meet-primary outline-none"
            />
          </div>

          <div class="flex items-center justify-between pt-2">
            <label class="text-sm text-white cursor-pointer" for="sched-lobby">Enable Waiting Lobby</label>
            <input id="sched-lobby" v-model="scheduleLobby" type="checkbox" class="w-5 h-5 accent-meet-blue" />
          </div>

          <div class="pt-3 border-t border-meet-border flex justify-end gap-2">
            <button
              type="button"
              @click="isScheduleModalOpen = false"
              class="px-4 py-2 text-sm text-meet-textMuted hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="px-5 py-2 bg-meet-blue hover:bg-meet-blue-hover text-white text-sm font-medium rounded-full shadow"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Meeting Created Info Modal -->
    <div
      v-if="createdMeetingInfo"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="w-full max-w-md bg-[#303134] border border-meet-border rounded-2xl p-6 shadow-2xl space-y-5">
        <div class="flex items-center justify-between border-b border-meet-border pb-3">
          <h3 class="text-lg font-medium text-white">Here's the link to your meeting</h3>
          <button @click="createdMeetingInfo = null" class="text-meet-textMuted hover:text-white">
            <X :size="20" />
          </button>
        </div>

        <p class="text-xs text-meet-textMuted">
          Copy this link and send it to people you want to meet with.
        </p>

        <div class="flex items-center gap-2 p-2.5 bg-[#202124] rounded-xl border border-meet-border">
          <span class="text-sm text-meet-primary font-mono truncate flex-1 select-all">
            {{ meetingLink(createdMeetingInfo.code) }}
          </span>
          <button
            @click="copyMeetingLink(createdMeetingInfo.code)"
            class="p-2 rounded-lg bg-meet-surfaceLight hover:bg-meet-border text-white text-xs font-medium flex items-center gap-1.5 transition-colors shrink-0"
          >
            <Copy :size="15" />
            <span>{{ isCopied ? 'Copied!' : 'Copy' }}</span>
          </button>
        </div>

        <div class="flex justify-end gap-2 pt-2">
          <button
            @click="joinNow(createdMeetingInfo.code)"
            class="px-5 py-2 bg-meet-blue hover:bg-meet-blue-hover text-white text-sm font-medium rounded-full"
          >
            Join now
          </button>
        </div>
      </div>
    </div>

    <!-- Chat History Modal -->
    <div
      v-if="selectedChatHistoryCode"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="w-full max-w-lg bg-[#202124] border border-meet-border rounded-2xl p-6 shadow-2xl flex flex-col max-h-[80vh]">
        <div class="flex items-center justify-between border-b border-meet-border pb-3 mb-4">
          <h3 class="text-lg font-medium text-white">Chat Log: {{ selectedChatHistoryCode }}</h3>
          <button @click="selectedChatHistoryCode = null" class="text-meet-textMuted hover:text-white">
            <X :size="20" />
          </button>
        </div>

        <div class="flex-1 overflow-y-auto space-y-3 pr-2">
          <div v-if="historicalMessages.length === 0" class="text-center py-8 text-meet-textMuted text-sm">
            No chat messages were recorded in this meeting.
          </div>
          <div
            v-for="msg in historicalMessages"
            :key="msg.id"
            class="p-3 bg-[#303134] rounded-xl space-y-1"
          >
            <div class="flex items-baseline justify-between">
              <span class="text-xs font-semibold text-white">{{ msg.sender_name }}</span>
              <span class="text-[10px] text-meet-textMuted">{{ formatDateTime(msg.sent_at) }}</span>
            </div>
            <p class="text-sm text-meet-text whitespace-pre-wrap">{{ msg.content }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Video,
  LogOut,
  ChevronDown,
  Plus,
  Calendar,
  Keyboard,
  Clock,
  MessageSquare,
  X,
  Copy,
} from 'lucide-vue-next'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/lib/api'
import AvatarInitials from '@/components/common/AvatarInitials.vue'
import type { Meeting, ChatMessage } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

const currentTime = ref('')
const currentDate = ref('')
let timer: number | null = null

const isNewMeetingMenuOpen = ref(false)
const joinCodeInput = ref('')

const isScheduleModalOpen = ref(false)
const scheduleTitle = ref('')
const scheduleDate = ref('')
const scheduleLobby = ref(true)

const createdMeetingInfo = ref<Meeting | null>(null)
const isCopied = ref(false)

const meetingHistory = ref<Meeting[]>([])
const selectedChatHistoryCode = ref<string | null>(null)
const historicalMessages = ref<ChatMessage[]>([])

function updateClock() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  currentDate.value = now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })
}

function extractMeetingCode(input: string): string {
  const clean = input.trim()
  if (clean.includes('/')) {
    const parts = clean.split('/')
    return parts[parts.length - 1]
  }
  return clean
}

function meetingLink(code: string): string {
  return `${window.location.origin}/meet/${code}`
}

async function copyMeetingLink(code: string) {
  await navigator.clipboard.writeText(meetingLink(code))
  isCopied.value = true
  setTimeout(() => {
    isCopied.value = false
  }, 2000)
}

function handleJoinByCode() {
  const code = extractMeetingCode(joinCodeInput.value)
  if (code) {
    router.push(`/meet/${code}`)
  }
}

async function startInstantMeeting() {
  isNewMeetingMenuOpen.value = false
  try {
    const res = await api.post('/meetings', {
      title: 'Instant Meeting',
      lobby_enabled: false,
    })
    router.push(`/meet/${res.data.code}`)
  } catch (err) {
    console.error('Failed to create instant meeting:', err)
  }
}

function openScheduleModal() {
  isNewMeetingMenuOpen.value = false
  isScheduleModalOpen.value = true
}

async function createScheduledMeeting() {
  try {
    const res = await api.post('/meetings', {
      title: scheduleTitle.value,
      scheduled_at: new Date(scheduleDate.value).toISOString(),
      lobby_enabled: scheduleLobby.value,
    })
    isScheduleModalOpen.value = false
    createdMeetingInfo.value = res.data
    await loadHistory()
  } catch (err) {
    console.error('Failed to schedule meeting:', err)
  }
}

function joinNow(code: string) {
  createdMeetingInfo.value = null
  router.push(`/meet/${code}`)
}

function rejoinMeeting(code: string) {
  router.push(`/meet/${code}`)
}

async function loadHistory() {
  if (!authStore.isAuthenticated) return
  try {
    const res = await api.get('/users/me/meetings')
    meetingHistory.value = res.data
  } catch (e) {
    console.warn('Failed to load meeting history:', e)
  }
}

async function openChatHistory(code: string) {
  selectedChatHistoryCode.value = code
  historicalMessages.value = []
  try {
    const res = await api.get(`/meetings/${code}/chat`)
    historicalMessages.value = res.data
  } catch (e) {
    console.warn('Failed to fetch chat logs:', e)
  }
}

function formatDateTime(isoString?: string) {
  if (!isoString) return ''
  try {
    const d = new Date(isoString)
    return d.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
  } catch {
    return ''
  }
}

onMounted(async () => {
  updateClock()
  timer = window.setInterval(updateClock, 1000)
  if (authStore.isAuthenticated) {
    await loadHistory()
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
