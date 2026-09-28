import React, { useState, useRef } from 'react'
import { Upload, Image, CheckCircle, Loader2, FileText, XCircle } from 'lucide-react'
import { uploadManuscript, generateDemo, getStats, listManuscripts } from '../api/client'

export default function UploadPage({ onUploaded }) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [language, setLanguage] = useState('tam')
  const [stats, setStats] = useState(null)
  const [recentMs, setRecentMs] = useState([])
  const fileInputRef = useRef(null)

  const handleFile = async (file) => {
    if (!file || !file.size) return
    setError(null)
    setUploading(true)
    try {
      const data = await uploadManuscript(file, language)
      setResult(data)
      if (onUploaded) onUploaded()
    } catch (err) {
      setError(err.message || 'Upload failed — is the API server running?')
    } finally {
      setUploading(false)
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files?.[0]
    handleFile(file)
  }

  const handleDemo = async () => {
    setUploading(true)
    try {
      const data = await generateDemo(5, 'medium')
      setResult({ ...data, isDemo: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const loadStats = async () => {
    try {
      const [s, ms] = await Promise.all([getStats(), listManuscripts(20)])
      setStats(s)
      setRecentMs(ms.manuscripts ?? [])
    } catch { /* silent */ }
  }

  const confidenceColor = (c) =>
    c >= 0.8 ? 'text-emerald-600' : c >= 0.5 ? 'text-amber-600' : 'text-red-500'

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-serif font-bold text-stone-900">Upload Manuscript</h1>
        <p className="text-sm text-stone-500 mt-1">
          Drop a palm-leaf image — it will be processed through the full pipeline:
          segmentation → script ID → recognition ensemble → post-correction → hybrid indexing.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ─── Left: Drop zone ──────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-4">
          <div
            className={[
              'card p-8 border-2 border-dashed transition-colors flex flex-col items-center justify-center min-h-56',
              dragging ? 'border-palm-400 bg-palm-50' : 'border-stone-300 hover:border-palm-300',
            ].join(' ')}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            <Image className="w-10 h-10 text-stone-300 mb-3" />
            <p className="text-sm text-stone-500 text-center">
              Drag and drop a manuscript image here, or{' '}
              <button
                className="text-palm-700 font-medium underline"
                onClick={() => fileInputRef.current?.click()}
              >
                browse files
              </button>
            </p>
            <p className="text-xs text-stone-400 mt-1">
              Supports: JPG, PNG, TIFF · Max 20 MB
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/tiff"
              className="hidden"
              onChange={(e) => handleFile(e.target.files?.[0])}
            />
          </div>

          {/* Language selector + demo button */}
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-stone-600">
              <span>Language:</span>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="input-field w-24 py-1.5"
              >
                <option value="tam">Tamil</option>
                <option value="mal">Malayalam</option>
                <option value="san">Sanskrit</option>
                <option value="tel">Telugu</option>
                <option value="kan">Kannada</option>
              </select>
            </label>
            <button className="btn-secondary text-xs" onClick={handleDemo}>
              <FileText className="w-3.5 h-3.5" />
              Generate Demo Samples
            </button>
          </div>

          {/* Progress indicator */}
          {uploading && (
            <div className="card p-4 flex items-center gap-3 animate-fade-in">
              <Loader2 className="w-5 h-5 text-palm-600 animate-spin" />
              <div>
                <p className="text-sm font-medium text-stone-700">Processing pipeline…</p>
                <p className="text-xs text-stone-400">
                  Segmentation → Recognition → Correction → Indexing
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="card p-4 bg-red-50 border-red-200 flex items-start gap-3 animate-fade-in">
              <XCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-700">Upload Failed</p>
                <p className="text-xs text-red-500 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {/* Result card */}
          {result && !uploading && (
            <div className="card p-5 animate-slide-up border-emerald-200 bg-emerald-50/50">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-emerald-800">
                    {result.isDemo ? 'Demo samples generated' : 'Manuscript processed'}
                  </p>
                  <p className="text-xs text-emerald-600 mt-0.5">{result.message}</p>

                  {result.msscript_id && (
                    <p className="text-xs font-mono text-emerald-700 mt-1.5 break-all">
                      MS ID: {result.msscript_id}
                    </p>
                  )}

                  {result.lines?.length > 0 && (
                    <div className="mt-3 space-y-1.5">
                      <p className="text-xs font-medium text-stone-500">
                        Lines ({result.lines.length}):
                      </p>
                      {result.lines.slice(0, 5).map((line, i) => (
                        <div key={i} className="text-xs flex items-center gap-2">
                          <span className="text-stone-400 font-mono w-4">{i + 1}</span>
                          <span className="flex-1 text-stone-700 truncate">{line.text ?? line.content}</span>
                          <span className={`text-xs font-mono ${confidenceColor(line.confidence ?? 0.8)}`}>
                            {(line.confidence ?? 0.8).toFixed(2)}
                          </span>
                        </div>
                      ))}
                      {result.lines.length > 5 && (
                        <p className="text-xs text-stone-400">+ {result.lines.length - 5} more lines…</p>
                      )}
                    </div>
                  )}

                  {result.sample_ids && (
                    <p className="text-xs text-stone-500 mt-2">
                      Sample IDs: <span className="font-mono">{result.sample_ids.join(', ')}</span>
                    </p>
                  )}

                  <button
                    className="text-xs text-palm-700 font-medium mt-3 flex items-center gap-1"
                    onClick={loadStats}
                  >
                    Refresh archive stats →
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Archive stats */}
          {stats && (
            <div className="card p-4 animate-fade-in">
              <p className="text-sm font-medium text-stone-700 mb-2">Archive Statistics</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {Object.entries(stats).map(([k, v]) => (
                  <div key={k} className="text-center p-2 bg-stone-50 rounded-lg">
                    <p className="text-lg font-bold text-palm-800">{v}</p>
                    <p className="text-xs text-stone-400">{k.replace(/_/g, ' ')}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ─── Right: Recent manuscripts ────────────────────────── */}
        <div className="card p-4">
          <p className="text-sm font-medium text-stone-700 mb-3">Recent Manuscripts</p>
          {recentMs.length === 0 ? (
            <p className="text-xs text-stone-400">No manuscripts yet. Upload one to begin.</p>
          ) : (
            <div className="space-y-2">
              {recentMs.map((ms) => (
                <div key={ms.id ?? ms.msscript_id} className="text-xs border border-stone-200 rounded-lg p-3">
                  <p className="font-medium text-stone-700 truncate">
                    {ms.language ?? ms.script ?? 'unknown'}
                  </p>
                  <p className="text-stone-400 font-mono mt-0.5 truncate">
                    {ms.id ?? ms.msscript_id}
                  </p>
                  <p className="text-stone-500 mt-1">
                    {ms.num_lines ?? ms.lines?.length ?? 0} lines indexed
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
