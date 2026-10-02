import assert from 'node:assert/strict'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { createServer as createHttpServer } from 'node:http'
import { chromium } from 'playwright'
import { createServer } from 'vite'

// Vite treats port:0 as its default port. Middleware on a Node HTTP listener
// gives this isolated test an actual ephemeral port, preserving the live UI.
const vite = await createServer({ server: { middlewareMode: true, hmr: false }, logLevel: 'silent' })
const server = createHttpServer(vite.middlewares)
await new Promise(done => server.listen(0, '127.0.0.1', done))
const port = server.address().port
assert.ok(port > 0 && port !== 5173, 'Use an actual ephemeral test port')
console.log('Isolated reroll test port: ' + port)
let browser
let held
try {
  browser = await chromium.launch({ headless: true })
  const context = await browser.newContext({ reducedMotion: 'reduce' })
  const page = await context.newPage()
  page.setDefaultTimeout(10000)
  const base = 'http://127.0.0.1:' + port
  const reviewDir = resolve('..', '.impeccable', 'review')
  await mkdir(reviewDir, { recursive: true })
  const uuid = n => `00000000-0000-4000-8000-${String(n).padStart(12, '0')}`
  const track = n => ({ id: uuid(n), title: 'Faixa ' + n, artist: 'Artista de teste', duration_ms: 180000 })
  const rec = (ids, offset = null, more = true, degraded = false) => ({
    recommendation_id: uuid(9000), items: ids.map((n, i) => ({ position: i + 1, item: track(n) })),
    meta: { has_more: more, next_offset: offset, degraded },
  })
  const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }
  const errors = [], requests = [], saves = []
  const user = { id: uuid(9999), email: 'test@example.com', username: 'leitor', created_at: '2026-10-02T12:00:00Z' }
  let next = rec([1], 15), failure = false, boundaryMode = false, boundaryNext = 1, expireSession = false
  page.on('pageerror', error => errors.push(error.message))
  await page.route('**/api/v1/**', async route => {
    const request = route.request(), path = new URL(request.url()).pathname.replace('/api/v1', '')
    if (path === '/recommendations/music') {
      const body = request.postDataJSON(); requests.push(body)
      const response = boundaryMode ? rec(Array.from({ length: body.excluded_music_ids ? body.limit : 9 }, () => boundaryNext++)) : next
      const failed = failure, hold = held
      if (hold) await hold.promise
      return route.fulfill(failed ? { status: 503, json: { detail: 'Fonte temporariamente indisponível.' } } : { json: response }).catch(() => {})
    }
    if (path === '/auth/login') return route.fulfill({ json: { access_token: 'access', refresh_token: 'refresh', expires_in: 900 } })
    if (path === '/auth/me') return route.fulfill({ json: user })
    if (path === '/auth/refresh') return route.fulfill({ status: 401, json: { detail: 'Sessão expirada.' } })
    if (path === '/users/me/favorites/status') return route.fulfill({ json: { favorites: {} } })
    if (path === '/users/me/favorites' && request.method() === 'POST') {
      saves.push(request.postDataJSON())
      if (expireSession) return route.fulfill({ status: 401, json: { detail: 'Sessão expirada.' } })
      throw new Error('Login must not save automatically')
    }
    throw new Error('Unexpected route: ' + path)
  })
  const reroll = () => page.getByRole('button', { name: 'Ver outras músicas', exact: true })
  const heading = n => page.getByRole('heading', { name: 'Faixa ' + n, exact: true })
  const search = async query => {
    await page.getByLabel('Seu pedido', { exact: true }).fill(query)
    await page.getByRole('button', { name: 'Encontrar sugestões', exact: true }).click()
  }
  async function capture(state) {
    for (const width of [1440, 390, 320]) {
      await page.setViewportSize({ width, height: width === 1440 ? 900 : 844 })
      for (const theme of ['dark', 'light']) {
        await page.evaluate(theme => document.documentElement.setAttribute('data-theme', theme), theme)
        await page.evaluate(() => document.fonts.ready)
        await page.waitForFunction(() => document.getAnimations().every(animation => animation.effect?.getComputedTiming().iterations === Infinity || animation.playState === 'finished'))
        await page.evaluate(() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))))
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${state}/${width}/${theme} fits`)
        assert.equal(await page.locator('.discovery-results-transition').evaluate(element => getComputedStyle(element).transform), 'none', 'Reduced motion keeps the list static')
        await page.screenshot({ path: resolve(reviewDir, `reroll-${state}-${width}-${theme}.png`), fullPage: true })
      }
    }
    await page.setViewportSize({ width: 1440, height: 900 })
  }
  await page.goto(base + '/music')
  await page.getByText('Ajustar preferências', { exact: false }).click()
  await page.getByRole('radiogroup', { name: 'Vocais' }).getByRole('radio', { name: 'Instrumental', exact: true }).click()
  await page.getByRole('radiogroup', { name: 'Energia' }).getByRole('radio', { name: 'Baixa', exact: true }).click()
  await search('Música para manter o foco')
  await heading(1).waitFor()
  await page.getByLabel('Seu pedido', { exact: true }).fill('Rascunho ainda não enviado')
  await page.getByRole('radiogroup', { name: 'Energia' }).getByRole('radio', { name: 'Alta', exact: true }).click()
  held = deferred(); next = rec([1, 2, 2, 3], null)
  // Enter through the real keyboard order after the last radio click. A
  // programmatic focus in pointer modality does not activate :focus-visible.
  for (let step = 0; step < 8 && !await reroll().evaluate(element => element === document.activeElement); step++) {
    await page.keyboard.press('Tab')
  }
  assert.equal(await reroll().evaluate(element => element === document.activeElement), true, 'The renewal control is reachable by keyboard')
  assert.notEqual(await reroll().evaluate(element => getComputedStyle(element).outlineStyle), 'none')
  await reroll().press('Enter')
  await page.getByRole('button', { name: 'Buscando outras músicas…', exact: true }).waitFor()
  assert.equal(await heading(1).count(), 1, 'Keep the old selection during loading')
  assert.deepEqual(requests.at(-1), { query: 'Música para manter o foco', limit: 10, offset: 15, filters: { vocals: 'none', energy: 'low' }, excluded_music_ids: [uuid(1)] })
  await capture('music-loading')
  held.resolve(); held = undefined
  await heading(2).waitFor(); await heading(3).waitFor()
  assert.equal(await heading(1).count(), 0)
  assert.equal(await heading(2).count(), 1, 'Duplicate IDs within a batch are suppressed')
  await capture('music-success')
  failure = true
  await reroll().click()
  await page.getByRole('alert').filter({ hasText: 'Fonte temporariamente indisponível.' }).waitFor()
  assert.equal(await heading(2).count(), 1)
  assert.equal(requests.at(-1).offset, 15, 'null next_offset keeps the last requested source page')
  await capture('music-error')
  failure = false; next = rec([], null, false, true)
  await reroll().click()
  await page.getByRole('alert').filter({ hasText: 'Esta tentativa teve uma limitação e não trouxe novas opções.' }).waitFor()
  assert.equal(await reroll().isDisabled(), false, 'Degraded empty result allows retry even with has_more false')
  assert.equal(await heading(2).count(), 1)
  next = rec([4], 30)
  await reroll().click(); await heading(4).waitFor()
  assert.deepEqual(requests.at(-1).excluded_music_ids, [uuid(1), uuid(2), uuid(3)])

  // Cancel, then start a new request before the old response is released.
  held = deferred(); next = rec([5], 45)
  await reroll().click()
  await page.getByRole('button', { name: 'Cancelar busca de outras músicas', exact: true }).click()
  assert.equal(await heading(4).count(), 1)
  const old = held; held = undefined; next = rec([6], 15)
  await search('Um novo pedido de música')
  await heading(6).waitFor()
  assert.equal(requests.at(-1).excluded_music_ids, undefined, 'A new search clears exclusions')
  old.resolve()
  await page.waitForTimeout(100)
  assert.equal(await heading(5).count(), 0, 'Late response cannot overwrite the new search')
  assert.equal(await heading(6).count(), 1)

  // Return from authentication without losing draft/submitted filters or seen IDs.
  next = rec([7], null)
  await reroll().click(); await heading(7).waitFor()
  await page.getByLabel('Seu pedido', { exact: true }).fill('Rascunho preservado no login')
  await page.getByRole('radiogroup', { name: 'Energia' }).getByRole('radio', { name: 'Baixa', exact: true }).click()
  await page.getByRole('button', { name: 'Salvar nos favoritos: Faixa 7', exact: true }).click()
  await page.getByRole('link', { name: 'Entrar para salvar', exact: true }).click()
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  const beforeLogin = requests.length
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await heading(7).waitFor()
  assert.equal(requests.length, beforeLogin, 'Login restores the current selection without refetch')
  assert.equal(saves.length, 0)
  assert.equal(await page.getByLabel('Seu pedido', { exact: true }).inputValue(), 'Rascunho preservado no login')
  await page.getByText('Ajustar preferências', { exact: false }).click()
  assert.equal(await page.getByRole('radiogroup', { name: 'Energia' }).getByRole('radio', { name: 'Baixa', exact: true }).getAttribute('aria-checked'), 'true', 'Draft filters are restored separately from submitted filters')
  next = rec([8], null)
  await reroll().click(); await heading(8).waitFor()
  assert.deepEqual(requests.at(-1), { query: 'Um novo pedido de música', limit: 10, offset: 15, filters: { vocals: 'none', energy: 'high' }, excluded_music_ids: [uuid(6), uuid(7)] })
  next = rec([], null, false)
  await reroll().click()
  await page.getByRole('status').filter({ hasText: 'Você já viu as sugestões disponíveis para este pedido.' }).waitFor()
  assert.ok(await reroll().isDisabled())
  assert.equal(await heading(8).count(), 1)
  await capture('music-exhausted')

  // An exhausted continuation remains exhausted through a login return.
  expireSession = true
  const bookmark = page.getByRole('button', { name: 'Salvar nos favoritos: Faixa 8', exact: true })
  await page.waitForFunction(() => !document.querySelector('.favorite-button')?.disabled)
  await bookmark.click()
  await page.getByRole('link', { name: 'Entrar na conta', exact: true }).waitFor()
  await bookmark.click()
  await page.getByRole('link', { name: 'Entrar para salvar', exact: true }).click()
  const beforeExhaustedLogin = { requests: requests.length, saves: saves.length }
  expireSession = false
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await heading(8).waitFor()
  assert.ok(await reroll().isDisabled(), 'Authentication cannot reopen an exhausted selection')
  assert.equal(requests.length, beforeExhaustedLogin.requests)
  assert.equal(saves.length, beforeExhaustedLogin.saves, 'Return from session expiry cannot retry a favorite automatically')
  // A new public search resets that state and permits all 200 unique IDs.
  boundaryMode = true
  await search('Outra seleção musical com limite')
  await heading(1).waitFor()
  for (let batch = 0; batch < 19; batch++) {
    const last = 19 + batch * 10
    await reroll().click(); await heading(last).waitFor()
  }
  assert.equal(requests.at(-1).excluded_music_ids.length, 189)
  assert.equal(await reroll().isDisabled(), false, '199 seen IDs still leave one slot')
  await reroll().click(); await heading(200).waitFor()
  assert.equal(requests.at(-1).limit, 1)
  assert.deepEqual(requests.at(-1).excluded_music_ids, Array.from({ length: 199 }, (_, i) => uuid(i + 1)))
  assert.ok(await reroll().isDisabled())
  await page.getByRole('status').filter({ hasText: 'Você chegou ao limite de sugestões desta busca.' }).waitFor()
  // A degraded attempt describes the new failure separately from metadata of
  // the selection we kept. Exercise both flows without real provider/IA calls.
  const limitation = 'Esta tentativa teve uma limitação e não trouxe novas opções. Sua seleção anterior continua aqui. Tente novamente.'
  const variants = [
    { has_more: false, hint: 'Uma fonte teve uma limitação nesta tentativa.' },
    { has_more: true, hint: 'A interpretação por IA teve uma limitação nesta tentativa.' },
    { has_more: false },
    {},
  ]
  for (const kind of ['music', 'books']) {
    for (const [index, variant] of variants.entries()) {
      const isolated = await browser.newContext({ reducedMotion: 'reduce' })
      try {
        const audit = await isolated.newPage()
        audit.setDefaultTimeout(10000)
        audit.on('pageerror', error => errors.push(error.message))
        const calls = [], favoriteWrites = []
        const selected = kind === 'music' ? track(700) : { id: uuid(700), title: 'Livro da seleção anterior', authors: ['Autora de fixture'], provider: 'open_library', cover_url: null }
        const selectionHint = 'Pedido interpretado e sugestões ordenadas por IA. ' + (kind === 'music' ? 'Metadados: MusicBrainz.' : 'Livros encontrados na Open Library.')
        const response = (entry, offset = 15) => ({ recommendation_id: uuid(9700), items: [{ position: 1, item: entry }], meta: { hint: selectionHint, ai_used: true, sources: [kind === 'music' ? 'musicbrainz' : 'open_library'], has_more: true, next_offset: offset, degraded: false } })
        let reply = response(selected)
        await audit.route('**/api/v1/**', route => {
          const request = route.request(), path = new URL(request.url()).pathname.replace('/api/v1', '')
          if (path === '/recommendations/' + kind) { calls.push(request.postDataJSON()); return route.fulfill({ json: reply }) }
          if (path === '/auth/login') return route.fulfill({ json: { access_token: 'fixture-access', refresh_token: 'fixture-refresh', expires_in: 900 } })
          if (path === '/auth/me') return route.fulfill({ json: user })
          if (path === '/users/me/favorites/status') return route.fulfill({ json: { favorites: {} } })
          if (path === '/users/me/favorites' && request.method() === 'POST') favoriteWrites.push(request.postDataJSON())
          throw new Error('Unexpected endpoint in degraded fixture: ' + path)
        })
        await audit.goto(base + '/' + kind)
        if (kind === 'music') {
          await audit.getByText('Ajustar preferências', { exact: false }).click()
          await audit.getByRole('radiogroup', { name: 'Vocais' }).getByRole('radio', { name: 'Instrumental', exact: true }).click()
          await audit.getByRole('radiogroup', { name: 'Energia' }).getByRole('radio', { name: 'Baixa', exact: true }).click()
        }
        const query = 'Pedido enviado antes da tentativa limitada'
        await audit.getByLabel('Seu pedido', { exact: true }).fill(query)
        await audit.getByRole('button', { name: 'Encontrar sugestões', exact: true }).click()
        await audit.getByRole('heading', { name: selected.title, exact: true }).waitFor()
        await audit.getByLabel('Seu pedido', { exact: true }).fill('Rascunho preservado após limitação')
        if (kind === 'music') await audit.getByRole('radiogroup', { name: 'Energia' }).getByRole('radio', { name: 'Alta', exact: true }).click()
        reply = { recommendation_id: uuid(9800), items: [], meta: { degraded: true, ai_used: false, sources: [], next_offset: null, ...variant } }
        const renew = () => audit.getByRole('button', { name: kind === 'music' ? 'Ver outras músicas' : 'Ver outros livros', exact: true })
        await renew().click()
        const alert = audit.locator('.reroll-message [role="alert"]')
        await audit.getByText(limitation, { exact: true }).waitFor()
        assert.equal(await alert.textContent(), limitation)
        assert.equal(await alert.getAttribute('aria-atomic'), 'true')
        assert.equal(await renew().isDisabled(), false, 'All degraded variants allow explicit retry')
        assert.equal(await audit.locator('.result-row').count(), 1)
        assert.equal(await audit.getByRole('heading', { name: selected.title, exact: true }).count(), 1)
        assert.equal(await audit.getByText(selectionHint, { exact: true }).count(), 1, 'Preserved hint still describes the preserved selection')
        if (variant.hint) assert.equal(await audit.getByText(variant.hint, { exact: true }).count(), 0, 'Do not replace the selection hint with the failed attempt metadata')
        const submitted = calls.at(-1)
        assert.equal(submitted.query, query)
        assert.equal(submitted.offset, 15)
        assert.deepEqual(submitted[kind === 'music' ? 'excluded_music_ids' : 'excluded_book_ids'], [selected.id])
        if (kind === 'music') assert.deepEqual(submitted.filters, { vocals: 'none', energy: 'low' })

        if (index === 0) {
          // An error snapshot must survive login without refetch or auto-save.
          await audit.getByRole('button', { name: 'Salvar nos favoritos: ' + selected.title, exact: true }).click()
          await audit.getByRole('link', { name: 'Entrar para salvar', exact: true }).click()
          await audit.getByLabel('E-mail', { exact: true }).fill(user.email)
          await audit.getByLabel('Senha', { exact: true }).fill('test phrase 123')
          const countBeforeLogin = calls.length
          await audit.getByRole('button', { name: 'Entrar', exact: true }).click()
          await audit.getByText(limitation, { exact: true }).waitFor()
          assert.equal(calls.length, countBeforeLogin, 'Login does not rerun the limited attempt')
          assert.deepEqual(favoriteWrites, [], 'Login never auto-saves')
          assert.equal(await renew().isDisabled(), false)
          assert.equal(await audit.getByLabel('Seu pedido', { exact: true }).inputValue(), 'Rascunho preservado após limitação')
          if (kind === 'music') {
            await audit.getByText('Ajustar preferências', { exact: false }).click()
            assert.equal(await audit.getByRole('radiogroup', { name: 'Energia' }).getByRole('radio', { name: 'Alta', exact: true }).getAttribute('aria-checked'), 'true')
          }
          for (const [width, theme, motion] of [[1440, 'dark', 'reduce'], [1440, 'light', 'reduce'], [390, 'dark', 'reduce'], [390, 'light', 'reduce'], [320, 'dark', 'reduce'], [320, 'light', 'reduce'], [320, 'dark', 'no-preference']]) {
            await audit.setViewportSize({ width, height: width === 1440 ? 900 : 844 })
            await audit.emulateMedia({ reducedMotion: motion })
            await audit.evaluate(theme => document.documentElement.setAttribute('data-theme', theme), theme)
            await audit.evaluate(() => document.fonts.ready)
            await audit.waitForFunction(() => document.getAnimations().every(animation => animation.effect?.getComputedTiming().iterations === Infinity || animation.playState === 'finished'))
            await audit.evaluate(() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))))
            assert.ok(await audit.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${kind} limitation fits ${width}/${theme}/${motion}`)
            assert.equal(await alert.textContent(), limitation)
            await audit.locator('.results-section').screenshot({ path: resolve(reviewDir, `reroll-${kind}-limited-${width}-${theme}-${motion}.png`) })
          }
        }
        const fresh = { ...selected, id: uuid(701), title: selected.title + ' nova' }
        reply = response(fresh, 30)
        await renew().click()
        await audit.getByRole('heading', { name: fresh.title, exact: true }).waitFor()
        assert.deepEqual(calls.at(-1), submitted, 'Retry keeps snapshot, exclusions and cursor after degradation/login')
        assert.equal(await audit.locator('.reroll-message [role="alert"]').count(), 0, 'A successful renewal clears the limited-attempt message')
        // Natural exhaustion has a distinct status, not a limitation alert.
        reply = { recommendation_id: uuid(9900), items: [], meta: { degraded: false, has_more: false, next_offset: null } }
        await renew().click()
        await audit.getByRole('status').filter({ hasText: 'Você já viu as sugestões disponíveis para este pedido.' }).waitFor()
        assert.equal(await renew().isDisabled(), true)
        assert.equal(await audit.getByRole('heading', { name: fresh.title, exact: true }).count(), 1)
        assert.equal(await audit.getByText(limitation, { exact: true }).count(), 0)
      } finally { await isolated.close() }
    }
  }
  assert.deepEqual(errors, [])
  console.log('Reroll UI passed: submitted query/filters, deduplication, null offset, retry/degradation, cancel then new search, auth return, 199+1 boundary; MUSIC/BOOK limited-attempt alerts with/without hint/has_more, error snapshots through login, unchanged cursor/IDs/selection metadata; reduced/normal motion and responsive themes. All APIs use fixtures.')
} finally {
  held?.resolve()
  await browser?.close()
  await new Promise(done => server.close(done))
  await vite.close()
}
