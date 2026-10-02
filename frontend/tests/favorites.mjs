import assert from 'node:assert/strict'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { createServer } from 'vite'

const server = await createServer({ server: { host: '127.0.0.1', port: 0 }, logLevel: 'silent' })
await server.listen()
const base = 'http://127.0.0.1:' + server.httpServer.address().port
const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ reducedMotion: 'reduce' })
page.setDefaultTimeout(10000)
const reviewDir = resolve('..', '.impeccable', 'review')
await mkdir(reviewDir, { recursive: true })
const user = { id: 'user-a', email: 'a@example.com', username: 'leitor', created_at: '2026-10-01T12:00:00Z' }
const track = { id: '11111111-1111-4111-8111-111111111111', title: 'Uma faixa para reencontrar', artist: 'Artista de teste', duration_ms: 180000, links: { provider: 'https://musicbrainz.org/recording/test' } }
const book = { id: '22222222-2222-4222-8222-222222222222', title: 'Um livro para reencontrar', authors: ['Autora de teste'], provider: 'local', publication_year: 2024 }
const recId = '33333333-3333-4333-8333-333333333333'
const favorite = (item, type, id = '44444444-4444-4444-8444-444444444444') => ({ id, type, item_id: item.id, item, created_at: user.created_at })
const saved = new Map()
const calls = [], errors = [], statusCalls = [], listCalls = [], saveCalls = [], deleteCalls = [], recommendationCalls = []
let saveStatus = 201, statusStatus = 200, listStatus = 200, deleteStatus = 204, refreshStatus = 200, rejectToken = false, refreshCalls = 0, listHold
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }
page.on('pageerror', error => errors.push(error.message))
async function capture(flow) {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: width === 1440 ? 900 : 844 })
    for (const theme of ['dark', 'light']) {
      await page.evaluate(theme => document.documentElement.setAttribute('data-theme', theme), theme)
      await page.evaluate(() => document.fonts.ready)
      await page.waitForFunction(() => document.getAnimations().every(animation =>
        animation.effect?.getComputedTiming().iterations === Infinity || animation.playState === 'finished'))
      await page.evaluate(() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))))
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${flow} ${width} ${theme} fits`)
      await page.screenshot({ path: resolve(reviewDir, `favorites-${flow}-${width}-${theme}.png`), fullPage: true })
    }
  }
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark'))
}
async function login() {
  await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
}
async function search(kind) {
  await page.getByRole('link', { name: kind === 'music' ? 'Música' : 'Livros', exact: true }).first().click()
  await page.getByRole('heading', { name: kind === 'music' ? 'Encontre a música certa para agora.' : 'Sua próxima história começa aqui.', exact: true }).waitFor()
  await page.getByLabel('Seu pedido', { exact: true }).fill(kind === 'music' ? 'Música para uma noite calma' : 'Livros para explorar outros mundos')
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByRole('heading', { name: kind === 'music' ? track.title : book.title, exact: true }).waitFor()
}
async function filterFavorites(type, label) {
  const response = page.waitForResponse(response => {
    const url = new URL(response.url())
    return url.pathname.endsWith('/users/me/favorites') && response.request().method() === 'GET' && (url.searchParams.get('type') || '') === type && response.ok()
  })
  await page.getByRole('group', { name: 'Tipos de favoritos' }).getByRole('button', { name: label, exact: true }).click()
  await (await response).finished()
  await page.waitForFunction(() => document.querySelector('.favorites-page')?.getAttribute('aria-busy') === 'false')
}
try {
  await page.route('**/api/v1/**', async route => {
    const request = route.request(), url = new URL(request.url()), path = url.pathname.replace('/api/v1', ''), method = request.method()
    calls.push(method + ' ' + path)
    const failure = status => ({ status, json: { error: { code: 'TEST', message: 'Falha simulada.' } } })
    let response
    if (path === '/auth/register') response = { status: 201, json: user }
    else if (path === '/auth/login') response = { json: { access_token: 'access-old', refresh_token: 'refresh-old', expires_in: 900 } }
    else if (path === '/auth/me') response = { json: user }
    else if (path === '/auth/logout') response = { status: 204, body: '' }
    else if (path === '/auth/refresh') { refreshCalls++; response = refreshStatus === 200 ? { json: { access_token: 'access-new', refresh_token: 'refresh-new', expires_in: 900 } } : failure(refreshStatus) }
    else if (path === '/playlists') response = { json: { items: [], total: 0, limit: 10, offset: 0 } }
    else if (path === '/recommendations/music' || path === '/recommendations/books') { recommendationCalls.push(request.postDataJSON()); response = { json: { recommendation_id: recId, items: [{ position: 1, item: path.endsWith('music') ? track : book }], meta: { has_more: true, next_offset: 10 } } } }
    else if (path === '/users/me/favorites/status') {
      const body = request.postDataJSON(); statusCalls.push(body)
      assert.deepEqual(Object.keys(body).sort(), ['item_ids', 'type'])
      assert.equal(new Set(body.item_ids).size, body.item_ids.length)
      response = statusStatus === 200 ? { json: { favorites: Object.fromEntries([...saved.values()].filter(item => item.type === body.type && body.item_ids.includes(item.item_id)).map(item => [item.item_id, item.id])) } } : failure(statusStatus)
    } else if (path === '/users/me/favorites' && method === 'POST') {
      const body = request.postDataJSON(); saveCalls.push(body)
      assert.deepEqual(body, { recommendation_id: recId, item_id: body.item_id })
      if (saveStatus === 200 || saveStatus === 201) {
        const entry = saved.get(body.item_id) || favorite(body.item_id === track.id ? track : book, body.item_id === track.id ? 'MUSIC' : 'BOOK', body.item_id === track.id ? '44444444-4444-4444-8444-444444444444' : '55555555-5555-4555-8555-555555555555')
        saved.set(body.item_id, entry); response = { status: saveStatus, json: entry }
      } else response = failure(saveStatus)
    } else if (path === '/users/me/favorites') {
      const type = url.searchParams.get('type'), offset = Number(url.searchParams.get('offset')), limit = Number(url.searchParams.get('limit'))
      listCalls.push({ type, offset, limit })
      const hold = listHold; if (hold) await hold.promise
      const items = [...saved.values()].filter(item => !type || type === item.type)
      response = listStatus === 200 ? { json: { items: items.slice(offset, offset + limit), total: items.length, limit, offset } } : failure(listStatus)
    } else if (path.startsWith('/users/me/favorites/') && method === 'DELETE') {
      const id = path.split('/').at(-1); deleteCalls.push(id)
      if (deleteStatus === 204) { for (const [key, entry] of saved) if (entry.id === id) saved.delete(key); response = { status: 204, body: '' } }
      else response = failure(deleteStatus)
    } else throw new Error('Unexpected endpoint: ' + path)
    if (path.startsWith('/users/me/favorites') && rejectToken && request.headers().authorization === 'Bearer access-old') response = failure(401)
    await route.fulfill(response).catch(() => {})
  })
  await page.goto(base + '/music')
  await page.getByLabel('Seu pedido', { exact: true }).fill('Música para uma noite calma')
  await page.getByText('Ajustar preferências', { exact: false }).click()
  await page.getByRole('radiogroup', { name: 'Vocais' }).getByRole('radio', { name: 'Instrumental', exact: true }).click()
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByRole('button', { name: 'Salvar nos favoritos: ' + track.title }).click()
  assert.equal(saveCalls.length, 0)
  assert.equal(statusCalls.length, 0, 'Anonymous results never request private status')
  await capture('invitation')
  await page.getByRole('link', { name: 'Entrar para salvar', exact: true }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
  await page.getByRole('link', { name: 'Criar conta', exact: true }).click()
  await page.getByRole('heading', { name: 'Crie sua conta.', exact: true }).waitFor()
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Nome de usuário').fill(user.username)
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  await page.getByLabel('Confirme a senha').fill('test phrase 123')
  await page.getByRole('button', { name: 'Criar conta', exact: true }).click()
  await page.getByRole('status').filter({ hasText: 'Conta criada.' }).waitFor()
  await login()
  await page.getByRole('heading', { name: track.title, exact: true }).waitFor()
  await page.waitForFunction(() => !document.querySelector('.favorite-button')?.disabled)
  assert.equal(saveCalls.length, 0, 'Authentication returns without auto-saving')
  assert.equal(calls.filter(path => path === 'POST /recommendations/music').length, 1, 'Returns the original public result without refetch')
  assert.equal(await page.getByLabel('Seu pedido', { exact: true }).inputValue(), 'Música para uma noite calma')
  await page.getByText('Ajustar preferências', { exact: false }).click()
  assert.equal(await page.getByRole('radiogroup', { name: 'Vocais' }).getByRole('radio', { name: 'Instrumental', exact: true }).getAttribute('aria-checked'), 'true')
  assert.deepEqual(statusCalls.at(-1), { type: 'MUSIC', item_ids: [track.id] })
  saveStatus = 503
  await page.getByRole('button', { name: 'Salvar nos favoritos: ' + track.title }).click()
  await page.getByRole('alert').filter({ hasText: 'indisponíveis agora' }).waitFor()
  assert.equal(await page.getByRole('button', { name: 'Salvar nos favoritos: ' + track.title }).getAttribute('aria-pressed'), 'false')
  saveStatus = 200
  await page.getByRole('button', { name: 'Salvar nos favoritos: ' + track.title }).click()
  await page.getByRole('status').filter({ hasText: 'Salvo nos seus favoritos.' }).waitFor()
  assert.equal(await page.getByRole('button', { name: 'Remover dos favoritos: ' + track.title }).getAttribute('aria-pressed'), 'true', 'Idempotent 200 marks saved')
  await capture('saved')
  deleteStatus = 503
  await page.getByRole('button', { name: 'Remover dos favoritos: ' + track.title }).click()
  await page.getByRole('alert').filter({ hasText: 'indisponíveis agora' }).waitFor()
  assert.equal(await page.getByRole('button', { name: 'Remover dos favoritos: ' + track.title }).getAttribute('aria-pressed'), 'true')
  deleteStatus = 204
  await page.getByRole('button', { name: 'Remover dos favoritos: ' + track.title }).click()
  await page.getByRole('status').filter({ hasText: 'Removido dos favoritos.' }).waitFor()
  assert.equal(deleteCalls.at(-1), favorite(track, 'MUSIC').id, 'DELETE uses favorite ID, not item ID')
  saveStatus = 404
  await page.getByRole('button', { name: 'Salvar nos favoritos: ' + track.title }).click()
  await page.getByRole('alert').filter({ hasText: 'seleção expirou' }).waitFor()
  await capture('expired')
  saveStatus = 201
  await search('books')
  await page.getByRole('button', { name: 'Salvar nos favoritos: ' + book.title }).click()
  await page.getByRole('status').filter({ hasText: 'Salvo nos seus favoritos.' }).waitFor()
  assert.deepEqual(statusCalls.at(-1), { type: 'BOOK', item_ids: [book.id] })
  statusStatus = 503
  await search('music')
  await page.getByRole('button', { name: 'Consultar favoritos novamente' }).waitFor()
  assert.equal(await page.getByRole('button', { name: 'Salvar nos favoritos: ' + track.title }).isDisabled(), true)
  statusStatus = 200
  await page.getByRole('button', { name: 'Consultar favoritos novamente' }).click()
  await page.getByRole('button', { name: 'Salvar nos favoritos: ' + track.title }).click()
  await page.getByRole('status').filter({ hasText: 'Salvo nos seus favoritos.' }).waitFor()
  await page.getByRole('link', { name: 'Minha conta', exact: true }).click()
  await page.getByRole('link', { name: 'Ver seus favoritos', exact: true }).click()
  await page.getByRole('heading', { name: book.title, exact: true }).waitFor()
  await page.getByRole('heading', { name: track.title, exact: true }).waitFor()
  await capture('collection')
  await filterFavorites('BOOK', 'Livros')
  await page.getByRole('heading', { name: book.title, exact: true }).waitFor()
  assert.equal(await page.getByRole('heading', { name: track.title, exact: true }).count(), 0)
  assert.deepEqual(listCalls.at(-1), { type: 'BOOK', offset: 0, limit: 10 })
  deleteStatus = 503
  await page.getByRole('button', { name: 'Remover dos favoritos: ' + book.title }).click()
  await page.getByRole('alert').waitFor()
  assert.equal(await page.getByRole('heading', { name: book.title, exact: true }).count(), 1, 'Failed deletion preserves snapshot')
  deleteStatus = 204
  await page.getByRole('button', { name: 'Remover dos favoritos: ' + book.title }).click()
  await page.getByRole('heading', { name: 'Nenhum favorito deste tipo por enquanto.' }).waitFor()
  await capture('empty')
  // A last item removed from page two returns to the preceding valid page.
  for (let index = 0; index < 10; index++) saved.set('extra-' + index, favorite({ ...track, id: 'extra-' + index, title: 'Outra faixa ' + index }, 'MUSIC', 'favorite-' + index))
  await filterFavorites('', 'Todos')
  await page.getByRole('button', { name: 'Próximas', exact: true }).click()
  await page.getByRole('heading', { name: 'Outra faixa 9', exact: true }).waitFor()
  assert.equal(listCalls.at(-1).offset, 10)
  await page.getByRole('button', { name: 'Remover dos favoritos: Outra faixa 9' }).click()
  await page.getByRole('heading', { name: track.title, exact: true }).waitFor()
  assert.equal(listCalls.at(-1).offset, 0)
  listStatus = 503
  await page.getByRole('button', { name: 'Atualizar favoritos' }).click()
  await page.getByRole('alert').waitFor()
  await capture('unavailable')
  listStatus = 200; rejectToken = true
  await page.getByRole('button', { name: 'Tentar novamente', exact: true }).click()
  await page.getByRole('heading', { name: track.title, exact: true }).waitFor()
  assert.equal(refreshCalls, 1, 'Favorites reuse token rotation')
  rejectToken = false
  listHold = deferred()
  await page.getByRole('button', { name: 'Atualizar favoritos' }).click()
  await page.getByText('Buscando seus favoritos…').waitFor()
  await page.getByRole('link', { name: 'Voltar à conta', exact: true }).click()
  await page.getByRole('button', { name: 'Sair da conta', exact: true }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
  listHold.resolve(); listHold = null
  assert.equal(await page.locator('.favorite-list').count(), 0, 'Late private responses never repopulate after logout')
  // A direct private route returns to the collection after authentication.
  await page.goto(base + '/account/favorites')
  await login()
  await page.getByRole('heading', { name: track.title, exact: true }).waitFor()
  refreshStatus = 401; rejectToken = true
  await page.getByRole('button', { name: 'Atualizar favoritos' }).click()
  await page.getByRole('heading', { name: 'Entre no Gandalf.', exact: true }).waitFor()
  await page.getByRole('status').filter({ hasText: 'Sua sessão terminou' }).waitFor()
  rejectToken = false; refreshStatus = 200
  await search('books')
  await page.getByRole('button', { name: 'Salvar nos favoritos: ' + book.title }).click()
  await page.getByRole('link', { name: 'Entrar para salvar', exact: true }).click()
  const beforeBookLogin = { saves: saveCalls.length, searches: recommendationCalls.length }
  await login()
  await page.getByRole('heading', { name: book.title, exact: true }).waitFor()
  assert.equal(saveCalls.length, beforeBookLogin.saves, 'Book invitation also requires an explicit save after login')
  assert.equal(recommendationCalls.length, beforeBookLogin.searches)
  await page.getByRole('button', { name: 'Ver outros livros', exact: true }).click()
  await page.getByText('Não encontramos novos livros nesta tentativa.', { exact: false }).waitFor()
  assert.deepEqual(recommendationCalls.at(-1), { query: 'Livros para explorar outros mundos', limit: 10, excluded_book_ids: [book.id], offset: 10 }, 'Book renewal retains seen IDs and pagination through authentication')
  assert.deepEqual(errors, [])
  console.log('Favorites UI passed: batch status, auth return without auto-save, save/200/delete/retry/expired source, filters, pagination fallback, token refresh, private-route return and cancellation.')
} catch (error) {
  console.error('Favorites diagnostics:', JSON.stringify({ url: page.url(), calls, alerts: await page.getByRole('alert').allTextContents(), errors }))
  throw error
} finally { await browser.close(); await server.close() }
