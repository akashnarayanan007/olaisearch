import { useState, useRef, useEffect } from 'react'
import {
  Archive,
  BookOpen,
  Check,
  Copy,
  Leaf,
  Loader2,
  Send,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import { chatQuestion } from '../api/client'

const EVIDENCE_ICONS = {
  MANUSCRIPT: Leaf,
  ARCHIVE: Archive,
  BACKGROUND: BookOpen,
}

const STARTER_PROMPTS = [
  'What is the central ethical theme of Line 1?',
  'Explain the historical date or Saka era mentioned in the colophon.',
  'Provide a word-by-word transliteration and English translation.',
  'What medicinal herbs or formulations are specified?',
]

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [manuscriptId, setManuscriptId] = useState('')
  const [mode, setMode] = useState('leaf')
  const [copiedIndex, setCopiedIndex] = useState(null)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (questionText) => {
    const question = (questionText ?? input).trim()
    if (!question || loading) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setLoading(true)
    setError(null)
    try {
      const data = await chatQuestion(question, { manuscriptId, mode })
      setMessages((prev) => [...prev, { role: 'assistant', content: data }])
    } catch (err) {
      setError(err.message || 'Chat failed — is the FastAPI server running?')
      setMessages((prev) => [
        ...prev,
        { role: 'error', content: err.message ?? String(err) },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const copyMessage = (text, idx) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(idx)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  const clearChat = () => {
    setMessages([])
    setError(null)
  }

  return (
    <div className="space-y-4 h-[calc(100vh-10rem)] flex flex-col max-w-5xl mx-auto animate-fade-in">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold mb-1">
            <ShieldCheck className="w-3.5 h-3.5" /> Three-Tier Grounded Evidence System
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-white">
            Manuscript Research Assistant
          </h1>
        </div>

        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="btn-secondary text-xs py-1 px-3 cursor-pointer"
            >
              Clear Chat
            </button>
          )}
        </div>
      </div>

      {/* Scope and Mode Controls */}
      <div className="card p-3 border border-slate-800 bg-slate-900/90 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          <label className="text-slate-400 font-medium">Focus Folio ID:</label>
          <input
            type="text"
            value={manuscriptId}
            onChange={(e) => setManuscriptId(e.target.value)}
            placeholder="Optional (searches entire corpus if empty)"
            className="input-field text-xs py-1.5 w-56 sm:w-72 bg-slate-950/80"
          />
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-slate-400 mr-1 hidden sm:inline">Context Mode:</span>
          {[
            { key: 'leaf', icon: Leaf, label: 'Leaf Folio' },
            { key: 'archive', icon: Archive, label: 'Full Archive' },
            { key: 'selection', icon: BookOpen, label: 'Hermeneutics' },
          ].map(({ key, icon: Icon, label }) => (
            <button
              key={key}
              onClick={() => setMode(key)}
              className={[
                'flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all cursor-pointer font-medium',
                mode === key
                  ? 'bg-amber-500 text-slate-950 font-bold shadow-glow'
                  : 'bg-slate-950/60 text-slate-400 hover:text-white border border-slate-800',
              ].join(' ')}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Canvas */}
      <div className="flex-1 card p-5 border border-slate-800 bg-slate-900/80 overflow-y-auto space-y-5">
        {messages.length === 0 && (
          <div className="text-center py-12 space-y-6">
            <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mx-auto shadow-glow">
              <Sparkles className="w-7 h-7 text-amber-400" />
            </div>

            <div className="space-y-2 max-w-md mx-auto">
              <h3 className="text-lg font-serif font-bold text-white">
                Grounded Philological Dialogue
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Ask targeted historical, linguistic, or medical questions about your uploaded manuscripts.
                Every assertion is verified with citations against the original physical leaf lines.
              </p>
            </div>

            {/* Quick Starter Chips */}
            <div className="pt-2 max-w-xl mx-auto space-y-2">
              <p className="text-[11px] text-slate-500 uppercase tracking-wider font-mono">
                Suggested Research Inquiries:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                {STARTER_PROMPTS.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => sendMessage(p)}
                    className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-amber-500/40 text-xs text-slate-300 hover:text-amber-200 transition-all text-left cursor-pointer group"
                  >
                    <span className="text-amber-400 group-hover:translate-x-1 inline-block transition-transform mr-1.5">
                      →
                    </span>
                    {p}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            msg={msg}
            idx={i}
            copiedIndex={copiedIndex}
            onCopy={copyMessage}
          />
        ))}

        {loading && (
          <div className="flex items-center gap-3 p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 animate-pulse w-fit">
            <Loader2 className="w-4 h-4 text-amber-400 animate-spin" />
            <span>Analyzing folio lines & verifying citation provenance…</span>
          </div>
        )}

        {error && (
          <div className="text-xs text-red-300 bg-red-950/40 border border-red-500/40 rounded-xl p-3">
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input controls */}
      <form onSubmit={(e) => { e.preventDefault(); sendMessage() }} className="relative flex gap-2">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about folio text, era, botanical recipes, or grammar…"
          className="input-field py-3 pl-4 pr-12 text-sm bg-slate-900/90 border-slate-700 focus:border-amber-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="btn-primary px-5 cursor-pointer"
        >
          <Send className="w-4 h-4 text-slate-950" />
        </button>
      </form>
    </div>
  )
}

function MessageBubble({ msg, idx, copiedIndex, onCopy }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end items-start gap-2.5">
        <div className="max-w-xl bg-gradient-to-r from-amber-600 to-saffron-600 text-slate-950 font-medium text-sm rounded-2xl rounded-tr-none px-4 py-3 shadow-glow">
          {msg.content}
        </div>
        <div className="w-8 h-8 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-xs font-bold text-amber-300 shrink-0">
          U
        </div>
      </div>
    )
  }

  if (msg.role === 'error') {
    return (
      <div className="text-xs text-red-300 bg-red-950/40 border border-red-500/40 rounded-xl p-3.5">
        {msg.content}
      </div>
    )
  }

  const rawText = typeof msg.content === 'string' ? msg.content : msg.content?.response || JSON.stringify(msg.content)

  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-amber-500 flex items-center justify-center text-xs font-bold text-white shrink-0 shadow-sm">
        AI
      </div>

      <div className="flex-1 space-y-3">
        <div className="card p-4 border border-slate-800 bg-slate-950/80 rounded-tl-none relative group">
          <button
            onClick={() => onCopy(rawText, idx)}
            className="absolute top-3 right-3 p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
            title="Copy answer"
          >
            {copiedIndex === idx ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          {typeof msg.content === 'string' ? (
            <p className="text-sm text-slate-200 leading-relaxed font-sans">{msg.content}</p>
          ) : (
            <ResponseStructure data={msg.content} />
          )}
        </div>

        {/* Suggested follow-up chips */}
        {msg.followups?.length > 0 && (
          <div className="flex flex-wrap gap-2 pt-1">
            {msg.followups.map((f, i) => (
              <span
                key={i}
                className="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/30 rounded-full px-3 py-1 cursor-pointer hover:bg-amber-500/20 transition-colors"
              >
                → {f}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function ResponseStructure({ data }) {
  if (!data) return null

  const renderEvidenceTier = (tier, items) => {
    if (!items || (Array.isArray(items) && items.length === 0)) return null
    const Icon = EVIDENCE_ICONS[tier] || Leaf

    const config =
      tier === 'MANUSCRIPT'
        ? {
            label: 'Tier 1: Manuscript Folio Line Evidence',
            border: 'border-l-emerald-500 bg-emerald-950/20 text-emerald-200',
            badge: 'badge-emerald',
          }
        : tier === 'ARCHIVE'
        ? {
            label: 'Tier 2: Archive Corpus Passage',
            border: 'border-l-sky-500 bg-sky-950/20 text-sky-200',
            badge: 'badge-indigo',
          }
        : {
            label: 'Tier 3: Historical Philology Context',
            border: 'border-l-purple-500 bg-purple-950/20 text-purple-200',
            badge: 'badge-palm',
          }

  return (
    <div className={`border-l-4 px-3.5 py-2.5 rounded-r-xl border border-slate-800/80 ${config.border} space-y-1 mt-2`}>
      <div className="flex items-center gap-1.5 text-xs font-semibold">
        <Icon className="w-3.5 h-3.5" />
        <span>{config.label}</span>
      </div>
      {Array.isArray(items) ? (
        <ul className="text-xs font-mono space-y-1 list-disc list-inside">
          {items.map((item, i) => (
            <li key={i} className="leading-relaxed">{item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-xs font-mono leading-relaxed">{items}</p>
      )}
    </div>
  )
}

  return (
    <div className="text-sm text-slate-200 space-y-3">
      {data.response && (
        <div className="leading-relaxed font-sans">{data.response}</div>
      )}

      {renderEvidenceTier('MANUSCRIPT', data.manuscript_evidence)}
      {renderEvidenceTier('ARCHIVE', data.archive_evidence)}
      {renderEvidenceTier('BACKGROUND', data.background)}

      {data.unverified_background && (
        <div className="text-xs text-amber-300/90 bg-amber-950/30 border border-amber-500/40 rounded-xl p-3">
          <strong className="block text-amber-200 uppercase text-[10px] tracking-wider mb-1">
            Historical Background (Unverified against leaf):
          </strong>
          {data.unverified_background}
        </div>
      )}

      {data.no_evidence && (
        <p className="text-xs text-slate-400 italic">{data.no_evidence}</p>
      )}
    </div>
  )
}
