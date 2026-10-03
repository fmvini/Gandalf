// Opt-in production gate. Docker, PostgreSQL and API lifecycle belong to the runner.
// No Vite, API mocks, credentials on disk, or existing development services.
import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
const forbiddenPorts = new Set([5173, 8080, 8000, 8001, 5432, 5433, 55432, 55433])
const fingerprint = token => createHash('sha256').update(token).digest('hex')

export function logoutProofTracker(base) {
  const observations = new WeakMap()
  const eligible = request => {
    if (!request || request.method() !== 'POST') return false
    const url = new URL(request.url())
    return url.origin === base && url.pathname === '/api/v1/auth/logout' && !url.search
  }
  return {
    observe(request, status) { observations.set(request, { status, proven: false }) },
    prove(request, proof) {
      const observed = observations.get(request)
      const complete = eligible(request) && observed?.status === 204 && proof.current_token === true && proof.ui_logged_out === true && proof.refresh_status === 401
      if (complete) observed.proven = true
      return complete
    },
    isProvenAbort(request, code) {
      const observed = observations.get(request)
      return code === 'net::ERR_ABORTED' && eligible(request) && observed?.status === 204 && observed.proven === true
    },
  }
}

export async function deadline(operation, ms = 10_000) {
  let timer
  const error = new Error('Operation deadline')
  error.name = 'DeadlineError'
  try {
    return await Promise.race([Promise.resolve().then(operation), new Promise((_, reject) => {
      timer = setTimeout(() => reject(error), ms)
    })])
  } finally { clearTimeout(timer) }
}

export function deploymentConfig(env) {
  assert.ok(env.GANDALF_DEPLOYMENT_ALLOW === 'isolated-coordinated', 'Explicit coordinated opt-in required')
  assert.ok(uuid.test(env.GANDALF_DEPLOYMENT_TOKEN || ''), 'Explicit disposable project UUID required')
  const raw = env.GANDALF_DEPLOYMENT_BASE_URL || ''
  const url = new URL(raw)
  assert.ok(url.protocol === 'http:' && url.hostname === '127.0.0.1', 'Only literal IPv4 loopback HTTP allowed')
  assert.ok(url.port && Number(url.port) >= 1024 && !forbiddenPorts.has(Number(url.port)), 'Exclusive non-development port required')
  assert.ok(!url.username && !url.password && !url.search && !url.hash && url.pathname === '/', 'Origin must not contain credentials, path, query or fragment')
  // Do not let URL canonicalization turn an obfuscated host/path into an accepted origin.
  assert.ok(raw === url.origin || raw === url.origin + '/', 'Canonical loopback origin required')
  assert.ok(['create', 'verify'].includes(env.GANDALF_DEPLOYMENT_PHASE), 'Explicit create or verify phase required')
  assert.ok(typeof env.GANDALF_DEPLOYMENT_PASSWORD === 'string' && env.GANDALF_DEPLOYMENT_PASSWORD.length >= 10 && env.GANDALF_DEPLOYMENT_PASSWORD.length <= 128, 'Disposable password required')
  assert.ok(env.GANDALF_DEPLOYMENT_ARTIFACT?.trim(), 'Runner-owned artifact path required')
  return { base: url.origin, token: env.GANDALF_DEPLOYMENT_TOKEN.toLowerCase(), phase: env.GANDALF_DEPLOYMENT_PHASE,
    password: env.GANDALF_DEPLOYMENT_PASSWORD, artifact: resolve(env.GANDALF_DEPLOYMENT_ARTIFACT) }
}

export function validateState(state, config) {
  assert.ok(state?.version === 1 && state.phase === 'create' && state.status === 'PASS', 'Successful create artifact required')
  assert.ok(state.run_fingerprint === fingerprint(config.token) && state.base_url === config.base, 'Artifact must belong to this project and origin')
  for (const [key, count] of [['user_ids', 2], ['favorite_ids', 2], ['playlist_ids', 1]]) {
    assert.ok(Array.isArray(state[key]) && state[key].length === count && state[key].every(id => uuid.test(id)) && new Set(state[key]).size === count, 'Invalid artifact ID set: ' + key)
  }
  assert.ok(uuid.test(state.public_snapshot_id) && Array.isArray(state.public_snapshot_music_ids) && state.public_snapshot_music_ids.length > 0 && state.public_snapshot_music_ids.every(id => uuid.test(id)), 'Public snapshot IDs required')
  assert.ok(Array.isArray(state.favorites) && state.favorites.length === 2 && state.favorites.every((item, index) => item.id === state.favorite_ids[index] && uuid.test(item.item_id) && item.type === (index ? 'BOOK' : 'MUSIC')), 'Favorite identities required')
  assert.ok(Array.isArray(state.playlist_music_ids) && state.playlist_music_ids.length > 0 && state.playlist_music_ids.every(id => uuid.test(id)), 'Ordered playlist identities required')
  // Reconstruct the public artifact instead of reflecting arbitrary input fields.
  return { version: 1, phase: 'create', status: 'PASS', run_fingerprint: state.run_fingerprint, base_url: config.base,
    user_ids: [...state.user_ids], favorite_ids: [...state.favorite_ids], playlist_ids: [...state.playlist_ids],
    public_snapshot_id: state.public_snapshot_id, public_snapshot_music_ids: [...state.public_snapshot_music_ids],
    playlist_music_ids: [...state.playlist_music_ids], favorites: state.favorites.map(item => ({ id: item.id, type: item.type, item_id: item.item_id })) }
}

