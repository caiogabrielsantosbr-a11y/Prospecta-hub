/**
 * InboxPage — Gmail multi-account inbox
 * OAuth2 via Supabase Edge Functions (sem backend Python)
 */
import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import { supabase } from '../config/supabase'

const SUPABASE_URL      = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_KEY

// ── Edge Function helper ──────────────────────────────────────
async function edgeFn(fnName, { method = 'GET', params = {}, body } = {}) {
  const { data: { session } } = await supabase.auth.getSession()
  const token = session?.access_token
  if (!token) throw new Error('Sessão expirada. Faça login novamente.')

  const url = new URL(`${SUPABASE_URL}/functions/v1/${fnName}`)
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v))
  })

  const res = await fetch(url.toString(), {
    method,
    headers: {
      Authorization:   `Bearer ${token}`,
      apikey:          SUPABASE_ANON_KEY,
      'Content-Type':  'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || 'Erro na API')
  }
  return res.json()
}

// ── MyMemory translation (free, direto do frontend) ───────────
async function translateText(text) {
  const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text.slice(0, 500))}&langpair=auto|pt-BR`
  const res  = await fetch(url)
  const data = await res.json()
  return data?.responseData?.translatedText || text
}

// ── Label colors ─────────────────────────────────────────────
const LABEL_STYLES = {
  'Interesse':     'bg-primary/20 text-primary',
  'Sem interesse': 'bg-error/20 text-error',
  'Pergunta':      'bg-yellow-500/20 text-yellow-500',
  'Irrelevante':   'bg-surface-container-high text-on-surface-variant',
  'Aguardar':      'bg-secondary/20 text-secondary',
}

const FILTER_TABS = [
  { id: 'all',        label: 'Todos',         icon: 'all_inbox' },
  { id: 'unread',     label: 'Não lidos',     icon: 'mark_email_unread' },
  { id: 'replied',    label: 'Respondidos',   icon: 'reply' },
  { id: 'week',       label: 'Última semana', icon: 'date_range' },
  { id: 'attachment', label: 'Com anexo',     icon: 'attach_file' },
]

// ─────────────────────────────────────────────────────────────

export default function InboxPage() {
  const [accounts, setAccounts]               = useState([])
  const [selectedAccount, setSelectedAccount] = useState(null)
  const [loadingAccounts, setLoadingAccounts] = useState(true)

  const [emails, setEmails]               = useState([])
  const [nextPageToken, setNextPageToken] = useState('')
  const [loadingEmails, setLoadingEmails] = useState(false)

  const [selectedEmail, setSelectedEmail] = useState(null)
  const [emailContent, setEmailContent]   = useState(null)
  const [loadingEmail, setLoadingEmail]   = useState(false)

  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const searchTimeout       = useRef(null)

  const [labels, setLabels] = useState({})   // { message_id: { label, confidence, reason } }

  const [replyBody, setReplyBody]             = useState('')
  const [sending, setSending]                 = useState(false)
  const [templates, setTemplates]             = useState([])
  const [showTemplateModal, setShowTemplateModal] = useState(false)

  const [translating, setTranslating]       = useState(false)
  const [translatedBody, setTranslatedBody] = useState(null)
  const [classifying, setClassifying]       = useState(false)

  const [showSettings, setShowSettings]   = useState(false)
  const [geminiKey, setGeminiKey]         = useState('')
  const [savingKey, setSavingKey]         = useState(false)

  useEffect(() => { loadAccounts(); loadGeminiKey() }, [])

  useEffect(() => {
    if (selectedAccount) { setEmails([]); setNextPageToken(''); fetchEmails('') }
  }, [selectedAccount, filter])

  useEffect(() => {
    if (!selectedAccount) return
    clearTimeout(searchTimeout.current)
    searchTimeout.current = setTimeout(() => { setEmails([]); setNextPageToken(''); fetchEmails('') }, 400)
    return () => clearTimeout(searchTimeout.current)
  }, [search])

  useEffect(() => {
    if (selectedAccount) loadTemplates()
  }, [selectedAccount])

  // ── Loaders ────────────────────────────────────────────────

  const loadAccounts = async () => {
    setLoadingAccounts(true)
    try {
      const data = await edgeFn('gmail-accounts')
      setAccounts(data || [])
      if (data?.length) setSelectedAccount(a => a || data[0])
    } catch (e) {
      toast.error('Erro ao carregar contas: ' + e.message)
    } finally {
      setLoadingAccounts(false)
    }
  }

  const fetchEmails = async (pageToken) => {
    if (!selectedAccount) return
    setLoadingEmails(true)
    try {
      const data = await edgeFn('gmail-messages', {
        params: {
          account_id: selectedAccount.id,
          filter,
          search,
          page_token: pageToken,
        },
      })
      const msgs = data.messages || []

      // Sincroniza labels já persistidos com o estado local
      const incoming = {}
      msgs.forEach(m => { if (m.label) incoming[m.id] = { label: m.label, confidence: m.label_confidence } })
      setLabels(prev => ({ ...prev, ...incoming }))

      setEmails(prev => pageToken ? [...prev, ...msgs] : msgs)
      setNextPageToken(data.next_page_token || '')
    } catch (e) {
      toast.error('Erro ao carregar emails: ' + e.message)
    } finally {
      setLoadingEmails(false)
    }
  }

  const loadEmail = async (email) => {
    setSelectedEmail(email)
    setEmailContent(null)
    setTranslatedBody(null)
    setReplyBody('')
    setLoadingEmail(true)
    try {
      const data = await edgeFn('gmail-messages', {
        params: { account_id: selectedAccount.id, message_id: email.id },
      })
      setEmailContent(data)
      setEmails(prev => prev.map(e => e.id === email.id ? { ...e, unread: false } : e))
    } catch (e) {
      toast.error('Erro ao carregar email: ' + e.message)
    } finally {
      setLoadingEmail(false)
    }
  }

  const loadTemplates = async () => {
    try {
      const data = await edgeFn('gmail-messages', { params: { action: 'templates' } })
      setTemplates(data || [])
    } catch (e) { console.error(e) }
  }

  const loadGeminiKey = async () => {
    try {
      const { data } = await supabase
        .from('app_settings')
        .select('value')
        .eq('key', 'gemini_api_key')
        .maybeSingle()
      if (data?.value) setGeminiKey(data.value)
    } catch (e) { console.error(e) }
  }

  const saveGeminiKey = async () => {
    if (!geminiKey.trim()) { toast.error('Cole sua Gemini API Key'); return }
    setSavingKey(true)
    try {
      const { data: { session } } = await supabase.auth.getSession()
      const userId = session?.user?.id
      await supabase.from('app_settings').upsert(
        { user_id: userId, key: 'gemini_api_key', value: geminiKey.trim() },
        { onConflict: 'user_id,key' }
      )
      toast.success('Gemini API Key salva!')
      setShowSettings(false)
    } catch (e) { toast.error('Erro ao salvar: ' + e.message) }
    finally { setSavingKey(false) }
  }

  // ── Connect / disconnect ───────────────────────────────────

  const connectAccount = async () => {
    try {
      const { url } = await edgeFn('gmail-accounts', { method: 'POST' })
      if (!url) throw new Error('URL de autenticação inválida')

      window.open(url, 'gmail_auth', 'width=500,height=640,scrollbars=yes')

      const handler = (e) => {
        if (e.data?.type === 'gmail_connected') {
          toast.success(`Conta ${e.data.email} conectada!`)
          loadAccounts()
          window.removeEventListener('message', handler)
        } else if (e.data?.type === 'gmail_error') {
          toast.error('Erro ao conectar: ' + e.data.error)
          window.removeEventListener('message', handler)
        }
      }
      window.addEventListener('message', handler)
    } catch (e) {
      toast.error('Erro ao iniciar autenticação: ' + e.message)
    }
  }

  const disconnectAccount = async (accountId) => {
    if (!confirm('Desconectar esta conta Gmail?')) return
    try {
      await edgeFn('gmail-accounts', { method: 'DELETE', params: { id: accountId } })
      toast.success('Conta desconectada')
      const updated = accounts.filter(a => a.id !== accountId)
      setAccounts(updated)
      if (selectedAccount?.id === accountId) {
        setSelectedAccount(updated[0] || null)
        setEmails([])
        setSelectedEmail(null)
        setEmailContent(null)
      }
    } catch (e) { toast.error('Erro: ' + e.message) }
  }

  // ── Email actions ──────────────────────────────────────────

  const handleReply = async () => {
    if (!replyBody.trim()) { toast.error('Escreva a resposta antes de enviar'); return }
    setSending(true)
    try {
      await edgeFn('gmail-messages', {
        method: 'POST',
        params: { action: 'reply', account_id: selectedAccount.id },
        body: {
          message_id: emailContent.id,
          thread_id:  emailContent.thread_id,
          to:         emailContent.from,
          subject:    emailContent.subject,
          body:       replyBody,
        },
      })
      toast.success('Resposta enviada!')
      setReplyBody('')
    } catch (e) { toast.error('Erro ao enviar: ' + e.message) }
    finally { setSending(false) }
  }

  const handleClassify = async () => {
    if (!emailContent) return
    setClassifying(true)
    try {
      const result = await edgeFn('gmail-messages', {
        method: 'POST',
        params: { action: 'classify', account_id: selectedAccount.id },
        body:   { message_id: emailContent.id },
      })
      setLabels(prev => ({ ...prev, [emailContent.id]: result }))
      toast.success(`Classificado: ${result.label}`)
    } catch (e) { toast.error('Erro na classificação: ' + e.message) }
    finally { setClassifying(false) }
  }

  const handleTranslate = async () => {
    if (!emailContent) return
    setTranslating(true)
    try {
      const text = emailContent.body_text || emailContent.snippet || ''
      setTranslatedBody(await translateText(text))
    } catch { toast.error('Erro na tradução') }
    finally { setTranslating(false) }
  }

  // ─────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 64px)' }}
      onClick={() => showSettings && setShowSettings(false)}>
      {/* Header */}
      <div className="px-8 py-4 border-b border-outline-variant/10 shrink-0">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <span className="text-primary font-bold text-[10px] tracking-[0.15em] uppercase">COMUNICAÇÃO</span>
            <h2 className="text-2xl font-bold tracking-tight">Inbox Gmail</h2>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {loadingAccounts ? (
              <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
            ) : accounts.map(acc => (
              <div key={acc.id} className="flex items-center gap-1">
                <button
                  onClick={() => setSelectedAccount(acc)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border transition-all cursor-pointer ${
                    selectedAccount?.id === acc.id
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-outline-variant/20 hover:bg-surface-container-low text-on-surface-variant'
                  }`}
                >
                  <span className="material-symbols-outlined text-sm">alternate_email</span>
                  {acc.email}
                </button>
                <button
                  onClick={() => disconnectAccount(acc.id)}
                  className="p-1 rounded hover:bg-error/10 text-on-surface-variant hover:text-error transition-colors cursor-pointer"
                  title="Desconectar conta">
                  <span className="material-symbols-outlined text-sm">close</span>
                </button>
              </div>
            ))}
            <button onClick={connectAccount} className="btn-primary">
              <span className="material-symbols-outlined text-lg">add</span>
              Conectar Gmail
            </button>

            {/* Configurações IA */}
            <div className="relative">
              <button
                onClick={() => setShowSettings(s => !s)}
                className={`p-2 rounded-lg border transition-colors cursor-pointer ${
                  showSettings
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-outline-variant/20 text-on-surface-variant hover:bg-surface-container-low'
                }`}
                title="Configurar IA (Gemini API Key)"
              >
                <span className="material-symbols-outlined text-lg">psychology</span>
              </button>

              {showSettings && (
                <div className="absolute right-0 top-11 z-50 w-80 bg-surface-container rounded-xl shadow-2xl border border-outline-variant/20 p-4"
                  onClick={e => e.stopPropagation()}>
                  <div className="flex items-center gap-2 mb-3">
                    <span className="material-symbols-outlined text-base text-primary">psychology</span>
                    <span className="font-semibold text-sm">Gemini API Key</span>
                  </div>
                  <p className="text-xs text-on-surface-variant mb-3 leading-relaxed">
                    Necessária para classificar emails com IA. Gratuita em{' '}
                    <span className="text-primary">aistudio.google.com</span>
                  </p>
                  <input
                    type="password"
                    value={geminiKey}
                    onChange={e => setGeminiKey(e.target.value)}
                    placeholder="AIza..."
                    className="input-field w-full text-sm mb-3"
                  />
                  <div className="flex gap-2">
                    <button onClick={saveGeminiKey} disabled={savingKey}
                      className="btn-primary flex-1 justify-center text-sm disabled:opacity-50">
                      {savingKey ? 'Salvando...' : 'Salvar'}
                    </button>
                    <button onClick={() => setShowSettings(false)} className="btn-ghost text-sm">
                      Fechar
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {accounts.length > 0 && (
          <div className="flex items-center gap-4 mt-3 flex-wrap">
            <div className="flex gap-1 flex-wrap">
              {FILTER_TABS.map(tab => (
                <button key={tab.id} onClick={() => setFilter(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                    filter === tab.id ? 'bg-primary/20 text-primary' : 'text-on-surface-variant hover:bg-surface-container-low'
                  }`}
                >
                  <span className="material-symbols-outlined text-sm">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </div>
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">search</span>
              <input type="text" value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Buscar emails..." className="pl-9 py-1.5 text-sm w-52" />
            </div>
          </div>
        )}
      </div>

      {/* No accounts */}
      {!loadingAccounts && accounts.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-sm">
            <span className="material-symbols-outlined text-7xl text-on-surface-variant opacity-20">inbox</span>
            <h3 className="text-xl font-bold mt-4 mb-2">Nenhuma conta Gmail conectada</h3>
            <p className="text-on-surface-variant text-sm mb-6">
              Conecte uma ou mais contas Gmail para visualizar e responder emails diretamente aqui.
            </p>
            <button onClick={connectAccount} className="btn-primary">
              <span className="material-symbols-outlined text-lg">add</span>
              Conectar conta Gmail
            </button>
          </div>
        </div>
      )}

      {/* Split view */}
      {accounts.length > 0 && (
        <div className="flex flex-1 overflow-hidden">
          {/* Email list */}
          <div className="w-72 shrink-0 border-r border-outline-variant/10 overflow-y-auto">
            {loadingEmails && emails.length === 0 ? (
              <div className="p-8 text-center">
                <div className="inline-block w-6 h-6 border-4 border-primary border-t-transparent rounded-full animate-spin" />
              </div>
            ) : emails.length === 0 ? (
              <div className="p-8 text-center">
                <span className="material-symbols-outlined text-4xl text-on-surface-variant opacity-30">search_off</span>
                <p className="mt-2 text-sm text-on-surface-variant">Nenhum email encontrado</p>
              </div>
            ) : (
              <>
                {emails.map(email => (
                  <button key={email.id} onClick={() => loadEmail(email)}
                    className={`w-full text-left px-4 py-3 border-b border-outline-variant/5 hover:bg-surface-container-low transition-colors cursor-pointer ${
                      selectedEmail?.id === email.id ? 'bg-surface-container-low border-l-2 border-l-primary pl-3.5' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between gap-1 mb-0.5">
                      <span className={`text-sm truncate flex-1 ${email.unread ? 'font-bold' : 'font-medium'}`}>
                        {email.from?.split('<')[0]?.trim() || email.from || '—'}
                      </span>
                      {email.unread && <span className="w-2 h-2 rounded-full bg-primary shrink-0" />}
                    </div>
                    <div className={`text-xs truncate mb-0.5 ${email.unread ? 'font-semibold' : 'text-on-surface-variant'}`}>
                      {email.subject || '(sem assunto)'}
                    </div>
                    <div className="text-xs text-on-surface-variant opacity-50 truncate mb-1">{email.snippet}</div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-on-surface-variant opacity-40">{email.date?.slice(5, 11)}</span>
                      {labels[email.id] && (
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${LABEL_STYLES[labels[email.id].label] || ''}`}>
                          {labels[email.id].label}
                        </span>
                      )}
                    </div>
                  </button>
                ))}
                {nextPageToken && (
                  <button onClick={() => fetchEmails(nextPageToken)} disabled={loadingEmails}
                    className="w-full p-3 text-sm text-primary hover:bg-surface-container-low text-center cursor-pointer disabled:opacity-50">
                    {loadingEmails ? 'Carregando...' : 'Carregar mais'}
                  </button>
                )}
              </>
            )}
          </div>

          {/* Email reader */}
          <div className="flex-1 overflow-y-auto flex flex-col">
            {!selectedEmail ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <span className="material-symbols-outlined text-5xl text-on-surface-variant opacity-20">mark_email_unread</span>
                  <p className="mt-2 text-sm text-on-surface-variant">Selecione um email para ler</p>
                </div>
              </div>
            ) : loadingEmail ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="inline-block w-6 h-6 border-4 border-primary border-t-transparent rounded-full animate-spin" />
              </div>
            ) : emailContent ? (
              <>
                {/* Email meta */}
                <div className="px-8 py-5 border-b border-outline-variant/10">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-bold mb-3 leading-tight">{emailContent.subject || '(sem assunto)'}</h3>
                      <div className="space-y-1 text-sm text-on-surface-variant">
                        <div><span className="font-semibold text-on-surface">De:</span> {emailContent.from}</div>
                        <div><span className="font-semibold text-on-surface">Para:</span> {emailContent.to}</div>
                        <div><span className="font-semibold text-on-surface">Data:</span> {emailContent.date}</div>
                      </div>
                    </div>
                    {labels[emailContent.id] && (
                      <span className={`px-3 py-1 rounded-full text-xs font-bold shrink-0 ${LABEL_STYLES[labels[emailContent.id].label] || ''}`}>
                        {labels[emailContent.id].label} {labels[emailContent.id].confidence}%
                      </span>
                    )}
                  </div>
                </div>

                {/* Body */}
                <div className="px-8 py-5 flex-1">
                  {translatedBody ? (
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-xs text-primary font-semibold uppercase tracking-wider">Traduzido (PT-BR)</span>
                        <button onClick={() => setTranslatedBody(null)} className="text-xs text-on-surface-variant hover:text-on-surface cursor-pointer">
                          ver original
                        </button>
                      </div>
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{translatedBody}</p>
                    </div>
                  ) : emailContent.body_html ? (
                    <iframe
                      srcDoc={emailContent.body_html}
                      sandbox="allow-same-origin"
                      className="w-full border-0 rounded-lg bg-white"
                      style={{ minHeight: 300 }}
                      title="Email"
                      onLoad={e => {
                        const doc = e.target.contentDocument
                        if (doc?.body) e.target.style.height = (doc.body.scrollHeight + 30) + 'px'
                      }}
                    />
                  ) : (
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{emailContent.body_text || emailContent.snippet}</p>
                  )}
                </div>

                {/* Toolbar */}
                <div className="px-8 py-3 border-t border-outline-variant/10 flex items-center gap-2 flex-wrap">
                  <button onClick={handleTranslate} disabled={translating} className="btn-ghost text-sm disabled:opacity-50 cursor-pointer">
                    {translating
                      ? <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      : <span className="material-symbols-outlined text-sm">translate</span>}
                    Traduzir para PT-BR
                  </button>
                  <button onClick={handleClassify} disabled={classifying} className="btn-ghost text-sm disabled:opacity-50 cursor-pointer">
                    {classifying
                      ? <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                      : <span className="material-symbols-outlined text-sm">psychology</span>}
                    Classificar com IA
                  </button>
                  {labels[emailContent.id]?.reason && (
                    <span className="text-xs text-on-surface-variant italic">{labels[emailContent.id].reason}</span>
                  )}
                </div>

                {/* Reply */}
                <div className="px-8 py-5 border-t border-outline-variant/10">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-sm text-primary">reply</span>
                      <span className="text-sm font-semibold">Responder</span>
                    </div>
                    <button onClick={() => setShowTemplateModal(true)} className="btn-ghost text-xs cursor-pointer">
                      <span className="material-symbols-outlined text-sm">bookmarks</span>
                      Templates
                    </button>
                  </div>
                  <textarea
                    value={replyBody}
                    onChange={e => setReplyBody(e.target.value)}
                    placeholder="Escreva sua resposta aqui..."
                    className="w-full h-28 resize-none p-3 text-sm rounded-lg border border-outline-variant/20 bg-surface-container focus:outline-none focus:border-primary transition-colors"
                  />
                  <div className="flex justify-end mt-3">
                    <button onClick={handleReply} disabled={sending || !replyBody.trim()}
                      className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer">
                      {sending
                        ? <><span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />Enviando...</>
                        : <><span className="material-symbols-outlined text-lg">send</span>Enviar Resposta</>}
                    </button>
                  </div>
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}

      {showTemplateModal && (
        <TemplatesModal
          templates={templates}
          onSelect={t => { setReplyBody(t.body); setShowTemplateModal(false) }}
          onClose={() => setShowTemplateModal(false)}
          onRefresh={loadTemplates}
        />
      )}
    </div>
  )
}

// ── Templates Modal ──────────────────────────────────────────

function TemplatesModal({ templates, onSelect, onClose, onRefresh }) {
  const [creating, setCreating] = useState(false)
  const [form, setForm]         = useState({ name: '', subject: '', body: '' })
  const [saving, setSaving]     = useState(false)

  const handleCreate = async () => {
    if (!form.name || !form.body) { toast.error('Nome e corpo são obrigatórios'); return }
    setSaving(true)
    try {
      await edgeFn('gmail-messages', {
        method: 'POST',
        params: { action: 'templates' },
        body:   form,
      })
      toast.success('Template criado!')
      onRefresh()
      setCreating(false)
      setForm({ name: '', subject: '', body: '' })
    } catch { toast.error('Erro ao salvar') }
    finally { setSaving(false) }
  }

  const handleDelete = async (id) => {
    if (!confirm('Excluir este template?')) return
    try {
      await edgeFn('gmail-messages', {
        method: 'DELETE',
        params: { action: 'templates', id },
      })
      toast.success('Excluído')
      onRefresh()
    } catch { toast.error('Erro') }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-surface-container rounded-2xl shadow-xl border border-outline-variant/20 w-full max-w-lg max-h-[80vh] flex flex-col"
        onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-outline-variant/10">
          <h3 className="font-bold text-lg">Templates de Resposta</h3>
          <div className="flex items-center gap-2">
            <button onClick={() => setCreating(!creating)} className="btn-primary text-sm cursor-pointer">
              <span className="material-symbols-outlined text-sm">add</span> Novo
            </button>
            <button onClick={onClose} className="p-2 rounded-lg hover:bg-surface-container-highest cursor-pointer">
              <span className="material-symbols-outlined text-on-surface-variant">close</span>
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {creating && (
            <div className="glass-card rounded-lg p-4 space-y-3">
              <input type="text" value={form.name} onChange={e => setForm({...form, name: e.target.value})}
                placeholder="Nome do template *" className="w-full" />
              <input type="text" value={form.subject} onChange={e => setForm({...form, subject: e.target.value})}
                placeholder="Assunto (opcional)" className="w-full" />
              <textarea value={form.body} onChange={e => setForm({...form, body: e.target.value})}
                placeholder="Corpo do email *" className="w-full h-24 resize-none" />
              <div className="flex gap-2">
                <button onClick={handleCreate} disabled={saving} className="btn-primary flex-1 justify-center disabled:opacity-50 cursor-pointer">
                  {saving ? 'Salvando...' : 'Salvar'}
                </button>
                <button onClick={() => setCreating(false)} className="btn-ghost cursor-pointer">Cancelar</button>
              </div>
            </div>
          )}
          {!creating && templates.length === 0 && (
            <div className="text-center py-8 text-on-surface-variant text-sm">
              Nenhum template. Clique em "Novo" para criar.
            </div>
          )}
          {templates.map(t => (
            <div key={t.id} className="glass-card rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <span className="font-semibold text-sm">{t.name}</span>
                <div className="flex gap-1">
                  <button onClick={() => onSelect(t)} className="btn-primary text-xs px-3 py-1 cursor-pointer">Usar</button>
                  <button onClick={() => handleDelete(t.id)} className="p-1.5 rounded hover:bg-error/10 text-error cursor-pointer">
                    <span className="material-symbols-outlined text-sm">delete</span>
                  </button>
                </div>
              </div>
              {t.subject && <div className="text-xs text-on-surface-variant mb-1">Assunto: {t.subject}</div>}
              <p className="text-xs text-on-surface-variant line-clamp-2">{t.body}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
