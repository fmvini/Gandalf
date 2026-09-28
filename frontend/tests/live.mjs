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
  // The complete public flow must work without any external browser resources.
  await page.route('**/*', route => new URL(route.request().url()).origin === base ? route.continue() : route.abort())
  await page.goto(base + '/music')
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('Músicas calmas para estudar')
  await page.getByText('Ajustar preferências').click()
  await page.getByRole('combobox', { name: 'Vocais' }).selectOption('none')
  await page.getByRole('combobox', { name: 'Energia' }).selectOption('low')
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByText(/Catálogo local selecionado/).waitFor()
  assert.ok(await page.locator('.result-row').count() > 0)
  await page.locator('.why summary').first().click()
  await page.getByText(/Temas em comum:.*Classificação editorial/).first().waitFor()
  assert.match(await page.getByRole('link', { name: /Buscar no YouTube:/ }).first().getAttribute('href'), /^https:\/\/www.youtube.com\/results/)

  await page.goto(base + '/books')
  await page.getByRole('textbox', { name: 'Seu pedido' }).fill('Fantasia com construção de mundo sem romance')
  await page.getByRole('button', { name: /Encontrar sugestões/ }).click()
  await page.getByRole('heading', { name: 'O Hobbit', exact: true }).waitFor()
  const reviewDir = resolve('..', '.impeccable', 'review')
  await mkdir(reviewDir, { recursive: true })
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
