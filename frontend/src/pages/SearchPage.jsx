import { useState, useRef, useEffect } from 'react'
import {
  AlertCircle,
  Check,
  Clock,
  Copy,
  Search,
  Sparkles,
  Zap,
} from 'lucide-react'
import { searchManuscripts } from '../api/client'

const SAMPLE_QUERIES = [
  { text: 'அகர முதல', label: 'Tirukkural Invocation', script: 'Tamil' },
  { text: 'மருத்துவம்', label: 'Herbology & Medicine', script: 'Tamil' },
  { text: 'அறம்', label: 'Dharma / Ethics', script: 'Tamil' },
  { text: 'अग्नि', label: 'Agni / Vedic Fire', script: 'Sanskrit' },
  { text: 'ഔഷധം', label: 'Medicinal Formulation', script: 'Malayalam' },
  { text: 'kanta', label: 'Phonetic Roman', script: 'Transliteration' },
]

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [elapsed, setElapsed] = useState(null)
  const [showQuery, setShowQuery] = useState('')
  const [hybridMode, setHybridMode] = useState(true)
  const [copiedIndex, setCopiedIndex] = useState(null)
  const inputRef = useRef(null)

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

  const executeSearch = async (searchQuery) => {
    const q = (searchQuery ?? query).trim()
    if (!q) return
    setLoading(true)
    setError(null)
    setShowQuery(q)
    try {
      const data = await searchManuscripts(q, 15, hybridMode)
      setResults(data.results ?? [])
      setElapsed(data.elapsed_ms)
    } catch (err) {
      setError(err.message || 'Search failed — is the API server running?')
    } finally {
      setLoading(false)
    }
  }

  const handleSearchSubmit = (e) => {
    e?.preventDefault()
    executeSearch(query)
  }

  const handleChipClick = (sampleQuery) => {
    setQuery(sampleQuery)
    executeSearch(sampleQuery)
  }

  const copyCitation = (item, idx) => {
    const citation = `[Folio: ${item.manuscript_id || 'MS'}, Line: ${item.line_id || '1'}] "${item.text}"`
    navigator.clipboard.writeText(citation)
    setCopiedIndex(idx)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  const highlightMatch = (text, term) => {
    if (!term || !text) return text
    const words = term.trim().split(/\s+/).filter(Boolean)
    const regex = new RegExp(`(${words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi')
    const parts = text.split(regex)

    return parts.map((p, i) =>
      regex.test(p) ? (
        <mark key={i} className="bg-amber-500/30 text-amber-200 px-1 py-0.5 rounded font-semibold border border-amber-500/40">
          {p}
        </mark>
      ) : (
        p
      )
    )
  }

  return (
    <div className="space-y-8 animate-fade-in max-w-5xl mx-auto">
      {/* Search Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold">
          <Zap className="w-3.5 h-3.5 text-indigo-400" />
          <span>FTS5 Lexical + FAISS Semantic RRF Search</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-serif font-bold text-white">
          Hybrid Manuscript Retrieval
        </h1>
        <p className="text-sm text-slate-400 max-w-xl mx-auto">
          Query across character n-grams, phonetic representations, full-text FTS5, and dense embeddings
          to recover degraded historical text.
        </p>
      </div>

      {/* Main Search Input Form */}
      <form onSubmit={handleSearchSubmit} className="space-y-4">
        <div className="card p-2 border border-slate-700/80 bg-slate-900/90 shadow-glow focus-within:border-amber-500 focus-within:shadow-glow-lg transition-all duration-300 flex items-center gap-3">
          <div className="pl-3">
            <Search className="w-5 h-5 text-amber-400" />
          </div>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search in Tamil (தமிழ்), Malayalam, Sanskrit (संस्कृतम्), or Roman transliteration…"
            className="flex-1 bg-transparent outline-none text-base text-white placeholder:text-slate-500 py-2.5"
          />
          <div className="hidden sm:flex items-center gap-1.5 pr-2">
            <kbd className="text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700 px-2 py-1 rounded">
              ⌘K
            </kbd>
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-primary px-6 py-2.5 cursor-pointer"
          >
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>

        {/* Options and Mode Toggles */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Sample Chips */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-slate-500 font-medium">Try:</span>
            {SAMPLE_QUERIES.map((sq) => (
              <button
                key={sq.text}
                type="button"
                onClick={() => handleChipClick(sq.text)}
                className="px-2.5 py-1 rounded-lg bg-slate-900/80 border border-slate-800 hover:border-amber-500/40 text-slate-300 hover:text-amber-200 transition-colors cursor-pointer flex items-center gap-1"
              >
                <span>{sq.text}</span>
                <span className="text-[10px] text-slate-500">({sq.script})</span>
              </button>
            ))}
          </div>

          {/* Hybrid Mode Toggle */}
          <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 rounded-xl px-3 py-1">
            <span className="text-slate-400">Search Engine:</span>
            <button
              type="button"
              onClick={() => setHybridMode(!hybridMode)}
              className={[
                'font-bold cursor-pointer transition-colors',
                hybridMode ? 'text-amber-400' : 'text-slate-500',
              ].join(' ')}
            >
              {hybridMode ? '⚡ Hybrid RRF (BM25 + FAISS)' : 'Lexical BM25 Only'}
            </button>
          </div>
        </div>
      </form>

      {/* Loading Skeleton */}
      {loading && (
        <div className="card p-8 border border-slate-800 text-center space-y-3 animate-pulse">
          <div className="w-8 h-8 mx-auto rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center animate-spin">
            <Sparkles className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-sm text-slate-300 font-medium">Querying Quad-Engine Hybrid Index…</p>
          <p className="text-xs text-slate-500">Evaluating BM25, Character N-Grams, Phonetic Normalization, and FAISS Dense Vectors</p>
        </div>
      )}

      {/* Error Alert */}
      {error && !loading && (
        <div className="card p-4 bg-red-950/30 border border-red-500/50 flex items-center gap-3 text-sm text-red-300">
          <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search Results Display */}
      {!loading && results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800/80 pb-3">
            <span>
              Found <strong className="text-white font-mono">{results.length}</strong> matching passages for "{showQuery}"
            </span>
            {elapsed !== null && (
              <span className="font-mono text-emerald-400 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" /> {elapsed.toFixed(1)} ms
              </span>
            )}
          </div>

          <div className="space-y-3">
            {results.map((res, i) => {
              const score = typeof res.score === 'number' ? res.score : 0.85
              const pct = Math.min(Math.round(score * 100), 100)
              return (
                <div
                  key={i}
                  className="card p-5 border border-slate-800/80 hover:border-amber-500/40 bg-slate-900/90 transition-all duration-200 space-y-3 group"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded">
                        #{i + 1}
                      </span>
                      <span className="text-xs font-mono text-slate-400 truncate max-w-[200px] sm:max-w-md">
                        MS ID: {res.manuscript_id || 'Historical Corpus Folio'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <div className="text-right">
                        <span className="text-[10px] font-mono text-slate-500 block">Relevance</span>
                        <span className="text-xs font-mono font-bold text-emerald-400">
                          {score.toFixed(4)}
                        </span>
                      </div>
                      <button
                        onClick={() => copyCitation(res, i)}
                        className="btn-secondary text-xs py-1 px-2.5 flex items-center gap-1 cursor-pointer"
                        title="Copy research citation"
                      >
                        {copiedIndex === i ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        <span>{copiedIndex === i ? 'Copied' : 'Cite'}</span>
                      </button>
                    </div>
                  </div>

                  {/* Main Transcript Line */}
                  <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80">
                    <p className="text-base text-slate-100 font-serif leading-relaxed">
                      {highlightMatch(res.text, showQuery)}
                    </p>
                  </div>

                  {/* Relevance bar */}
                  <div className="space-y-1">
                    <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-amber-500 to-emerald-400 rounded-full transition-all duration-500"
                        style={{ width: `${Math.max(pct, 15)}%` }}
                      />
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Empty State after search */}
      {!loading && showQuery && results.length === 0 && !error && (
        <div className="card p-12 text-center border border-slate-800 space-y-3">
          <Search className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-white">No Matching Folios Found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Try a broader word, character n-gram, or upload and index sample manuscripts from the Digitize Studio first.
          </p>
        </div>
      )}
    </div>
  )
}
