import React, { useState } from 'react'
import {
  Upload, Search, MessageSquare, BarChart3, Leaf, Menu, X,
} from 'lucide-react'

import UploadPage from './pages/UploadPage'
import SearchPage from './pages/SearchPage'
import ChatPage from './pages/ChatPage'
import AnalyticsPage from './pages/AnalyticsPage'

const NAV_TABS = [
  { key: 'upload', label: 'Upload', icon: Upload },
  { key: 'search', label: 'Search', icon: Search },
  { key: 'chat', label: 'Chat', icon: MessageSquare },
  { key: 'analytics', label: 'Analytics', icon: BarChart3 },
]

export default function App() {
  const [activeTab, setActiveTab] = useState('upload')
  const [mobileOpen, setMobileOpen] = useState(false)

  const PAGE_MAP = {
    upload: <UploadPage onUploaded={() => setActiveTab('search')} />,
    search: <SearchPage />,
    chat: <ChatPage />,
    analytics: <AnalyticsPage />,
  }

  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      {/* ─── Header ───────────────────────────────────────────── */}
      <header className="bg-white border-b border-stone-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <button
              onClick={() => setActiveTab('upload')}
              className="flex items-center gap-2.5 text-palm-800 font-serif text-lg cursor-pointer"
            >
              <Leaf className="w-5 h-5 text-palm-600" />
              <span>OlaiSearch</span>
              <span className="text-xs font-sans font-normal text-stone-400 bg-stone-100 px-1.5 py-0.5 rounded">
                v0.3
              </span>
            </button>

            {/* Desktop nav */}
            <nav className="hidden md:flex items-center gap-1">
              {NAV_TABS.map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={[
                    'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-md transition-colors',
                    activeTab === key
                      ? 'bg-palm-100 text-palm-800 font-medium'
                      : 'text-stone-600 hover:bg-stone-100 hover:text-stone-900',
                  ].join(' ')}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </button>
              ))}
            </nav>

            {/* Mobile menu button */}
            <button
              className="md:hidden p-2 text-stone-500"
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile nav */}
        {mobileOpen && (
          <div className="md:hidden border-t border-stone-200 bg-white pb-2">
            {NAV_TABS.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                className={[
                  'w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors text-left',
                  activeTab === key
                    ? 'bg-palm-50 text-palm-800'
                    : 'text-stone-600 hover:bg-stone-50',
                ].join(' ')}
                onClick={() => { setActiveTab(key); setMobileOpen(false) }}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>
        )}
      </header>

      {/* ─── Main content ─────────────────────────────────────── */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {PAGE_MAP[activeTab]}
      </main>

      {/* ─── Footer ───────────────────────────────────────────── */}
      <footer className="border-t border-stone-200 bg-white py-4">
        <div className="max-w-7xl mx-auto px-4 text-xs text-stone-400 flex flex-col sm:flex-row justify-between gap-1">
          <span>OlaiSearch — Palm-Leaf Manuscript Digitization Platform</span>
          <span className="font-mono">SQLite FTS5 · FAISS Dense · RRF Fusion</span>
        </div>
      </footer>
    </div>
  )
}
