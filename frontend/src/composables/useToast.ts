import { ref } from 'vue'

export interface ToastItem {
  id: number
  message: string
  actionLabel?: string
  onAction?: () => void
}

const toasts = ref<ToastItem[]>([])
let seq = 0

export function useToast() {
  function show(
    message: string,
    opts: { duration?: number; actionLabel?: string; onAction?: () => void } = {},
  ) {
    const id = ++seq
    toasts.value.push({ id, message, actionLabel: opts.actionLabel, onAction: opts.onAction })
    const duration = opts.duration ?? 3000
    if (duration > 0) setTimeout(() => dismiss(id), duration)
    return id
  }
  function dismiss(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }
  return { toasts, show, dismiss }
}
