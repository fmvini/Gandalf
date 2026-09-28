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
  await page.getByRole('combobox', { name: 'Vocais' }).selectOption('required')
  await page.getByRole('combobox', { name: 'Energia' }).selectOption('low')
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

  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true })
  const mobilePage = await mobile.newPage()
  mobilePage.on('pageerror', error => consoleErrors.push(error.message))
  await mobilePage.goto(base)
  await mobilePage.getByRole('heading', { name: /Encontre o que combina/ }).waitFor()
  await mobilePage.evaluate(() => document.fonts.ready)
  await mobilePage.screenshot({ path: resolve(reviewDir, 'mobile.png'), fullPage: true })
  const overflow = await mobilePage.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
  assert.ok(overflow <= 1, 'Mobile has horizontal overflow of ' + overflow + 'px')
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
