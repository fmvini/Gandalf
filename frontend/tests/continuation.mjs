import assert from 'node:assert/strict'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { createServer } from 'vite'

const server = await createServer({ server: { host: '127.0.0.1', port: 0 }, logLevel: 'silent' })
await server.listen()
const base = 'http://127.0.0.1:' + server.httpServer.address().port
const browser = await chromium.launch({ headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' })
page.setDefaultTimeout(10000)
const reviewDir = resolve('..', '.impeccable', 'review')
await mkdir(reviewDir, { recursive: true })
const errors = []
page.on('pageerror', error => errors.push(error.message))
const requests = []
const book = id => ({ id, title: 'Livro ' + id, authors: ['Autora de teste'], description: 'Um universo de fantasia e aventura para explorar.', external_url: 'https://openlibrary.org' })
const response = (id, offset = 15, hasMore = true) => ({ recommendation_id: null, items: id ? [{ position: 1, item: book(id) }] : [], meta: { has_more: hasMore, next_offset: offset } })
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }
let next = response('A')
let failure = false
let held
async function capture(name) {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: width === 1440 ? 900 : 844 })
    for (const theme of ['dark', 'light']) {
      await page.evaluate(theme => document.documentElement.setAttribute('data-theme', theme), theme)
      await page.evaluate(() => document.fonts.ready)
      await page.waitForFunction(() => document.getAnimations().every(animation =>
        animation.effect?.getComputedTiming().iterations === Infinity || animation.playState === 'finished'))
      await page.evaluate(() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))))
      await page.evaluate(() => window.scrollTo(0, 0))
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${name} ${width} ${theme} fits`)
      if (['books-success', 'reading-full'].includes(name) || (width === 1440 && theme === 'dark') || (width === 320 && theme === 'light')) {
        await page.screenshot({ path: resolve(reviewDir, `continuation-${name}-${width}-${theme}.png`), fullPage: true })
      }
    }
  }
  await page.setViewportSize({ width: 1440, height: 900 })
}
const reroll = () => page.getByRole('button', { name: 'Ver outros livros', exact: true })
try {
  await page.route('**/api/v1/recommendations/books', async route => {
    requests.push(route.request().postDataJSON())
    const result = next
    const fail = failure
    const hold = held
    if (hold) await hold.promise
    await route.fulfill(fail ? { status: 503, json: { detail: 'Catálogo temporariamente indisponível.' } } : { json: result }).catch(() => {})
  })
  await page.goto(base + '/books')
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('Fantasia medieval com aventura')
  await page.getByRole('button', { name: 'Encontrar sugestões', exact: true }).click()
  await page.getByRole('heading', { name: 'Livro A', exact: true }).waitFor()
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('Texto editado ainda não enviado')
  await page.keyboard.press('Tab')
  await reroll().focus()
  assert.ok(await reroll().evaluate(element => getComputedStyle(element).outlineStyle !== 'none'), 'Keyboard focus is visible')
  held = deferred()
  next = response('B', 30)
  await reroll().press('Enter')
  await page.getByRole('button', { name: 'Buscando outros livros…', exact: true }).waitFor()
  assert.equal(await page.getByRole('heading', { name: 'Livro A', exact: true }).count(), 1)
  assert.equal(requests.at(-1).query, 'Fantasia medieval com aventura')
  assert.deepEqual(requests.at(-1).excluded_book_ids, ['A'])
  assert.equal(requests.at(-1).offset, 15)
  await capture('books-loading')
  held.resolve(); held = undefined
  await page.getByRole('heading', { name: 'Livro B', exact: true }).waitFor()
  assert.equal(await page.getByRole('heading', { name: 'Livro A', exact: true }).count(), 0)
  await capture('books-success')

  failure = true
  await reroll().click()
  await page.getByText('Catálogo temporariamente indisponível.', { exact: true }).waitFor()
  assert.equal(await page.getByRole('heading', { name: 'Livro B', exact: true }).count(), 1)
  assert.deepEqual(requests.at(-1).excluded_book_ids, ['A', 'B'])
  await capture('books-error')
  failure = false
  next = response('C', 45)
  await reroll().click()
  await page.getByRole('heading', { name: 'Livro C', exact: true }).waitFor()
  assert.equal(requests.at(-1).offset, 30, 'Retry keeps the failed page')

  held = deferred(); next = response('stale', 60)
  await reroll().click()
  await page.getByRole('button', { name: 'Cancelar busca de outros livros' }).click()
  held.resolve(); held = undefined
  await page.waitForTimeout(100)
  assert.equal(await page.getByRole('heading', { name: 'Livro C', exact: true }).count(), 1)
  assert.equal(await page.getByRole('heading', { name: 'Livro stale', exact: true }).count(), 0)
  next = response(null, null, false)
  await reroll().click()
  await page.getByText(/Você já viu as sugestões disponíveis para este pedido/).waitFor()
  assert.ok(await reroll().isDisabled())
  assert.deepEqual(requests.at(-1).excluded_book_ids, ['A', 'B', 'C'])
  await capture('books-exhausted')

  next = response('D')
  await page.getByRole('button', { name: 'Encontrar sugestões', exact: true }).click()
  await page.getByRole('heading', { name: 'Livro D', exact: true }).waitFor()
  assert.equal(requests.at(-1).excluded_book_ids, undefined, 'New request resets previous exclusions')

  await page.route('**/api/v1/books/search?*', route => route.fulfill({ json: { items: [book('Reading')], total: 1 } }))
  let shortfall = false
  await page.route('**/api/v1/recommendations/read-with-music', route => {
    const body = route.request().postDataJSON()
    assert.equal(body.target_duration_min, 90)
    assert.equal(body.context, 'Piano suave para ler')
    if (shortfall) return route.fulfill({ status: 503, json: { error: {
      code: 'SOUNDTRACK_INCOMPLETE', message: 'Não foi possível montar 90 minutos de faixas reais. Tente novamente.', request_id: 'test' }
    } })
    return route.fulfill({ json: {
      recommendation_id: null, items: Array.from({ length: 18 }, (_, i) => ({ position: i + 1, item: { id: 'track-' + i, title: 'Piano de teste ' + (i + 1), artist: 'Artista de teste ' + (i + 1), duration_ms: 300000 } })),
      playlist: { tracks_count: 18, total_duration_ms: 90 * 60000, target_duration_ms: 5400000, target_met: true, shortfall_ms: 0, duration_estimated: false },
    } })
  })
  await page.goto(base + '/read-with-music')
  await page.getByRole('textbox', { name: 'Qual livro você está lendo?' }).fill('Reading')
  await page.getByRole('button', { name: /Livro Reading Autora/ }).click()
  await page.getByLabel('Seu contexto').fill('Piano suave para ler')
  await page.getByLabel('Duração', { exact: true }).selectOption('90')
  await page.getByRole('button', { name: 'Criar minha trilha', exact: true }).click()
  await page.getByText(/Duração das faixas: 90 min · Pedido: 90 min/).waitFor()
  await page.getByLabel('Duração', { exact: true }).selectOption('30')
  await page.getByText(/Pedido: 90 min/).waitFor()
  await capture('reading-full')
  await page.getByLabel('Duração', { exact: true }).selectOption('90')
  shortfall = true
  await page.getByRole('button', { name: 'Criar minha trilha', exact: true }).click()
  await page.getByText('Não foi possível montar 90 minutos de faixas reais. Tente novamente.', { exact: true }).waitFor()
  assert.equal(await page.getByText(/Duração das faixas:/).count(), 0)
  assert.equal(await page.getByRole('heading', { name: 'Piano de teste 1', exact: true }).count(), 0)
  await capture('reading-short')
  assert.deepEqual(errors, [])
  console.log('Continuation UI passed: reroll, retry, cancellation, exhaustion, duration and responsive states.')
} finally {
  held?.resolve()
  await browser.close()
  await server.close()
}