async function selfTest() {
  const env = { GANDALF_DEPLOYMENT_ALLOW: 'isolated-coordinated', GANDALF_DEPLOYMENT_BASE_URL: 'http://127.0.0.1:49152', GANDALF_DEPLOYMENT_TOKEN: '9e1e2a1f-6a86-4e63-91ce-fd06d39da55d', GANDALF_DEPLOYMENT_PHASE: 'create', GANDALF_DEPLOYMENT_PASSWORD: 'disposable test password', GANDALF_DEPLOYMENT_ARTIFACT: 'deployment-test.json' }
  const config = deploymentConfig(env)
  let checks = 1
  for (const value of ['', 'http://localhost:49152', 'https://127.0.0.1:49152', 'http://example.test:49152', 'http://127.0.0.2:49152', 'http://127.1:49152', 'http://2130706433:49152', 'http://[::1]:49152', 'http://127.0.0.1', 'http://127.0.0.1:80', ...[...forbiddenPorts].map(port => 'http://127.0.0.1:' + port), 'http://user:password@127.0.0.1:49152', 'http://127.0.0.1:49152/path', 'http://127.0.0.1:49152/?q=x', 'http://127.0.0.1:49152/#x', 'http://127.0.0.1:49152/a/..']) {
    assert.throws(() => deploymentConfig({ ...env, GANDALF_DEPLOYMENT_BASE_URL: value })); checks++
  }
  for (const [key, value] of [['GANDALF_DEPLOYMENT_ALLOW', ''], ['GANDALF_DEPLOYMENT_ALLOW', 'true'], ['GANDALF_DEPLOYMENT_TOKEN', ''], ['GANDALF_DEPLOYMENT_TOKEN', 'not-a-uuid'], ['GANDALF_DEPLOYMENT_PHASE', ''], ['GANDALF_DEPLOYMENT_PHASE', 'seed'], ['GANDALF_DEPLOYMENT_PASSWORD', 'short'], ['GANDALF_DEPLOYMENT_PASSWORD', 'x'.repeat(129)], ['GANDALF_DEPLOYMENT_ARTIFACT', '']]) {
    assert.throws(() => deploymentConfig({ ...env, [key]: value })); checks++
  }
  const ids = ['51ba605b-25e0-4b20-9bf4-661637a2d134', 'a38e6b90-752e-43ba-b7aa-f24ec3b35749']
  const state = { version: 1, phase: 'create', status: 'PASS', run_fingerprint: fingerprint(config.token), base_url: config.base,
    user_ids: ids, favorite_ids: ids, playlist_ids: [ids[0]], public_snapshot_id: ids[0], public_snapshot_music_ids: ids,
    favorites: ids.map((id, i) => ({ id, item_id: id, type: i ? 'BOOK' : 'MUSIC' })), playlist_music_ids: ids }
  validateState(state, config); checks++
  const sanitized = validateState({ ...state, email: 'private@example.test', access_token: 'private-credential', favorites: state.favorites.map(item => ({ ...item, password: 'private-password' })) }, config)
  assert.ok(!JSON.stringify(sanitized).includes('private')); checks++
  for (const patch of [{ status: 'FAIL' }, { phase: 'verify' }, { run_fingerprint: 'wrong' }, { base_url: 'http://127.0.0.1:49153' }, { user_ids: [ids[0], ids[0]] }, { favorite_ids: [] }, { playlist_ids: ['not-uuid'] }, { public_snapshot_music_ids: [] }, { favorites: [] }, { playlist_music_ids: [] }]) {
    assert.throws(() => validateState({ ...state, ...patch }, config)); checks++
  }
  assert.equal(await deadline(() => Promise.resolve('completed'), 20), 'completed'); checks++
  await assert.rejects(deadline(() => new Promise(() => {}), 5), { name: 'DeadlineError' }); checks++
  await assert.rejects(deadline(() => Promise.reject(new TypeError('synthetic')), 20), { name: 'TypeError' }); checks++
  const fakeRequest = (method = 'POST', path = '/api/v1/auth/logout', base = config.base) => ({ method: () => method, url: () => base + path })
  const proofs = logoutProofTracker(config.base)
  const complete = { current_token: true, ui_logged_out: true, refresh_status: 401 }
  const first = fakeRequest()
  assert.ok(!proofs.prove(first, complete) && !proofs.isProvenAbort(first, 'net::ERR_ABORTED')); checks++
  proofs.observe(first, 204)
  assert.ok(!proofs.isProvenAbort(first, 'net::ERR_ABORTED')); checks++
  for (const incomplete of [{ ...complete, current_token: false }, { ...complete, ui_logged_out: false }, { ...complete, refresh_status: 200 }, {}]) {
    assert.ok(!proofs.prove(first, incomplete) && !proofs.isProvenAbort(first, 'net::ERR_ABORTED')); checks++
  }
  assert.ok(proofs.prove(first, complete) && proofs.isProvenAbort(first, 'net::ERR_ABORTED')); checks++
  const sameUrlDifferentObject = fakeRequest()
  proofs.observe(sameUrlDifferentObject, 204)
  assert.ok(!proofs.isProvenAbort(sameUrlDifferentObject, 'net::ERR_ABORTED')); checks++
  for (const code of ['net::ERR_FAILED', 'net::ERR_CONNECTION_REFUSED', 'other']) {
    assert.ok(!proofs.isProvenAbort(first, code)); checks++
  }
  for (const status of [200, 201, 401, 500]) {
    const request = fakeRequest(); proofs.observe(request, status)
    assert.ok(!proofs.prove(request, complete) && !proofs.isProvenAbort(request, 'net::ERR_ABORTED')); checks++
  }
  for (const request of [fakeRequest('GET'), fakeRequest('POST', '/api/v1/auth/login'), fakeRequest('POST', '/api/v1/auth/logout?x=1'), fakeRequest('POST', '/api/v1/auth/logout', 'http://127.0.0.1:49153')]) {
    proofs.observe(request, 204)
    assert.ok(!proofs.prove(request, complete) && !proofs.isProvenAbort(request, 'net::ERR_ABORTED')); checks++
  }
  console.log(JSON.stringify({ status: 'PASS', mode: 'offline-guards', checks, browser_executed: false, network_executed: false }))
}

