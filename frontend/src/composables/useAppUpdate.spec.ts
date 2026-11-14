import { afterEach, describe, expect, it, vi } from 'vitest'
import { APP_VERSION, fetchServerVersion, updateMessage } from './useAppUpdate'

afterEach(() => vi.unstubAllGlobals())

describe('app version', () => {
  it('comes from VITE_APP_VERSION', () => {
    expect(APP_VERSION).toBe('1.2.3')
  })

  it('reads the deployed version without the HTTP cache', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ version: '9.9.9' })))
    vi.stubGlobal('fetch', fetchMock)
    expect(await fetchServerVersion()).toBe('9.9.9')
    expect(fetchMock.mock.calls[0]![0]).toMatch(/^\/version\.json\?t=\d+$/)
    expect(fetchMock.mock.calls[0]![1]).toEqual({ cache: 'no-store' })
  })

  it('returns null when the server version is unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('nope', { status: 404 })))
    expect(await fetchServerVersion()).toBeNull()
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    expect(await fetchServerVersion()).toBeNull()
  })

  it('labels the update toast with the new version', () => {
    expect(updateMessage('9.9.9')).toBe('فيه نسخة جديدة (9.9.9)')
    expect(updateMessage(APP_VERSION)).toBe('فيه نسخة جديدة')
    expect(updateMessage(null)).toBe('فيه نسخة جديدة')
  })
})
