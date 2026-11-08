<script setup lang="ts">
import { ref } from 'vue'
import { Share, X } from 'lucide-vue-next'
import BottomSheet from '@/components/ui/BottomSheet.vue'
import Button from '@/components/ui/Button.vue'
import { useInstallPrompt } from '@/composables/useInstallPrompt'

const { canShow, ios, install, dismiss } = useInstallPrompt()
const showIos = ref(false)

function onInstall() {
  if (ios) showIos.value = true
  else void install()
}
</script>

<template>
  <section
    v-if="canShow"
    aria-label="تثبيت التطبيق"
    class="mx-4 mt-4 flex flex-col gap-3 rounded-card border border-primary bg-primary-soft p-4"
  >
    <p class="text-[15px] font-extrabold text-ink">نزّل تطبيق أبو سمرة على موبايلك</p>
    <div class="grid grid-cols-2 gap-2">
      <Button size="md" @click="onInstall">تثبيت</Button>
      <Button size="md" variant="secondary" @click="dismiss">مش دلوقتي</Button>
    </div>
  </section>

  <BottomSheet v-if="showIos" title="تثبيت على الآيفون" @close="showIos = false">
    <ol class="flex list-decimal flex-col gap-3 ps-5 text-[15px] text-ink">
      <li>
        افتح الموقع في سفاري واضغط على زرار المشاركة
        <Share class="inline h-5 w-5" aria-hidden="true" />
      </li>
      <li>اختار "إضافة إلى الشاشة الرئيسية"</li>
      <li>اضغط "إضافة"</li>
    </ol>
    <Button class="mt-4" block variant="secondary" @click="((showIos = false), dismiss())">
      <template #icon><X class="h-5 w-5" aria-hidden="true" /></template>
      تمام
    </Button>
  </BottomSheet>
</template>
