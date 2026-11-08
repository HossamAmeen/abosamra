// Bridge between the axios client and the auth store (avoids a circular import).
// Access token lives in memory only; the refresh token is persisted by the auth store.
export interface TokenBridge {
  getAccess: () => string | null
  getRefresh: () => string | null
  setTokens: (access: string, refresh?: string) => void
  onAuthFailure: () => void
}

let bridge: TokenBridge = {
  getAccess: () => null,
  getRefresh: () => null,
  setTokens: () => {},
  onAuthFailure: () => {},
}

export function registerTokenBridge(b: TokenBridge): void {
  bridge = b
}

export function tokens(): TokenBridge {
  return bridge
}
