import assert from 'node:assert/strict'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { createServer } from 'vite'

const server = await createServer({ server: { host: '127.0.0.1', port: 0 }, logLevel: 'silent' })
await server.listen()
const base = 'http://127.0.0.1:' + server.httpServer.address().port
const browser = await chromium.launch({ headless: true })
const context = await browser.newContext({ reducedMotion: 'reduce' })
const page = await context.newPage()
page.setDefaultTimeout(10_000)
page.setDefaultNavigationTimeout(30_000)
const errors = []
const reviewDir = resolve('..', '.impeccable', 'review')
await mkdir(reviewDir, { recursive: true })
page.on('pageerror', error => errors.push(error.message))
const recommendation = id => ({ recommendation_id: id, items: [{ position: 1, item: {
  id: 'same-item', title: 'Sugestão atual', artist: 'Artista', authors: ['Autora'],
} }] })
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }
const search = async text => {
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill(text)
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
}
const explanation = () => page.getByRole('button', { name: 'Por que esta sugestão?', exact: true }).first()
let requests = []
let nextId = 'first'
let heldSearch
let heldExplanation
let explanationCalls = []
let failExplanation = false
async function reviewLoading(kind) {
  for (const [width, theme] of [[1440, 'dark'], [320, 'light']]) {
    await page.setViewportSize({ width, height: 900 })
    await page.evaluate(theme => document.documentElement.setAttribute('data-theme', theme), theme)
    await page.waitForFunction(() => document.documentElement.scrollWidth <= innerWidth + 1)
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${kind} loading fits ${width}px`)
    await page.locator('.results-section').screenshot({ path: resolve(reviewDir, `components-loading-${kind}-${width}-${theme}.png`) })
  }
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark'))
}

try {
  await page.route('**/api/v1/recommendations/music', async route => {
    requests.push(route.request().postDataJSON())
    const id = nextId
    const hold = heldSearch
    if (hold) await hold.promise
    await route.fulfill({ json: recommendation(id) }).catch(() => {})
  })
  await page.route('**/api/v1/recommendations/*/items/*/explanation', async route => {
    const id = route.request().url().split('/recommendations/')[1].split('/')[0]
    explanationCalls.push(id)
    const hold = heldExplanation
    if (hold) await hold.promise
    await route.fulfill(failExplanation
      ? { status: 503, json: { detail: 'Indisponível' } }
      : { json: { text: 'Explicação de ' + id } }).catch(() => {})
  })
  await page.goto(base + '/music')
  const filters = page.getByRole('button', { name: /Ajustar preferências/ })
  await filters.focus()
  await filters.press('Enter')
  assert.equal(await filters.getAttribute('aria-expanded'), 'true')
  const vocals = page.getByRole('radiogroup', { name: 'Vocais', exact: true })
  const energy = page.getByRole('radiogroup', { name: 'Energia', exact: true })
  const any = vocals.getByRole('radio', { name: 'Tanto faz', exact: true })
  await any.focus()
  await any.press('ArrowRight')
  await page.waitForFunction(() => document.activeElement?.textContent === 'Instrumental')
  await vocals.getByRole('radio', { name: 'Instrumental', exact: true }).press('Space')
  await page.waitForFunction(() => document.querySelector('[aria-label="Vocais"] [aria-checked="true"]')?.textContent === 'Instrumental')
  assert.equal(await vocals.getByRole('radio', { name: 'Instrumental', exact: true }).getAttribute('aria-checked'), 'true')
  await vocals.getByRole('radio', { name: 'Instrumental', exact: true }).click()
  assert.equal(await vocals.getByRole('radio', { checked: true }).count(), 1, 'A preference cannot be deselected')
  await energy.getByRole('radio', { name: 'Baixa', exact: true }).click()
  await search('Pedido inicial')
  await page.getByRole('heading', { name: 'Sugestão atual', exact: true }).waitFor()
  assert.deepEqual(requests.at(-1).filters, { vocals: 'none', energy: 'low' })
  assert.deepEqual(explanationCalls, [], 'Explanations load only when opened')
  await vocals.getByRole('radio', { name: 'Com voz', exact: true }).click()
  await energy.getByRole('radio', { name: 'Alta', exact: true }).click()
  await page.getByText('Preferências alteradas. Busque novamente para aplicá-las.').waitFor()
  const submitted = page.getByLabel('Preferências usadas nesta busca')
  assert.match(await submitted.textContent(), /Instrumental.*Energia baixa/)
  await explanation().press('Enter')
  await page.getByText('Explicação de first', { exact: true }).waitFor()
  await explanation().click()
  await explanation().click()
  assert.deepEqual(explanationCalls, ['first'], 'Reopening uses the loaded explanation')

  nextId = 'second'
  await search('Pedido com novos filtros')
  await page.getByRole('heading', { name: 'Sugestão atual', exact: true }).waitFor()
  assert.deepEqual(requests.at(-1).filters, { vocals: 'required', energy: 'high' })
  assert.equal(await explanation().getAttribute('aria-expanded'), 'false')
  failExplanation = true
  await explanation().click()
  await page.getByRole('button', { name: 'Tentar explicação novamente', exact: true }).waitFor()
  await explanation().click()
  await explanation().click()
  assert.deepEqual(explanationCalls, ['first', 'second'], 'An error requires explicit retry')
  failExplanation = false
  await page.getByRole('button', { name: 'Tentar explicação novamente', exact: true }).click()
  await page.getByText('Explicação de second', { exact: true }).waitFor()
  await page.getByRole('button', { name: 'Limpar preferências', exact: true }).click()
  assert.equal(await vocals.getByRole('radio', { name: 'Tanto faz', exact: true }).getAttribute('aria-checked'), 'true')
  assert.equal(await energy.getByRole('radio', { name: 'Tanto faz', exact: true }).getAttribute('aria-checked'), 'true')
  await energy.getByRole('radio', { name: 'Média', exact: true }).click()
  nextId = 'medium'
  await search('Pedido com energia média')
  await page.getByRole('heading', { name: 'Sugestão atual', exact: true }).waitFor()
  assert.deepEqual(requests.at(-1).filters, { energy: 'medium' })
  await page.getByRole('button', { name: 'Limpar preferências', exact: true }).click()
  nextId = 'third'
  await search('Pedido indiferente')
  await page.getByRole('heading', { name: 'Sugestão atual', exact: true }).waitFor()
  assert.deepEqual(requests.at(-1).filters, {})
  assert.equal(await submitted.count(), 0)
  heldExplanation = deferred()
  await explanation().click()
  await page.getByText('Buscando explicação…', { exact: true }).waitFor()
  nextId = 'fourth'
  await search('Outra recomendação')
  await page.getByRole('heading', { name: 'Sugestão atual', exact: true }).waitFor()
  heldExplanation.resolve()
  heldExplanation = null
  await explanation().click()
  await page.getByText('Explicação de fourth', { exact: true }).waitFor()
  assert.equal(await page.getByText('Explicação de third', { exact: true }).count(), 0)

  heldSearch = deferred()
  nextId = 'cancelled'
  await search('Busca que será cancelada')
  await page.locator('.result-skeletons.music').waitFor()
  assert.equal(await page.locator('.result-skeletons').getAttribute('aria-hidden'), 'true')
  assert.equal(await page.locator('.skeleton').first().evaluate(element => getComputedStyle(element).animationName), 'none')
  await reviewLoading('music')
  await page.getByRole('button', { name: 'Cancelar busca', exact: true }).click()
  const cancelled = heldSearch
  heldSearch = null
  nextId = 'after-cancel'
  await search('Busca válida após cancelar')
  await page.getByRole('heading', { name: 'Sugestão atual', exact: true }).waitFor()
  cancelled.resolve()
  await explanation().click()
  await page.getByText('Explicação de after-cancel', { exact: true }).waitFor()
  assert.equal(await page.locator('.result-skeletons').count(), 0)

  const booksHold = deferred()
  await page.route('**/api/v1/recommendations/books', async route => {
    await booksHold.promise
    await route.fulfill({ json: recommendation('book') }).catch(() => {})
  })
  await page.goto(base + '/books')
  await search('Livro calmo')
  await page.locator('.result-skeletons.books').waitFor()
  await reviewLoading('books')
  booksHold.resolve()
  await page.getByRole('heading', { name: 'Sugestão atual', exact: true }).waitFor()
  await explanation().click()
  await page.getByText('Explicação de book', { exact: true }).waitFor()

  await page.route('**/api/v1/books/search**', route => route.fulfill({ json: { items: [{ id: 'book', title: 'Duna', authors: ['Frank Herbert'] }] } }))
  let playlistHold = deferred()
  await page.route('**/api/v1/recommendations/read-with-music', async route => {
    const hold = playlistHold
    if (hold) await hold.promise
    await route.fulfill({ json: recommendation('reading') }).catch(() => {})
  })
  await page.goto(base + '/read-with-music')
  const chooseBook = async () => {
    await page.getByRole('textbox', { name: 'Qual livro você está lendo?' }).fill('Duna')
    await page.getByRole('button', { name: /Duna Frank Herbert/ }).click()
  }
  await chooseBook()
  await page.getByRole('button', { name: /Criar minha trilha/ }).click()
  await page.locator('.result-skeletons.playlist').waitFor()
  await reviewLoading('playlist')
  await page.getByRole('button', { name: 'Cancelar', exact: true }).click()
  playlistHold.resolve()
  playlistHold = deferred()
  await page.getByRole('button', { name: /Criar minha trilha/ }).click()
  await page.locator('.result-skeletons.playlist').waitFor()
  await page.getByRole('button', { name: 'Trocar', exact: true }).click()
  playlistHold.resolve()
  playlistHold = null
  assert.equal(await page.locator('.playlist-list li').count(), 0)
  assert.equal(await page.locator('.result-skeletons').count(), 0)
  await chooseBook()
  await page.getByRole('button', { name: /Criar minha trilha/ }).click()
  await page.locator('.playlist-list li').waitFor()
  await explanation().click()
  await page.getByText('Explicação de reading', { exact: true }).waitFor()
  assert.deepEqual(errors, [])
  console.log('Component integration passed: keyboard, filter snapshots/contracts, lazy/cache/retry, cancellation, stale requests and reading explanations.')
} finally {
  heldSearch?.resolve()
  heldExplanation?.resolve()
  await browser.close()
  await server.close()
}
