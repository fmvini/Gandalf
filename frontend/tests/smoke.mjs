import assert from 'node:assert/strict'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium } from 'playwright'
import { createServer } from 'vite'

const server = await createServer({ server: { host: '127.0.0.1', port: 0 }, logLevel: 'silent' })
await server.listen()
const port = server.httpServer.address().port
const base = 'http://127.0.0.1:' + port
const browser = await chromium.launch({ headless: true })
const reviewDir = resolve('..', '.impeccable', 'review')
await mkdir(reviewDir, { recursive: true })
const consoleErrors = []

try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 })
  const page = await context.newPage()
  page.on('pageerror', error => consoleErrors.push(error.message))
  await page.goto(base)
  await page.getByRole('heading', { name: /Encontre o que combina/ }).waitFor()
  await page.evaluate(() => document.fonts.ready)
  await page.waitForFunction(() => getComputedStyle(document.querySelector('.hero-copy h1')).opacity === '1')
  await page.getByRole('button', { name: 'Próximo livro' }).click()
  await page.getByRole('heading', { name: 'O Hobbit', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Próximo livro' }).press('ArrowRight')
  await page.getByRole('heading', { name: 'O Jardim Secreto', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Próximo livro' }).click()
  await page.getByRole('heading', { name: 'Duna', exact: true }).waitFor()
  await page.waitForFunction(() => {
    const cover = document.querySelector('.showcase-cover:not([aria-hidden="true"])')
    return Math.abs(new DOMMatrix(getComputedStyle(cover).transform).m41) < 0.05 && getComputedStyle(cover).opacity === '1'
  })
  assert.ok(await page.locator('.showcase-cover img').evaluateAll(images => images.every(image => image.complete && image.naturalWidth > 0)), 'Local covers load')
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'dark')
  await page.screenshot({ path: resolve(reviewDir, 'desktop.png'), fullPage: true })

  await page.getByRole('button', { name: 'Ativar tema claro' }).click()
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'light')
  await page.screenshot({ path: resolve(reviewDir, 'light.png'), fullPage: true })
  await page.reload()
  assert.equal(await page.locator('html').getAttribute('data-theme'), 'light')
  await page.getByRole('button', { name: 'Ativar tema escuro' }).click()

  await page.route('**/api/v1/recommendations/books', async route => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      recommendation_id: null,
      parsed_query: { genres: ['fantasia'], atmosphere: ['acolhedor'] },
      items: [{ position: 1, item: {
        id: 'book-test', title: 'Livro de teste', authors: ['Autora de teste'],
        description: 'Descrição de teste.', external_url: 'https://example.org/book',
      }, scores: { semantic: 0.9 } }],
    }) })
  })
  await page.getByRole('button', { name: 'Livros', exact: true }).click()
  await page.getByRole('textbox', { name: 'Descreva o que você procura' }).fill('Fantasia acolhedora para ler hoje')
  await page.getByRole('button', { name: 'Explorar pedido' }).click()
  await page.getByRole('heading', { name: 'Livro de teste' }).waitFor()
  await page.screenshot({ path: resolve(reviewDir, 'books-results.png'), fullPage: true })
  assert.match(page.url(), /\/books$/)
  assert.equal(await page.getByText('fantasia', { exact: true }).count(), 1)
  await page.getByText('Por que esta sugestão?').click()
  await page.getByText('Esta sugestão foi selecionada para o pedido acima. A explicação detalhada não está disponível nesta busca.').waitFor()
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('Outro pedido ainda não enviado')
  assert.equal(await page.getByRole('heading', { name: 'Fantasia acolhedora para ler hoje' }).count(), 1)

  await page.unroute('**/api/v1/recommendations/books')
  await page.route('**/api/v1/recommendations/books', async route => {
    await route.fulfill({ json: { recommendation_id: null, items: [
      { position: 1, item: { id: 'local-dune', title: 'Duna', authors: ['Frank Herbert'], provider: 'local' } },
      { position: 2, item: { id: 'external-dune', title: 'Duna', authors: ['Outro autor'], provider: 'openlibrary' } },
    ] } })
  })
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByText('Outro autor', { exact: true }).waitFor()
  assert.equal(await page.locator('.result-row').nth(0).locator('img').getAttribute('src'), '/images/covers/dune.jpg')
  assert.equal(await page.locator('.result-row').nth(1).locator('img').count(), 0, 'An external homonym does not inherit a local cover')

  let musicRequest
  await page.route('**/api/v1/recommendations/music', async route => {
    musicRequest = route.request().postDataJSON()
    await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({
      error: { message: 'Serviço temporariamente indisponível.' },
    }) })
  })
  await page.goto(base + '/music')
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('Músicas calmas para ler')
  await page.getByText('Ajustar preferências').click()
  await page.getByRole('radiogroup', { name: 'Vocais' }).getByRole('radio', { name: 'Com voz', exact: true }).click()
  await page.getByRole('radiogroup', { name: 'Energia' }).getByRole('radio', { name: 'Baixa', exact: true }).click()
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByRole('heading', { name: 'Não foi possível buscar agora.' }).waitFor()
  await page.screenshot({ path: resolve(reviewDir, 'music-error.png'), fullPage: true })
  assert.equal(await page.getByText('Serviço temporariamente indisponível.').count(), 1)
  assert.deepEqual(musicRequest.filters, { vocals: 'required', energy: 'low' })

  await page.unroute('**/api/v1/recommendations/music')
  await page.route('**/api/v1/recommendations/music', async route => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      recommendation_id: null,
      items: [{ position: 1, item: {
        id: 'track-provider', title: 'Faixa da fonte', artist: 'Artista de teste',
        links: { provider: 'https://musicbrainz.org/recording/test' },
      } }],
    }) })
  })
  await page.getByRole('button', { name: /Tentar novamente/ }).click()
  await page.getByRole('heading', { name: 'Faixa da fonte' }).waitFor()
  assert.equal(await page.getByRole('link', { name: 'Ver fonte: Faixa da fonte' }).getAttribute('href'), 'https://musicbrainz.org/recording/test')

  await page.route('**/api/v1/books/search**', async route => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      items: [{ id: 'book-1', title: 'Duna', authors: ['Frank Herbert'] }], total: 1,
    }) })
  })
  await page.route('**/api/v1/recommendations/read-with-music', async route => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
      recommendation_id: null,
      items: [{ position: 1, item: { id: 'track-1', title: 'Faixa de teste', artist: 'Artista de teste', duration_ms: 240000, links: { provider: 'https://musicbrainz.org/recording/test' } } }],
      playlist: { total_duration_ms: 240000, tracks_count: 1 },
    }) })
  })
  await page.goto(base + '/read-with-music')
  await page.getByRole('textbox', { name: 'Qual livro você está lendo?' }).fill('Duna')
  await page.getByRole('button', { name: /Duna Frank Herbert/ }).click()
  await page.getByRole('button', { name: /Criar minha trilha/ }).click()
  await page.getByText('Faixa de teste').waitFor()
  await page.screenshot({ path: resolve(reviewDir, 'reading-results.png'), fullPage: true })
  assert.equal(await page.getByRole('link', { name: 'Ver fonte: Faixa de teste' }).getAttribute('href'), 'https://musicbrainz.org/recording/test')
  await page.getByRole('button', { name: 'Trocar' }).click()
  assert.equal(await page.getByText('Faixa de teste').count(), 0)

  await page.goto(base)
  await page.getByRole('button', { name: 'Próximo livro' }).click()
  await page.getByRole('link', { name: 'Encontrar a trilha deste livro' }).click()
  assert.equal(await page.getByRole('textbox', { name: 'Qual livro você está lendo?' }).inputValue(), 'O Hobbit')

  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true, reducedMotion: 'reduce' })
  const mobilePage = await mobile.newPage()
  mobilePage.on('pageerror', error => consoleErrors.push(error.message))
  await mobilePage.goto(base)
  await mobilePage.getByRole('heading', { name: /Encontre o que combina/ }).waitFor()
  await mobilePage.evaluate(() => document.fonts.ready)
  assert.equal(await mobilePage.locator('.hero-copy h1').evaluate(element => getComputedStyle(element).transform), 'none', 'Reduced motion removes entrance movement')
  await mobilePage.getByRole('button', { name: 'Próximo livro' }).click()
  await mobilePage.getByRole('heading', { name: 'O Hobbit', exact: true }).waitFor()
  await mobilePage.getByRole('button', { name: 'Livro anterior' }).click()
  await mobilePage.getByRole('heading', { name: 'Duna', exact: true }).waitFor()
  await mobilePage.screenshot({ path: resolve(reviewDir, 'mobile.png'), fullPage: true })
  const overflow = await mobilePage.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
  assert.ok(overflow <= 1, 'Mobile has horizontal overflow of ' + overflow + 'px')
  await mobilePage.setViewportSize({ width: 320, height: 740 })
  assert.ok(await mobilePage.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1), '320px layout fits')
  await mobilePage.screenshot({ path: resolve(reviewDir, 'mobile-small.png'), fullPage: true })
  await mobilePage.getByRole('button', { name: 'Abrir menu' }).click()
  await mobilePage.getByRole('link', { name: 'Música', exact: true }).click()
  await mobilePage.getByRole('heading', { name: /Encontre a música certa/ }).waitFor()
  await mobile.close()
  await context.close()
  assert.deepEqual(consoleErrors, [])
  console.log('Smoke test passed: routes, dark/light theme, results, reading playlist, mobile layout.')
} finally {
  await browser.close()
  await server.close()
}
