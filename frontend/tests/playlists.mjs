import assert from 'node:assert/strict'
import { chromium } from 'playwright'
import { createServer } from 'vite'

const server = await createServer({ server: { host: '127.0.0.1', port: 0 }, logLevel: 'silent' })
await server.listen()
const base = 'http://127.0.0.1:' + server.httpServer.address().port
const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ reducedMotion: 'reduce' })
page.setDefaultTimeout(10000)
const errors = []
const requestPaths = []
page.on('pageerror', error => errors.push(error.message))
const user = { id: 'user-a', email: 'a@example.com', username: 'leitor', created_at: '2026-10-01T12:00:00Z' }
const track = { id: 'track-a', title: 'Faixa de teste', artist: 'Artista de teste', duration_ms: 180000, links: { provider: 'https://musicbrainz.org/recording/test' } }
const summary = id => ({ id, name: 'Playlist ' + id, description: null, source: 'READ_WITH_MUSIC', source_recommendation_id: 'reading-a', total_duration_ms: 180000, duration_estimated: false, tracks_count: 1, created_at: user.created_at, updated_at: user.created_at })
let listFailure = false, saveStatus = 201, detailStatus = 200, deleteStatus = 204, rejectToken = false, refreshStatus = 200
let saveHold, listHold, saveCalls = [], listCalls = [], refreshCalls = 0, deleted = false
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }
async function login() {
  await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
}
async function reading() {
  await page.getByRole('link', { name: 'Ler com música', exact: true }).click()
  await page.getByLabel('Qual livro você está lendo?').fill('Livro')
  await page.getByRole('button', { name: /Livro de teste Autora/ }).click()
  await page.getByRole('button', { name: /Cinematográfica Como uma trilha de filme/ }).click()
  await page.getByLabel('Seu contexto').fill('Chuva e drama')
  await page.getByLabel('Duração', { exact: true }).selectOption('90')
  await page.getByRole('button', { name: 'Criar minha trilha', exact: true }).click()
  await page.getByRole('heading', { name: 'Livro de teste', exact: true }).waitFor()
}
try {
  await page.route('**/api/v1/**', async route => {
    const request = route.request(), url = new URL(request.url()), path = url.pathname.replace('/api/v1', '')
    requestPaths.push(request.method() + ' ' + path)
    const failure = status => ({ status, json: { error: { code: 'TEST', message: 'Falha simulada.' } } })
    let response
    if (path === '/auth/login') response = { json: { access_token: 'access-old', refresh_token: 'refresh-old', expires_in: 900 } }
    else if (path === '/auth/register') response = { status: 201, json: user }
    else if (path === '/auth/me') response = { json: user }
    else if (path === '/auth/logout') response = { status: 204, body: '' }
    else if (path === '/auth/refresh') { refreshCalls++; response = refreshStatus === 200 ? { json: { access_token: 'access-new', refresh_token: 'refresh-new', expires_in: 900 } } : failure(refreshStatus) }
    else if (path === '/users/me/favorites/status') response = { json: { favorites: {} } }
    else if (path === '/books/search') response = { json: { items: [{ id: 'book-a', title: 'Livro de teste', authors: ['Autora'] }] } }
    else if (path === '/recommendations/read-with-music') response = { json: { recommendation_id: 'reading-a', items: [{ position: 1, item: track }], playlist: { total_duration_ms: 180000, tracks_count: 1 } } }
    else if (path === '/playlists' && request.method() === 'POST') {
      saveCalls.push(request.postDataJSON())
      const hold = saveHold
      if (hold) await hold.promise
      response = saveStatus === 201 ? { status: 201, json: { ...summary('saved'), name: request.postDataJSON().name, tracks: [{ position: 1, item: track }] } } : failure(saveStatus)
    } else if (path === '/playlists') {
      const offset = Number(url.searchParams.get('offset'))
      listCalls.push(offset)
      const hold = listHold
      if (hold) await hold.promise
      response = listFailure ? failure(503) : { json: { items: deleted ? [] : Array.from({ length: offset ? 1 : 10 }, (_, index) => summary(String(offset + index))), total: deleted ? 0 : 11, limit: 10, offset } }
    } else if (path.startsWith('/playlists/')) {
      if (request.method() === 'DELETE') { deleted = deleteStatus === 204; response = deleteStatus === 204 ? { status: 204, body: '' } : failure(deleteStatus) }
      else response = detailStatus === 200 ? { json: { ...summary(path.split('/').at(-1)), tracks: [{ position: 1, item: track }] } } : failure(detailStatus)
    } else throw new Error('Unexpected endpoint: ' + path)
    if (path.startsWith('/playlists') && rejectToken && request.headers().authorization === 'Bearer access-old') response = failure(401)
    await route.fulfill(response).catch(() => {})
  })
  await page.goto(base + '/read-with-music')
  await page.getByLabel('Qual livro você está lendo?').fill('Livro')
  await page.getByRole('button', { name: /Livro de teste Autora/ }).click()
  await page.getByRole('button', { name: /Cinematográfica Como uma trilha de filme/ }).click()
  await page.getByLabel('Seu contexto').fill('Chuva e drama')
  await page.getByLabel('Duração', { exact: true }).selectOption('90')
  await page.getByRole('button', { name: 'Criar minha trilha', exact: true }).click()
  await page.getByRole('link', { name: 'Entrar para salvar' }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
  await page.getByRole('link', { name: 'Criar conta', exact: true }).click()
  await page.getByRole('heading', { name: 'Crie sua conta.', exact: true }).waitFor()
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Nome de usuário').fill('leitor')
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  await page.getByLabel('Confirme a senha').fill('test phrase 123')
  assert.deepEqual(await page.locator('.account-form input').evaluateAll(inputs => inputs.filter(input => !input.checkValidity()).map(input => ({ id: input.id, message: input.validationMessage }))), [], 'Registration fields are valid before submit')
  await page.getByRole('button', { name: 'Criar conta', exact: true }).click()
  await page.getByRole('status').filter({ hasText: 'Conta criada.' }).waitFor()
  await login()
  await page.getByLabel('Nome da playlist').waitFor()
  assert.equal(await page.locator('.playlist-list li').count(), 1, 'Registration/login preserves the generated reading source')
  assert.equal(await page.getByLabel('Duração', { exact: true }).inputValue(), '90')
  assert.equal(await page.getByLabel('Seu contexto').inputValue(), 'Chuva e drama')
  assert.equal(await page.getByRole('button', { name: /Cinematográfica Como uma trilha de filme/ }).getAttribute('aria-pressed'), 'true')
  saveStatus = 503
  await page.getByRole('button', { name: 'Salvar na minha conta', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'indisponíveis agora' }).waitFor()
  assert.equal(await page.getByRole('alert').evaluate(element => document.activeElement === element), true)
  saveStatus = 201; saveHold = deferred()
  await page.getByLabel('Nome da playlist').fill('  Minha leitura  ')
  await page.getByRole('button', { name: 'Tentar salvar novamente' }).click()
  await page.getByRole('button', { name: 'Salvando…' }).waitFor()
  assert.equal(await page.getByRole('button', { name: 'Salvando…' }).isDisabled(), true)
  saveHold.resolve(); saveHold = null
  await page.getByRole('link', { name: 'Ver playlist', exact: true }).waitFor()
  assert.deepEqual(saveCalls.at(-1), { name: 'Minha leitura', source_recommendation_id: 'reading-a' })
  await page.getByRole('link', { name: 'Minha conta', exact: true }).click()
  await page.getByRole('link', { name: /Playlist 0 / }).waitFor()
  await page.getByRole('button', { name: 'Próximas', exact: true }).click()
  await page.getByRole('link', { name: /Playlist 10 / }).waitFor()
  assert.equal(listCalls.at(-1), 10)
  assert.equal(await page.getByRole('button', { name: 'Próximas', exact: true }).isDisabled(), true)
  listFailure = true
  await page.getByRole('button', { name: 'Atualizar playlists' }).click()
  await page.getByRole('alert').filter({ hasText: 'indisponíveis agora' }).waitFor()
  listFailure = false
  await page.getByRole('button', { name: 'Tentar novamente', exact: true }).click()
  await page.getByRole('link', { name: /Playlist 10 / }).click()
  await page.getByRole('heading', { name: 'Playlist 10', exact: true }).waitFor()
  assert.equal(await page.getByRole('link', { name: 'Ver fonte: Faixa de teste' }).getAttribute('href'), track.links.provider)
  await page.getByRole('button', { name: 'Excluir playlist', exact: true }).click()
  assert.equal(await page.getByRole('button', { name: 'Confirmar exclusão' }).evaluate(element => document.activeElement === element), true)
  await page.getByRole('button', { name: 'Manter playlist', exact: true }).click()
  await page.getByRole('button', { name: 'Excluir playlist', exact: true }).click()
  deleteStatus = 503
  await page.getByRole('button', { name: 'Confirmar exclusão' }).click()
  await page.getByRole('alert').filter({ hasText: 'indisponíveis agora' }).waitFor()
  assert.equal(await page.locator('.playlist-list li').count(), 1, 'Failed deletion preserves the playlist')
  deleteStatus = 204
  await page.getByRole('button', { name: 'Confirmar exclusão' }).click()
  await page.getByRole('status').filter({ hasText: 'Playlist excluída' }).waitFor()
  await page.getByRole('heading', { name: 'Sua próxima leitura pode ter uma trilha.' }).waitFor()
  await reading()
  saveStatus = 404
  await page.getByRole('button', { name: 'Salvar na minha conta', exact: true }).click()
  await page.getByRole('alert').filter({ hasText: 'saiu do cache' }).waitFor()
  assert.equal(await page.getByRole('button', { name: 'Tentar salvar novamente' }).isDisabled(), true)
  await page.getByRole('button', { name: 'Criar minha trilha', exact: true }).click()
  await page.getByLabel('Nome da playlist').waitFor()
  // Even if the provider reuses an ID, a newly generated source resets save state.
  await page.getByRole('link', { name: 'Minha conta', exact: true }).click()
  rejectToken = true
  await page.getByRole('button', { name: 'Atualizar playlists' }).click()
  await page.getByRole('button', { name: 'Atualizar playlists' }).waitFor({ state: 'visible' })
  await page.waitForFunction(() => !document.querySelector('.account-playlists').getAttribute('aria-busy')?.includes('true'))
  assert.equal(refreshCalls, 1, 'Playlist requests use the existing refresh flow')
  rejectToken = false; deleted = false
  await page.getByRole('button', { name: 'Atualizar playlists' }).click()
  await page.getByRole('link', { name: /Playlist 0 / }).waitFor()
  detailStatus = 404
  await page.getByRole('link', { name: /Playlist 0 / }).click()
  await page.getByRole('alert').filter({ hasText: 'não está disponível nesta conta' }).waitFor()
  detailStatus = 200
  await page.getByRole('button', { name: 'Tentar novamente', exact: true }).click()
  await page.getByRole('heading', { name: 'Playlist 0', exact: true }).waitFor()
  // A late list response after sign-out never repopulates the private library.
  await page.getByRole('link', { name: 'Voltar às playlists' }).click()
  await page.getByRole('button', { name: 'Atualizar playlists' }).waitFor()
  listHold = deferred()
  await page.getByRole('button', { name: 'Atualizar playlists' }).click()
  await page.getByText('Buscando suas playlists…').waitFor()
  await page.getByRole('button', { name: 'Sair da conta', exact: true }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.' }).waitFor()
  listHold.resolve(); listHold = null
  assert.equal(await page.locator('.saved-playlists').count(), 0)
  refreshStatus = 401
  await login()
  await page.getByRole('link', { name: /Playlist 0 / }).waitFor()
  rejectToken = true
  await page.getByRole('button', { name: 'Atualizar playlists' }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.' }).waitFor()
  await page.getByRole('status').filter({ hasText: 'Sua sessão terminou' }).waitFor()
  assert.deepEqual(errors, [])
  console.log('Playlist UI passed: auth return, save/retry/expired source, pagination, detail/404, delete/retry, refresh and cancellation.')
} catch (error) {
  console.error('Playlist test diagnostics:', JSON.stringify({ url: page.url(), requests: requestPaths, alerts: await page.getByRole('alert').allTextContents(), statuses: await page.getByRole('status').allTextContents(), errors }))
  throw error
} finally { await browser.close(); await server.close() }
