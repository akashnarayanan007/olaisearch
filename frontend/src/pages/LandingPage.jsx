import {
  ArrowRight,
  BarChart3,
  BookOpen,
  CheckCircle2,
  Cpu,
  Database,
  Feather,
  Globe,
  Layers,
  MessageSquare,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
  Zap,
} from 'lucide-react'

const PIPELINE_STEPS = [
  {
    step: '01',
    title: 'Adaptive Restoration',
    tech: 'CLAHE · Sauvola · Flattening',
    desc: 'Compensates for age degradation, wood grain ink absorption, and background stains.',
    color: 'from-amber-500/20 to-amber-600/10 border-amber-500/30 text-amber-400',
    icon: Sparkles,
  },
  {
    step: '02',
    title: 'Projection Profile Segmentation',
    tech: 'Connected Components · CC Analysis',
    desc: 'Extracts irregular horizontal palm-leaf text lines while preserving reading order.',
    color: 'from-orange-500/20 to-orange-600/10 border-orange-500/30 text-orange-400',
    icon: Layers,
  },
  {
    step: '03',
    title: 'Script Identification',
    tech: 'PyTorch CNN · Unicode Heuristics',
    desc: 'Accurately classifies script between Tamil, Malayalam, Sanskrit, and mixed scripts.',
    color: 'from-yellow-500/20 to-yellow-600/10 border-yellow-500/30 text-yellow-400',
    icon: Globe,
  },
  {
    step: '04',
    title: 'Ensemble OCR & Voting',
    tech: 'Tesseract Indic + VLM + ROVER',
    desc: 'Combines multiple recognition hypotheses via confidence-weighted ROVER voting.',
    color: 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30 text-emerald-400',
    icon: Cpu,
  },
  {
    step: '05',
    title: 'Philological Post-Correction',
    tech: 'ISO 15919 · NER · Date Normalizer',
    desc: 'Corrects OCR errors via historical lexicons, resolves Saka/Kali dates, extracts entities.',
    color: 'from-teal-500/20 to-teal-600/10 border-teal-500/30 text-teal-400',
    icon: Feather,
  },
  {
    step: '06',
    title: 'Quad-Index Hybrid Retrieval',
    tech: 'FTS5 + Char N-grams + Phonetic + FAISS',
    desc: 'Handles fragmented, smudged, or partially decayed words through multi-tier indexing.',
    color: 'from-indigo-500/20 to-indigo-600/10 border-indigo-500/30 text-indigo-400',
    icon: Database,
  },
  {
    step: '07',
    title: 'Reciprocal Rank Fusion (RRF)',
    tech: 'RRF (k=60) Fusion Algorithm',
    desc: 'Merges sparse and dense search results into unified, calibration-free relevancy ranks.',
    color: 'from-violet-500/20 to-violet-600/10 border-violet-500/30 text-violet-400',
    icon: Zap,
  },
  {
    step: '08',
    title: '3-Tier Evidence Grounding',
    tech: 'CitationVerifier · Strict Attribution',
    desc: 'Q&A answers categorized into Leaf Manuscript, Archive Corpus, and Background Knowledge.',
    color: 'from-rose-500/20 to-rose-600/10 border-rose-500/30 text-rose-400',
    icon: ShieldCheck,
  },
]

const SAMPLE_MANUSCRIPTS = [
  {
    title: 'Tirukkural Palm-Leaf Folio',
    script: 'Tamil (Grantha mix)',
    era: 'c. 17th Century CE',
    lines: 6,
    sampleText: 'அகர முதல எழுத்தெல்லாம் ஆதி பகவன் முதற்றே உலகு...',
    translation: 'A is the first of all letters; likewise, the Primeval God is foremost in the universe.',
    badge: 'Popular Classic',
    gradient: 'from-amber-950/60 to-slate-900 border-amber-500/40 text-amber-300',
  },
  {
    title: 'Ayurvedic Medical Herbology Folio',
    script: 'Malayalam (Kolezhuthu influence)',
    era: 'c. 18th Century CE',
    lines: 8,
    sampleText: 'ഔഷധഗുണങ്ങൾ അടങ്ങിയ സസ്യങ്ങളുടെ വിവരണം...',
    translation: 'Treatise detailing medicinal plant concoctions, decoction preparation, and leaf remedies.',
    badge: 'Herbal Medicine',
    gradient: 'from-emerald-950/60 to-slate-900 border-emerald-500/40 text-emerald-300',
  },
  {
    title: 'Rigvedic Hymn Grantha Folio',
    script: 'Sanskrit (Grantha/Devanagari)',
    era: 'c. 16th Century CE',
    lines: 5,
    sampleText: 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजम् । होतारं रत्नधातमम् ॥',
    translation: 'I laud Agni, the chosen priest, god, minister of sacrifice, the hotar, greatest dispenser of treasures.',
    badge: 'Vedic Sanskrit',
    gradient: 'from-indigo-950/60 to-slate-900 border-indigo-500/40 text-indigo-300',
  },
]

