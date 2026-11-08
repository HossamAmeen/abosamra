import { onMounted, onUnmounted, ref } from 'vue'

export function useOnline() {
  const online = ref(typeof navigator === 'undefined' ? true : navigator.onLine)
  const on = () => (online.value = true)
  const off = () => (online.value = false)
  onMounted(() => {
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
  })
  onUnmounted(() => {
    window.removeEventListener('online', on)
    window.removeEventListener('offline', off)
  })
  return { online }
}
