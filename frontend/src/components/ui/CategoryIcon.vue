<script setup lang="ts">
import { computed } from 'vue'
import { Droplet, Flame, Leaf, Nut, Wheat } from 'lucide-vue-next'
import SpiceIcon from './SpiceIcon.vue'

const props = defineProps<{ name: string }>()
const MAP = { leaf: Leaf, droplet: Droplet, nut: Nut, wheat: Wheat, flame: Flame }
const icon = computed(() => MAP[props.name as keyof typeof MAP] ?? SpiceIcon)
</script>

<template>
  <component :is="icon" :stroke-width="2" color="#6B3E1C" aria-hidden="true" />
</template>
