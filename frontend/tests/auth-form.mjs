import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createRequire } from 'node:module'
import { Script, createContext } from 'node:vm'
import ts from 'typescript'

// Execute the production submit handler with batched state setters and stable
// refs. This checks same-turn submissions without claiming browser/native form QA.
const require = createRequire(import.meta.url)
const source = await readFile(new URL('../src/pages/Authentication.tsx', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX } }).outputText
const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done }); return { promise, resolve } }
function fixture(mode, { returnTo, mismatch = false, failure = false } = {}) {
  const hold = deferred(), calls = [], navigation = []
  const state = ['reader@example.com', 'reader', 'fixture phrase 123', mismatch ? 'different phrase' : 'fixture phrase 123', false, false, '']
  let index = 0
  const exports = {}
  const request = async (...args) => { calls.push(args); await hold.promise; if (failure) throw new Error('Fixture retry error') }
  const deps = {
    react: { useState: () => { const position = index++; return [state[position], value => { state[position] = value }] }, useRef: value => ({ current: value }), useEffect: () => {} },
    'react/jsx-runtime': require('react/jsx-runtime'),
    'react-router-dom': { Link: 'a', Navigate: 'redirect', useLocation: () => ({ state: { returnTo } }), useNavigate: () => (...args) => navigation.push(args) },
    'lucide-react': { ArrowRight: 'svg', Eye: 'svg', EyeOff: 'svg' },
    '../lib/auth': { authSession: { signIn: request, register: request } },
    '../lib/useSession': { useSession: () => ({ user: null, expired: false }) },
  }
  new Script(compiled, { filename: 'Authentication.tsx' }).runInContext(createContext({ exports, AbortController, require: path => {
    assert.ok(Object.hasOwn(deps, path), 'Only explicit production imports are mocked')
    return deps[path]
  }, Error }))
  const root = exports.default({ mode })
  function find(node, predicate) {
    if (!node || typeof node !== 'object') return undefined
    if (predicate(node)) return node
    for (const child of [node.props?.children].flat(Infinity)) { const found = find(child, predicate); if (found) return found }
  }
  return { hold, calls, state, navigation, submit: find(root, node => node.type === 'form').props.onSubmit,
    input: id => find(root, node => node.type === 'input' && node.props.id === id).props }
}
const event = { preventDefault() {} }
for (const mode of ['login', 'register']) {
  const f = fixture(mode)
  const first = f.submit(event), second = f.submit(event)
  assert.equal(f.calls.length, 1, `${mode}: same-turn submits make one request`)
  assert.equal(f.state[5], true, 'UI pending state is set')
  f.hold.resolve()
  await Promise.all([first, second])
  assert.equal(f.state[5], false)
  assert.equal(f.navigation.length, 1)
  assert.equal(f.input('auth-email').name, 'email')
  assert.equal(f.input('auth-password').name, 'password')
  assert.equal(f.input('auth-password').autoComplete, mode === 'login' ? 'current-password' : 'new-password')
  assert.equal(f.input('auth-email').autoComplete, mode === 'login' ? 'username' : 'email')
  assert.equal(f.calls[0].at(-1).aborted, false)
  if (mode === 'register') {
    assert.equal(f.input('auth-username').name, 'username')
    assert.equal(f.input('auth-confirmation').name, 'password_confirmation')
    assert.equal(f.input('auth-confirmation').autoComplete, 'new-password')
  }
  // Releasing the synchronous lock must allow a later attempt as well.
  await f.submit(event)
  assert.equal(f.calls.length, 2)
}
{
  const f = fixture('register', { mismatch: true })
  await f.submit(event)
  assert.equal(f.calls.length, 0)
  assert.match(f.state[6], /As senhas precisam ser iguais/)
}
for (const mode of ['login', 'register']) {
  const f = fixture(mode, { failure: true })
  f.hold.resolve()
  await f.submit(event)
  assert.equal(f.state[5], false)
  assert.equal(f.state[6], 'Fixture retry error')
  await f.submit(event)
  assert.equal(f.calls.length, 2, 'A failed request releases the lock for retry')
}
for (const pathname of ['https://example.com', '//example.com', '/account/other', '/music?redirect=https://example.com']) {
  const f = fixture('login', { returnTo: { pathname } })
  f.hold.resolve()
  await f.submit(event)
  assert.equal(f.navigation[0][0], '/account', 'Unapproved targets cannot redirect outside the allowlist')
}
for (const pathname of ['/music', '/books', '/read-with-music', '/account/favorites']) {
  const saved = { fixture: 'public selection snapshot' }
  const f = fixture('login', { returnTo: { pathname, state: saved } })
  f.hold.resolve()
  await f.submit(event)
  assert.equal(f.navigation[0][0], pathname)
  assert.equal(f.navigation[0][1].state, saved, 'Allowed internal return preserves its snapshot')
}
console.log('Auth form handler passed: same-turn login/register submit lock, release/retry, mismatch, input names/autocomplete and internal return allowlist/snapshot. Browser QA remains separate.')
