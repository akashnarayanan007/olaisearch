import React, { useState, useRef, useEffect } from 'react'
import { Search, Filter, AlertCircle, ChevronRight } from 'lucide-react'
import { searchManuscripts } from '../api/client'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [elapsed, setElapsed] = useState(null)
  const [showQuery, setShowQuery] = useState('')
  const inputRef = useRef(null)

  // Keyboard shortcut: Ctrl/Cmd+K to focus search
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const handleSearch = async (e) => {
    e?.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setShowQuery(query.trim())
    try {
      const data = await searchManuscripts(query.trim(), 10, true)
      setResults(data.results ?? [])
      setElapsed(data.elapsed_ms)
    } catch (err) {
      setError(err.message || 'Search failed — is the API server running?')
    } finally {
      setLoading(false)
    }
  }

  const highlightMatch = (text, term) => {
    if (!term || !text) return text
    const parts = text.split(new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'))
    return parts.map((p, i) =>
      p.toLowerCase() === term.toLowerCase()
        ? <mark key={i} className="bg-palm-200 text-palm-900 rounded px-0.5">{p}</mark>
        : p,
    )
  }

  const confidenceColor = (c) =>
    c >= 0.8 ? 'bg-emerald-500' : c >= 0.5 ? 'bg-amber-500' : 'bg-red-400'

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-serif font-bold text-stone-900">Search Manuscripts</h1>
        <p className="text-sm text-stone-500 mt-1">
          Cross-lingual search across BM25, character n-grams, phonetic, and dense indexes.
          {' '}<kbd className="text-xs font-mono bg-stone-100 border border-stone-300 rounded px-1">⌘K</kbd> to focus
        </p>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="relative">
        <div className="card flex items-center gap-2 p-2">
          <Search className="w-5 h-5 text-stone-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search in Tamil, Malayalam, Sanskrit, or Roman transliteration…"
            className="flex-1 bg-transparent outline-none text-sm text-stone-800 placeholder:text-stone-400"
          />
          <button type="submit" disabled={loading || !query.trim()} className="btn-primary">
            {loading ? <LoaderIcon /> : 'Search'}
          </button>
        </div>
      </form>

      {/* Results area */}
      {loading && (
        <div className="card p-6 text-center text-sm text-stone-400 animate-pulse">
          <p>Searching across indexes…</p>
        </div>
      )}

      {error && !loading && (
        <div className="card p-4 bg-red-50 border-red-200 flex items-center gap-2 text-sm text-red-600">
          <AlertCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {results.length > 0 && (
        <>
          <div className="flex items-center justify-between text-xs text-stone-400">
            <span>
              {results.length} result{results.length !== 1 ? 's' : ''} ·{' '}
              {elapsed != null ? `${elapsed.toFixed(1)} ms` : ''}
            </span>
            <span className="font-mono">Query: {showQuery}</span>
          </div>

          <div className="space-y-2">
            {results.map((r, i) => (
              <ResultCard key={r.line_id ?? r.id ?? i} result={r} query={showQuery} />
            ))}
          </div>
        </>
      )}

      {!loading && results.length === 0 && !error && showQuery && (
        <div className="card p-8 text-center text-stone-400">
          <p>No results found.</p>
          <p className="text-xs mt-1">Try a different query or check the language code.</p>
        </div>
      )}
    </div>
  )
}

function ResultCard({ result, query }) {
  const conf = result.confidence ?? result.score ?? 0.8
  return (
    <div className="card p-4 hover:border-palm-300 transition-colors cursor-pointer group">
      <div className="flex items-start gap-3">
        <span className="text-xs font-mono text-stone-400 w-6 pt-0.5">
          {String(result.rank ?? '-')}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-stone-800 leading-relaxed">
            {highlightMatch(result.text ?? result.content ?? result.line_text ?? '', query)}
          </p>
          <div className="flex items-center gap-3 mt-1.5 text-xs text-stone-500">
            <span className="badge badge-palm">{result.script ?? result.language ?? 'tam'}</span>
            <span className="font-mono truncate">
              {result.msscript_id ?? result.manuscript_id ?? result.id ?? '?'}
            </span>
            <span className="text-stone-400">·</span>
            <span className="flex items-center gap-1">
              <span className={`w-1.5 h-1.5 rounded-full ${confidenceColor(conf)}`} />
              {(conf * 100).toFixed(0)}%
            </span>
            {result.score != null && (
              <>
                <span className="text-stone-400">·</span>
                <span className="font-mono text-stone-400">
                  score: {result.score.toFixed(4)}
                </span>
              </>
            )}
          </div>
        </div>
        <ChevronRight className="w-4 h-4 text-stone-300 group-hover:text-palm-500 shrink-0 transition-colors" />
      </div>
    </div>
  )
}

function LoaderIcon() {
  return (
    <svg className="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v8H4z"
      />
    </svg>
  )
}
