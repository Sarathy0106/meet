<template>
  <div class="flex items-end gap-0.5 h-3.5 px-1 py-0.5 bg-black/40 backdrop-blur-sm rounded" :title="'Connection: ' + quality">
    <div
      class="w-1 rounded-sm transition-colors duration-200"
      :class="bar1Class"
      style="height: 30%"
    ></div>
    <div
      class="w-1 rounded-sm transition-colors duration-200"
      :class="bar2Class"
      style="height: 65%"
    ></div>
    <div
      class="w-1 rounded-sm transition-colors duration-200"
      :class="bar3Class"
      style="height: 100%"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    quality?: 'excellent' | 'good' | 'poor' | 'unknown'
  }>(),
  {
    quality: 'good',
  }
)

const bar1Class = computed(() => {
  if (props.quality === 'poor') return 'bg-meet-red'
  if (props.quality === 'good' || props.quality === 'excellent') return 'bg-meet-green'
  return 'bg-gray-500'
})

const bar2Class = computed(() => {
  if (props.quality === 'good' || props.quality === 'excellent') return 'bg-meet-green'
  return 'bg-gray-600'
})

const bar3Class = computed(() => {
  if (props.quality === 'excellent') return 'bg-meet-green'
  return 'bg-gray-600'
})
</script>
