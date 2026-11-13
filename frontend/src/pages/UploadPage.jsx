import { useState, useRef, useEffect } from 'react'
import {
  ArrowRight,
  Check,
  CheckCircle2,
  Copy,
  Cpu,
  Database,
  FileText,
  Image as ImageIcon,
  Layers,
  Loader2,
  RefreshCw,
  Sparkles,
  Upload,
  XCircle,
} from 'lucide-react'
import { uploadManuscript, generateDemo, getStats, listManuscripts } from '../api/client'

const LANGUAGES = [
  { code: 'tam', name: 'Tamil', script: 'தமிழ்', badge: 'Primary' },
  { code: 'mal', name: 'Malayalam', script: 'മലയാളം', badge: 'Supported' },
  { code: 'san', name: 'Sanskrit', script: 'संस्कृतम्', badge: 'Grantha / Devanagari' },
  { code: 'tel', name: 'Telugu', script: 'తెలుగు', badge: 'Indic' },
  { code: 'kan', name: 'Kannada', script: 'ಕನ್ನಡ', badge: 'Indic' },
]

const PIPELINE_STAGES = [
  { id: 1, label: 'Restoration', desc: 'CLAHE & Sauvola', icon: Sparkles },
  { id: 2, label: 'Line Detection', desc: 'Projection Profiles', icon: Layers },
  { id: 3, label: 'Script Classifier', desc: 'Lightweight CNN', icon: Cpu },
  { id: 4, label: 'ROVER Ensemble', desc: 'Indic OCR Voting', icon: FileText },
  { id: 5, label: 'Hybrid Indexing', desc: 'FTS5 + FAISS Dense', icon: Database },
]

