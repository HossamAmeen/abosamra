<script setup lang="ts">
import CategoryIcon from './CategoryIcon.vue'

withDefaults(
  defineProps<{
    image?: string | null
    alt?: string
    tint?: string
    icon?: string
    iconSize?: number
  }>(),
  { tint: '#F6D9B8', icon: 'soup', iconSize: 40, alt: '' },
)
</script>

<template>
  <div
    class="relative flex h-full w-full items-center justify-center overflow-hidden rounded-thumb"
    :style="{ backgroundColor: tint }"
  >
    <img
      v-if="image"
      :src="image"
      :alt="alt"
      loading="lazy"
      decoding="async"
      class="h-full w-full object-cover"
    />
    <CategoryIcon
      v-else
      :name="icon"
      :style="{ width: iconSize + 'px', height: iconSize + 'px' }"
    />
    <slot />
  </div>
</template>
