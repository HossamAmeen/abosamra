import { describe, expect, it } from 'vitest'
import { __setInstallState, useInstallPrompt } from './useInstallPrompt'

describe('useInstallPrompt', () => {
  it('shows only from the 2nd visit, when installable and not dismissed', () => {
    const { canShow, dismiss } = useInstallPrompt()
    __setInstallState({
      visits: 1,
      dismissed: false,
      event: { prompt: async () => {}, userChoice: Promise.resolve({ outcome: 'dismissed' }) },
    })
    expect(canShow.value).toBe(false)
    __setInstallState({ visits: 2 })
    expect(canShow.value).toBe(true)
    dismiss()
    expect(canShow.value).toBe(false)
  })
})
