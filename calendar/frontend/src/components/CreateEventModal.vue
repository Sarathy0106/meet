<template>
  <div
    v-if="eventsStore.isCreateModalOpen"
    class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 select-none animate-in fade-in duration-150"
    @click.self="eventsStore.closeCreateModal()"
  >
    <div class="w-full max-w-xl bg-white border border-cal-border rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
        <h2 class="text-base font-semibold text-gray-800">Add Event</h2>
        <button
          @click="eventsStore.closeCreateModal()"
          class="p-1.5 rounded-full hover:bg-gray-200 text-gray-400 hover:text-gray-700 transition-colors"
        >
          <X :size="18" />
        </button>
      </div>

      <!-- Form Body -->
      <form @submit.prevent="handleSubmit" class="p-6 overflow-y-auto space-y-5">
        <!-- Title -->
        <div>
          <input
            v-model="form.title"
            type="text"
            required
            placeholder="Add title"
            class="w-full px-3 py-2 text-xl font-medium text-gray-900 border-b-2 border-gray-200 focus:border-cal-blue outline-none transition-colors placeholder:text-gray-400"
          />
        </div>

        <!-- Date & Time Row -->
        <div class="space-y-3 p-3.5 bg-gray-50/70 rounded-xl border border-gray-100">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 text-xs font-semibold text-gray-600">
              <Clock :size="15" class="text-cal-blue" />
              <span>Date & Time</span>
            </div>
            <label class="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
              <input
                v-model="form.all_day"
                type="checkbox"
                class="rounded text-cal-blue focus:ring-0 cursor-pointer"
              />
              <span>All day</span>
            </label>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <!-- Start -->
            <div class="space-y-1">
              <label class="text-[11px] font-medium text-gray-500">Starts</label>
              <div class="flex items-center gap-2">
                <input
                  v-model="form.startDate"
                  type="date"
                  required
                  class="w-full px-2.5 py-1.5 bg-white border border-gray-300 rounded-lg text-xs outline-none focus:border-cal-blue"
                />
                <input
                  v-if="!form.all_day"
                  v-model="form.startTime"
                  type="time"
                  required
                  class="w-28 px-2 py-1.5 bg-white border border-gray-300 rounded-lg text-xs outline-none focus:border-cal-blue"
                />
              </div>
            </div>

            <!-- End -->
            <div class="space-y-1">
              <label class="text-[11px] font-medium text-gray-500">Ends</label>
              <div class="flex items-center gap-2">
                <input
                  v-model="form.endDate"
                  type="date"
                  required
                  class="w-full px-2.5 py-1.5 bg-white border border-gray-300 rounded-lg text-xs outline-none focus:border-cal-blue"
                />
                <input
                  v-if="!form.all_day"
                  v-model="form.endTime"
                  type="time"
                  required
                  class="w-28 px-2 py-1.5 bg-white border border-gray-300 rounded-lg text-xs outline-none focus:border-cal-blue"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Add Video Conferencing Switch (Sidaz Meet) -->
        <div class="p-3.5 bg-blue-50/60 border border-blue-100 rounded-xl flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-xl bg-blue-500 text-white shadow-sm">
              <Video :size="18" />
            </div>
            <div>
              <p class="text-xs font-semibold text-gray-800">Add Sidaz Meet video conferencing</p>
              <p class="text-[11px] text-gray-500">Automatically creates a high-definition video meeting room</p>
            </div>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input
              v-model="form.add_video"
              type="checkbox"
              class="sr-only peer"
            />
            <div class="w-10 h-5 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cal-blue"></div>
          </label>
        </div>

        <!-- Add Attendees / Guests -->
        <div class="space-y-2">
          <label class="block text-xs font-semibold text-gray-600 flex items-center gap-1.5">
            <Users :size="14" class="text-cal-blue" />
            <span>Add Guests / Attendees</span>
          </label>
          <div class="flex items-center gap-2">
            <input
              v-model="newAttendeeEmail"
              type="email"
              placeholder="Enter attendee email and press enter"
              class="flex-1 px-3 py-2 bg-white border border-gray-300 rounded-lg text-xs outline-none focus:border-cal-blue"
              @keydown.enter.prevent="handleAddAttendee"
            />
            <button
              @click.prevent="handleAddAttendee"
              type="button"
              class="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium rounded-lg transition-colors"
            >
              Add
            </button>
          </div>

          <!-- Attendee Email Chips -->
          <div v-if="form.attendees.length > 0" class="flex flex-wrap gap-1.5 pt-1">
            <span
              v-for="(att, idx) in form.attendees"
              :key="idx"
              class="inline-flex items-center gap-1 px-2.5 py-1 bg-gray-100 border border-gray-200 rounded-full text-xs text-gray-700 font-medium"
            >
              <span>{{ att.email }}</span>
              <button
                @click="removeAttendee(idx)"
                type="button"
                class="hover:text-red-500 text-gray-400"
              >
                <X :size="12" />
              </button>
            </span>
          </div>
          <p class="text-[11px] text-gray-400">
            ✉️ External attendees will receive an email invitation with an .ics file attached.
          </p>
        </div>

        <!-- Recurrence & Reminder Options -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <!-- Recurrence -->
          <div class="space-y-1">
            <label class="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
              <Repeat :size="14" class="text-cal-blue" />
              <span>Repeat</span>
            </label>
            <select
              v-model="form.recurrence_type"
              class="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-xs outline-none focus:border-cal-blue"
            >
              <option value="none">Does not repeat</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>

          <!-- Reminder -->
          <div class="space-y-1">
            <label class="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
              <Bell :size="14" class="text-cal-blue" />
              <span>Notification</span>
            </label>
            <select
              v-model="form.reminder_minutes_before"
              class="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-xs outline-none focus:border-cal-blue"
            >
              <option :value="5">5 minutes before</option>
              <option :value="10">10 minutes before</option>
              <option :value="15">15 minutes before</option>
              <option :value="30">30 minutes before</option>
              <option :value="60">1 hour before</option>
              <option :value="1440">1 day before</option>
            </select>
          </div>
        </div>

        <!-- Location -->
        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
            <MapPin :size="14" class="text-cal-blue" />
            <span>Location</span>
          </label>
          <input
            v-model="form.location"
            type="text"
            placeholder="Add location or room"
            class="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-xs outline-none focus:border-cal-blue"
          />
        </div>

        <!-- Description -->
        <div class="space-y-1">
          <label class="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
            <AlignLeft :size="14" class="text-cal-blue" />
            <span>Description</span>
          </label>
          <textarea
            v-model="form.description"
            rows="2"
            placeholder="Add description or notes"
            class="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-xs outline-none focus:border-cal-blue resize-none"
          ></textarea>
        </div>

        <!-- Color & Calendar Pickers -->
        <div class="flex items-center justify-between pt-2 border-t border-gray-100">
          <!-- Color palette -->
          <div class="flex items-center gap-1.5">
            <button
              v-for="c in colorOptions"
              :key="c"
              type="button"
              @click="form.color = c"
              class="w-5 h-5 rounded-full transition-transform"
              :class="form.color === c ? 'ring-2 ring-offset-1 ring-gray-600 scale-110' : 'hover:scale-105'"
              :style="{ backgroundColor: c }"
            ></button>
          </div>

          <!-- Calendar selector -->
          <select
            v-model="form.calendar_id"
            class="px-2 py-1 bg-gray-50 border border-gray-200 rounded text-xs text-gray-700 outline-none"
          >
            <option
              v-for="cal in eventsStore.calendars"
              :key="cal.id"
              :value="cal.id"
            >
              {{ cal.name }}
            </option>
          </select>
        </div>

        <!-- Footer Actions -->
        <div class="flex items-center justify-end gap-2 pt-4">
          <button
            @click="eventsStore.closeCreateModal()"
            type="button"
            class="px-4 py-2 text-xs font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="isSubmitting || !form.title.trim()"
            class="px-6 py-2 bg-cal-blue hover:bg-cal-blueHover disabled:opacity-50 text-white text-xs font-semibold rounded-full shadow transition-all flex items-center gap-2"
          >
            <span v-if="isSubmitting" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
            <span>Save</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { X, Clock, Video, Users, Repeat, Bell, MapPin, AlignLeft } from 'lucide-vue-next'
