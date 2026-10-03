import assert from 'node:assert/strict'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { createServer as createHttpServer } from 'node:http'
import { chromium } from 'playwright'
import { createServer } from 'vite'

const vite = await createServer({ server: { middlewareMode: true, hmr: false }, logLevel: 'silent' })
const server = createHttpServer(vite.middlewares)
await new Promise(done => server.listen(0, '127.0.0.1', done))
const port = server.address().port
const base = 'http://127.0.0.1:' + port
assert.ok(port > 0 && port !== 5173, 'Preserve the existing frontend with an actual ephemeral port')
console.log('Music metadata fixture port: ' + port)
const reviewDir = resolve('..', '.impeccable', 'review')
await mkdir(reviewDir, { recursive: true })
const fixtures = [
  { title: 'IA instrumental', fields: { provider: 'musicbrainz', classification_source: 'ai_estimate', has_vocals: false, energy: 'low' }, label: 'MusicBrainz · Estimativa por IA · Instrumental · Energia baixa' },
  { title: 'Origem sem IA', fields: { provider: 'musicbrainz', has_vocals: true, energy: 'high' }, label: 'MusicBrainz · Com voz · Energia alta' },
  { title: 'Tag instrumental', fields: { provider: 'musicbrainz', classification_source: 'provider_tags', has_vocals: false, energy: null }, label: 'MusicBrainz · Tags da fonte · Instrumental · Energia não informada' },
  { title: 'IA inconclusiva', fields: { provider: 'musicbrainz', classification_source: 'ai_estimate', has_vocals: null, energy: null }, label: 'MusicBrainz · Estimativa por IA · Vocais não informados · Energia não informada' },
  { title: 'Campos nulos', fields: { provider: 'musicbrainz', has_vocals: null, energy: null, classification_source: null }, label: 'MusicBrainz · Vocais não informados · Energia não informada' },
  { title: 'Campos ausentes', fields: { tags: ['instrumental', 'energia alta'] }, label: 'Vocais não informados · Energia não informada' },
  { title: 'Catálogo local', fields: { provider: 'local', has_vocals: true, energy: 'medium' }, label: 'Catálogo local · Com voz · Energia média' },
  { title: 'Local sem origem', fields: { has_vocals: false, energy: 'low' }, label: 'Instrumental · Energia baixa' },
  { title: 'IA sem origem', fields: { classification_source: 'ai_estimate', has_vocals: null, energy: 'medium' }, label: 'Estimativa por IA · Vocais não informados · Energia média' },
  { title: 'Outra fonte', fields: { provider: 'fonte-de-fixture', classification_source: 'desconhecida', has_vocals: true }, label: 'Fonte: fonte-de-fixture · Com voz · Energia não informada' },
  { title: 'Alternativa conhecida', fields: { provider: 'fonte-alternativa', has_vocals: false, energy: 'high', links: { provider: 'https://catalog.example.test/track/known', search: 'https://search.example.test/?q=known' } }, label: 'Fonte: fonte-alternativa · Instrumental · Energia alta', destination: { href: 'https://catalog.example.test/track/known', label: 'Ver fonte' } },
  { title: 'Alternativa por tags', fields: { provider: 'fonte-alternativa', classification_source: 'provider_tags', has_vocals: null, energy: 'low', links: { search: 'https://search.example.test/?q=track' } }, label: 'Fonte: fonte-alternativa · Tags da fonte · Vocais não informados · Energia baixa', destination: { href: 'https://search.example.test/?q=track', label: 'Buscar faixa' } },
  { title: 'Alternativa estimada', fields: { provider: 'fonte-alternativa', classification_source: 'ai_estimate', has_vocals: true, energy: 'medium', links: { search: 'https://www.youtube.com/results?search_query=track' } }, label: 'Fonte: fonte-alternativa · Estimativa por IA · Com voz · Energia média', destination: { href: 'https://www.youtube.com/results?search_query=track', label: 'Buscar no YouTube' } },
  { title: 'Alternativa desconhecida', fields: { provider: 'fonte-alternativa', classification_source: 'unknown', has_vocals: null, energy: null, duration_ms: null, links: { search: 'https://www.youtube.com.search.example.test/?q=track' } }, label: 'Fonte: fonte-alternativa · Vocais não informados · Energia não informada', destination: { href: 'https://www.youtube.com.search.example.test/?q=track', label: 'Buscar faixa' } },
]
const items = fixtures.map((fixture, index) => ({ position: index + 1, item: { id: `00000000-0000-4000-8000-${String(index + 1).padStart(12, '0')}`, title: fixture.title, artist: 'Artista de fixture', duration_ms: 180000, ...fixture.fields } }))
// Discovery caps each response at ten items. Keep all fourteen assertions using
// two independent searches; put alternate links in the first batch for pre-fix proof.
const batches = [[...fixtures.slice(10), ...fixtures.slice(0, 6)], fixtures.slice(6, 10)].map((batch, index) => ({
  query: 'Música para explorar classificações de fixture — lote ' + (index + 1),
  fixtures: batch, items: batch.map((fixture, position) => ({ ...items[fixtures.indexOf(fixture)], position: position + 1 })),
}))
assert.equal(batches.flatMap(batch => batch.fixtures).length, 14, 'Keep all fourteen fixtures')
assert.ok(batches.every(batch => batch.items.length <= 10), 'Respect the production request limit')
const requests = [], responses = [], errors = [], metrics = [], blocked = [], destinations = [], observed = [], failed = []
let browser, page, activeBatch = 0
const luminance = color => {
  const [r, g, b] = color.match(/[\d.]+/g).slice(0, 3).map(value => {
    const channel = Number(value) / 255
    return channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4
  })
  return r * .2126 + g * .7152 + b * .0722
}
try {
  browser = await chromium.launch({ headless: true })
  page = await browser.newPage({ reducedMotion: 'reduce' })
  page.setDefaultTimeout(10000)
  page.on('pageerror', error => errors.push(error.message))
  page.on('requestfailed', request => {
    const url = new URL(request.url())
    failed.push({ origin: url.origin, path: url.pathname, type: request.resourceType(), error: request.failure()?.errorText })
  })
  await page.route('**/*', route => {
    if (new URL(route.request().url()).origin === base) return route.continue()
    blocked.push(new URL(route.request().url()).origin)
    return route.abort()
  })
  await page.route('**/api/v1/**', route => {
    assert.equal(new URL(route.request().url()).pathname, '/api/v1/recommendations/music', 'No real or incidental API request')
    const batch = batches[activeBatch], body = route.request().postDataJSON()
    assert.equal(requests.length, activeBatch, 'Exactly one request per independent fixture search')
    assert.deepEqual(body, { query: batch.query, filters: {}, limit: 10 })
    requests.push(body)
    responses.push({ batch: activeBatch + 1, count: batch.items.length })
    return route.fulfill({ json: { recommendation_id: '00000000-0000-4000-8000-' + String(9999 + activeBatch).padStart(12, '0'), items: batch.items, meta: {
      ai_used: true, sources: ['local', 'musicbrainz', 'fonte-de-fixture', 'fonte-alternativa'], has_more: false,
      hint: 'Lote simulado com metadados de fontes distintas; classificações informadas por faixa.',
    } } })
  })
  await page.goto(base + '/music')
  for (const [batchIndex, batch] of batches.entries()) {
    activeBatch = batchIndex
    await page.getByLabel('Seu pedido', { exact: true }).fill(batch.query)
    await page.getByRole('button', { name: 'Encontrar sugestões', exact: true }).click()
    const rows = page.locator('.result-row')
    await rows.nth(batch.fixtures.length - 1).waitFor()
    assert.equal(await rows.count(), batch.fixtures.length, 'Every item of the current batch is rendered')
    assert.deepEqual(await rows.locator('.result-heading > h3').allTextContents(), batch.fixtures.map(fixture => fixture.title), 'New query replaces the prior selection with its own snapshot')
    assert.deepEqual(await page.locator('.music-metadata').allTextContents(), batch.fixtures.map(fixture => fixture.label))
    for (const [index, fixture] of batch.fixtures.entries()) {
      const row = rows.nth(index), label = row.locator('.music-metadata')
      assert.equal(await label.count(), 1, 'Exactly one metadata paragraph per track')
      assert.equal(await label.isVisible(), true)
      assert.equal(await label.evaluate(element => !!element.closest('[aria-hidden="true"], [hidden]')), false)
      assert.ok((await row.ariaSnapshot()).includes(fixture.label), 'The visible metadata is also accessible text')
      assert.equal(await row.locator('.result-heading > span').textContent(), fixture.fields.duration_ms === null ? '' : '3:00', 'Unknown duration stays blank; known duration formatting is preserved')
      if (fixture.destination) {
        const link = row.locator('.result-link')
        assert.equal(await link.getAttribute('href'), fixture.destination.href, 'Preserve destination URL and link precedence')
        const actual = (await link.textContent()).trim()
        console.log(`Fixture destination ${fixture.title}: ${actual}`)
        assert.equal(actual, fixture.destination.label, `Accurate search/source label for ${fixture.title}`)
        assert.equal(await link.getAttribute('aria-label'), fixture.destination.label + ': ' + fixture.title)
        assert.equal(await link.getAttribute('target'), '_blank')
        assert.equal(await link.getAttribute('rel'), 'noopener noreferrer')
        destinations.push({ title: fixture.title, ...fixture.destination })
      }
      observed.push({ title: fixture.title, label: await label.textContent() })
    }

    const variants = [1440, 390, 320].flatMap(width => ['dark', 'light'].map(theme => ({ width, theme, motion: 'reduce' })))
    variants.push({ width: 320, theme: 'dark', motion: 'no-preference' }, { width: 320, theme: 'light', motion: 'no-preference' })
    for (const { width, theme, motion } of variants) {
      await page.setViewportSize({ width, height: width === 1440 ? 900 : 844 })
      await page.emulateMedia({ reducedMotion: motion })
      await page.evaluate(theme => document.documentElement.setAttribute('data-theme', theme), theme)
      await page.evaluate(() => document.fonts.ready)
      await page.waitForFunction(() => document.getAnimations().every(animation => animation.effect?.getComputedTiming().iterations === Infinity || animation.playState === 'finished'))
      await page.evaluate(() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done))))
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `Page fits ${width}/${theme}/${motion}`)
      const layout = await page.locator('.music-metadata').evaluateAll(labels => labels.map(label => {
        const box = label.parentElement.getBoundingClientRect(), range = document.createRange()
        range.selectNodeContents(label)
        const style = getComputedStyle(label)
        return { text: label.textContent, overflow: [...range.getClientRects()].some(line => line.left < box.left - 1 || line.right > box.right + 1), fontSize: parseFloat(style.fontSize), color: style.color, background: getComputedStyle(document.body).backgroundColor }
      }))
      assert.ok(layout.every(label => !label.overflow), 'Each line stays inside its own track column')
      for (const label of layout) {
        assert.ok(label.fontSize >= 14, 'Keep the existing readable font size')
        const a = luminance(label.color), b = luminance(label.background)
        const contrast = (Math.max(a, b) + .05) / (Math.min(a, b) + .05)
        assert.ok(contrast >= 4.5, 'Existing tokens keep metadata text contrast >=4.5:1')
        metrics.push({ batch: batchIndex + 1, width, theme, motion, text: label.text, fontSize: label.fontSize, contrast })
      }
      await page.locator('.results-section').screenshot({ path: resolve(reviewDir, `music-metadata-batch-${batchIndex + 1}-${width}-${theme}-${motion}.png`) })
    }
  }
  assert.equal(observed.length, 14, 'All fourteen fixture rows were checked across both searches')
  assert.deepEqual(observed, batches.flatMap(batch => batch.fixtures.map(fixture => ({ title: fixture.title, label: fixture.label }))))
  // These facts cannot be inferred from tags, aggregate sources or ai_used.
  for (const index of [5, 7, 1]) assert.equal(observed.find(row => row.title === fixtures[index].title).label, fixtures[index].label)
  assert.equal(requests.length, 2, 'Exactly two mocked searches, no extra recommendations')
  assert.equal(new Set(requests.map(body => body.query)).size, 2, 'Independent queries do not reuse a snapshot')
  assert.deepEqual(errors, [])
  assert.deepEqual(blocked, [], 'All API requests are mocked; no external source/LLM/link is visited')
  assert.deepEqual(failed, [], 'No asset or API request failure')
  await writeFile(resolve(reviewDir, 'music-metadata-evidence.json'), JSON.stringify({ fixtureOnly: true, port, errors, requests, responses, blocked, failed, observed, destinations, metrics }, null, 2))
  console.log('Music metadata UI passed: 14 fixtures in two independent searches, alternate provider known/tags/AI/unknown, accurate source/search links, no source/classification inference, accessible text/contrast and paragraph overflow; 16 focused captures. All API data is mocked.')
} catch (error) {
  const diagnostics = { fixtureOnly: true, port, batch: activeBatch + 1, expectedCount: batches[activeBatch].fixtures.length,
    requests, responses, blocked, failed, errors,
    rows: page ? await page.locator('.result-row').count().catch(() => null) : null,
    statusText: page ? await page.locator('.status-panel').allTextContents().catch(() => []) : [],
  }
  console.error('Fixture-only diagnostics (no headers or credentials):', JSON.stringify(diagnostics))
  await writeFile(resolve(reviewDir, 'music-metadata-failure.json'), JSON.stringify(diagnostics, null, 2))
  throw error
} finally {
  await browser?.close()
  await new Promise(done => server.close(done))
  await vite.close()
}
