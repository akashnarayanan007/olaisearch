/**
 * ManuscriptViewer — zoomable image with bounding-box overlays.
 *
 * Renders a uploaded/manuscript image with optional detection boxes
 * drawn as an SVG overlay (no external library dependency).
 */
import React, { useState, useRef, useCallback } from 'react'
import { ZoomIn, ZoomOut, Maximize, RotateCw, Info } from 'lucide-react'

export default function ManuscriptViewer({ imageSrc, lines, loading }) {
  const containerRef = useRef(null)
  const [scale, setScale] = useState(1)
  const [origin, setOrigin] = useState({ x: 0, y: 0 })
  const [dragging, setDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [selectedLine, setSelectedLine] = useState(null)

  // Pan handler
  const handleMouseDown = useCallback((e) => {
    if (e.button !== 0) return
    setDragging(true)
    setDragStart({ x: e.clientX - origin.x, y: e.clientY - origin.y })
  }, [origin])

  const handleMouseMove = useCallback((e) => {
    if (!dragging) return
    e.preventDefault()
    setOrigin({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    })
  }, [dragging, dragStart])

  const handleMouseUp = useCallback(() => setDragging(false), [])

  const zoom = (delta) => {
    setScale((s) => Math.min(5, Math.max(0.2, s + delta)))
  }

  const reset = () => {
    setScale(1)
    setOrigin({ x: 0, y: 0 })
    setSelectedLine(null)
  }

  return (
    <div className="card overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-stone-100 bg-stone-50">
        <button onClick={() => zoom(-0.2)} className="p-1 hover:bg-stone-200 rounded" title="Zoom out">
          <ZoomIn className="w-4 h-4 text-stone-600 rotate-180" />
        </button>
        <button onClick={() => zoom(0.2)} className="p-1 hover:bg-stone-200 rounded" title="Zoom in">
          <ZoomIn className="w-4 h-4 text-stone-600" />
        </button>
        <span className="text-xs text-stone-400 w-12 text-center font-mono">
          {(scale * 100).toFixed(0)}%
        </span>
        <button onClick={reset} className="p-1 hover:bg-stone-200 rounded ml-auto" title="Reset view">
          <RotateCw className="w-4 h-4 text-stone-600" />
        </button>
        {lines?.length > 0 && (
          <span className="text-xs text-stone-400 flex items-center gap-1">
            <Info className="w-3 h-3" />
            {lines.length} line{lines.length !== 1 ? 's' : ''} detected
          </span>
        )}
      </div>

      {/* Canvas area */}
      <div
        ref={containerRef}
        className="zoom-container relative h-96 overflow-hidden"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-stone-100">
            <div className="text-center text-sm text-stone-400 space-y-2">
              <div className="w-8 h-8 border-2 border-palm-300 border-t-palm-600 rounded-full animate-spin mx-auto" />
              <p>Processing…</p>
            </div>
          </div>
        ) : imageSrc ? (
          <div
            className="origin-top-left transition-transform duration-75"
            style={{
              transform: `scale(${scale}) translate(${origin.x / scale}px, ${origin.y / scale}px)`,
            }}
          >
            <img
              src={imageSrc}
              alt="Manuscript"
              className="max-w-none block"
              style={{ maxWidth: '100%', userSelect: 'none' }}
            />
            {/* Bounding box overlay */}
            {lines && (
              <BBoxOverlay
                lines={lines}
                imageW={getImageWidth(containerRef)}
                imageH={getImageHeight(containerRef)}
                selected={selectedLine}
                onSelect={setSelectedLine}
              />
            )}
          </div>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-stone-300 text-sm">
            No image loaded
          </div>
        )}
      </div>

      {/* Line list */}
      {lines?.length > 0 && (
        <div className="border-t border-stone-100 max-h-40 overflow-y-auto">
          {lines.map((line, i) => (
            <button
              key={i}
              onClick={() => setSelectedLine(selectedLine === i ? null : i)}
              className={[
                'w-full text-left px-4 py-2 text-xs flex items-center gap-2 transition-colors',
                selectedLine === i ? 'bg-palm-50 border-l-2 border-palm-500' : 'hover:bg-stone-50',
              ].join(' ')}
            >
              <span className="text-stone-400 font-mono w-4">{i + 1}</span>
              <span className="flex-1 truncate text-stone-600">{line.text ?? line.content ?? ''}</span>
              <span className={`font-mono ${
                (line.confidence ?? 0.8) >= 0.8 ? 'text-emerald-600'
                : (line.confidence ?? 0.8) >= 0.5 ? 'text-amber-600'
                : 'text-red-500'
              }`}>
                {(line.confidence ?? 0.8).toFixed(2)}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function BBoxOverlay({ lines, imageW, imageH, selected, onSelect }) {
  if (!lines || lines.length === 0 || !imageW) return null
  const ratioX = imageW / imageW
  const ratioY = imageH / imageH

  return (
    <svg
      className="absolute inset-0 pointer-events-auto"
      width={imageW}
      height={imageH}
    >
      {lines.map((line, i) => {
        const cx = line.x ?? 0
        const cy = line.y ?? 0
        const cw = line.width ?? 200
        const ch = line.height ?? 30
        const isSelected = selected === i
        return (
          <rect
            key={i}
            x={cx}
            y={cy}
            width={cw}
            height={ch}
            fill={isSelected ? 'rgba(168,115,72,0.3)' : 'rgba(168,115,72,0.08)'}
            stroke={isSelected ? '#a87348' : 'rgba(168,115,72,0.5)'}
            strokeWidth={isSelected ? 2 : 1}
            className="cursor-pointer transition-all hover:opacity-80"
            onClick={() => onSelect(isSelected ? null : i)}
          />
        )
      })}
    </svg>
  )
}

// Helpers to read image dimensions from DOM — simplified for demo
function getImageWidth(container) {
  if (!container?.current) return 0
  const img = container.current.querySelector('img')
  return img?.naturalWidth ?? container.current.offsetWidth
}
function getImageHeight(container) {
  if (!container?.current) return 0
  const img = container.current.querySelector('img')
  return img?.naturalHeight ?? container.current.offsetHeight
}