export default function LandingPage({ onNavigate }) {
  return (
    <div className="space-y-24 py-4">
      {/* ─── Hero Section ────────────────────────────────────────────── */}
      <section className="relative overflow-hidden pt-8 pb-16">
        {/* Ambient background glows */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-5xl h-96 bg-gradient-to-tr from-amber-500/20 via-saffron-500/15 to-indigo-600/20 blur-3xl rounded-full pointer-events-none -z-10" />
        <div className="absolute top-1/3 -right-20 w-80 h-80 bg-violet-600/15 blur-3xl rounded-full pointer-events-none -z-10" />

        <div className="text-center max-w-4xl mx-auto space-y-6">
          {/* Top pill badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-900/90 border border-amber-500/40 text-xs font-medium text-amber-300 shadow-glow backdrop-blur-md animate-fade-in">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
            </span>
            <span>OlaiSearch v0.3 · Production Palm-Leaf Manuscript Digitization Platform</span>
            <span className="bg-amber-500/20 text-amber-200 text-[10px] font-mono px-2 py-0.5 rounded-full border border-amber-500/30">
              Open Source
            </span>
          </div>

          {/* Main heading with radiant gradient */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-serif font-extrabold tracking-tight text-white leading-tight">
            Digitize & Query{' '}
            <span className="bg-gradient-to-r from-amber-300 via-saffron-400 to-amber-500 bg-clip-text text-transparent">
              Palm-Leaf Manuscripts
            </span>{' '}
            with Multilingual AI
          </h1>

          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto font-normal leading-relaxed">
            Preserve centuries of fragile heritage across <span className="text-amber-300 font-semibold">Tamil</span>,{' '}
            <span className="text-emerald-300 font-semibold">Malayalam</span>, and{' '}
            <span className="text-indigo-300 font-semibold">Sanskrit</span>. Featuring adaptive restoration, ensemble OCR,
            quad-index hybrid retrieval, and three-tier verified research chat.
          </p>

          {/* CTA Action Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <button
              onClick={() => onNavigate('upload')}
              className="btn-primary text-base px-7 py-3 shadow-glow-lg flex items-center gap-2.5 cursor-pointer"
            >
              <Upload className="w-5 h-5 text-slate-950" />
              <span>Launch Digitization Studio</span>
              <ArrowRight className="w-4 h-4 text-slate-950" />
            </button>

            <button
              onClick={() => onNavigate('search')}
              className="btn-secondary text-base px-6 py-3 flex items-center gap-2 cursor-pointer"
            >
              <Search className="w-4 h-4 text-amber-400" />
              <span>Explore Hybrid Search</span>
            </button>

            <button
              onClick={() => onNavigate('chat')}
              className="btn-ai text-base px-6 py-3 flex items-center gap-2 cursor-pointer"
            >
              <MessageSquare className="w-4 h-4 text-white" />
              <span>Ask ManuscriptChat</span>
            </button>
          </div>

          {/* Tech stack pills bar */}
          <div className="pt-8 flex flex-wrap items-center justify-center gap-2 sm:gap-4 text-xs text-slate-400">
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/60 border border-slate-800">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> SQLite FTS5 (BM25 + N-Grams)
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/60 border border-slate-800">
              <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" /> FAISS Dense Embeddings
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/60 border border-slate-800">
              <CheckCircle2 className="w-3.5 h-3.5 text-amber-400" /> ROVER Confidence Voting
            </span>
            <span className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/60 border border-slate-800">
              <CheckCircle2 className="w-3.5 h-3.5 text-rose-400" /> Three-Tier Evidence Verification
            </span>
          </div>
        </div>
      </section>

      {/* ─── Highlights Stats Counters ─────────────────────────────────── */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Supported Scripts', val: 'Tamil · Malayalam · Sanskrit', desc: 'Grantha & Devanagari extensions', icon: Globe, color: 'text-amber-400 border-amber-500/30' },
          { label: 'Retrieval Engine', val: '4-Way Hybrid Search', desc: 'BM25 + N-gram + Phonetic + Dense', icon: Zap, color: 'text-indigo-400 border-indigo-500/30' },
          { label: 'Grounding Reliability', val: '100% Attributed Citations', desc: 'Hallucination-resistant verification', icon: ShieldCheck, color: 'text-emerald-400 border-emerald-500/30' },
          { label: 'Query Latency', val: '< 35 ms Average', desc: 'Sub-second real-time indexing & search', icon: Cpu, color: 'text-saffron-400 border-saffron-500/30' },
        ].map(({ label, val, desc, icon: Icon, color }) => (
          <div key={label} className="card p-5 border border-slate-800 bg-slate-900/80 relative overflow-hidden group hover:border-amber-500/40 transition-all duration-300">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs uppercase tracking-wider text-slate-400 font-medium">{label}</p>
              <div className={`p-2 rounded-lg bg-slate-800/80 border ${color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <p className="text-lg font-bold text-white mb-1">{val}</p>
            <p className="text-xs text-slate-400">{desc}</p>
          </div>
        ))}
      </section>

      {/* ─── Interactive Pipeline Architecture ───────────────────────────── */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold">
            <Layers className="w-3.5 h-3.5" /> Complete Machine Learning Pipeline
          </div>
          <h2 className="text-3xl sm:text-4xl font-serif font-bold text-white">
            From Weathered Palm Leaves to Structured Knowledge
          </h2>
          <p className="text-sm text-slate-400">
            An end-to-end philological AI pipeline specifically tuned for physical manuscript degradation,
            ink fading, holes, and ancient cursive ligatures.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {PIPELINE_STEPS.map(({ step, title, tech, desc, color, icon: Icon }) => (
            <div
              key={step}
              className={`card p-5 border bg-gradient-to-b ${color} hover:-translate-y-1 transition-all duration-300 group flex flex-col justify-between`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs font-bold text-slate-500 group-hover:text-amber-400 transition-colors">
                    STAGE {step}
                  </span>
                  <div className="p-2 rounded-lg bg-slate-900/90 border border-slate-700/60 shadow-sm">
                    <Icon className="w-4 h-4" />
                  </div>
                </div>
                <h3 className="text-base font-bold text-white mb-1 group-hover:text-amber-200 transition-colors">
                  {title}
                </h3>
                <p className="text-[11px] font-mono text-amber-400/90 mb-2">
                  {tech}
                </p>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Sample Manuscripts Showcase ─────────────────────────────────── */}
      <section className="card p-8 border border-slate-800 bg-gradient-to-b from-slate-900/90 to-slate-950 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold mb-2">
              <BookOpen className="w-3.5 h-3.5" /> Curated Ancient Folios
            </div>
            <h2 className="text-2xl sm:text-3xl font-serif font-bold text-white">
              Try Ready-To-Process Manuscripts
            </h2>
            <p className="text-xs sm:text-sm text-slate-400">
              No manuscript images handy? Jump straight into recognition and indexing with historical samples.
            </p>
          </div>
          <button
            onClick={() => onNavigate('upload')}
            className="btn-primary self-start sm:self-auto cursor-pointer text-xs"
          >
            Open Upload Studio →
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {SAMPLE_MANUSCRIPTS.map((ms) => (
            <div
              key={ms.title}
              className={`p-5 rounded-2xl border bg-gradient-to-br ${ms.gradient} flex flex-col justify-between space-y-4 hover:border-amber-400/60 transition-all duration-300`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="badge badge-palm text-[10px]">{ms.badge}</span>
                  <span className="text-[11px] font-mono text-slate-400">{ms.era}</span>
                </div>
                <div>
                  <h3 className="text-lg font-serif font-bold text-white">{ms.title}</h3>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">{ms.script} · {ms.lines} lines</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1.5">
                  <p className="text-xs text-amber-200 font-serif leading-relaxed line-clamp-2">
                    "{ms.sampleText}"
                  </p>
                  <p className="text-[11px] text-slate-400 italic line-clamp-2">
                    {ms.translation}
                  </p>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <button
                  onClick={() => onNavigate('upload')}
                  className="text-xs font-semibold text-amber-400 hover:text-amber-300 flex items-center gap-1 cursor-pointer"
                >
                  Analyze Folio <ArrowRight className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={() => onNavigate('search')}
                  className="text-xs text-slate-400 hover:text-white transition-colors cursor-pointer"
                >
                  Search Similar
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Evidence-Grounded Manuscript Chat Demo ──────────────────────── */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        <div className="lg:col-span-5 space-y-4">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" /> Three-Tier Evidence Verification
          </div>
          <h2 className="text-3xl font-serif font-bold text-white">
            Trustworthy Philological AI with Verifiable Citations
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed">
            Standard LLMs hallucinate ancient text translations and attribute non-existent verses. OlaiSearch
            implements strict three-tier evidence grounding:
          </p>

          <div className="space-y-3 pt-2">
            <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-950/20 text-emerald-200 text-xs flex items-start gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 mt-1 shrink-0" />
              <div>
                <strong className="block text-emerald-300 font-semibold mb-0.5">TIER 1: MANUSCRIPT LEAF</strong>
                Directly visible, verified line transcription extracted from the physical leaf.
              </div>
            </div>
            <div className="p-3.5 rounded-xl border border-sky-500/30 bg-sky-950/20 text-sky-200 text-xs flex items-start gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-400 mt-1 shrink-0" />
              <div>
                <strong className="block text-sky-300 font-semibold mb-0.5">TIER 2: ARCHIVE CORPUS</strong>
                Matching passages from the broader palm-leaf manuscript database.
              </div>
            </div>
            <div className="p-3.5 rounded-xl border border-purple-500/30 bg-purple-950/20 text-purple-200 text-xs flex items-start gap-3">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-400 mt-1 shrink-0" />
              <div>
                <strong className="block text-purple-300 font-semibold mb-0.5">TIER 3: HISTORICAL BACKGROUND</strong>
                Lexical commentaries, era chronologies, and philological context.
              </div>
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={() => onNavigate('chat')}
              className="btn-ai cursor-pointer flex items-center gap-2"
            >
              <MessageSquare className="w-4 h-4" />
              <span>Open Research Chat Assistant</span>
            </button>
          </div>
        </div>

        {/* Mock Chat Preview UI */}
        <div className="lg:col-span-7 card p-5 border border-slate-800 bg-slate-900/95 space-y-4 shadow-glass">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-semibold text-white">ManuscriptChat Session</span>
              <span className="text-[10px] font-mono bg-slate-800 text-amber-300 px-2 py-0.5 rounded border border-slate-700">
                Mode: Leaf Grounded
              </span>
            </div>
            <span className="text-[11px] text-slate-400">CitationVerifier: Active (1.00)</span>
          </div>

          {/* User query */}
          <div className="flex items-start gap-3 justify-end">
            <div className="bg-amber-500/20 border border-amber-500/40 text-amber-100 p-3 rounded-2xl rounded-tr-none text-xs max-w-md">
              What does Line 1 state regarding the initial invocation or deity?
            </div>
            <div className="w-7 h-7 rounded-full bg-amber-600 flex items-center justify-center text-xs font-bold text-slate-950 shrink-0">
              U
            </div>
          </div>

          {/* Assistant response */}
          <div className="flex items-start gap-3">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-indigo-500 to-amber-500 flex items-center justify-center text-xs font-bold text-white shrink-0">
              AI
            </div>
            <div className="space-y-2.5 flex-1 text-xs">
              <div className="bg-slate-800/80 border border-slate-700/80 p-3.5 rounded-2xl rounded-tl-none text-slate-200 space-y-2">
                <p>
                  According to the primary palm-leaf transcription, Line 1 contains the foundational invocation:
                </p>
                <div className="p-2 rounded bg-slate-950/80 border-l-2 border-emerald-400 text-emerald-200 font-serif">
                  "அகர முதல எழுத்தெல்லாம் ஆதி பகவன் முதற்றே உலகு"
                </div>
                <p className="text-slate-300">
                  It establishes the philosophical premise comparing the letter 'A' as the primordial phonetic root to the Supreme entity as the origin of existence.
                </p>
              </div>

              {/* Citations cards */}
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="p-2 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-emerald-300">
                  <span className="font-bold block text-[10px] uppercase text-emerald-400">Verified Citation #1</span>
                  Folio Line 1 · Confidence: 0.94
                </div>
                <div className="p-2 rounded-xl bg-sky-950/30 border border-sky-500/40 text-sky-300">
                  <span className="font-bold block text-[10px] uppercase text-sky-400">Corpus Match #2</span>
                  Tirukkural Chapter 1 (Kadavul Vazhthu)
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Bottom CTA Bar ─────────────────────────────────────────── */}
      <section className="card p-10 text-center bg-gradient-to-r from-amber-950/40 via-slate-900 to-indigo-950/40 border border-amber-500/30 space-y-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/10 blur-3xl pointer-events-none rounded-full" />
        <div className="space-y-3 max-w-xl mx-auto">
          <h2 className="text-3xl font-serif font-bold text-white">
            Ready to Digitize Historical Manuscripts?
          </h2>
          <p className="text-sm text-slate-300">
            Start processing folios, running cross-lingual fuzzy searches, and inspecting philological metrics in seconds.
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <button
            onClick={() => onNavigate('upload')}
            className="btn-primary text-base px-8 py-3 shadow-glow cursor-pointer"
          >
            Start Ingesting Manuscripts →
          </button>
          <button
            onClick={() => onNavigate('analytics')}
            className="btn-secondary text-base px-6 py-3 cursor-pointer"
          >
            <BarChart3 className="w-4 h-4 text-amber-400" />
            <span>View System Analytics</span>
          </button>
        </div>
      </section>
    </div>
  )
}

