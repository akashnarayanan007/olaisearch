import React, { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Leaf, Archive, BookOpen } from 'lucide-react'
import { chatQuestion } from '../api/client'

const EVIDENCE_ICONS = {
  MANUSCRIPT: Leaf,
  ARCHIVE: Archive,
  BACKGROUND: BookOpen,
}

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [manuscriptId, setManuscriptId] = useState('')
  const [mode, setMode] = useState('leaf')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (e) => {
    e?.preventDefault()
    if (!input.trim() || loading) return
    const question = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: question }])
    setLoading(true)
    setError(null)
    try {
      const data = await chatQuestion(question, { manuscriptId, mode })
      setMessages((prev) => [...prev, { role: 'assistant', content: data }])
    } catch (err) {
      setError(err.message || 'Chat failed — is the API server running?')
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

  return (
    <div className="space-y-4 h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-serif font-bold text-stone-900">Manuscript Chat</h1>
        <p className="text-sm text-stone-500 mt-1">
          Ask questions about indexed manuscripts. Responses show evidence from three tiers.
        </p>
      </div>

      {/* Controls bar */}
      <div className="card p-3 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <label className="text-xs text-stone-500">Manuscript ID:</label>
          <input
            type="text"
            value={manuscriptId}
            onChange={(e) => setManuscriptId(e.target.value)}
            placeholder="Optional — search all if empty"
            className="input-field text-xs py-1 w-48"
          />
        </div>
        <div className="flex items-center gap-1 ml-auto">
          {[
            { key: 'leaf', icon: Leaf, label: 'Leaf text' },
            { key: 'archive', icon: Archive, label: 'Archive' },
            { key: 'selection', icon: BookOpen, label: 'Selection' },
          ].map(({ key, icon: Icon, label }) => (
            <button
              key={key}
              onClick={() => setMode(key)}
              className={[
                'flex items-center gap-1 px-2.5 py-1 text-xs rounded-lg transition-colors',
                mode === key
                  ? 'bg-palm-100 text-palm-800 font-medium'
                  : 'text-stone-500 hover:bg-stone-100',
              ].join(' ')}
            >
              <Icon className="w-3 h-3" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 card p-4 overflow-y-auto space-y-4">
        {messages.length === 0 && (
          <EmptyState />
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-sm text-stone-400 animate-pulse">
            <Loader2 className="w-4 h-4 animate-spin" />
            Generating response…
          </div>
        )}

        {error && (
          <div className="text-xs text-red-500 bg-red-50 border border-red-200 rounded-lg p-3">
            {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={sendMessage} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about a manuscript… (e.g. 'What are the herbs mentioned?')"
          className="input-field flex-1"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()} className="btn-primary">
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="text-center py-12 text-stone-400 space-y-3">
      <Leaf className="w-10 h-10 mx-auto text-stone-300" />
      <p className="text-sm font-medium text-stone-500">Ask a question about your manuscripts</p>
      <div className="text-xs text-stone-400 space-y-1">
        <p>"What herbs are mentioned in this Siddha text?"</p>
        <p>"When was this manuscript written?"</p>
        <p>"Summarize the content in English"</p>
      </div>
      <p className="text-xs text-stone-300 italic mt-4">
        Three-tier evidence: Manuscript → Archive → Background (unverified)
      </p>
    </div>
  )
}

function MessageBubble({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-lg bg-palm-700 text-white text-sm rounded-xl px-4 py-2.5">
          {msg.content}
        </div>
      </div>
    )
  }

  if (msg.role === 'error') {
    return (
      <div className="text-xs text-red-500 bg-red-50 border border-red-200 rounded-lg p-3">
        {msg.content}
      </div>
    )
  }

  // Assistant — render structured response
  return (
    <div className="space-y-3">
      {/* Main response text */}
      {typeof msg.content === 'string' ? (
        <p className="text-sm text-stone-700 leading-relaxed bg-stone-50 rounded-lg p-3">
          {msg.content}
        </p>
      ) : (
        <ResponseStructure data={msg.content} />
      )}

      {/* Suggested follow-ups */}
      {msg.followups?.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {msg.followups.map((f, i) => (
            <span key={i} className="text-xs text-palm-600 bg-palm-50 border border-palm-200 rounded-full px-3 py-1">
              → {f}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function ResponseStructure({ data }) {
  if (!data) return null

  const renderEvidenceTier = (tier, items) => {
    if (!items || items.length === 0) return null
    const Icon = EVIDENCE_ICONS[tier] || Leaf
    return (
      <div className={`border-l-4 px-3 py-2 rounded ${
        tier === 'MANUSCRIPT' ? 'border-palm-500 bg-palm-50'
        : tier === 'ARCHIVE' ? 'border-blue-400 bg-blue-50'
        : 'border-amber-400 bg-amber-50'
      }`}>
        <div className="flex items-center gap-1.5 text-xs font-medium text-stone-500 mb-1">
          <Icon className="w-3 h-3" />
          {tier.replace('_', ' ')} Evidence
        </div>
        {Array.isArray(items) ? (
          <ul className="text-xs text-stone-700 space-y-0.5 list-disc list-inside">
            {items.map((item, i) => (
              <li key={i} className="font-mono break-all">{item}</li>
            ))}
          </ul>
        ) : (
          <p className="text-xs font-mono text-stone-700">{items}</p>
        )}
      </div>
    )
  }

  return (
    <div className="text-sm text-stone-700 space-y-2">
      {data.response && (
        <p className="leading-relaxed">{data.response}</p>
      )}
      {renderEvidenceTier('MANUSCRIPT', data.manuscript_evidence)}
      {renderEvidenceTier('ARCHIVE', data.archive_evidence)}
      {renderEvidenceTier('BACKGROUND', data.background)}
      {data.unverified_background && (
        <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
          <strong>Unverified background:</strong> {data.unverified_background}
        </div>
      )}
      {data.no_evidence && (
        <p className="text-xs text-stone-400 italic">{data.no_evidence}</p>
      )}
    </div>
  )
}