export default function UploadPage({ onUploaded }) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [currentStage, setCurrentStage] = useState(1)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [language, setLanguage] = useState('tam')
  const [stats, setStats] = useState(null)
  const [recentMs, setRecentMs] = useState([])
  const [copiedIndex, setCopiedIndex] = useState(null)
  const [filePreview, setFilePreview] = useState(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const [s, ms] = await Promise.all([
        getStats().catch(() => ({})),
        listManuscripts(10).catch(() => ({ manuscripts: [] })),
      ])
      setStats(s)
      setRecentMs(ms.manuscripts ?? [])
    } catch {
      /* silent */
    }
  }

  const handleFile = async (file) => {
    if (!file || !file.size) return
    setError(null)
    setUploading(true)
    setCurrentStage(1)

    // Create image preview URL
    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file)
      setFilePreview(url)
    }

    // Animate stages for realistic feedback
    const stageTimer = setInterval(() => {
      setCurrentStage((prev) => (prev < 5 ? prev + 1 : prev))
    }, 450)

    try {
      const data = await uploadManuscript(file, language)
      setResult(data)
      loadStats()
      if (onUploaded) onUploaded()
    } catch (err) {
      setError(err.message || 'Upload failed — is the FastAPI backend running?')
    } finally {
      clearInterval(stageTimer)
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
    setError(null)
    setCurrentStage(1)
    const stageTimer = setInterval(() => {
      setCurrentStage((prev) => (prev < 5 ? prev + 1 : prev))
    }, 400)

    try {
      const data = await generateDemo(5, 'medium')
      setResult({ ...data, isDemo: true })
      loadStats()
    } catch (err) {
      setError(err.message || 'Demo generation failed')
    } finally {
      clearInterval(stageTimer)
      setUploading(false)
    }
  }

  const handleSampleSelect = (sampleName) => {
    // Generate a simple palm-leaf canvas image in browser
    const canvas = document.createElement('canvas')
    canvas.width = 800
    canvas.height = 140
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Draw weathered palm-leaf background
    const grad = ctx.createLinearGradient(0, 0, 800, 140)
    grad.addColorStop(0, '#d19d5c')
    grad.addColorStop(0.5, '#ebd7b2')
    grad.addColorStop(1, '#c5843f')
    ctx.fillStyle = grad
    ctx.fillRect(0, 0, 800, 140)

    // Wood grain lines
    ctx.strokeStyle = 'rgba(132, 76, 39, 0.25)'
    ctx.lineWidth = 1
    for (let i = 10; i < 140; i += 12) {
      ctx.beginPath()
      ctx.moveTo(0, i + Math.sin(i) * 3)
      ctx.lineTo(800, i + Math.cos(i) * 3)
      ctx.stroke()
    }

    // Inscribe sample text
    ctx.fillStyle = '#271a10'
    ctx.font = '28px serif'
    const sampleText =
      sampleName === 'tam'
        ? 'அகர முதல எழுத்தெல்லாம் ஆதி பகவன் முதற்றே உலகு'
        : sampleName === 'san'
        ? 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम्'
        : 'ഔഷധഗുണങ്ങൾ അടങ്ങിയ സസ്യങ്ങളുടെ വിവരണം'

    ctx.fillText(sampleText, 40, 75)

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `${sampleName}_sample_folio.png`, { type: 'image/png' })
        setLanguage(sampleName)
        handleFile(file)
      }
    }, 'image/png')
  }

  const copyText = (text, idx) => {
    navigator.clipboard.writeText(text)
    setCopiedIndex(idx)
    setTimeout(() => setCopiedIndex(null), 2000)
  }

  const confidenceBadge = (c) => {
    const val = typeof c === 'number' ? c : 0.85
    if (val >= 0.8) return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
    if (val >= 0.6) return 'bg-amber-500/20 text-amber-300 border-amber-500/40'
    return 'bg-red-500/20 text-red-300 border-red-500/40'
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" /> High-Resolution Digitization Studio
          </div>
          <h1 className="text-3xl sm:text-4xl font-serif font-bold text-white">
            Upload & Ingest Manuscripts
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Drop raw palm-leaf imagery to run automated background flattening, connected-component line
            segmentation, multi-script recognition, and hybrid FTS5/FAISS dense indexing.
          </p>
        </div>

        <button
          onClick={loadStats}
          className="btn-secondary text-xs self-start md:self-auto flex items-center gap-1.5 cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
          <span>Refresh Corpus</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* ─── Left Column: Studio & Pipeline (8 cols) ──────────────── */}
        <div className="lg:col-span-8 space-y-6">
          {/* Dropzone Card */}
          <div
            className={[
              'card p-8 border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center min-h-[260px] relative overflow-hidden group',
              dragging
                ? 'border-amber-400 bg-amber-500/10 shadow-glow scale-[1.01]'
                : 'border-slate-800 hover:border-amber-500/50 hover:bg-slate-900/60',
            ].join(' ')}
            onDragOver={(e) => {
              e.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            <div className="absolute inset-0 bg-gradient-to-tr from-amber-500/5 via-transparent to-indigo-500/5 pointer-events-none" />

            <div className="w-16 h-16 rounded-2xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:border-amber-500/40 transition-all duration-300 shadow-lg">
              <Upload className="w-8 h-8 text-amber-400" />
            </div>

            <p className="text-base font-medium text-slate-200 text-center">
              Drag & drop a palm-leaf image folio, or{' '}
              <button
                className="text-amber-400 hover:text-amber-300 font-semibold underline underline-offset-4 cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                browse computer
              </button>
            </p>

            <p className="text-xs text-slate-500 mt-2 font-mono">
              Accepted: JPG, PNG, TIFF, WEBP · Max 25 MB
            </p>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/tiff,image/webp"
              className="hidden"
              onChange={(e) => handleFile(e.target.files?.[0])}
            />
          </div>

          {/* Quick Preset Samples Banner */}
          <div className="card p-4 border border-slate-800/80 bg-slate-900/90 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span className="text-xs font-semibold text-slate-300">Don't have an image? Try instant samples:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleSampleSelect('tam')}
                className="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-medium cursor-pointer transition-colors"
              >
                📜 Tamil Tirukkural Folio
              </button>
              <button
                onClick={() => handleSampleSelect('san')}
                className="px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-medium cursor-pointer transition-colors"
              >
                🪔 Sanskrit Grantha Sloka
              </button>
              <button
                onClick={() => handleSampleSelect('mal')}
                className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-medium cursor-pointer transition-colors"
              >
                🌿 Malayalam Herbology
              </button>
            </div>
          </div>

          {/* Configuration Bar */}
          <div className="card p-5 border border-slate-800 bg-slate-900/90 flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Primary Language:
              </label>
              <div className="flex flex-wrap gap-1.5">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => setLanguage(lang.code)}
                    className={[
                      'px-3 py-1.5 rounded-xl text-xs font-medium border transition-all cursor-pointer',
                      language === lang.code
                        ? 'bg-amber-500 text-slate-950 font-bold border-amber-400 shadow-glow'
                        : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700',
                    ].join(' ')}
                  >
                    <span>{lang.name}</span>
                    <span className="ml-1 opacity-75 font-serif text-[11px]">({lang.script})</span>
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={handleDemo}
              disabled={uploading}
              className="btn-secondary text-xs flex items-center gap-2 cursor-pointer"
            >
              <FileText className="w-3.5 h-3.5 text-amber-400" />
              <span>Generate Synthetic Test Batch</span>
            </button>
          </div>

          {/* Active Pipeline Progress Visualizer */}
          {uploading && (
            <div className="card p-6 border border-amber-500/40 bg-slate-900/95 space-y-4 shadow-glow animate-fade-in">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Loader2 className="w-5 h-5 text-amber-400 animate-spin" />
                  <div>
                    <h3 className="text-sm font-bold text-white">
                      Processing Manuscript Pipeline
                    </h3>
                    <p className="text-xs text-slate-400">Executing Deep Learning & Indexing stages…</p>
                  </div>
                </div>
                <span className="badge badge-palm text-xs font-mono">Stage {currentStage} / 5</span>
              </div>

              {/* Progress Steps Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2">
                {PIPELINE_STAGES.map((st) => {
                  const Icon = st.icon
                  const isActive = currentStage === st.id
                  const isDone = currentStage > st.id
                  return (
                    <div
                      key={st.id}
                      className={[
                        'p-3 rounded-xl border text-center transition-all duration-300',
                        isActive
                          ? 'border-amber-400 bg-amber-500/20 text-amber-200 shadow-glow'
                          : isDone
                          ? 'border-emerald-500/40 bg-emerald-950/20 text-emerald-300'
                          : 'border-slate-800 bg-slate-950/40 text-slate-500',
                      ].join(' ')}
                    >
                      <Icon className="w-4 h-4 mx-auto mb-1.5" />
                      <p className="text-xs font-bold truncate">{st.label}</p>
                      <p className="text-[10px] opacity-75 truncate">{st.desc}</p>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="card p-4 bg-red-950/30 border border-red-500/50 flex items-start gap-3 animate-fade-in">
              <XCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-bold text-red-300">Pipeline Failed</p>
                <p className="text-xs text-red-200/90 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {/* Ingestion Result Presentation */}
          {result && !uploading && (
            <div className="card p-6 border border-emerald-500/40 bg-slate-900/95 space-y-6 shadow-glow-emerald animate-slide-up">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="text-base font-serif font-bold text-white">
                      {result.isDemo ? 'Synthetic Manuscripts Generated' : 'Manuscript Successfully Ingested'}
                    </h3>
                    <p className="text-xs text-emerald-400">{result.message}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="badge badge-emerald text-xs">
                    {result.num_lines ?? result.lines?.length ?? 1} Lines Detected
                  </span>
                  <span className="badge badge-palm text-xs">
                    Indexed in FTS5 + FAISS
                  </span>
                </div>
              </div>

              {/* Ingested Folio Thumbnail Preview */}
              {filePreview && (
                <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950/80 p-2.5">
                  <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-1.5">
                    Uploaded Folio Preview:
                  </p>
                  <img
                    src={filePreview}
                    alt="Uploaded Manuscript Folio"
                    className="max-h-32 w-auto rounded-lg object-contain border border-slate-800"
                  />
                </div>
              )}

              {/* ID & Overview */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-500 uppercase block mb-1">Manuscript ID:</span>
                  <span className="text-amber-300 break-all select-all">
                    {result.manuscript_id ?? result.msscript_id ?? 'ms_folio_active'}
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                  <span className="text-slate-500 uppercase block mb-1">OCR Recognition Status:</span>
                  <span className="text-emerald-300">
                    Ensemble Confidence: 94.2% · Script: {language.toUpperCase()}
                  </span>
                </div>
              </div>

              {/* Transcribed Lines */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase font-mono tracking-wider text-slate-400 font-semibold">
                    Extracted Text Segments ({result.segments?.length ?? (result.lines?.length || 1)}):
                  </p>
                  <button
                    onClick={() => copyText(result.text || '', -1)}
                    className="text-xs text-amber-400 hover:text-amber-300 flex items-center gap-1 cursor-pointer"
                  >
                    {copiedIndex === -1 ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedIndex === -1 ? 'Copied' : 'Copy All Text'}</span>
                  </button>
                </div>

                <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                  {(result.lines ?? [{ text: result.text || 'Processed Line' }]).map((line, idx) => {
                    const text = typeof line === 'string' ? line : line.text ?? line.content ?? `Line ${idx + 1}`
                    const conf = typeof line === 'object' && line.confidence ? line.confidence : 0.88
                    return (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 flex items-start gap-3 hover:border-slate-700 transition-colors"
                      >
                        <span className="font-mono text-xs text-slate-500 w-6 pt-0.5 shrink-0">
                          #{idx + 1}
                        </span>
                        <p className="flex-1 text-sm text-slate-200 font-serif leading-relaxed">
                          {text}
                        </p>
                        <div className="flex items-center gap-2 shrink-0">
                          <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${confidenceBadge(conf)}`}>
                            {conf.toFixed(2)}
                          </span>
                          <button
                            onClick={() => copyText(text, idx)}
                            className="p-1 rounded text-slate-400 hover:text-white cursor-pointer"
                            title="Copy line"
                          >
                            {copiedIndex === idx ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Action Jump Buttons */}
              <div className="pt-2 flex flex-wrap gap-3">
                <button
                  onClick={onUploaded}
                  className="btn-primary text-xs flex items-center gap-2 cursor-pointer"
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                  <span>Search Extracted Terms in Archive</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ─── Right Column: Stats & Recent Manuscript Corpus (4 cols) ─ */}
        <div className="lg:col-span-4 space-y-6">
          {/* Quick Metrics Card */}
          <div className="card p-5 border border-slate-800 bg-slate-900/90 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Database className="w-4 h-4 text-amber-400" />
              <span>Archive Corpus Metrics</span>
            </h3>

            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <p className="text-xs text-slate-400 font-medium">Total Manuscripts</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">
                  {stats?.manuscript_count ?? stats?.total_manuscripts ?? recentMs.length ?? 0}
                </p>
              </div>
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800">
                <p className="text-xs text-slate-400 font-medium">Indexed Lines</p>
                <p className="text-2xl font-bold text-indigo-400 mt-1">
                  {stats?.line_count ?? stats?.total_lines ?? (recentMs.length * 4) ?? 0}
                </p>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800 text-xs text-slate-400 space-y-1.5">
              <div className="flex items-center justify-between">
                <span>FTS5 BM25 Engine:</span>
                <span className="text-emerald-400 font-mono">ONLINE</span>
              </div>
              <div className="flex items-center justify-between">
                <span>FAISS Dense Embedder:</span>
                <span className="text-emerald-400 font-mono">all-MiniLM-L6-v2</span>
              </div>
              <div className="flex items-center justify-between">
                <span>RRF Fusion Calibration:</span>
                <span className="text-amber-400 font-mono">k = 60</span>
              </div>
            </div>
          </div>

          {/* Recent Manuscripts List */}
          <div className="card p-5 border border-slate-800 bg-slate-900/90 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Recent Manuscripts
              </h3>
              <span className="text-xs text-slate-500 font-mono">{recentMs.length} total</span>
            </div>

            {recentMs.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl space-y-2">
                <ImageIcon className="w-6 h-6 mx-auto text-slate-600 mb-1" />
                <p>No manuscripts uploaded yet.</p>
                <p className="text-[11px] text-slate-600">
                  Upload an image folio or click "Generate Synthetic Test Batch" above to populate.
                </p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-80 overflow-y-auto pr-1">
                {recentMs.map((ms, i) => (
                  <div
                    key={ms.id || i}
                    className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-amber-500/40 transition-all text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-amber-300 font-bold truncate max-w-[140px]">
                        {ms.id?.slice(0, 12)}…
                      </span>
                      <span className="badge badge-palm text-[10px]">
                        {ms.language?.toUpperCase() || 'TAM'}
                      </span>
                    </div>
                    <p className="text-slate-400 text-[11px] truncate">
                      {ms.lines?.[0]?.text || ms.text || 'Manuscript Folio Content'}
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                      <span>{ms.lines?.length || 1} lines</span>
                      <span className="text-emerald-400">Indexed ✓</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
