import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import ts from 'typescript'

// Exercise the actual TypeScript without Vite/browser subprocesses. Keeps the
// existing Node compatibility by using the project's installed compiler.
const source = await readFile(new URL('../src/lib/discovery.ts', import.meta.url), 'utf8')
const { outputText } = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext } })
const { continuationBody, freshSuggestions } = await import('data:text/javascript;base64,' + Buffer.from(outputText).toString('base64'))
const id = n => `00000000-0000-4000-8000-${String(n).padStart(12, '0')}`
const rows = (...ids) => ids.map(itemId => ({ position: 1, item: { id: itemId, title: 'Real candidate', artist: 'Artist' } }))
const seen = new Set([id(1), id(2)])
assert.deepEqual(continuationBody('music', 'Pedido enviado', { vocals: 'none', energy: 'low' }, seen, 15), {
  query: 'Pedido enviado', filters: { vocals: 'none', energy: 'low' }, limit: 10, excluded_music_ids: [id(1), id(2)], offset: 15,
})
assert.deepEqual(continuationBody('books', 'Pedido enviado', { vocals: 'none', energy: 'low' }, seen, 300), {
  query: 'Pedido enviado', limit: 10, excluded_book_ids: [id(1), id(2)], offset: 300,
})
assert.deepEqual(continuationBody('music', 'Pedido enviado', { vocals: '', energy: '' }, seen, 0).filters, {})
const priorIds = Array.from({ length: 199 }, (_, i) => id(i))
const boundary = new Set(priorIds)
const lastRequest = continuationBody('music', 'Pedido enviado', { vocals: '', energy: '' }, boundary, 0)
assert.equal(lastRequest.limit, 1)
assert.deepEqual(lastRequest.excluded_music_ids, priorIds, 'All 199 exclusions are sent in order, without truncation')
const fresh = freshSuggestions(rows(id(0), id(200), id(200), id(201)), boundary, lastRequest.limit)
assert.deepEqual(fresh.map(row => row.item.id), [id(200)], 'Suppress already seen IDs, duplicates and excess beyond the remaining slot')
assert.equal(boundary.size, 199, 'Filtering cannot mutate seen state before a successful request is accepted')
fresh.forEach(row => boundary.add(row.item.id))
assert.equal(boundary.size, 200)
assert.equal(continuationBody('music', 'Pedido enviado', { vocals: '', energy: '' }, boundary, 0), null, 'Stop at 200, never recycle previous exclusions')
assert.equal(continuationBody('books', 'Pedido enviado', { vocals: '', energy: '' }, boundary, 300), null)
assert.deepEqual(freshSuggestions(rows(id(1), id(3), id(3), id(2), id(4)), seen).map(row => row.item.id), [id(3), id(4)])
console.log('Discovery state passed: MUSIC/BOOK contracts, indifferent filters, offset 0/300, cumulative exclusions, duplicates, 199+1 boundary and stop at 200.')
