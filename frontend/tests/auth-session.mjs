import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { Script, createContext } from 'node:vm'
import ts from 'typescript'

// Execute the production session module. Only its HTTP boundary and clock are
// mocked; no server, subprocess, network, storage or real credential is used.
const source = await readFile(new URL('../src/lib/auth.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }
const pair = index => ({ access_token: `fixture-access-${index}`, refresh_token: `fixture-refresh-${index}`, expires_in: 900 })
const user = index => ({ id: `fixture-owner-${index}`, email: `owner${index}@example.com`, username: `owner${index}`, created_at: '2026-10-02T12:00:00Z' })
class ApiError extends Error {
  constructor(message, status, code) { super(message); this.status = status; this.code = code }
}
function fixture() {
  let clock = 0
  const calls = [], handlers = new Map()
  const api = async (path, init = {}) => {
    init.signal?.throwIfAborted()
    const call = { path, body: init.body ? JSON.parse(init.body) : null, token: new Headers(init.headers).get('Authorization') }
    calls.push(call)
    let result
    if (handlers.has(path)) result = await handlers.get(path)(call)
    else if (path === '/auth/login') result = pair(1)
    else if (path === '/auth/refresh') result = pair(2)
    else if (path === '/auth/me') result = user(1)
    else if (path === '/auth/logout') result = undefined
    else throw new Error('Unexpected fixture path')
    init.signal?.throwIfAborted()
    return result
  }
  const exports = {}
  const context = createContext({ exports, require: path => {
    assert.equal(path, './api')
    return { api, ApiError, post: (path, body, signal) => api(path, { method: 'POST', body: JSON.stringify(body), signal }) }
  }, Date: { now: () => clock }, Headers })
  new Script(compiled, { filename: 'auth.ts' }).runInContext(context)
  return { session: exports.authSession, calls, handlers, expire: () => { clock += 900_000 }, count: path => calls.filter(call => call.path === path).length }
}

// Regression: an already-aborted operation must not consume a refresh token.
{
  const f = fixture()
  await f.session.signIn('owner1@example.com', 'fixture phrase')
  f.expire()
  const controller = new AbortController()
  controller.abort()
  await assert.rejects(f.session.loadProfile(controller.signal))
  assert.equal(f.count('/auth/refresh'), 0, 'Pre-aborted request must not start a rotation')
}

// Registration is not a login, and passwords are never normalized or trimmed.
{
  const f = fixture(), password = '  fixture phrase 123  '
  f.handlers.set('/auth/register', () => user(1))
  await f.session.register(' reader@example.com ', ' reader ', password)
  assert.deepEqual(f.calls[0].body, { email: 'reader@example.com', username: 'reader', password })
  assert.equal(f.session.getSnapshot().user, null)
  assert.equal(f.count('/auth/login'), 0)
  await f.session.signIn(' reader@example.com ', password)
  assert.deepEqual(f.calls[1].body, { email: 'reader@example.com', password })
}

// Concurrent protected 401s share one refresh instead of replaying its token.
{
  const f = fixture(), hold = deferred(), started = deferred()
  await f.session.signIn('owner1@example.com', 'fixture phrase')
  f.handlers.set('/auth/me', call => {
    if (call.token === 'Bearer fixture-access-1') throw new ApiError('Fixture unauthorized', 401)
    return user(1)
  })
  f.handlers.set('/auth/refresh', () => { started.resolve(); return hold.promise })
  const work = Promise.all([f.session.loadProfile(), f.session.loadProfile(), f.session.loadProfile()])
  await started.promise
  assert.equal(f.count('/auth/refresh'), 1)
  hold.resolve(pair(2))
  await work
  assert.equal(f.count('/auth/refresh'), 1)
  assert.equal(f.calls.filter(call => call.path === '/auth/me' && call.token === 'Bearer fixture-access-2').length, 3)
}

// Canceling one caller during a shared rotation must not cancel the other or
// send an authenticated retry on behalf of the canceled caller.
{
  const f = fixture(), hold = deferred(), started = deferred()
  await f.session.signIn('owner1@example.com', 'fixture phrase')
  f.expire()
  f.handlers.set('/auth/refresh', () => { started.resolve(); return hold.promise })
  const controller = new AbortController()
  const canceled = f.session.loadProfile(controller.signal)
  const settled = Promise.allSettled([canceled, f.session.loadProfile()])
  await started.promise
  controller.abort()
  hold.resolve(pair(2))
  const results = await settled
  assert.equal(results[0].status, 'rejected')
  assert.equal(results[1].status, 'fulfilled')
  assert.equal(f.count('/auth/refresh'), 1)
  assert.equal(f.count('/auth/me'), 2, 'Initial login plus the uncanceled caller only')
  assert.equal(f.calls.at(-1).token, 'Bearer fixture-access-2')
  assert.equal(f.session.getSnapshot().user.id, 'fixture-owner-1')
}

// Profile for A and rotation for A cannot publish tokens/data over owner B.
for (const pendingPath of ['/auth/me', '/auth/refresh']) {
  const f = fixture(), hold = deferred(), started = deferred()
  await f.session.signIn('owner1@example.com', 'fixture phrase')
  f.handlers.set(pendingPath, () => { started.resolve(); return hold.promise })
  if (pendingPath === '/auth/refresh') f.expire()
  const oldResult = Promise.allSettled([f.session.loadProfile()])
  await started.promise
  f.handlers.set('/auth/login', () => pair(3))
  f.handlers.set('/auth/me', () => user(2))
  await f.session.signIn('owner2@example.com', 'fixture phrase')
  hold.resolve(pendingPath === '/auth/me' ? user(1) : pair(2))
  assert.equal((await oldResult)[0].status, 'rejected')
  assert.equal(f.session.getSnapshot().user.id, 'fixture-owner-2')
  await f.session.loadProfile()
  assert.equal(f.calls.at(-1).token, 'Bearer fixture-access-3')
}

// Logout is single-flight and waits for rotation before revoking its pair.
{
  const f = fixture(), hold = deferred(), started = deferred()
  await f.session.signIn('owner1@example.com', 'fixture phrase')
  f.expire()
  f.handlers.set('/auth/refresh', () => { started.resolve(); return hold.promise })
  const profile = Promise.allSettled([f.session.loadProfile()])
  await started.promise
  const logout = Promise.all([f.session.signOut(), f.session.signOut()])
  assert.equal(f.count('/auth/logout'), 0)
  await assert.rejects(f.session.loadProfile(), error => error.code === 'SESSION_CLOSING')
  hold.resolve(pair(2))
  await logout
  assert.equal((await profile)[0].status, 'rejected')
  assert.equal(f.count('/auth/logout'), 1)
  assert.equal(f.calls.at(-1).body.refresh_token, 'fixture-refresh-2')
  assert.equal(f.calls.at(-1).token, 'Bearer fixture-access-2')
  assert.equal(f.session.getSnapshot().user, null)
}

// A failed rotation expires the session; transport failure leaves logout retryable.
{
  const f = fixture()
  await f.session.signIn('owner1@example.com', 'fixture phrase')
  f.expire()
  f.handlers.set('/auth/refresh', () => { throw new ApiError('Fixture expired', 401) })
  await assert.rejects(f.session.loadProfile())
  assert.equal(f.session.getSnapshot().user, null)
  assert.equal(f.session.getSnapshot().expired, true)
  assert.equal(f.count('/auth/refresh'), 1)
}
{
  const f = fixture()
  await f.session.signIn('owner1@example.com', 'fixture phrase')
  f.handlers.set('/auth/logout', () => { throw new Error('Fixture transport failure') })
  await assert.rejects(f.session.signOut())
  assert.equal(f.session.getSnapshot().user.id, 'fixture-owner-1')
  f.handlers.delete('/auth/logout')
  await f.session.signOut()
  assert.equal(f.session.getSnapshot().user, null)
  assert.equal(f.count('/auth/logout'), 2)
}

// A canceled login cannot publish a user even if its HTTP response arrives late.
{
  const f = fixture(), hold = deferred(), started = deferred(), controller = new AbortController()
  f.handlers.set('/auth/login', () => { started.resolve(); return hold.promise })
  const login = Promise.allSettled([f.session.signIn('owner1@example.com', 'fixture phrase', controller.signal)])
  await started.promise
  controller.abort()
  hold.resolve(pair(1))
  assert.equal((await login)[0].status, 'rejected')
  assert.equal(f.count('/auth/me'), 0)
  assert.equal(f.session.getSnapshot().user, null)
}
console.log('Auth session passed: pre-abort, shared refresh/cancel, owner switch with late profile/rotation, logout concurrency/retry, expiry and canceled login. Production module, HTTP mocks only.')
