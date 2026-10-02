import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { mkdir, mkdtemp, rm } from 'node:fs/promises'
import { createServer as createTcpServer } from 'node:net'
import { createServer as createHttpServer } from 'node:http'
import { tmpdir } from 'node:os'
import { resolve, sep } from 'node:path'
import { chromium } from 'playwright'
import { createServer } from 'vite'

const reservation = createTcpServer()
await new Promise(resolve => reservation.listen(0, '127.0.0.1', resolve))
const apiPort = reservation.address().port
assert.ok(apiPort > 0 && apiPort !== 8000 && apiPort !== 5432, 'Preserve existing API and PostgreSQL ports')
await new Promise(resolve => reservation.close(resolve))
const temporaryRoot = resolve(tmpdir())
const dataDir = await mkdtemp(resolve(temporaryRoot, 'gandalf-e2e-'))
const apiRoot = resolve('..', 'api')
const python = process.env.GANDALF_PYTHON || resolve(apiRoot, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python')
let api, apiClosed, apiSpawnError
let apiLog = ''
let browser
let server
let vite
try {
  api = spawn(python, ['local.py'], {
    cwd: apiRoot,
    env: { ...process.env, GANDALF_PORT: String(apiPort), GANDALF_LOCAL_DATA: dataDir, GANDALF_ONLINE: '0', GANDALF_HOST: '127.0.0.1', ONLINE_CATALOG: 'false', BOOK_PROVIDER: 'local' },
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  apiClosed = new Promise(done => api.once('close', done))
  api.stdout.on('data', data => { apiLog += data })
  api.stderr.on('data', data => { apiLog += data })
  api.on('error', error => { apiSpawnError = error })
  const apiUrl = `http://127.0.0.1:${apiPort}`
  let ready = false
  for (let attempt = 0; attempt < 100; attempt++) {
    if (apiSpawnError) throw apiSpawnError
    if (api.exitCode !== null) throw new Error('API exited: ' + apiLog)
    try {
      ready = (await fetch(apiUrl + '/health/ready', { signal: AbortSignal.timeout(500) })).ok
      if (ready) break
    } catch { /* Startup is still in progress. */ }
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  assert.ok(ready, 'Real API did not become ready: ' + apiLog)
  process.env.VITE_API_BASE_URL = '/api/v1'
  vite = await createServer({
    server: { middlewareMode: true, hmr: false, proxy: { '/api': apiUrl } }, logLevel: 'silent',
  })
  server = createHttpServer(vite.middlewares)
  await new Promise(done => server.listen(0, '127.0.0.1', done))
  const frontPort = server.address().port
  assert.ok(frontPort > 0 && frontPort !== 5173, 'Preserve the existing frontend port')
  console.log(`Live isolated ports: frontend ${frontPort}, API ${apiPort}; offline temporary SQLite`)
  const base = 'http://127.0.0.1:' + frontPort
  browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  page.setDefaultTimeout(10_000)
  page.setDefaultNavigationTimeout(30_000)
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  const reviewDir = resolve('..', '.impeccable', 'review')
  await mkdir(reviewDir, { recursive: true })
  async function signOut() {
    const response = page.waitForResponse(response => response.url().endsWith('/auth/logout') && response.status() === 204)
    await page.getByRole('button', { name: 'Sair da conta', exact: true }).click()
    const completed = await response
    await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
    return completed.request().postDataJSON().refresh_token
  }
  async function filterFavorites(type, label) {
    const response = page.waitForResponse(response => {
      const url = new URL(response.url())
      return url.pathname.endsWith('/users/me/favorites') && response.request().method() === 'GET' && url.searchParams.get('type') === type && response.ok()
    })
    await page.getByRole('group', { name: 'Tipos de favoritos' }).getByRole('button', { name: label, exact: true }).click()
    await (await response).finished()
    await page.waitForFunction(() => document.querySelector('.favorites-page')?.getAttribute('aria-busy') === 'false')
  }
  async function reviewVariants(flow) {
    for (const width of [1440, 390, 320]) {
      await page.setViewportSize({ width, height: width === 1440 ? 900 : 844 })
      for (const theme of ['dark', 'light']) {
        await page.evaluate(theme => document.documentElement.setAttribute('data-theme', theme), theme)
        await page.evaluate(() => document.fonts.ready)
        await page.waitForFunction(() => document.getAnimations().every(animation =>
          animation.effect?.getComputedTiming().iterations === Infinity || animation.playState === 'finished'))
        const contrasts = await page.locator('.preference-choice').evaluateAll(elements => {
          const luminance = color => {
            const rgb = color.match(/[\d.]+/g).slice(0, 3).map(value => Number(value) / 255)
            const linear = rgb.map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4)
            return linear[0] * .2126 + linear[1] * .7152 + linear[2] * .0722
          }
          return elements.map(element => {
            const style = getComputedStyle(element)
            const values = [luminance(style.color), luminance(style.backgroundColor)].sort((a, b) => b - a)
            return { label: element.textContent, ratio: (values[0] + .05) / (values[1] + .05) }
          })
        })
        assert.ok(contrasts.every(item => item.ratio >= 4.5), `${theme} preference contrast: ${JSON.stringify(contrasts)}`)
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${flow} ${width}px ${theme} fits`)
        const capture = flow.startsWith('auth-') ? flow : 'components-' + flow
        await page.screenshot({ path: resolve(reviewDir, `${capture}-${width}-${theme}.png`), fullPage: true })
      }
    }
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark'))
  }
  // The complete public flow must work without any external browser resources.
  await page.route('**/*', route => new URL(route.request().url()).origin === base ? route.continue() : route.abort())
  await page.goto(base + '/music')
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('Músicas calmas para estudar')
  await page.getByText('Ajustar preferências').click()
  await page.getByRole('radiogroup', { name: 'Vocais' }).getByRole('radio', { name: 'Instrumental', exact: true }).click()
  await page.getByRole('radiogroup', { name: 'Energia' }).getByRole('radio', { name: 'Baixa', exact: true }).click()
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByText(/Catálogo local selecionado/).waitFor()
  assert.ok(await page.locator('.result-row').count() > 0)
  await page.getByRole('button', { name: 'Por que esta sugestão?', exact: true }).first().click()
  await page.getByText(/Temas em comum:.*Classificação editorial/).first().waitFor()
  assert.match(await page.getByRole('link', { name: /Buscar no YouTube:/ }).first().getAttribute('href'), /^https:\/\/www.youtube.com\/results/)
  await reviewVariants('music')

  await page.goto(base + '/books')
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('Fantasia com construção de mundo sem romance')
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByRole('heading', { name: 'O Hobbit', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Por que esta sugestão?', exact: true }).first().click()
  await page.getByText(/Temas em comum:/).first().waitFor()
  await reviewVariants('books')
  await page.screenshot({ path: resolve(reviewDir, 'live-books.png'), fullPage: true })
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('xyzabcdefgh')
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByRole('heading', { name: 'Nenhuma boa opção por enquanto.' }).waitFor()

  await page.goto(base + '/read-with-music')
  await page.getByRole('textbox', { name: 'Qual livro você está lendo?' }).fill('Duna')
  await page.getByRole('button', { name: /Duna Frank Herbert/ }).click()
  await page.getByRole('button', { name: /Criar minha trilha/ }).click()
  await page.getByText(/Duração estimada em 5 minutos/).waitFor()
  assert.ok(await page.locator('.playlist-list li').count() > 0)
  assert.ok(await page.getByRole('link', { name: /Buscar no YouTube:/ }).count() > 0)
  await page.getByRole('button', { name: 'Por que esta sugestão?', exact: true }).first().click()
  await page.getByText(/Temas em comum:/).first().waitFor()
  await reviewVariants('reading')
  await page.screenshot({ path: resolve(reviewDir, 'live-reading.png'), fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 })
  await page.screenshot({ path: resolve(reviewDir, 'live-reading-mobile.png'), fullPage: true })
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1))
  await page.getByRole('button', { name: 'Trocar' }).click()
  assert.equal(await page.locator('.playlist-list li').count(), 0)

  // Account data and refresh revocation use the same real API and isolated DB.
  await page.getByRole('link', { name: 'Entrar na conta' }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.' }).waitFor()
  await reviewVariants('auth-login')
  await page.getByRole('link', { name: 'Criar conta', exact: true }).click()
  await page.getByRole('heading', { name: 'Crie sua conta.' }).waitFor()
  await reviewVariants('auth-register')
  const email = 'leitor@example.com'
  const password = 'a fictitious test phrase 123'
  await page.getByLabel('E-mail', { exact: true }).fill(email)
  await page.getByLabel('Nome de usuário', { exact: true }).fill('leitor')
  await page.getByLabel('Senha', { exact: true }).fill(password)
  await page.getByLabel('Confirme a senha', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Criar conta', exact: true }).click()
  await page.getByRole('status').filter({ hasText: 'Conta criada.' }).waitFor()
  assert.equal(await page.getByLabel('E-mail', { exact: true }).inputValue(), email)
  await page.getByLabel('Senha', { exact: true }).fill(password)
  const loginResponse = page.waitForResponse(response => response.url().endsWith('/auth/login') && response.status() === 200)
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await loginResponse
  await page.getByRole('heading', { name: 'Sua conta.' }).waitFor()
  await page.getByRole('button', { name: 'Atualizar dados', exact: true }).waitFor()
  assert.equal(await page.locator('.account-details dd').nth(1).textContent(), email)
  await reviewVariants('auth-account')
  // Persist a complete public reading source, then reload its snapshot and
  // verify that another account cannot read or delete it.
  await page.getByRole('link', { name: 'Criar uma trilha', exact: true }).click()
  await page.getByRole('textbox', { name: 'Qual livro você está lendo?' }).fill('Duna')
  await page.getByRole('button', { name: /Duna Frank Herbert/ }).click()
  await page.getByRole('button', { name: /Criar minha trilha/ }).click()
  await page.getByLabel('Nome da playlist').waitFor()
  const trackTitles = await page.locator('.playlist-track-main > strong').allTextContents()
  // Individual favorites share result status, but remain separate from playlists.
  const favoriteSave = page.waitForResponse(response => response.url().endsWith('/users/me/favorites') && response.request().method() === 'POST' && response.status() === 201)
  await page.getByRole('button', { name: 'Salvar nos favoritos: ' + trackTitles[0], exact: true }).click()
  const musicFavorite = await (await favoriteSave).json()
  assert.equal(musicFavorite.type, 'MUSIC')
  assert.equal(await page.getByRole('button', { name: 'Remover dos favoritos: ' + trackTitles[0], exact: true }).getAttribute('aria-pressed'), 'true')
  await page.getByLabel('Nome da playlist').fill('Duna para ler com chuva')
  await reviewVariants('playlists-save')
  await page.getByRole('button', { name: 'Salvar na minha conta', exact: true }).click()
  await page.getByRole('link', { name: 'Ver playlist', exact: true }).click()
  await page.getByRole('heading', { name: 'Duna para ler com chuva', exact: true }).waitFor()
  const playlistId = page.url().split('/').at(-1)
  assert.deepEqual(await page.locator('.playlist-list strong').allTextContents(), trackTitles)
  await reviewVariants('playlists-detail')
  await page.getByRole('link', { name: 'Voltar às playlists', exact: true }).click()
  await page.getByRole('link', { name: /Duna para ler com chuva/ }).waitFor()
  await reviewVariants('playlists-list')
  await page.getByRole('link', { name: 'Livros', exact: true }).first().click()
  await page.getByRole('heading', { name: 'Sua próxima história começa aqui.', exact: true }).waitFor()
  await page.getByLabel('Seu pedido', { exact: true }).fill('Fantasia com construção de mundo sem romance')
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByRole('heading', { name: 'O Hobbit', exact: true }).waitFor()
  const bookSave = page.waitForResponse(response => response.url().endsWith('/users/me/favorites') && response.request().method() === 'POST' && response.status() === 201)
  await page.getByRole('button', { name: 'Salvar nos favoritos: O Hobbit', exact: true }).click()
  const bookFavorite = await (await bookSave).json()
  assert.equal(bookFavorite.type, 'BOOK')
  await page.getByRole('link', { name: 'Minha conta', exact: true }).click()
  await page.getByRole('link', { name: 'Ver seus favoritos', exact: true }).click()
  await page.getByRole('heading', { name: 'O Hobbit', exact: true }).waitFor()
  await page.getByRole('heading', { name: trackTitles[0], exact: true }).waitFor()
  await reviewVariants('favorites-real')
  await page.getByRole('link', { name: 'Voltar à conta', exact: true }).click()
  const firstLoggedOutToken = await signOut()
  const revokedFirst = await fetch(apiUrl + '/api/v1/auth/refresh', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: firstLoggedOutToken }),
  })
  assert.equal(revokedFirst.status, 401)
  await fetch(apiUrl + '/api/v1/auth/register', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'outro@example.com', username: 'outro', password }),
  })
  await page.getByLabel('E-mail', { exact: true }).fill('outro@example.com')
  await page.getByLabel('Senha', { exact: true }).fill(password)
  const secondLogin = page.waitForResponse(response => response.url().endsWith('/auth/login') && response.ok())
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  const secondTokens = await (await secondLogin).json()
  await page.getByRole('heading', { name: 'Sua próxima leitura pode ter uma trilha.' }).waitFor()
  for (const method of ['GET', 'DELETE']) {
    const result = await fetch(apiUrl + '/api/v1/playlists/' + playlistId, { method, headers: { Authorization: 'Bearer ' + secondTokens.access_token } })
    assert.equal(result.status, 404, 'Another account cannot access the playlist')
  }
  const otherHeaders = { Authorization: 'Bearer ' + secondTokens.access_token, 'Content-Type': 'application/json' }
  const otherList = await fetch(apiUrl + '/api/v1/users/me/favorites', { headers: otherHeaders })
  assert.equal((await otherList.json()).total, 0)
  const otherStatus = await fetch(apiUrl + '/api/v1/users/me/favorites/status', { method: 'POST', headers: otherHeaders, body: JSON.stringify({ type: 'MUSIC', item_ids: [musicFavorite.item_id] }) })
  assert.deepEqual((await otherStatus.json()).favorites, {})
  const otherDelete = await fetch(apiUrl + '/api/v1/users/me/favorites/' + musicFavorite.id, { method: 'DELETE', headers: otherHeaders })
  assert.equal(otherDelete.status, 204, 'Deleting another account favorite is harmless and opaque')
  await page.getByRole('link', { name: 'Ver seus favoritos', exact: true }).click()
  await page.getByRole('heading', { name: 'Guarde o que você quer reencontrar.', exact: true }).waitFor()
  await page.getByRole('link', { name: 'Voltar à conta', exact: true }).click()
  await signOut()
  await page.getByLabel('E-mail', { exact: true }).fill(email)
  await page.getByLabel('Senha', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await page.getByRole('link', { name: 'Ver seus favoritos', exact: true }).click()
  await page.getByRole('heading', { name: 'O Hobbit', exact: true }).waitFor()
  await page.getByRole('heading', { name: trackTitles[0], exact: true }).waitFor()
  const persistedFavorite = page.waitForResponse(response => response.url().includes('/users/me/favorites?') && response.ok())
  await page.getByRole('button', { name: 'Atualizar favoritos', exact: true }).click()
  const persistedPage = await (await persistedFavorite).json()
  assert.deepEqual(persistedPage.items.find(item => item.id === musicFavorite.id), musicFavorite, 'Snapshot survives logout, account switching and an opaque foreign DELETE')
  await page.getByRole('heading', { name: trackTitles[0], exact: true }).waitFor()
  await filterFavorites('BOOK', 'Livros')
  await page.getByRole('heading', { name: 'O Hobbit', exact: true }).waitFor()
  assert.equal(await page.getByRole('heading', { name: trackTitles[0], exact: true }).count(), 0)
  await page.getByRole('button', { name: 'Remover dos favoritos: O Hobbit', exact: true }).click()
  await page.getByRole('heading', { name: 'Nenhum favorito deste tipo por enquanto.' }).waitFor()
  await filterFavorites('MUSIC', 'Músicas')
  await page.getByRole('heading', { name: trackTitles[0], exact: true }).waitFor()
  await page.getByRole('button', { name: 'Remover dos favoritos: ' + trackTitles[0], exact: true }).click()
  await page.getByRole('heading', { name: 'Nenhum favorito deste tipo por enquanto.' }).waitFor()
  await page.getByRole('link', { name: 'Voltar à conta', exact: true }).click()
  await page.getByRole('link', { name: /Duna para ler com chuva/ }).click()
  await page.getByRole('heading', { name: 'Duna para ler com chuva', exact: true }).waitFor()
  assert.deepEqual(await page.locator('.playlist-list strong').allTextContents(), trackTitles, 'Saved tracks survive logout and account switching')
  await page.getByRole('button', { name: 'Excluir playlist', exact: true }).click()
  await page.getByRole('button', { name: 'Manter playlist', exact: true }).click()
  await page.waitForFunction(button => document.activeElement === button, await page.getByRole('button', { name: 'Excluir playlist', exact: true }).elementHandle())
  assert.equal(await page.getByRole('button', { name: 'Excluir playlist', exact: true }).evaluate(element => document.activeElement === element), true)
  await page.getByRole('button', { name: 'Excluir playlist', exact: true }).click()
  await reviewVariants('playlists-delete')
  await page.getByRole('button', { name: 'Confirmar exclusão', exact: true }).click()
  await page.getByRole('status').filter({ hasText: 'Playlist excluída' }).waitFor()
  await page.getByRole('heading', { name: 'Sua próxima leitura pode ter uma trilha.' }).waitFor()
  await page.getByRole('link', { name: 'Explorar sugestões', exact: true }).click()
  await page.getByRole('link', { name: 'Minha conta', exact: true }).click()
  await page.getByRole('button', { name: 'Atualizar dados', exact: true }).waitFor()
  const lastLoggedOutToken = await signOut()
  const revoked = await fetch(apiUrl + '/api/v1/auth/refresh', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: lastLoggedOutToken }),
  })
  assert.equal(revoked.status, 401, 'Logout revokes the refresh token in the database')
  assert.deepEqual(errors, [])
  console.log('Live E2E passed: real API, SQLite, public flows, registration/login/account/logout/revocation, music/book favorites and account isolation, desktop/mobile and both themes.')
} finally {
  await browser?.close()
  if (server) await new Promise(done => server.close(done))
  await vite?.close()
  if (api?.pid && api.exitCode === null) api.kill()
  await apiClosed
  assert.ok(dataDir.startsWith(temporaryRoot + sep) && dataDir.split(sep).at(-1).startsWith('gandalf-e2e-'))
  await rm(dataDir, { recursive: true, force: true })
}
