<script setup lang="ts">
defineProps<{ percent: number }>()
</script>

<template>
  <span
    dir="ltr"
    class="absolute start-1.5 top-1.5 rounded-full bg-danger px-2 py-0.5 text-[12px] font-bold text-white"
  >
    -{{ percent }}%
  </span>
</template>
