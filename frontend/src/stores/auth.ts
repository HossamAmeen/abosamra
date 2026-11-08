import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'
import { registerTokenBridge } from '@/api/tokens'
import type { AuthResponse, RegisterPayload, User } from '@/types/api'
import { normalizePhone } from '@/utils/phone'

export const useAuthStore = defineStore(
  'auth',
  () => {
    const user = ref<User | null>(null)
    const refresh = ref<string | null>(null)
    const access = ref<string | null>(null) // memory only (not persisted)

    const isLoggedIn = computed(() => !!user.value && !!refresh.value)
    const isStaff = computed(() => !!user.value?.is_staff)

    function applyAuth(res: AuthResponse) {
      user.value = res.user
      access.value = res.access
      refresh.value = res.refresh
    }

    function clear() {
      user.value = null
      access.value = null
      refresh.value = null
    }

    async function register(payload: RegisterPayload) {
      applyAuth(await authApi.register({ ...payload, phone: normalizePhone(payload.phone) }))
    }
    async function login(phone: string) {
      applyAuth(await authApi.login(normalizePhone(phone)))
    }
    async function adminLogin(phone: string, password: string) {
      applyAuth(await authApi.adminLogin(normalizePhone(phone), password))
    }
    async function logout() {
      const token = refresh.value
      clear()
      if (token) {
        try {
          await authApi.logout(token)
        } catch {
          /* already logged out locally */
        }
      }
    }
    async function fetchMe() {
      user.value = await authApi.getMe()
    }
    async function updateProfile(patch: Parameters<typeof authApi.updateMe>[0]) {
      user.value = await authApi.updateMe(patch)
    }

    registerTokenBridge({
      getAccess: () => access.value,
      getRefresh: () => refresh.value,
      setTokens: (a, r) => {
        access.value = a
        if (r) refresh.value = r
      },
      onAuthFailure: clear,
    })

    return {
      user,
      refresh,
      access,
      isLoggedIn,
      isStaff,
      register,
      login,
      adminLogin,
      logout,
      fetchMe,
      updateProfile,
      clear,
    }
  },
  { persist: { pick: ['user', 'refresh'] } },
)
