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
]
const items = fixtures.map((fixture, index) => ({ position: index + 1, item: { id: `00000000-0000-4000-8000-${String(index + 1).padStart(12, '0')}`, title: fixture.title, artist: 'Artista de fixture', duration_ms: 180000, ...fixture.fields } }))
const requests = [], errors = [], metrics = []
let browser
const luminance = color => {
  const [r, g, b] = color.match(/[\d.]+/g).slice(0, 3).map(value => {
    const channel = Number(value) / 255
    return channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4
  })
  return r * .2126 + g * .7152 + b * .0722
}
try {
  browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ reducedMotion: 'reduce' })
  page.setDefaultTimeout(10000)
  page.on('pageerror', error => errors.push(error.message))
  await page.route('**/api/v1/**', route => {
    assert.equal(new URL(route.request().url()).pathname, '/api/v1/recommendations/music', 'No real or incidental API request')
    requests.push(route.request().postDataJSON())
    return route.fulfill({ json: { recommendation_id: '00000000-0000-4000-8000-000000009999', items, meta: {
      ai_used: true, sources: ['local', 'musicbrainz'], has_more: false,
      hint: 'Pedido interpretado e sugestões ordenadas por IA. Metadados: MusicBrainz. Inclui seleção do catálogo local.',
    } } })
  })
  await page.goto('http://127.0.0.1:' + port + '/music')
  await page.getByLabel('Seu pedido', { exact: true }).fill('Música para explorar classificações de fixture')
  await page.getByRole('button', { name: 'Encontrar sugestões', exact: true }).click()
  const rows = page.locator('.result-row')
  await rows.nth(9).waitFor()
  assert.equal(await rows.count(), fixtures.length)
  assert.deepEqual(await page.locator('.music-metadata').allTextContents(), fixtures.map(fixture => fixture.label))
  for (const [index, fixture] of fixtures.entries()) {
    const row = rows.nth(index), label = row.locator('.music-metadata')
    assert.equal(await label.count(), 1, 'Exactly one metadata paragraph per track')
    assert.equal(await label.isVisible(), true)
    assert.equal(await label.evaluate(element => !!element.closest('[aria-hidden="true"], [hidden]')), false)
    assert.ok((await row.ariaSnapshot()).includes(fixture.label), 'The visible metadata is also accessible text')
  }
  // These facts cannot be inferred from tags, aggregate sources or ai_used.
  assert.equal(await rows.nth(5).locator('.music-metadata').textContent(), fixtures[5].label)
  assert.equal(await rows.nth(7).locator('.music-metadata').textContent(), fixtures[7].label)
  assert.equal(await rows.nth(1).locator('.music-metadata').textContent(), fixtures[1].label)

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
      metrics.push({ width, theme, motion, text: label.text, fontSize: label.fontSize, contrast })
    }
    await page.locator('.results-section').screenshot({ path: resolve(reviewDir, `music-metadata-${width}-${theme}-${motion}.png`) })
  }
  assert.equal(requests.length, 1, 'Only one mocked discovery request, no extra recommendations')
  assert.deepEqual(errors, [])
  await writeFile(resolve(reviewDir, 'music-metadata-evidence.json'), JSON.stringify({ fixtureOnly: true, port, errors, requests, metrics }, null, 2))
  console.log('Music metadata UI passed: known/AI estimate/provider tags/null/absent fields, no inference from source absence/tags/aggregate IA, local vs MusicBrainz, accessible text/contrast and paragraph overflow; 8 focused captures. All API data is mocked.')
} finally {
  await browser?.close()
  await new Promise(done => server.close(done))
  await vite.close()
}
