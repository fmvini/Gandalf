import assert from 'node:assert/strict'
import { spawn } from 'node:child_process'
import { once } from 'node:events'
import { mkdir, mkdtemp, rm } from 'node:fs/promises'
import { createServer as createTcpServer } from 'node:net'
import { tmpdir } from 'node:os'
import { resolve, sep } from 'node:path'
import { chromium } from 'playwright'
import { createServer } from 'vite'

const reservation = createTcpServer()
await new Promise(resolve => reservation.listen(0, '127.0.0.1', resolve))
const apiPort = reservation.address().port
await new Promise(resolve => reservation.close(resolve))
const temporaryRoot = resolve(tmpdir())
const dataDir = await mkdtemp(resolve(temporaryRoot, 'gandalf-e2e-'))
const apiRoot = resolve('..', 'api')
const python = process.env.GANDALF_PYTHON || resolve(apiRoot, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python')
const api = spawn(python, ['local.py'], {
  cwd: apiRoot,
  env: { ...process.env, GANDALF_PORT: String(apiPort), GANDALF_LOCAL_DATA: dataDir },
  windowsHide: true,
  stdio: ['ignore', 'pipe', 'pipe'],
})
let apiLog = ''
api.stdout.on('data', data => { apiLog += data })
api.stderr.on('data', data => { apiLog += data })
api.on('error', error => { apiLog += error.message })
let browser
let server
try {
  const apiUrl = `http://127.0.0.1:${apiPort}`
  let ready = false
  for (let attempt = 0; attempt < 100; attempt++) {
    if (api.exitCode !== null) throw new Error('API exited: ' + apiLog)
    try {
      ready = (await fetch(apiUrl + '/health/ready', { signal: AbortSignal.timeout(500) })).ok
      if (ready) break
    } catch { /* Startup is still in progress. */ }
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  assert.ok(ready, 'Real API did not become ready: ' + apiLog)
  process.env.VITE_API_BASE_URL = '/api/v1'
  server = await createServer({
    server: { host: '127.0.0.1', port: 0, proxy: { '/api': apiUrl } }, logLevel: 'silent',
  })
  await server.listen()
  const base = 'http://127.0.0.1:' + server.httpServer.address().port
  browser = await chromium.launch({ headless: true })
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  page.setDefaultTimeout(10_000)
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  const reviewDir = resolve('..', '.impeccable', 'review')
  await mkdir(reviewDir, { recursive: true })
  async function reviewVariants(flow) {
    for (const width of [1440, 390, 320]) {
      await page.setViewportSize({ width, height: width === 1440 ? 900 : 844 })
      for (const theme of ['dark', 'light']) {
        await page.evaluate(theme => document.documentElement.setAttribute('data-theme', theme), theme)
        await page.evaluate(() => document.fonts.ready)
        await page.waitForFunction(() => document.getAnimations().every(animation =>
          animation.effect?.getComputedTiming().iterations === Infinity || animation.playState === 'finished'))
        const contrasts = await page.locator('.preference-choice').evaluateAll(elements => {
          const luminance = color => {
            const rgb = color.match(/[\d.]+/g).slice(0, 3).map(value => Number(value) / 255)
            const linear = rgb.map(value => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4)
            return linear[0] * .2126 + linear[1] * .7152 + linear[2] * .0722
          }
          return elements.map(element => {
            const style = getComputedStyle(element)
            const values = [luminance(style.color), luminance(style.backgroundColor)].sort((a, b) => b - a)
            return { label: element.textContent, ratio: (values[0] + .05) / (values[1] + .05) }
          })
        })
        assert.ok(contrasts.every(item => item.ratio >= 4.5), `${theme} preference contrast: ${JSON.stringify(contrasts)}`)
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${flow} ${width}px ${theme} fits`)
        await page.screenshot({ path: resolve(reviewDir, `components-${flow}-${width}-${theme}.png`), fullPage: true })
      }
    }
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark'))
  }
  // The complete public flow must work without any external browser resources.
  await page.route('**/*', route => new URL(route.request().url()).origin === base ? route.continue() : route.abort())
  await page.goto(base + '/music')
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('Músicas calmas para estudar')
  await page.getByText('Ajustar preferências').click()
  await page.getByRole('radiogroup', { name: 'Vocais' }).getByRole('radio', { name: 'Instrumental', exact: true }).click()
  await page.getByRole('radiogroup', { name: 'Energia' }).getByRole('radio', { name: 'Baixa', exact: true }).click()
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByText(/Catálogo local selecionado/).waitFor()
  assert.ok(await page.locator('.result-row').count() > 0)
  await page.getByRole('button', { name: 'Por que esta sugestão?', exact: true }).first().click()
  await page.getByText(/Temas em comum:.*Classificação editorial/).first().waitFor()
  assert.match(await page.getByRole('link', { name: /Buscar no YouTube:/ }).first().getAttribute('href'), /^https:\/\/www.youtube.com\/results/)
  await reviewVariants('music')

  await page.goto(base + '/books')
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('Fantasia com construção de mundo sem romance')
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByRole('heading', { name: 'O Hobbit', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Por que esta sugestão?', exact: true }).first().click()
  await page.getByText(/Temas em comum:/).first().waitFor()
  await reviewVariants('books')
  await page.screenshot({ path: resolve(reviewDir, 'live-books.png'), fullPage: true })
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('xyzabcdefgh')
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByRole('heading', { name: 'Nenhuma boa opção por enquanto.' }).waitFor()

  await page.goto(base + '/read-with-music')
  await page.getByRole('textbox', { name: 'Qual livro você está lendo?' }).fill('Duna')
  await page.getByRole('button', { name: /Duna Frank Herbert/ }).click()
  await page.getByRole('button', { name: /Criar minha trilha/ }).click()
  await page.getByText(/Duração estimada em 5 minutos/).waitFor()
  assert.ok(await page.locator('.playlist-list li').count() > 0)
  assert.ok(await page.getByRole('link', { name: /Buscar no YouTube:/ }).count() > 0)
  await page.getByRole('button', { name: 'Por que esta sugestão?', exact: true }).first().click()
  await page.getByText(/Temas em comum:/).first().waitFor()
  await reviewVariants('reading')
  await page.screenshot({ path: resolve(reviewDir, 'live-reading.png'), fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 })
  await page.screenshot({ path: resolve(reviewDir, 'live-reading-mobile.png'), fullPage: true })
  assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1))
  await page.getByRole('button', { name: 'Trocar' }).click()
  assert.equal(await page.locator('.playlist-list li').count(), 0)
  assert.deepEqual(errors, [])
  console.log('Live E2E passed: real API, SQLite, offline books/music/reading, filters, explanations, empty state and mobile.')
} finally {
  await browser?.close()
  await server?.close()
  if (api.exitCode === null) {
    const closed = once(api, 'close')
    api.kill()
    await closed
  }
  assert.ok(dataDir.startsWith(temporaryRoot + sep) && dataDir.split(sep).at(-1).startsWith('gandalf-e2e-'))
  await rm(dataDir, { recursive: true, force: true })
}
