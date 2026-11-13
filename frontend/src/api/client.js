/**
 * OlaiSearch API Client
 *
 * Wraps the FastAPI backend with typed request/response helpers.
 * Falls back gracefully when the server is unreachable.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ─── HTTP helpers ──────────────────────────────────────────────────────────────

export async function uploadManuscript(file, language = 'tam', script = null) {
  const form = new FormData()
  form.append('file', file)
  const params = new URLSearchParams({ language })
  if (script) params.append('script', script)

  const resp = await api.post(`/upload?${params}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return resp.data
}

export async function recognizeEnsemble(manuscriptId, language = 'tam') {
  const resp = await api.post('/recognize', { manuscript_id: manuscriptId, language })
  return resp.data
}

export async function searchManuscripts(query, limit = 10, hybrid = true) {
  const resp = await api.post('/search', { query, limit, use_hybrid: hybrid })
  return resp.data
}

export async function chatQuestion(question, options = {}) {
  const resp = await api.post('/chat', {
    question,
    manuscript_id: options.manuscriptId ?? null,
    line_id: options.lineId ?? null,
    mode: options.mode ?? 'leaf',
    explain_mode: options.explainMode ?? 'simple',
  })
  return resp.data
}

export async function transliterateText(text, script = 'tam', scheme = 'iso_15919') {
  const resp = await api.post('/transliterate', { text, script, scheme })
  return resp.data
}

export async function translateText(text, script = 'tam') {
  const resp = await api.post('/translate', { text, script })
  return resp.data
}

export async function extractEntities(text, script = 'tam') {
  const resp = await api.post('/extract_entities', { text, script })
  return resp.data
}

export async function normalizeDates(text, era = 'tamil') {
  const resp = await api.post('/normalize_dates', text, { params: { era } })
  return resp.data
}

export async function generateDemo(count = 5, level = 'medium') {
  const resp = await api.post('/demo/generate', { count, level })
  return resp.data
}

export async function listManuscripts(limit = 50) {
  const resp = await api.get(`/manuscripts?limit=${limit}`)
  return resp.data
}

export async function getManuscript(id) {
  const resp = await api.get(`/manuscripts/${id}`)
  return resp.data
}

export async function getStats() {
  const resp = await api.get('/stats')
  return resp.data
}

export async function healthCheck() {
  const resp = await api.get('/health')
  return resp.data
}

export async function callChatStream(question, options = {}, onChunk) {
  /**
    SSE stream — opens EventSource manually for this endpoint.
    Falls back to regular POST if streaming is unavailable.
  */
  try {
    const resp = await api.post('/chat/stream', { question, ...options }, {
      responseType: 'stream',
    })
    const reader = resp.data.getReader()
    const decoder = new TextDecoder()
    let reading = true
    while (reading) {
      const { done, value } = await reader.read()
      if (done) {
        reading = false
        break
      }
      const text = decoder.decode(value, { stream: true })
      onChunk(text)
    }
  } catch {
    // Fallback to non-streaming
    const resp = await chatQuestion(question, options)
    onChunk?.(JSON.stringify(resp))
    return resp
  }
}

export default api
