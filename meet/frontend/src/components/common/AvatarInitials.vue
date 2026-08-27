<template>
  <div
    class="flex items-center justify-center rounded-full font-medium text-white select-none shrink-0"
    :class="[sizeClass, customClass]"
    :style="{ backgroundColor: bgColor }"
  >
    {{ initials }}
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    name: string
    size?: 'sm' | 'md' | 'lg' | 'xl' | '2xl'
    customClass?: string
  }>(),
  {
    size: 'md',
    customClass: '',
  }
)

const colors = [
  '#d93025', // Red
  '#188038', // Green
  '#1a73e8', // Blue
  '#e37400', // Orange
  '#9334e6', // Purple
  '#129eaf', // Cyan
  '#c5221f', // Dark Red
  '#e52592', // Pink
  '#0d652d', // Dark Green
  '#f29900', // Yellow/Orange
]

const bgColor = computed(() => {
  if (!props.name) return colors[0]
  let hash = 0
  for (let i = 0; i < props.name.length; i++) {
    hash = props.name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % colors.length
  return colors[index]
})

const initials = computed(() => {
  if (!props.name) return '?'
  const parts = props.name.trim().split(/\s+/)
  if (parts.length === 1) {
    return parts[0].substring(0, 2).toUpperCase()
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
})

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'w-7 h-7 text-xs'
    case 'md':
      return 'w-10 h-10 text-sm'
    case 'lg':
      return 'w-16 h-16 text-xl'
    case 'xl':
      return 'w-24 h-24 text-3xl'
    case '2xl':
      return 'w-32 h-32 text-4xl font-semibold'
    default:
      return 'w-10 h-10 text-sm'
  }
})
</script>
