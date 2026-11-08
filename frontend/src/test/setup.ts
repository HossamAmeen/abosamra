import { afterAll, afterEach, beforeAll } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { server } from '@/mocks/server'
import { db } from '@/mocks/db'
import { registerTokenBridge } from '@/api/tokens'

beforeAll(() => server.listen({ onUnhandledFrame: 'error' }))
afterEach(() => {
  server.resetHandlers()
  db.reset()
  registerTokenBridge({
    getAccess: () => null,
    getRefresh: () => null,
    setTokens: () => {},
    onAuthFailure: () => {},
  })
  setActivePinia(createPinia())
  localStorage.clear()
})
afterAll(() => server.close())