import { useEventsStore } from '@/stores/events'

const eventsStore = useEventsStore()
const isSubmitting = ref(false)
const newAttendeeEmail = ref('')

const colorOptions = ['#1a73e8', '#0b8043', '#8e24aa', '#d93025', '#f6bf26', '#3f51b5']

function formatLocalDate(date: Date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function formatLocalTime(date: Date) {
  const h = String(date.getHours()).padStart(2, '0')
  const m = String(date.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}

const form = ref({
  title: '',
  calendar_id: eventsStore.calendars[0]?.id || '',
  startDate: formatLocalDate(new Date()),
  startTime: '09:00',
  endDate: formatLocalDate(new Date()),
  endTime: '10:00',
  all_day: false,
  add_video: true,
  recurrence_type: 'none',
  reminder_minutes_before: 10,
  location: '',
  description: '',
  color: '#1a73e8',
  attendees: [] as { email: string }[],
})

function initForm(initDate: Date) {
  const start = new Date(initDate)
  start.setMinutes(0, 0, 0)
  start.setHours(start.getHours() + 1)

  const end = new Date(start)
  end.setHours(end.getHours() + 1)

  form.value = {
    title: '',
    calendar_id: eventsStore.calendars[0]?.id || '',
    startDate: formatLocalDate(start),
    startTime: formatLocalTime(start),
    endDate: formatLocalDate(end),
    endTime: formatLocalTime(end),
    all_day: false,
    add_video: true,
    recurrence_type: 'none',
    reminder_minutes_before: 10,
    location: '',
    description: '',
    color: '#1a73e8',
    attendees: [],
  }
}

watch(
  () => eventsStore.isCreateModalOpen,
  (open) => {
    if (open) {
      initForm(eventsStore.createModalDefaultDate)
    }
  }
)

function handleAddAttendee() {
  const email = newAttendeeEmail.value.trim().toLowerCase()
  if (email && email.includes('@')) {
    if (!form.value.attendees.some((a) => a.email === email)) {
      form.value.attendees.push({ email })
    }
    newAttendeeEmail.value = ''
  }
}

function removeAttendee(index: number) {
  form.value.attendees.splice(index, 1)
}

async function handleSubmit() {
  if (!form.value.title.trim()) return

  isSubmitting.value = true
  try {
    let startAt: string
    let endAt: string

    if (form.value.all_day) {
      startAt = new Date(`${form.value.startDate}T00:00:00`).toISOString()
      endAt = new Date(`${form.value.endDate}T23:59:59`).toISOString()
    } else {
      startAt = new Date(`${form.value.startDate}T${form.value.startTime}:00`).toISOString()
      endAt = new Date(`${form.value.endDate}T${form.value.endTime}:00`).toISOString()
    }

    let recurrenceRule: string | null = null
    if (form.value.recurrence_type === 'daily') {
      recurrenceRule = 'FREQ=DAILY'
    } else if (form.value.recurrence_type === 'weekly') {
      recurrenceRule = 'FREQ=WEEKLY'
    } else if (form.value.recurrence_type === 'monthly') {
      recurrenceRule = 'FREQ=MONTHLY'
    }

    await eventsStore.createEvent({
      calendar_id: form.value.calendar_id || undefined,
      title: form.value.title.trim(),
      description: form.value.description.trim() || undefined,
      location: form.value.location.trim() || undefined,
      start_at: startAt,
      end_at: endAt,
      all_day: form.value.all_day,
      recurrence_rule: recurrenceRule,
      reminder_minutes_before: form.value.reminder_minutes_before,
      color: form.value.color,
      add_video: form.value.add_video,
      attendees: form.value.attendees.map((a) => ({ email: a.email })),
    })

    eventsStore.closeCreateModal()
  } catch (e) {
    console.error('Error creating event:', e)
  } finally {
    isSubmitting.value = false
  }
}
</script>
