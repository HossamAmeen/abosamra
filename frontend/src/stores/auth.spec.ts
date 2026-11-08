import { beforeEach, describe, expect, it } from 'vitest'
import { createApp, nextTick } from 'vue'
import { createPinia, setActivePinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import { apiError } from '@/api/client'
import { useAuthStore } from './auth'

beforeEach(() => setActivePinia(createPinia()))

describe('auth store', () => {
  it('register normalizes phone and stores tokens', async () => {
    const a = useAuthStore()
    await a.register({ name: 'علي حسن', phone: '٠١٠٠٠٠٠٠٠٠١' })
    expect(a.isLoggedIn).toBe(true)
    expect(a.user?.phone).toBe('01000000001')
    expect(a.access).toBeTruthy()
    expect(a.isStaff).toBe(false)
  })
  it('login unknown -> 404 not_found, state unchanged', async () => {
    const a = useAuthStore()
    const err = await a.login('01000000009').catch(apiError)
    expect(err).toMatchObject({ status: 404, body: { code: 'not_found' } })
    expect(a.isLoggedIn).toBe(false)
  })
  it('admin login sets isStaff; logout clears', async () => {
    const a = useAuthStore()
    await a.adminLogin('01099999999', 'admin123')
    expect(a.isStaff).toBe(true)
    await a.logout()
    expect(a.isLoggedIn).toBe(false)
    expect(a.access).toBeNull()
  })
  it('expired access token is refreshed transparently via the interceptor', async () => {
    const a = useAuthStore()
    await a.login('01012345678')
    a.access = 'mock-access-100-expired'
    await a.fetchMe()
    expect(a.user?.name).toBe('محمد أحمد')
    expect(a.access).not.toContain('expired')
  })
  it('persists user + refresh but never the access token', async () => {
    const pinia = createPinia()
    pinia.use(piniaPluginPersistedstate)
    createApp({}).use(pinia)
    setActivePinia(pinia)
    const a = useAuthStore()
    await a.login('01012345678')
    await nextTick()
    const saved = JSON.parse(localStorage.getItem('auth') ?? 'null')
    expect(Object.keys(saved).sort()).toEqual(['refresh', 'user'])
  })
})
