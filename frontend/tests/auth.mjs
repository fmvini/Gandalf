import assert from 'node:assert/strict'
import { createServer as createHttpServer } from 'node:http'
import { chromium } from 'playwright'
import { createServer } from 'vite'

const vite = await createServer({ server: { middlewareMode: true, hmr: false }, logLevel: 'silent' })
const server = createHttpServer(vite.middlewares)
await new Promise(done => server.listen(0, '127.0.0.1', done))
const port = server.address().port
assert.ok(port > 0 && port !== 5173, 'Use a real ephemeral port, preserving the existing frontend')
console.log('Auth fixture port: ' + port)
const base = 'http://127.0.0.1:' + port
let browser, page
const errors = []
const user = { id: 'test-user', email: 'leitor@example.com', username: 'leitor', created_at: '2026-10-01T12:00:00Z' }
const pair = index => ({ access_token: 'fake-access-' + index, refresh_token: 'fake-refresh-' + index, expires_in: 900 })
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }
let state
function reset() {
  state = { register: [], login: [], logout: [], refresh: [], me: [], loginStatus: 200, registerStatus: 201, logoutStatus: 204,
    rejectOld: false, oldRequests: 0, holdRefresh: null, holdLate: null, holdLogin: null, holdProfile: null, refreshStatus: 200,
    loginExpires: 900, rejectLogoutOnce: false, holdRegister: null }
}
async function waitFor(check) {
  const deadline = Date.now() + 10_000
  while (!check()) {
    assert.ok(Date.now() < deadline, 'Expected mocked request did not arrive')
    await new Promise(resolve => setTimeout(resolve, 20))
  }
}
async function login() {
  await page.goto(base + '/login')
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await page.getByRole('heading', { name: 'Sua conta.', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Atualizar dados', exact: true }).waitFor()
}
async function profileCalls(count) {
  await page.evaluate(async count => {
    const { authSession } = await import('/src/lib/auth.ts')
    window.authWork = Promise.allSettled(Array.from({ length: count }, () => authSession.loadProfile()))
  }, count)
}
try {
  browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({ reducedMotion: 'reduce' })
  page = await context.newPage()
  page.setDefaultTimeout(10_000)
  page.setDefaultNavigationTimeout(30_000)
  page.on('pageerror', error => errors.push(error.message))
  reset()
  await page.route('**/api/v1/**', route => route.abort())
  await page.route('**/api/v1/playlists?*', route => route.fulfill({ json: { items: [], total: 0, limit: 10, offset: 0 } }))
  await page.route('**/api/v1/auth/*', async route => {
    const active = state
    const endpoint = new URL(route.request().url()).pathname.split('/').at(-1)
    const body = route.request().method() === 'POST' ? route.request().postDataJSON() : null
    const failure = status => ({ status, json: { error: { code: 'TEST', message: status === 401 ? 'E-mail ou senha inválidos.' : 'Não foi possível concluir o cadastro.' } } })
    let response
    if (endpoint === 'register') {
      active.register.push(body)
      if (active.holdRegister) await active.holdRegister.promise
      response = active.registerStatus === 201 ? { status: 201, json: user } : failure(active.registerStatus)
    } else if (endpoint === 'login') {
      active.login.push(body)
      if (active.holdLogin) await active.holdLogin.promise
      response = active.loginStatus === 200 ? { json: { ...pair(1), expires_in: active.loginExpires } } : failure(active.loginStatus)
    } else if (endpoint === 'me') {
      const authorization = route.request().headers().authorization
      active.me.push(authorization)
      if (active.holdProfile) await active.holdProfile.promise
      if (active.rejectOld && authorization === 'Bearer fake-access-1') {
        active.oldRequests++
        if (active.oldRequests === 2 && active.holdLate) await active.holdLate.promise
        response = failure(401)
      } else response = { json: user }
    } else if (endpoint === 'refresh') {
      active.refresh.push(body)
      if (active.holdRefresh) await active.holdRefresh.promise
      response = active.refreshStatus === 200 ? { json: pair(2) } : failure(active.refreshStatus)
    } else if (endpoint === 'logout') {
      active.logout.push({ body, authorization: route.request().headers().authorization })
      if (active.logoutStatus === 'network') return route.abort()
      if (active.rejectLogoutOnce) { active.rejectLogoutOnce = false; response = failure(401) }
      else response = active.logoutStatus === 204 ? { status: 204, body: '' } : failure(active.logoutStatus)
    } else throw new Error('Unexpected auth endpoint')
    await route.fulfill(response).catch(() => {})
  })
  await page.goto(base + '/account')
  await page.waitForURL('**/login')
  await page.getByRole('heading', { name: 'Entre no Gandalf.' }).waitFor()
  await page.getByRole('link', { name: 'Criar conta', exact: true }).click()
  await page.getByRole('heading', { name: 'Crie sua conta.' }).waitFor()
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Nome de usuário', { exact: true }).fill(user.username)
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  await page.getByLabel('Confirme a senha', { exact: true }).fill('different phrase')
  await page.getByLabel('Nome de usuário', { exact: true }).fill('invalid name')
  await page.getByRole('button', { name: 'Criar conta', exact: true }).click()
  assert.equal(await page.getByLabel('Nome de usuário', { exact: true }).evaluate(input => input.validity.patternMismatch), true)
  assert.equal(state.register.length, 0)
  await page.getByLabel('Nome de usuário', { exact: true }).fill(user.username)
  await page.getByRole('button', { name: 'Mostrar senha' }).click()
  assert.equal(await page.getByLabel('Senha', { exact: true }).getAttribute('type'), 'text')
  await page.getByRole('button', { name: 'Ocultar senha' }).click()
  await page.getByRole('button', { name: 'Criar conta', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'As senhas precisam ser iguais' }).waitFor()
  assert.equal(state.register.length, 0, 'Mismatched passwords never reach the API')
  assert.equal(await page.getByRole('alert').evaluate(element => element === document.activeElement), true)
  await page.getByLabel('Confirme a senha', { exact: true }).fill('test phrase 123')
  state.registerStatus = 409
  await page.getByRole('button', { name: 'Criar conta', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'Não foi possível concluir o cadastro.' }).waitFor()
  state.registerStatus = 201
  await page.getByRole('button', { name: 'Criar conta', exact: true }).click()
  await page.getByRole('status').filter({ hasText: 'Conta criada.' }).waitFor()
  assert.equal(await page.getByLabel('E-mail', { exact: true }).inputValue(), user.email)
  assert.equal(await page.getByLabel('Senha', { exact: true }).inputValue(), '')
  assert.deepEqual(state.register.at(-1), { email: user.email, username: user.username, password: 'test phrase 123' })
  state.loginStatus = 401
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'E-mail ou senha inválidos.' }).waitFor()
  state.loginStatus = 429
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'Muitas tentativas' }).waitFor()
  state.loginStatus = 200
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await page.getByRole('heading', { name: 'Sua conta.' }).waitFor()
  await page.getByRole('button', { name: 'Atualizar dados', exact: true }).waitFor()
  assert.equal(await page.getByRole('link', { name: 'Minha conta', exact: true }).count(), 1)
  const storage = await page.evaluate(() => ({ local: { ...localStorage }, session: { ...sessionStorage }, cookie: document.cookie }))
  assert.deepEqual(storage.session, {})
  assert.equal(storage.cookie, '')
  assert.ok(Object.keys(storage.local).every(key => key === 'gandalf-theme'), 'Only the existing theme preference may persist')
  state.logoutStatus = 'network'
  await page.getByRole('button', { name: 'Sair da conta', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'Não foi possível encerrar a sessão.' }).waitFor()
  assert.equal(await page.getByRole('heading', { name: 'Sua conta.' }).count(), 1, 'A failed logout remains retryable')
  state.logoutStatus = 204
  await page.getByRole('button', { name: 'Sair da conta', exact: true }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.' }).waitFor()
  assert.equal(await page.getByRole('link', { name: 'Entrar na conta' }).count(), 1)

  // Two failures share one rotation; a late 401 reuses the new token pair.
  reset()
  await login()
  state.rejectOld = true
  state.holdRefresh = deferred()
  state.holdLate = deferred()
  await profileCalls(3)
  await waitFor(() => state.refresh.length === 1 && state.oldRequests === 3)
  state.holdRefresh.resolve()
  await waitFor(() => state.me.filter(value => value === 'Bearer fake-access-2').length === 2)
  state.holdLate.resolve()
  const results = await page.evaluate(() => window.authWork.then(results => results.map(result => result.status)))
  assert.deepEqual(results, ['fulfilled', 'fulfilled', 'fulfilled'])
  assert.equal(state.refresh.length, 1)
  await page.reload()
  await page.getByRole('heading', { name: 'Entre no Gandalf.' }).waitFor()

  // Logout waits for an existing rotation and revokes its new refresh token.
  reset()
  await login()
  state.rejectOld = true
  state.holdRefresh = deferred()
  await profileCalls(1)
  await waitFor(() => state.refresh.length === 1)
  await page.evaluate(async () => {
    const { authSession } = await import('/src/lib/auth.ts')
    window.authLogout = Promise.all([authSession.signOut(), authSession.signOut()])
  })
  assert.equal(state.logout.length, 0)
  state.holdRefresh.resolve()
  await page.evaluate(() => Promise.all([window.authWork, window.authLogout]))
  assert.equal(state.logout.length, 1, 'Concurrent logout requests share the same operation')
  assert.deepEqual(state.logout[0], { body: { refresh_token: 'fake-refresh-2' }, authorization: 'Bearer fake-access-2' })
  assert.equal(await page.evaluate(async () => (await import('/src/lib/auth.ts')).authSession.getSnapshot().user), null)

  // A failed refresh ends the account session instead of endlessly retrying.
  reset()
  await login()
  state.rejectOld = true
  state.refreshStatus = 401
  await page.getByRole('button', { name: 'Atualizar dados', exact: true }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.' }).waitFor()
  await page.getByRole('status').filter({ hasText: 'Sua sessão terminou.' }).waitFor()
  assert.equal(state.refresh.length, 1)

  // Expiration renews proactively, before a request can send an expired token.
  reset()
  state.loginExpires = 1
  await login()
  assert.equal(state.refresh.length, 1)
  assert.equal(state.me.at(-1), 'Bearer fake-access-2')
  await page.getByRole('button', { name: 'Sair da conta', exact: true }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.' }).waitFor()

  // Logout itself may receive a 401 and must rotate and retry only once.
  reset()
  await login()
  state.rejectLogoutOnce = true
  await page.getByRole('button', { name: 'Sair da conta', exact: true }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.' }).waitFor()
  assert.equal(state.refresh.length, 1)
  assert.equal(state.logout.length, 2)
  assert.equal(state.logout.at(-1).body.refresh_token, 'fake-refresh-2')

  // A profile response arriving after logout cannot republish the account.
  reset()
  await login()
  state.holdProfile = deferred()
  const profileCount = state.me.length
  await profileCalls(1)
  await waitFor(() => state.me.length === profileCount + 1)
  await page.getByRole('button', { name: 'Sair da conta', exact: true }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.' }).waitFor()
  state.holdProfile.resolve()
  await page.evaluate(() => window.authWork)
  assert.equal(await page.evaluate(async () => (await import('/src/lib/auth.ts')).authSession.getSnapshot().user), null)

  // Navigation cancels an unfinished login; its response cannot revive a session.
  reset()
  await page.goto(base + '/login')
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  state.holdLogin = deferred()
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await page.getByRole('button', { name: 'Entrando…', exact: true }).waitFor()
  assert.equal(await page.getByLabel('E-mail', { exact: true }).isDisabled(), true)
  await page.getByRole('link', { name: /Continuar explorando sem conta/ }).click()
  state.holdLogin.resolve()
  await page.getByRole('link', { name: 'Entrar na conta' }).waitFor()
  await page.evaluate(async () => { const { authSession } = await import('/src/lib/auth.ts'); if (authSession.getSnapshot().user) throw new Error('Aborted login restored a session') })

  // Autofill/Enter or script-triggered events in one turn must not duplicate login.
  reset()
  await page.goto(base + '/login')
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  state.holdLogin = deferred()
  await page.locator('form').evaluate(form => {
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
  })
  await waitFor(() => state.login.length >= 1)
  await page.getByRole('button', { name: 'Entrando…', exact: true }).waitFor()
  // Barrier: every already-dispatched fetch has reached the mock route.
  await page.evaluate(() => new Promise(done => setTimeout(done, 100)))
  assert.equal(state.login.length, 1, 'Same-turn submit must produce exactly one login')
  state.holdLogin.resolve()
  await page.getByRole('heading', { name: 'Sua conta.' }).waitFor()

  // An already-canceled call must not start a rotation, even near expiry.
  const preAbort = await page.evaluate(async () => {
    const { authSession } = await import('/src/lib/auth.ts')
    const realNow = Date.now
    Date.now = () => realNow() + 900_000
    const controller = new AbortController()
    controller.abort()
    try {
      await authSession.loadProfile(controller.signal)
      return 'fulfilled'
    } catch { return 'rejected' } finally { Date.now = realNow }
  })
  assert.equal(preAbort, 'rejected')
  assert.equal(state.refresh.length, 0, 'An already-aborted request never consumes a refresh token')

  // The same guard also protects registration; its successful response must
  // still clear the password and return to login without issuing tokens.
  reset()
  await page.goto(base + '/register')
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Nome de usuário', { exact: true }).fill(user.username)
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  await page.getByLabel('Confirme a senha', { exact: true }).fill('test phrase 123')
  state.holdRegister = deferred()
  await page.locator('form').evaluate(form => {
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
  })
  await waitFor(() => state.register.length >= 1)
  await page.getByRole('button', { name: 'Criando conta…', exact: true }).waitFor()
  await page.evaluate(() => new Promise(done => setTimeout(done, 100)))
  assert.equal(state.register.length, 1, 'Same-turn submit must produce exactly one registration')
  state.holdRegister.resolve()
  await page.getByRole('status').filter({ hasText: 'Conta criada.' }).waitFor()
  assert.equal(await page.getByLabel('Senha', { exact: true }).inputValue(), '')
  assert.equal(await page.getByLabel('E-mail', { exact: true }).getAttribute('name'), 'email')
  assert.equal(await page.getByLabel('E-mail', { exact: true }).getAttribute('autocomplete'), 'username')
  assert.equal(await page.getByLabel('Senha', { exact: true }).getAttribute('autocomplete'), 'current-password')
  assert.equal(state.login.length, 0)
  assert.deepEqual(errors, [])
  console.log('Auth passed: forms, errors, memory-only session, rotation/concurrency, logout retry/revocation, expiry and canceled login.')
} catch (error) {
  console.error('Auth failure context:', page ? await page.locator('.account-form input').evaluateAll(inputs => inputs.map(input => ({ id: input.id, length: input.value.length, valid: input.checkValidity(), validation: input.validationMessage }))) : 'Browser unavailable')
  throw error
} finally {
  for (const value of Object.values(state || {})) if (value?.resolve) value.resolve()
  await browser?.close()
  await new Promise(done => server.close(done))
  await vite.close()
}
