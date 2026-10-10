import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { Script, createContext } from 'node:vm'
import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter } from 'react-router-dom'
import ts from 'typescript'

const localRequire = createRequire(import.meta.url)
const sources = new Map()
for (const name of ['App', 'pages/Legal', 'lib/legal']) {
  const extension = name === 'lib/legal' ? 'ts' : 'tsx'
  const source = await readFile(new URL('../src/' + name + '.' + extension, import.meta.url), 'utf8')
  sources.set(name, ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
  } }).outputText)
}

function fixture(blocked = false, hooks = false) {
  const effects = []
  const document = { title: 'Gandalf', documentElement: { dataset: {} } }
  const window = { scrollTo() {} }
  const localStorage = {
    getItem() { if (blocked) throw new Error('Storage blocked'); return 'light' },
    setItem() { if (blocked) throw new Error('Storage blocked') },
  }
  const modules = new Map()
  function load(name) {
    if (modules.has(name)) return modules.get(name)
    const exports = {}
    const context = createContext({ exports, document, window, localStorage, require: specifier => {
      if (specifier === '../lib/legal' || specifier === './lib/legal') return load('lib/legal')
      if (specifier === './pages/Legal') return load('pages/Legal')
      if (specifier === './lib/useSession') return { useSession: () => ({ user: null }) }
      if (specifier.startsWith('./pages/')) return { default: () => React.createElement('p', null, 'Public page fixture') }
      if (hooks && specifier === 'react') return { ...React,
        useState: initial => [typeof initial === 'function' ? initial() : initial, () => {}],
        useEffect: callback => effects.push(callback),
      }
      if (hooks && specifier === 'react-router-dom') return { ...localRequire(specifier), useLocation: () => ({ pathname: '/' }) }
      return localRequire(specifier)
    } })
    new Script(sources.get(name), { filename: name }).runInContext(context)
    modules.set(name, exports)
    return exports
  }
  return { App: load('App').default, config: load('lib/legal'), effects, document }
}

const app = fixture()
for (const link of app.config.legalLinks) {
  const html = renderToStaticMarkup(React.createElement(MemoryRouter, { initialEntries: [link.to] }, React.createElement(app.App)))
  assert.match(html, new RegExp('<h1[^>]*>' + link.label + '</h1>'), 'Direct legal URL renders its document')
  assert.match(html, /aria-current="page"/, 'Current legal document is indicated')
  assert.match(html, /datetime="2026-10-10"/i, 'Version date is present')
  assert.match(html, /Vinícius F. Marrocos/)
  assert.match(html, /href="mailto:viniciusfmarrocos@gmail.com"/)
  assert.ok(!html.includes('Esse caminho não existe.'))
  for (const anchor of html.matchAll(/href="#([^"]+)"/g)) {
    assert.ok(html.includes('id="' + anchor[1] + '"'), 'Every index and skip link reaches an existing target')
  }
  for (const target of app.config.legalLinks) {
    assert.ok(html.includes('href="' + target.to + '"'), 'All legal documents remain accessible')
  }
  assert.match(html, /aria-label="Políticas e termos"/, 'Global footer navigation is present')
  if (link.kind === 'cookies') {
    assert.match(html, /gandalf-theme/)
    assert.match(html, /não define cookies próprios/)
  }
}
for (const blocked of [false, true]) {
  const theme = fixture(blocked, true)
  assert.doesNotThrow(() => theme.App(), 'Blocked storage does not prevent initial rendering')
  assert.doesNotThrow(() => theme.effects.forEach(effect => effect()), 'Blocked storage does not break theme persistence')
  assert.equal(theme.document.documentElement.dataset.theme, blocked ? 'dark' : 'light')
}
console.log('Legal routes passed: three direct routes, headings, contact, version, navigation, anchors and blocked-storage fallback. Browser QA remains separate.')
