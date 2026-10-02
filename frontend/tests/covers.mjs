import assert from 'node:assert/strict'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { createServer } from 'vite'

const reviewDir = resolve('..', '.impeccable', 'review')
const runtimeDir = resolve('..', '.impeccable', 'runtime')
await Promise.all([mkdir(reviewDir, { recursive: true }), mkdir(runtimeDir, { recursive: true })])
const server = await createServer({ server: { host: '127.0.0.1', port: 0 }, logLevel: 'silent' })
let browser
const errors = [], evidence = []
// Duna metadata observed in the running API; other provider/error cases are
// explicit fixtures, not evidence that external Open Library images load.
const local = { id: '2e59b23c-8acd-5423-897c-6edddf2c3859', title: 'Duna', authors: ['Frank Herbert'], provider: 'local', cover_url: null }
const books = [local,
  { ...local, id: 'external-null', provider: 'open_library' },
  { ...local, id: 'external-url', title: 'O Hobbit', authors: ['J. R. R. Tolkien'], provider: 'open_library', cover_url: '/images/covers/hobbit.jpg' },
  { ...local, id: 'external-error', provider: 'open_library', cover_url: '/images/covers/test-missing.jpg' },
  { ...local, id: 'external-blank', provider: 'open_library', cover_url: '/images/covers/test-blank.gif' },
]
const user = { id: 'cover-test-user', email: 'covers@example.com', username: 'leitor', created_at: '2026-10-02T12:00:00Z' }
const track = { id: 'test-track', title: 'Gymnopédie No. 1', artist: 'Erik Satie', links: { search: 'https://www.youtube.com/results?search_query=Gymnopedie' } }
const saved = [
  { id: 'favorite-music', type: 'MUSIC', item_id: track.id, item: track },
  ...books.map((book, index) => ({ id: 'favorite-book-' + index, type: 'BOOK', item_id: book.id, item: book })),
]

async function loaded(image, suffix) {
  await image.scrollIntoViewIfNeeded()
  await image.evaluate(async element => {
    await element.decode()
    assertDimensions(element)
    function assertDimensions(image) {
      if (image.naturalWidth <= 1 || image.naturalHeight <= 1) throw new Error('Blank image')
    }
  })
  assert.ok((await image.getAttribute('src')).endsWith(suffix), `Expected cover ${suffix}`)
}

async function capture(page, flow) {
  for (const motion of ['reduce', 'no-preference']) {
    await page.emulateMedia({ reducedMotion: motion })
    for (const width of [1440, 390, 320]) {
      await page.setViewportSize({ width, height: width === 1440 ? 900 : 844 })
      for (const theme of ['dark', 'light']) {
        await page.evaluate(theme => document.documentElement.setAttribute('data-theme', theme), theme)
        await page.evaluate(() => document.fonts.ready)
        await page.waitForFunction(() => [...document.images].every(image => image.complete))
        await page.waitForFunction(() => document.getAnimations().every(animation =>
          animation.effect?.getComputedTiming().iterations === Infinity || animation.playState === 'finished'))
        await page.evaluate(() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))))
        const geometry = await page.evaluate(() => ({ width: innerWidth, scrollWidth: document.documentElement.scrollWidth }))
        assert.ok(geometry.scrollWidth <= width + 1, `${flow} ${width}px ${theme} ${motion} fits`)
        if (flow.startsWith('reading-')) {
          const overlappingLabels = await page.locator('.reading-mode').evaluateAll(buttons => buttons.flatMap(button => {
            const box = button.getBoundingClientRect()
            return [...button.children].flatMap(label => {
              const range = document.createRange()
              range.selectNodeContents(label)
              return [...range.getClientRects()].filter(line => line.left < box.left || line.right > box.right)
                .map(line => ({ label: label.textContent, right: line.right, cardRight: box.right }))
            })
          }))
          assert.deepEqual(overlappingLabels, [], `${flow} labels stay inside their own mode at ${width}px ${theme} ${motion}`)
        }
        evidence.push({ flow, motion, theme, ...geometry })
        await page.screenshot({ path: resolve(reviewDir, `covers-${flow}-${width}-${theme}-${motion}.png`), fullPage: true })
      }
    }
  }
}

