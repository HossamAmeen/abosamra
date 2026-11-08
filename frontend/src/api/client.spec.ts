import { describe, expect, it, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '@/mocks/server'
import { url } from '@/mocks/handlers/util'
import { registerTokenBridge } from './tokens'
import { api } from './client'

function bridge(state: { access: string | null; refresh: string | null }, onFail = vi.fn()) {
  registerTokenBridge({
    getAccess: () => state.access,
    getRefresh: () => state.refresh,
    setTokens: (a, r) => {
      state.access = a
      if (r) state.refresh = r
    },
    onAuthFailure: onFail,
  })
  return onFail
}

describe('axios client', () => {
  it('attaches the Bearer token', async () => {
    let auth = ''
    server.use(
      http.get(url('/me/'), ({ request }) => {
        auth = request.headers.get('authorization') ?? ''
        return HttpResponse.json({})
      }),
    )
    bridge({ access: 'tok', refresh: 'r' })
    await api.get('/me/')
    expect(auth).toBe('Bearer tok')
  })

  it('refreshes once on 401 and retries; concurrent 401s share one refresh', async () => {
    let refreshCalls = 0
    server.use(
      http.get(url('/me/'), ({ request }) =>
        request.headers.get('authorization') === 'Bearer fresh'
          ? HttpResponse.json({ ok: true })
          : HttpResponse.json({ detail: 'x' }, { status: 401 }),
      ),
      http.post(url('/auth/token/refresh/'), () => {
        refreshCalls += 1
        return HttpResponse.json({ access: 'fresh', refresh: 'r2' })
      }),
    )
    const state = { access: 'old', refresh: 'r1' }
    bridge(state)
    const [a, b] = await Promise.all([api.get('/me/'), api.get('/me/')])
    expect(a.data.ok && b.data.ok).toBe(true)
    expect(refreshCalls).toBe(1)
    expect(state).toEqual({ access: 'fresh', refresh: 'r2' })
  })

  it('logs out (onAuthFailure) when refresh fails, and does not loop', async () => {
    let meCalls = 0
    server.use(
      http.get(url('/me/'), () => {
        meCalls += 1
        return HttpResponse.json({ detail: 'x' }, { status: 401 })
      }),
      http.post(url('/auth/token/refresh/'), () =>
        HttpResponse.json({ detail: 'bad' }, { status: 401 }),
      ),
    )
    const onFail = bridge({ access: 'old', refresh: 'r1' })
    await expect(api.get('/me/')).rejects.toMatchObject({ response: { status: 401 } })
    expect(onFail).toHaveBeenCalledTimes(1)
    expect(meCalls).toBe(1)
  })

  it('does not try to refresh for /auth/ endpoint 401s (wrong admin password)', async () => {
    const onFail = bridge({ access: null, refresh: 'r1' })
    await expect(
      api.post('/auth/admin/login/', { phone: '01099999999', password: 'nope' }),
    ).rejects.toMatchObject({
      response: { status: 401 },
    })
    expect(onFail).not.toHaveBeenCalled()
  })
})
