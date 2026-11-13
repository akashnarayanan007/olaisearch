import { useState, useEffect } from 'react'
import {
  BarChart3,
  ExternalLink,
  Github,
  Leaf,
  Menu,
  MessageSquare,
  Search,
  Sparkles,
  Upload,
  X,
} from 'lucide-react'

import LandingPage from './pages/LandingPage'
import UploadPage from './pages/UploadPage'
import SearchPage from './pages/SearchPage'
import ChatPage from './pages/ChatPage'
import AnalyticsPage from './pages/AnalyticsPage'
import { healthCheck } from './api/client'

const NAV_TABS = [
  { key: 'home', label: 'Overview', icon: Sparkles },
  { key: 'upload', label: 'Digitize Studio', icon: Upload },
  { key: 'search', label: 'Hybrid Search', icon: Search },
  { key: 'chat', label: 'ManuscriptChat', icon: MessageSquare },
  { key: 'analytics', label: 'Analytics', icon: BarChart3 },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('home')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [apiStatus, setApiStatus] = useState('checking')

  useEffect(() => {
    let isMounted = true
    const checkApi = async () => {
      try {
        const res = await healthCheck()
        if (isMounted) setApiStatus(res?.status === 'healthy' ? 'online' : 'degraded')
      } catch {
        if (isMounted) setApiStatus('offline')
      }
    }
    checkApi()
    const interval = setInterval(checkApi, 25000)
    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [])

  const PAGE_MAP = {
    home: <LandingPage onNavigate={(tab) => setActiveTab(tab)} />,
    upload: <UploadPage onUploaded={() => setActiveTab('search')} />,
    search: <SearchPage />,
    chat: <ChatPage />,
    analytics: <AnalyticsPage />,
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 bg-mesh-pattern">
      {/* ─── Top Global Announcement Banner ─────────────────────── */}
      <div className="bg-gradient-to-r from-amber-600/20 via-saffron-500/20 to-indigo-600/20 border-b border-amber-500/20 px-4 py-1.5 text-center text-xs text-amber-200/90 font-medium">
        <span className="font-semibold text-amber-300">OlaiSearch Research Platform:</span> Multilingual Palm-Leaf OCR, FAISS Semantic Dense Retrieval, and 3-Tier Grounded Q&A
      </div>

      {/* ─── Sticky Header Navbar ────────────────────────────────── */}
      <header className="bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Brand */}
            <button
              onClick={() => setActiveTab('home')}
              className="flex items-center gap-3 text-left group cursor-pointer focus:outline-none"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-saffron-400 p-0.5 shadow-glow transition-transform group-hover:scale-105">
                <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                  <Leaf className="w-5 h-5 text-amber-400" />
                </div>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-serif font-bold text-white tracking-wide">OlaiSearch</span>
                  <span className="text-[10px] font-mono font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2 py-0.5 rounded-full">
                    v0.3.0
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 hidden sm:block">Palm-Leaf Manuscript AI Platform</p>
              </div>
            </button>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-1.5 p-1 bg-slate-900/80 border border-slate-800/80 rounded-2xl backdrop-blur-lg">
              {NAV_TABS.map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={[
                    'flex items-center gap-2 px-3.5 py-1.5 text-xs font-semibold rounded-xl transition-all duration-200 cursor-pointer',
                    activeTab === key
                      ? 'bg-gradient-to-r from-amber-500 to-saffron-500 text-slate-950 shadow-glow font-bold'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/80',
                  ].join(' ')}
                >
                  <Icon className={`w-3.5 h-3.5 ${activeTab === key ? 'text-slate-950' : 'text-slate-400'}`} />
                  {label}
                </button>
              ))}
            </nav>

            {/* Right Status & GitHub Link */}
            <div className="hidden sm:flex items-center gap-3">
              {/* API Status indicator */}
              <div
                className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px]"
                title={`FastAPI backend status: ${apiStatus}`}
              >
                <span className={`w-2 h-2 rounded-full ${
                  apiStatus === 'online' ? 'bg-emerald-400 animate-pulse' :
                  apiStatus === 'checking' ? 'bg-amber-400' : 'bg-red-400'
                }`} />
                <span className="text-slate-300 font-mono text-[10px] uppercase">
                  API: {apiStatus}
                </span>
              </div>

              {/* GitHub Button */}
              <a
                href="https://github.com/akashnarayanan007/olaisearch"
                target="_blank"
                rel="noreferrer"
                className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-2 cursor-pointer hover:border-slate-600"
              >
                <Github className="w-4 h-4 text-slate-300" />
                <span>GitHub</span>
                <span className="bg-slate-800 text-amber-300 text-[10px] px-1.5 py-0.2 rounded font-mono">
                  ★ Star
                </span>
              </a>
            </div>

            {/* Mobile menu toggle */}
            <button
              className="md:hidden p-2 text-slate-400 hover:text-white"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle navigation menu"
            >
              {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden border-t border-slate-800 bg-slate-950/95 backdrop-blur-xl px-4 py-3 space-y-1">
            {NAV_TABS.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => {
                  setActiveTab(key)
                  setMobileOpen(false)
                }}
                className={[
                  'w-full flex items-center gap-3 px-3.5 py-2.5 text-sm rounded-xl font-medium transition-colors text-left',
                  activeTab === key
                    ? 'bg-amber-500 text-slate-950 font-bold'
                    : 'text-slate-300 hover:bg-slate-900',
                ].join(' ')}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}

            <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
              <span className="text-xs text-slate-400 flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${apiStatus === 'online' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                API {apiStatus}
              </span>
              <a
                href="https://github.com/akashnarayanan007/olaisearch"
                target="_blank"
                rel="noreferrer"
                className="text-xs text-amber-400 flex items-center gap-1 font-semibold"
              >
                View on GitHub <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        )}
      </header>

      {/* ─── Main Content Canvas ─────────────────────────────────── */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {PAGE_MAP[activeTab]}
      </main>

      {/* ─── Modern Professional Footer ─────────────────────────── */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 backdrop-blur-md mt-16 py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8 text-sm">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Leaf className="w-5 h-5 text-amber-400" />
                <span className="text-lg font-serif font-bold text-white">OlaiSearch</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Open-source palm-leaf manuscript preservation platform combining image restoration,
                deep learning script identification, ensemble OCR, and verifiable RRF hybrid search.
              </p>
            </div>

            <div>
              <p className="text-xs uppercase font-mono font-bold text-amber-400 tracking-wider mb-3">
                Core Engines
              </p>
              <ul className="space-y-2 text-xs text-slate-400">
                <li>• CLAHE & Sauvola Adaptive Restoration</li>
                <li>• Projection Profile Line Segmentation</li>
                <li>• PyTorch Lightweight Script Classifier</li>
                <li>• Tesseract Indic + VLM + ROVER Voting</li>
              </ul>
            </div>

            <div>
              <p className="text-xs uppercase font-mono font-bold text-amber-400 tracking-wider mb-3">
                Retrieval & Chat
              </p>
              <ul className="space-y-2 text-xs text-slate-400">
                <li>• SQLite FTS5 (BM25 + Phonetic)</li>
                <li>• FAISS Dense Semantic Embeddings</li>
                <li>• Reciprocal Rank Fusion (k=60)</li>
                <li>• Three-Tier Citation Verification</li>
              </ul>
            </div>

            <div>
              <p className="text-xs uppercase font-mono font-bold text-amber-400 tracking-wider mb-3">
                Languages & Scripts
              </p>
              <div className="flex flex-wrap gap-1.5">
                {['Tamil', 'Malayalam', 'Sanskrit', 'Grantha', 'Vatteluttu', 'Devanagari', 'ISO 15919'].map((s) => (
                  <span key={s} className="px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-6 border-t border-slate-900 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
            <p>© {new Date().getFullYear()} OlaiSearch Contributors · Published under MIT License</p>
            <div className="flex items-center gap-4">
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="hover:text-amber-300 transition-colors">
                FastAPI Swagger Docs
              </a>
              <span className="text-slate-800">•</span>
              <button onClick={() => setActiveTab('analytics')} className="hover:text-amber-300 transition-colors">
                System Health
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