try {
  await server.listen()
  const base = 'http://127.0.0.1:' + server.httpServer.address().port
  browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ reducedMotion: 'reduce' })
  page.setDefaultTimeout(10000)
  page.on('pageerror', error => errors.push(error.message))
  await page.addInitScript(() => {
    window.coverEvents = []
    for (const type of ['load', 'error']) document.addEventListener(type, event => {
      const image = event.target
      if (image instanceof HTMLImageElement && /test-(blank|missing)/.test(image.src)) {
        window.coverEvents.push({ type, src: image.src, width: image.naturalWidth, height: image.naturalHeight })
      }
    }, true)
  })
  await page.route('**/images/covers/test-missing.jpg', route => route.fulfill({ status: 404, body: '' }))
  await page.route('**/images/covers/test-blank.gif', route => route.fulfill({ contentType: 'image/gif', body: Buffer.from('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7', 'base64') }))
  await page.route('**/api/v1/**', route => {
    const path = new URL(route.request().url()).pathname.replace('/api/v1', '')
    if (path === '/auth/login') return route.fulfill({ json: { access_token: 'cover-fixture', refresh_token: 'cover-fixture', expires_in: 900 } })
    if (path === '/auth/me') return route.fulfill({ json: user })
    if (path === '/books/search') return route.fulfill({ json: { items: books } })
    if (path === '/recommendations/books') return route.fulfill({ json: { recommendation_id: 'cover-recommendation', items: books.map((item, index) => ({ position: index + 1, item })), meta: { has_more: false, next_offset: null } } })
    if (path === '/users/me/favorites') return route.fulfill({ json: { items: saved, total: saved.length, limit: 10, offset: 0 } })
    if (path === '/users/me/favorites/status') return route.fulfill({ json: { favorites: {} } })
    throw new Error('Unexpected API request: ' + path)
  })

  await page.goto(base)
  for (const cover of ['dune', 'hobbit', 'secret-garden']) await loaded(page.locator(`img[src="/images/covers/${cover}.jpg"]`).first(), `${cover}.jpg`)
  await page.evaluate(() => scrollTo(0, 0))
  await capture(page, 'home')

  await page.evaluate(async () => { window.coverFixture = await import('/tests/fixtures/book-cover.tsx') })
  const fixture = page.locator('#cover-regression-fixture')
  const render = book => page.evaluate(book => window.coverFixture.render(book), book)
  await render(books[3])
  await fixture.locator('.book-cover-fallback').waitFor()
  assert.equal(await fixture.locator('img').count(), 0, 'HTTP error uses a placeholder')
  await render(books[2])
  await loaded(fixture.locator('img'), 'hobbit.jpg')
  await render(books[4])
  await fixture.locator('.book-cover-fallback').waitFor()
  assert.equal(await fixture.locator('img').count(), 0, 'Successful 1x1 response uses a placeholder')
  const fixtureEvents = await page.evaluate(() => window.coverEvents)
  assert.ok(fixtureEvents.some(event => event.src.endsWith('test-missing.jpg') && event.type === 'error'), '404 triggers onError')
  assert.ok(fixtureEvents.some(event => event.src.endsWith('test-blank.gif') && event.type === 'load' && event.width === 1 && event.height === 1), 'Blank HTTP 200 loads at 1x1 and does not rely on onError')
  await render(local)
  await loaded(fixture.locator('img'), 'dune.jpg')
  await render(books[1])
  await fixture.locator('.book-cover-fallback').waitFor()
  assert.equal(await fixture.locator('img').count(), 0, 'External namesake never gets a local cover')
  await page.evaluate(() => window.coverFixture.dispose())

  await page.goto(base + '/books')
  await page.getByLabel('Seu pedido', { exact: true }).fill('Livros para explorar outros mundos')
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  const rows = page.locator('.result-row')
  await rows.nth(4).waitFor()
  await loaded(rows.nth(0).locator('img'), 'dune.jpg')
  await loaded(rows.nth(2).locator('img'), 'hobbit.jpg')
  for (const index of [1, 3, 4]) await rows.nth(index).locator('.book-cover-fallback').waitFor()
  assert.deepEqual(await rows.locator('.result-heading h3').allTextContents(), books.map(book => book.title), 'Cover handling preserves titles')
  await page.evaluate(() => scrollTo(0, 0))
  await capture(page, 'books')

  await page.goto(base + '/read-with-music')
  await page.getByLabel('Qual livro você está lendo?', { exact: true }).fill('Duna')
  const options = page.locator('.book-options li')
  await options.nth(4).waitFor()
  await loaded(options.nth(0).locator('img'), 'dune.jpg')
  await loaded(options.nth(2).locator('img'), 'hobbit.jpg')
  for (const index of [1, 3, 4]) await options.nth(index).locator('.book-cover-fallback').waitFor()
  await page.evaluate(() => scrollTo(0, 0))
  await capture(page, 'reading-picker')
  await options.nth(0).getByRole('button').click()
  await loaded(page.locator('.selected-book img'), 'dune.jpg')
  assert.equal(await page.locator('.selected-book strong').textContent(), local.title)
  assert.equal(await page.locator('.selected-book small').textContent(), local.authors.join(', '))
  await capture(page, 'reading-selected')
  await page.getByRole('button', { name: 'Trocar', exact: true }).click()
  await page.getByLabel('Qual livro você está lendo?', { exact: true }).fill('Duna')
  await options.nth(1).getByRole('button').click()
  await page.locator('.selected-book .book-cover-fallback').waitFor()
  assert.equal(await page.locator('.selected-book img').count(), 0)

  await page.goto(base + '/account/favorites')
  await page.getByLabel('E-mail', { exact: true }).fill(user.email)
  await page.getByLabel('Senha', { exact: true }).fill('test phrase 123')
  await page.getByRole('button', { name: 'Entrar', exact: true }).click()
  await page.locator('.favorite-list .result-row').nth(5).waitFor()
  const favoriteRows = page.locator('.favorite-list .result-row')
  await loaded(favoriteRows.nth(1).locator('img'), 'dune.jpg')
  await loaded(favoriteRows.nth(3).locator('img'), 'hobbit.jpg')
  for (const index of [2, 4, 5]) await favoriteRows.nth(index).locator('.book-cover-fallback').waitFor()
  assert.equal(await page.getByRole('link', { name: 'Buscar no YouTube: ' + track.title }).count(), 1)
  await page.evaluate(() => scrollTo(0, 0))
  await capture(page, 'favorites')

  assert.deepEqual(errors, [], 'No browser runtime errors')
  await writeFile(resolve(runtimeDir, 'covers-ui-matrix.json'), JSON.stringify({ fixtureAPI: true, errors, fixtureEvents, evidence }, null, 2))
  console.log('Book covers passed: HTTP errors, blank 1x1, URL changes on a mounted component, local/provider identity, Home/Books/reading/favorites; 60 theme/viewport/motion captures; no runtime errors. API fixtures are not external online approval.')
} finally {
  await browser?.close()
  await server.close()
}