async function run(config) {
  let stage = 'offline-status'
  let substage = 'status-request'
  let browser
  let closeStarted = false
  let page
  const checks = []
  const traffic = new Map()
  const failures = []
  const failedRequests = new WeakMap()
  const logoutProofs = logoutProofTracker(config.base)
  const unresolvedFailures = () => failures.filter(failure => failure.kind !== 'requestfailed' || !logoutProofs.isProvenAbort(failedRequests.get(failure), failure.error_code))
  let blocked = 0
  let pageErrors = 0
  let consoleErrors = 0
  const progress = mark => console.error(JSON.stringify({ status: 'PROGRESS', phase: config.phase, stage, substage, ...(mark ? { check: mark } : {}) }))
  const setStage = next => { stage = next; substage = 'start'; progress() }
  const setSubstage = next => { substage = next; progress() }
  const mark = name => { checks.push(name); progress(name) }
  const json = response => { setSubstage('response-json'); return deadline(() => response.json()) }
  progress()
  const record = (method, path, status) => {
    const key = method + ' ' + path + ' ' + status
    traffic.set(key, (traffic.get(key) || 0) + 1)
  }
  // This function never accepts an arbitrary URL and never follows redirects.
  async function request(path, { method = 'GET', token, body, status = 200 } = {}) {
    assert.ok(path.startsWith('/api/v1/') && !path.includes('://'), 'Only same-origin API paths allowed')
    setSubstage('node-' + method.toLowerCase() + '-' + path)
    const response = await fetch(config.base + path, { method, redirect: 'error', signal: AbortSignal.timeout(10_000),
      headers: { ...(token ? { Authorization: 'Bearer ' + token } : {}), ...(body ? { 'Content-Type': 'application/json' } : {}) },
      ...(body ? { body: JSON.stringify(body) } : {}) })
    record(method, new URL(response.url).pathname, response.status)
    assert.ok(response.status === status, 'Unexpected API status')
    return status === 204 ? undefined : json(response)
  }
  try {
    const status = await request('/api/v1/system/status')
    assert.ok(status.catalog === 'local' && status.ai?.configured === false && status.ai?.provider === null, 'Offline API required before opening browser')
    mark('offline-status')
    const previous = config.phase === 'verify' ? validateState(JSON.parse(await readFile(config.artifact, 'utf8')), config) : null
    const { chromium } = await import('playwright')
    setStage('browser-start')
    browser = await chromium.launch({ headless: true })
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, serviceWorkers: 'block' })
    page = await context.newPage()
    page.setDefaultTimeout(10_000)
    page.setDefaultNavigationTimeout(30_000)
    page.on('pageerror', () => { pageErrors++ })
    page.on('console', message => { if (message.type() === 'error') consoleErrors++ })
    page.on('response', response => {
      const url = new URL(response.url())
      if (url.origin !== config.base) return
      logoutProofs.observe(response.request(), response.status())
      if (url.pathname.startsWith('/api/v1/')) record(response.request().method(), url.pathname, response.status())
      if (response.status() >= 400) failures.push({ kind: 'http', method: response.request().method(), path: url.pathname, status: response.status() })
    })
    page.on('requestfailed', req => {
      const path = new URL(req.url()).pathname
      const rawCode = req.failure()?.errorText
      const errorCode = ['net::ERR_ABORTED', 'net::ERR_FAILED', 'net::ERR_CONNECTION_REFUSED'].includes(rawCode) ? rawCode : 'other'
      // A debounced search can cancel a superseded GET. Other failures must fail the gate.
      if (req.method() === 'GET' && path === '/api/v1/books/search' && errorCode === 'net::ERR_ABORTED') return
      const failure = { kind: 'requestfailed', method: req.method(), path, error_code: errorCode }
      failedRequests.set(failure, req)
      failures.push(failure)
    })
    await context.route('**/*', route => {
      if (new URL(route.request().url()).origin === config.base) return route.continue()
      blocked++
      return route.abort('blockedbyclient')
    })
    async function apiResponse(path, method, expected, action) {
      setSubstage('api-' + method.toLowerCase() + '-' + path)
      const waiting = page.waitForResponse(response => new URL(response.url()).pathname === '/api/v1' + path && response.request().method() === method)
      // Observe both promises even when the click fails, avoiding a second unhandled timeout.
      const [response] = await Promise.all([waiting, action()])
      assert.ok(response.status() === expected, 'Unexpected browser API status')
      // 204 has no body; its observed status and subsequent UI/revocation checks
      // are the logout proof. Playwright finished() hung on this real nginx 204.
      if (expected !== 204) {
        setSubstage('response-finished-' + expected)
        await deadline(() => response.finished())
      }
      return response
    }
    async function navigate(path) {
      const response = await page.goto(config.base + path, { waitUntil: 'load' })
      assert.ok(response?.status() === 200 && /nginx/i.test((await deadline(() => response.allHeaders())).server || ''), 'Direct SPA path must be served by production nginx')
      assert.ok(!(await deadline(() => page.content())).includes('/@vite/client'), 'Vite is forbidden')
    }
    async function memoryOnly() {
      setSubstage('memory-only-evaluate')
      const clean = await deadline(() => page.evaluate(() => {
        const forbidden = /token|password|email|username|authorization|bearer/i
        return [localStorage, sessionStorage].every(storage => Object.keys(storage).every(key => !forbidden.test(key) && !forbidden.test(storage.getItem(key) || '')))
      }))
      assert.ok(clean && (await deadline(() => context.cookies())).length === 0, 'Authentication must not persist in browser storage or cookies')
    }
    const compact = config.token.replaceAll('-', '')
    const playlistName = 'Gate Duna ' + compact.slice(0, 12)
    let activePair
    const credentials = index => ({ email: 'gate-' + compact + '-' + index + '@example.com', username: 'gate_' + compact.slice(0, 20) + '_' + index, password: config.password })
    async function accountReady() {
      setSubstage('account-profile-ready')
      await page.getByRole('button', { name: 'Atualizar dados', exact: true }).waitFor()
      setSubstage('account-playlists-ready')
      await page.waitForFunction(() => document.querySelector('.account-playlists')?.getAttribute('aria-busy') === 'false')
    }
    async function login(index) {
      setSubstage('login-page-ready')
      await page.waitForURL(config.base + '/login')
      await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
      setSubstage('login-destination-evaluate')
      const destination = await deadline(() => page.evaluate(() => {
        const pathname = history.state?.usr?.returnTo?.pathname
        return ['/music', '/books', '/read-with-music', '/account/favorites'].includes(pathname) ? pathname : '/account'
      }))
      const account = credentials(index)
      setSubstage('login-fill-email')
      await page.getByLabel('E-mail', { exact: true }).fill(account.email)
      setSubstage('login-fill-password')
      await page.getByLabel('Senha', { exact: true }).fill(account.password)
      const response = await apiResponse('/auth/login', 'POST', 200, () => page.getByRole('button', { name: 'Entrar', exact: true }).click())
      const pair = await json(response)
      assert.ok(typeof pair.access_token === 'string' && typeof pair.refresh_token === 'string', 'Real token pair required')
      activePair = pair
      setSubstage('login-return-destination')
      await page.waitForURL(config.base + destination)
      await page.getByRole('link', { name: 'Minha conta', exact: true }).waitFor()
      if (destination !== '/account') {
        setSubstage('login-open-account-spa')
        await page.getByRole('link', { name: 'Minha conta', exact: true }).click()
      }
      setSubstage('login-account-heading')
      await page.getByRole('heading', { name: 'Sua conta.', exact: true }).waitFor()
      await accountReady()
      assert.ok(await page.locator('.account-details dd').nth(1).textContent() === account.email, 'Correct account required')
      if (previous) {
        const profile = await request('/api/v1/auth/me', { token: pair.access_token })
        assert.ok(profile.id === previous.user_ids[index - 1], 'Account identity must survive API restart')
      }
      await memoryOnly()
      return pair
    }
    async function register(index) {
      setSubstage('register-open-link')
      await page.getByRole('link', { name: 'Criar conta', exact: true }).click()
      setSubstage('register-page-ready')
      await page.waitForURL(config.base + '/register')
      await page.getByRole('heading', { name: 'Crie sua conta.', exact: true }).waitFor()
      const account = credentials(index)
      for (const [field, label, value] of [['email', 'E-mail', account.email], ['username', 'Nome de usuário', account.username], ['password', 'Senha', account.password], ['confirmation', 'Confirme a senha', account.password]]) {
        setSubstage('register-fill-' + field)
        await page.getByLabel(label, { exact: true }).fill(value)
      }
      setSubstage('register-native-validation')
      assert.ok(await deadline(() => page.locator('.account-form').evaluate(form => form.checkValidity())), 'Registration fixture must satisfy native validation before submit')
      const response = await apiResponse('/auth/register', 'POST', 201, () => page.getByRole('button', { name: 'Criar conta', exact: true }).click())
      const user = await json(response)
      assert.ok(uuid.test(user.id), 'Account UUID required')
      setSubstage('register-login-notice')
      await page.waitForURL(config.base + '/login')
      await page.getByRole('status').filter({ hasText: 'Conta criada.' }).waitFor()
      await login(index)
      return user.id
    }
    async function logout() {
      await accountReady()
      const response = await apiResponse('/auth/logout', 'POST', 204, () => page.getByRole('button', { name: 'Sair da conta', exact: true }).click())
      // Read only in memory, never serialize this body or include it in an assertion failure.
      const revoked = response.request().postDataJSON().refresh_token
      assert.ok(revoked === activePair.refresh_token, 'Logout must revoke the current rotated pair')
      await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
      await request('/api/v1/auth/refresh', { method: 'POST', body: { refresh_token: revoked }, status: 401 })
      await memoryOnly()
      assert.ok(logoutProofs.prove(response.request(), { current_token: revoked === activePair.refresh_token, ui_logged_out: new URL(page.url()).pathname === '/login', refresh_status: 401 }), 'Same logout request must have real 204 and complete UI/token/revocation proof')
      activePair = null
    }
    async function refresh() {
      setStage('real-refresh')
      // Advance only the client expiry check; API clock/responses/tokens remain real.
      setSubstage('refresh-clock-evaluate')
      await deadline(() => page.evaluate(() => { window.__deploymentRealNow = Date.now; Date.now = () => window.__deploymentRealNow() + 900_000 }))
      try {
        const response = await apiResponse('/auth/refresh', 'POST', 200, () => page.getByRole('button', { name: 'Atualizar dados', exact: true }).click())
        const rotated = await json(response)
        assert.ok(typeof rotated.access_token === 'string' && typeof rotated.refresh_token === 'string' && rotated.access_token !== activePair.access_token && rotated.refresh_token !== activePair.refresh_token, 'Refresh must rotate both credentials')
        activePair = rotated
        await page.getByRole('button', { name: 'Atualizar dados', exact: true }).waitFor()
      } finally {
        setSubstage('refresh-clock-restore-evaluate')
        await deadline(() => page.evaluate(() => { Date.now = window.__deploymentRealNow; delete window.__deploymentRealNow }))
      }
      mark('real-refresh-via-ui')
    }
    async function readPlaylist(expectedTitles) {
      await accountReady()
      const response = await apiResponse('/playlists/' + (previous?.playlist_ids[0] || state.playlist_ids[0]), 'GET', 200, () => page.getByRole('link', { name: playlistName, exact: false }).click())
      const data = await json(response)
      assert.ok(JSON.stringify(data.tracks.map(row => row.item.id)) === JSON.stringify(state.playlist_music_ids), 'Saved playlist must preserve ordered track identities')
      await page.getByRole('heading', { name: playlistName, exact: true }).waitFor()
      assert.ok(JSON.stringify(await page.locator('.playlist-list strong').allTextContents()) === JSON.stringify(expectedTitles || data.tracks.map(row => row.item.title)), 'Saved playlist UI must match ordered track titles')
    }
    async function readFavorites(state) {
      await accountReady()
      const response = await apiResponse('/users/me/favorites', 'GET', 200, () => page.getByRole('link', { name: 'Ver seus favoritos', exact: true }).click())
      const data = await json(response)
      assert.ok(data.total === 2 && data.items.length === 2, 'Exactly two saved favorites required')
      for (const expected of state.favorites) {
        const item = data.items.find(item => item.id === expected.id)
        assert.ok(item?.item_id === expected.item_id && item.type === expected.type && typeof item.item?.title === 'string', 'Favorite identities must survive account switch and restart')
        if (item.type === 'BOOK') assert.ok(item.item.title === 'O Hobbit', 'Book fixture title must be preserved')
        await page.getByRole('heading', { name: item.item.title, exact: true }).waitFor()
      }
    }
    let state
    if (config.phase === 'create') {
      setStage('direct-spa-paths')
      for (const path of ['/music', '/books', '/read-with-music', '/register', '/login', '/account', '/account/favorites', '/account/playlists/' + config.token]) {
        await navigate(path)
        if (path.startsWith('/account')) await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
      }
      mark('nginx-direct-spa-paths')
      setStage('public-offline-music')
      await navigate('/music')
      await page.getByLabel('Seu pedido', { exact: true }).fill('Músicas calmas para estudar')
      await page.getByText('Ajustar preferências').click()
      await page.getByRole('radiogroup', { name: 'Vocais' }).getByRole('radio', { name: 'Instrumental', exact: true }).click()
      await page.getByRole('radiogroup', { name: 'Energia' }).getByRole('radio', { name: 'Baixa', exact: true }).click()
      const musicResponse = await apiResponse('/recommendations/music', 'POST', 200, () => page.getByRole('button', { name: /Encontrar sugestões/ }).click())
      const music = await json(musicResponse)
      assert.ok(uuid.test(music.recommendation_id) && music.items.length > 0, 'Real offline music selection required')
      await page.getByText(/Catálogo local selecionado/).waitFor()
      assert.ok(await page.locator('.result-row').count() === music.items.length, 'Music UI must show returned items')
      await apiResponse('/recommendations/' + music.recommendation_id + '/items/' + music.items[0].item.id + '/explanation', 'GET', 200, () => page.getByRole('button', { name: 'Por que esta sugestão?', exact: true }).first().click())
      await page.getByText(/Temas em comum:/).first().waitFor()
      mark('public-music-and-explanation')
      setStage('account-a-register')
      await page.getByRole('link', { name: 'Entrar na conta', exact: true }).click()
      const firstUser = await register(1)
      await refresh()
      setStage('save-reading-playlist-and-music')
      await page.getByRole('link', { name: 'Criar uma trilha', exact: true }).click()
      await page.getByLabel('Qual livro você está lendo?', { exact: true }).fill('Duna')
      await page.getByRole('button', { name: /Duna Frank Herbert/ }).click()
      await apiResponse('/recommendations/read-with-music', 'POST', 200, () => page.getByRole('button', { name: /Criar minha trilha/ }).click())
      await page.getByLabel('Nome da playlist').waitFor()
      const titles = await page.locator('.playlist-track-main > strong').allTextContents()
      assert.ok(titles.length > 0, 'Reading soundtrack required')
      const favorite = await json(await apiResponse('/users/me/favorites', 'POST', 201, () => page.getByRole('button', { name: 'Salvar nos favoritos: ' + titles[0], exact: true }).click()))
      await page.getByLabel('Nome da playlist').fill(playlistName)
      const playlist = await json(await apiResponse('/playlists', 'POST', 201, () => page.getByRole('button', { name: 'Salvar na minha conta', exact: true }).click()))
      await page.getByRole('link', { name: 'Ver playlist', exact: true }).click()
      await page.getByRole('heading', { name: playlistName, exact: true }).waitFor()
      assert.ok(JSON.stringify(await page.locator('.playlist-list strong').allTextContents()) === JSON.stringify(titles), 'Saved reading tracks must match UI')
      await page.getByRole('link', { name: 'Voltar às playlists', exact: true }).click()
      await accountReady()
      setStage('public-books-and-book-favorite')
      await page.getByRole('link', { name: 'Livros', exact: true }).first().click()
      await page.getByLabel('Seu pedido', { exact: true }).fill('Fantasia com construção de mundo sem romance')
      await apiResponse('/recommendations/books', 'POST', 200, () => page.getByRole('button', { name: /Encontrar sugestões/ }).click())
      await page.getByRole('heading', { name: 'O Hobbit', exact: true }).waitFor()
      const bookFavorite = await json(await apiResponse('/users/me/favorites', 'POST', 201, () => page.getByRole('button', { name: 'Salvar nos favoritos: O Hobbit', exact: true }).click()))
      state = { version: 1, phase: 'create', status: 'PASS', run_fingerprint: fingerprint(config.token), base_url: config.base,
        user_ids: [firstUser], favorite_ids: [favorite.id, bookFavorite.id], playlist_ids: [playlist.id],
        public_snapshot_id: music.recommendation_id, public_snapshot_music_ids: music.items.map(row => row.item.id),
        playlist_music_ids: playlist.tracks.map(row => row.item.id),
        favorites: [favorite, bookFavorite].map(item => ({ id: item.id, type: item.type, item_id: item.item_id })) }
      await page.getByRole('link', { name: 'Minha conta', exact: true }).click()
      await readFavorites(state)
      await page.getByRole('link', { name: 'Voltar à conta', exact: true }).click()
      await logout()
      setStage('account-b-register-and-isolation')
      const secondUser = await register(2)
      state.user_ids.push(secondUser)
      // API isolation checks also traverse nginx; expected opaque statuses never enter browser console.
      await logout()
      const pair = await login(2)
      const otherList = await request('/api/v1/users/me/favorites', { token: pair.access_token })
      assert.ok(otherList.total === 0 && otherList.items.length === 0, 'Second account favorites must be empty')
      for (const method of ['GET', 'DELETE']) await request('/api/v1/playlists/' + playlist.id, { method, token: pair.access_token, status: 404 })
      await request('/api/v1/users/me/favorites/' + favorite.id, { method: 'DELETE', token: pair.access_token, status: 204 })
      const otherStatus = await request('/api/v1/users/me/favorites/status', { method: 'POST', token: pair.access_token, body: { type: 'MUSIC', item_ids: [favorite.item_id] } })
      assert.ok(Object.keys(otherStatus.favorites).length === 0, 'Foreign favorite status must be opaque')
      await page.getByRole('link', { name: 'Ver seus favoritos', exact: true }).click()
      await page.getByRole('heading', { name: 'Guarde o que você quer reencontrar.', exact: true }).waitFor()
      await page.getByRole('link', { name: 'Voltar à conta', exact: true }).click()
      await logout()
      mark('two-accounts-ownership-and-logout-revocation')
      setStage('same-process-persistence')
      await login(1)
      await readPlaylist(titles)
      await page.getByRole('link', { name: 'Voltar às playlists', exact: true }).click()
      await readFavorites(state)
      await page.getByRole('link', { name: 'Voltar à conta', exact: true }).click()
      await logout()
      validateState(state, config)
      mark('saved-snapshots-preserved-for-runner-sql-and-restart')
    } else {
      state = previous
      setStage('restart-public-cache')
      const explanation = await request('/api/v1/recommendations/' + state.public_snapshot_id + '/items/' + state.public_snapshot_music_ids[0] + '/explanation')
      assert.ok(typeof explanation.text === 'string' && explanation.text.length > 0, 'Public source must survive API restart')
      mark('public-source-survives-restart')
      setStage('restart-login-and-snapshots')
      await navigate('/account/playlists/' + state.playlist_ids[0])
      await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
      await login(1)
      await refresh()
      await readPlaylist()
      const pair = await json(await apiResponse('/auth/login', 'POST', 200, async () => {
        // A reload intentionally ends the in-memory session, then sign in through the UI again.
        await page.reload()
        await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
        const account = credentials(1)
        await page.getByLabel('E-mail', { exact: true }).fill(account.email)
        await page.getByLabel('Senha', { exact: true }).fill(account.password)
        await page.getByRole('button', { name: 'Entrar', exact: true }).click()
      }))
      activePair = pair
      await page.getByRole('heading', { name: 'Sua conta.', exact: true }).waitFor()
      const storedPlaylist = await request('/api/v1/playlists/' + state.playlist_ids[0], { token: pair.access_token })
      assert.ok(JSON.stringify(storedPlaylist.tracks.map(row => row.item.id)) === JSON.stringify(state.playlist_music_ids), 'Ordered playlist identities must survive restart')
      await readFavorites(state)
      mark('browser-relogin-and-snapshot-persistence-after-restart')
      await page.getByRole('link', { name: 'Voltar à conta', exact: true }).click()
      await logout()
      await login(2)
      await page.getByRole('heading', { name: 'Sua próxima leitura pode ter uma trilha.', exact: true }).waitFor()
      await logout()
      mark('second-account-relogin-and-preserved-sql-fixtures')
    }
    setStage('traffic-and-browser-gates')
    assert.ok(pageErrors === 0 && consoleErrors === 0 && blocked === 0 && unresolvedFailures().length === 0, 'Browser, HTTP and external-request gates must be clean')
    for (const path of ['/api/v1/auth/login', '/api/v1/auth/me', '/api/v1/auth/refresh', '/api/v1/auth/logout', '/api/v1/users/me/favorites', '/api/v1/playlists']) {
      assert.ok([...traffic.keys()].some(key => key.includes(' ' + path + ' ')), 'Required real API traffic absent')
    }
    mark('real-same-origin-api-and-clean-browser')
    setSubstage('browser-close-success')
    closeStarted = true
    await deadline(() => browser.close(), 5_000)
    browser = null
    const artifact = { ...state, phase: config.phase, checks, traffic: [...traffic].map(([request, count]) => ({ request, count })), browser_errors: pageErrors, console_errors: consoleErrors, blocked_external_requests: blocked, proven_logout_abort_count: failures.length - unresolvedFailures().length }
    if (config.phase === 'create') await writeFile(config.artifact, JSON.stringify(artifact, null, 2) + '\n', { flag: 'wx' })
    console.log(JSON.stringify(artifact))
  } catch (error) {
    // Do not log Error.message, Playwright call logs, bodies, headers, emails or tokens.
    const failureLocation = [...(error?.stack || '').matchAll(/deployment\.mjs:(\d+):(\d+)/g)].slice(0, 3).map(match => ({ file: 'deployment.mjs', line: Number(match[1]), column: Number(match[2]) }))
    let authDiagnostic = null
    try {
      authDiagnostic = await deadline(() => page?.evaluate(() => {
        const routes = ['/login', '/register', '/account', '/account/favorites', '/music', '/books', '/read-with-music']
        const path = routes.includes(location.pathname) ? location.pathname : '/other'
        const form = document.querySelector('.account-form')
        const fields = ['auth-email', 'auth-username', 'auth-password', 'auth-confirmation']
        return { path, form_present: !!form, form_busy: form?.getAttribute('aria-busy') === 'true', alert_count: document.querySelectorAll('.account-error[role="alert"]').length,
          invalid_fields: fields.filter(id => { const input = document.getElementById(id); return input && !input.validity.valid }) }
      }), 2_000)
    } catch { /* Closed browser: keep the remaining diagnostic sanitized. */ }
    console.error(JSON.stringify({ status: 'FAIL', phase: config.phase, stage, substage, failure_location: failureLocation, auth_diagnostic: authDiagnostic, traffic: [...traffic].map(([request, count]) => ({ request, count })), error_kind: error?.name || 'Error', checks, browser_errors: pageErrors, console_errors: consoleErrors, blocked_external_requests: blocked, failures: unresolvedFailures(), proven_logout_abort_count: failures.length - unresolvedFailures().length }))
    process.exitCode = 1
  } finally {
    if (browser) {
      // Success-path close already consumed its 5s budget and the FAIL was emitted above.
      if (closeStarted) process.exit(1)
      setSubstage('browser-close-finally')
      closeStarted = true
      try { await deadline(() => browser.close(), 5_000) } catch {
        console.error(JSON.stringify({ status: 'FAIL', phase: config.phase, stage, substage, error_kind: 'BrowserCleanupDeadline' }))
        // An open Playwright transport must not keep this own Node child alive indefinitely.
        process.exit(1)
      }
    }
  }
}

if (process.argv.includes('--self-test')) await selfTest()
else {
  try { await run(deploymentConfig(process.env)) } catch {
    console.error(JSON.stringify({ status: 'FAIL', stage: 'opt-in-guard', error_kind: 'InvalidDeploymentConfiguration' }))
    process.exitCode = 1
  }
}
