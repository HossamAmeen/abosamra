<script setup lang="ts">
import type { Component } from 'vue'
import { RouterLink } from 'vue-router'

defineProps<{ icon?: Component; text: string; actionLabel?: string; to?: string }>()
defineEmits<{ action: [] }>()
</script>

<template>
  <div class="flex flex-col items-center gap-3 px-6 py-12 text-center">
    <component
      :is="icon"
      v-if="icon"
      class="h-12 w-12 text-switch-off"
      :stroke-width="2"
      aria-hidden="true"
    />
    <p class="text-[16px] font-bold text-ink">{{ text }}</p>
    <RouterLink
      v-if="actionLabel && to"
      :to="to"
      class="inline-flex min-h-[44px] items-center font-bold text-link hover:text-link-hover"
    >
      {{ actionLabel }}
    </RouterLink>
    <button
      v-else-if="actionLabel"
      type="button"
      class="min-h-[44px] font-bold text-link hover:text-link-hover"
      @click="$emit('action')"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>
