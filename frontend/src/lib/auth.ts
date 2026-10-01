import { api, ApiError, post } from './api'

export type Account = { id: string; email: string; username: string; created_at: string }
type TokenPair = { access_token: string; refresh_token: string; expires_in: number }
type Session = { user: Account | null; expired: boolean }

// ADR-0006: credentials live only in memory. Reloading ends the client session.
let tokens: (TokenPair & { expiresAt: number }) | null = null
let snapshot: Session = { user: null, expired: false }
let revision = 0
let pendingRefresh: { revision: number; promise: Promise<void> } | null = null
let closingRevision: number | null = null
let pendingLogout: { revision: number; promise: Promise<void> } | null = null
const listeners = new Set<() => void>()

function publish(user: Account | null, expired = false) {
  snapshot = { user, expired }
  listeners.forEach(listener => listener())
}

function clear(expired = false) {
  revision += 1
  tokens = null
  pendingRefresh = null
  closingRevision = null
  publish(null, expired)
}

function sessionError() {
  return new ApiError('Sua sessão terminou. Entre novamente.', 401, 'SESSION_ENDED')
}

function checkSession(expected: number) {
  if (revision !== expected || !tokens) throw sessionError()
  return tokens
}

function tokenState(pair: TokenPair) {
  return { ...pair, expiresAt: Date.now() + pair.expires_in * 1000 }
}

function checkOpen(expected: number) {
  if (closingRevision === expected) throw new ApiError('Aguarde a saída da conta.', 409, 'SESSION_CLOSING')
}

async function refresh(expected: number, usedAccessToken: string, duringLogout = false) {
  if (!duringLogout) checkOpen(expected)
  const current = checkSession(expected)
  // Another request may already have rotated this pair after our 401.
  if (current.access_token !== usedAccessToken) return
  if (pendingRefresh?.revision === expected) return pendingRefresh.promise
  const pending = {
    revision: expected,
    promise: post<TokenPair>('/auth/refresh', { refresh_token: current.refresh_token })
      .then(pair => { checkSession(expected); tokens = tokenState(pair) })
      .catch(error => {
        if (revision === expected && error instanceof ApiError && error.status === 401) clear(true)
        throw error
      }),
  }
  pendingRefresh = pending
  try { await pending.promise } finally {
    if (pendingRefresh === pending) pendingRefresh = null
  }
}

async function authenticated<T>(path: string, init?: RequestInit): Promise<T> {
  const expected = revision
  checkOpen(expected)
  let current = checkSession(expected)
  if (Date.now() + 10_000 >= current.expiresAt) {
    await refresh(expected, current.access_token)
    current = checkSession(expected)
  }
  const usedAccessToken = current.access_token
  const request = () => {
    checkOpen(expected)
    const headers = new Headers(init?.headers)
    headers.set('Authorization', 'Bearer ' + checkSession(expected).access_token)
    return api<T>(path, { ...init, headers })
  }
  try { return await request() } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 401 || init?.signal?.aborted) throw error
    await refresh(expected, usedAccessToken)
    try { return await request() } catch (retryError) {
      if (revision === expected && retryError instanceof ApiError && retryError.status === 401) clear(true)
      throw retryError
    }
  }
}

async function endSession(expected: number) {
  closingRevision = expected
  try {
    // Wait for a rotation already in progress and prevent new ones until logout
    // completes. Otherwise an old refresh token could be revoked instead.
    if (pendingRefresh?.revision === expected) await pendingRefresh.promise
    const current = checkSession(expected)
    if (Date.now() + 10_000 >= current.expiresAt) await refresh(expected, current.access_token, true)
    const request = () => {
      const active = checkSession(expected)
      return api<void>('/auth/logout', {
        method: 'POST', headers: { Authorization: 'Bearer ' + active.access_token },
        body: JSON.stringify({ refresh_token: active.refresh_token }),
      })
    }
    try { await request() } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401) throw error
      await refresh(expected, checkSession(expected).access_token, true)
      try { await request() } catch (retryError) {
        if (revision === expected && retryError instanceof ApiError && retryError.status === 401) clear(true)
        throw retryError
      }
    }
    if (revision === expected) clear()
  } finally {
    if (closingRevision === expected) closingRevision = null
  }
}

export const authSession = {
  subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener) } },
  getSnapshot() { return snapshot },
  async signIn(email: string, password: string, signal?: AbortSignal) {
    const expected = ++revision
    const pair = await post<TokenPair>('/auth/login', { email: email.trim(), password }, signal)
    const user = await api<Account>('/auth/me', { headers: { Authorization: 'Bearer ' + pair.access_token }, signal })
    if (signal?.aborted || revision !== expected) return
    tokens = tokenState(pair)
    pendingRefresh = null
    publish(user)
  },
  register(email: string, username: string, password: string, signal?: AbortSignal) {
    return post<Account>('/auth/register', { email: email.trim(), username: username.trim(), password }, signal)
  },
  async loadProfile(signal?: AbortSignal) {
    const expected = revision
    const user = await authenticated<Account>('/auth/me', { signal })
    if (!signal?.aborted && revision === expected && closingRevision !== expected) publish(user)
    return user
  },
  signOut() {
    const expected = revision
    if (pendingLogout?.revision === expected) return pendingLogout.promise
    const pending = { revision: expected, promise: endSession(expected) }
    pendingLogout = pending
    return pending.promise.finally(() => { if (pendingLogout === pending) pendingLogout = null })
  },
}
