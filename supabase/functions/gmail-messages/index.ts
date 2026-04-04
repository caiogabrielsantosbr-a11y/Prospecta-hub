import { createClient } from 'jsr:@supabase/supabase-js@2'

const SUPABASE_URL     = Deno.env.get('SUPABASE_URL')!
const SERVICE_KEY      = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
const GEMINI_KEY_ENV   = Deno.env.get('GEMINI_API_KEY') ?? ''
const CLIENT_ID        = Deno.env.get('GMAIL_CLIENT_ID')!
const CLIENT_SECRET    = Deno.env.get('GMAIL_CLIENT_SECRET')!
const GMAIL_BASE       = 'https://gmail.googleapis.com/gmail/v1/users/me'

const corsHeaders = {
  'Access-Control-Allow-Origin':  '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

const supabase = createClient(SUPABASE_URL, SERVICE_KEY)

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  })
}

async function getUserId(req: Request): Promise<string> {
  const token = req.headers.get('Authorization')?.replace('Bearer ', '')
  if (!token) throw new Error('Token ausente')
  const { data: { user }, error } = await supabase.auth.getUser(token)
  if (error || !user) throw new Error('Sessão inválida ou expirada')
  return user.id
}

async function getGeminiKey(userId: string): Promise<string> {
  const { data } = await supabase
    .from('app_settings')
    .select('value')
    .eq('user_id', userId)
    .eq('key', 'gemini_api_key')
    .maybeSingle()
  return data?.value || GEMINI_KEY_ENV
}

async function getValidToken(accountId: string): Promise<{ token: string; email: string }> {
  const { data: acct, error } = await supabase
    .from('gmail_accounts').select('*').eq('id', accountId).single()
  if (error || !acct) throw new Error('Conta não encontrada')

  const expiry = new Date(acct.token_expiry).getTime()
  if (expiry - Date.now() < 5 * 60 * 1000) {
    const res = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'refresh_token', refresh_token: acct.refresh_token,
        client_id: CLIENT_ID, client_secret: CLIENT_SECRET,
      }),
    })
    const t = await res.json()
    if (t.access_token) {
      const newExpiry = new Date(Date.now() + (t.expires_in ?? 3600) * 1000).toISOString()
      await supabase.from('gmail_accounts').update({ access_token: t.access_token, token_expiry: newExpiry }).eq('id', accountId)
      return { token: t.access_token, email: acct.email }
    }
  }
  return { token: acct.access_token, email: acct.email }
}

function decodeB64url(str: string): string {
  try {
    const b64 = str.replace(/-/g, '+').replace(/_/g, '/')
    const binary = atob(b64 + '=='.slice((2 - b64.length * 3) & 3))
    const bytes = Uint8Array.from(binary, c => c.charCodeAt(0))
    return new TextDecoder('utf-8').decode(bytes)
  } catch { return '' }
}

function extractBody(payload: any): { html: string; text: string } {
  let html = '', text = ''
  function walk(p: any) {
    if (!p) return
    if (p.mimeType === 'text/html'  && p.body?.data) html = decodeB64url(p.body.data)
    if (p.mimeType === 'text/plain' && p.body?.data) text = decodeB64url(p.body.data)
    p.parts?.forEach(walk)
  }
  walk(payload)
  return { html, text }
}

function hdr(headers: any[], name: string): string {
  return headers?.find((h: any) => h.name.toLowerCase() === name.toLowerCase())?.value ?? ''
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })

  try {
    const userId = await getUserId(req)
    const url    = new URL(req.url)
    const action = url.searchParams.get('action')

    // TEMPLATES
    if (action === 'templates') {
      if (req.method === 'GET') {
        const { data } = await supabase.from('email_templates').select('*').eq('user_id', userId).order('created_at', { ascending: false })
        return json(data ?? [])
      }
      if (req.method === 'POST') {
        const body = await req.json()
        const { data } = await supabase.from('email_templates').insert({ ...body, user_id: userId }).select().single()
        return json(data)
      }
      if (req.method === 'DELETE') {
        await supabase.from('email_templates').delete().eq('id', url.searchParams.get('id')).eq('user_id', userId)
        return json({ success: true })
      }
    }

    const accountId = url.searchParams.get('account_id')
    if (!accountId) return json({ error: 'account_id obrigatório' }, 400)

    const { data: acctCheck } = await supabase.from('gmail_accounts').select('user_id').eq('id', accountId).single()
    if (!acctCheck || acctCheck.user_id !== userId) return json({ error: 'Forbidden' }, 403)

    const { token, email: senderEmail } = await getValidToken(accountId)

    // REPLY
    if (req.method === 'POST' && action === 'reply') {
      const { thread_id, message_id, to, subject, body } = await req.json()
      const raw = [
        `From: ${senderEmail}`, `To: ${to}`,
        `Subject: Re: ${subject.startsWith('Re:') ? subject.slice(3).trim() : subject}`,
        `In-Reply-To: ${message_id}`, `References: ${message_id}`,
        'MIME-Version: 1.0', 'Content-Type: text/html; charset=utf-8', '', body,
      ].join('\r\n')
      const bytes = new TextEncoder().encode(raw)
      let bin = ''; bytes.forEach(b => bin += String.fromCharCode(b))
      const encoded = btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
      const res = await fetch(`${GMAIL_BASE}/messages/send`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw: encoded, threadId: thread_id }),
      })
      const d = await res.json()
      if (d.error) throw new Error(d.error.message)
      return json({ success: true, id: d.id })
    }

    // CLASSIFY
    if (req.method === 'POST' && action === 'classify') {
      const { message_id } = await req.json()
      const geminiKey = await getGeminiKey(userId)
      if (!geminiKey) return json({ error: 'Gemini API Key não configurada. Clique no ícone ➡ no topo do Inbox.' }, 400)

      const msgRes  = await fetch(`${GMAIL_BASE}/messages/${message_id}?format=metadata&metadataHeaders=Subject`, { headers: { Authorization: `Bearer ${token}` } })
      const msgData = await msgRes.json()
      const subject = hdr(msgData.payload?.headers ?? [], 'Subject')
      const snippet = msgData.snippet ?? ''

      const gemRes = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiKey}`,
        {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: `Você é um assistente de prospecção comercial. Classifique este email:\nAssunto: ${subject}\nPreview: ${snippet}\n\nResponda APENAS com JSON válido (sem markdown):\n{"label":"Interesse"|"Sem interesse"|"Pergunta"|"Irrelevante"|"Aguardar","confidence":0-100,"reason":"..."}` }] }],
            generationConfig: { response_mime_type: 'application/json' },
          }),
        }
      )
      const gemData = await gemRes.json()
      const raw     = gemData.candidates?.[0]?.content?.parts?.[0]?.text ?? '{}'
      let result: any = {}
      try { result = JSON.parse(raw) } catch { result = { label: 'Irrelevante', confidence: 0, reason: 'Parse error' } }

      await supabase.from('email_inbox_labels').upsert(
        { user_id: userId, account_id: accountId, message_id, label: result.label, confidence: result.confidence, reason: result.reason },
        { onConflict: 'user_id,message_id' }
      )
      return json(result)
    }

    // LIST
    if (req.method === 'GET' && !url.searchParams.get('message_id')) {
      const q         = url.searchParams.get('q') ?? 'in:sent'
      const pageToken = url.searchParams.get('page_token') ?? ''
      const isSent    = q.includes('in:sent')

      const listUrl = new URL(`${GMAIL_BASE}/messages`)
      listUrl.searchParams.set('maxResults', '30')
      if (!isSent) listUrl.searchParams.set('labelIds', 'INBOX')
      listUrl.searchParams.set('q', q)
      if (pageToken) listUrl.searchParams.set('pageToken', pageToken)

      const listRes  = await fetch(listUrl.toString(), { headers: { Authorization: `Bearer ${token}` } })
      const listData = await listRes.json()
      const messages = listData.messages ?? []

      const metaList = await Promise.all(messages.map(async (m: any) => {
        const res = await fetch(
          `${GMAIL_BASE}/messages/${m.id}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
        const d = await res.json()
        const headers = d.payload?.headers ?? []
        const { data: lbl } = await supabase.from('email_inbox_labels').select('label, confidence').eq('message_id', m.id).eq('user_id', userId).maybeSingle()
        return {
          id: d.id, thread_id: d.threadId,
          from: hdr(headers, 'From'), subject: hdr(headers, 'Subject'), date: hdr(headers, 'Date'),
          snippet: d.snippet ?? '', unread: d.labelIds?.includes('UNREAD') ?? false,
          label: lbl?.label ?? null, label_confidence: lbl?.confidence ?? null,
        }
      }))
      return json({ messages: metaList, next_page_token: listData.nextPageToken ?? null })
    }

    // READ SINGLE
    if (req.method === 'GET' && url.searchParams.get('message_id')) {
      const messageId = url.searchParams.get('message_id')!
      const res = await fetch(`${GMAIL_BASE}/messages/${messageId}?format=full`, { headers: { Authorization: `Bearer ${token}` } })
      const d   = await res.json()
      const headers = d.payload?.headers ?? []
      const { html, text } = extractBody(d.payload)
      await fetch(`${GMAIL_BASE}/messages/${messageId}/modify`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ removeLabelIds: ['UNREAD'] }),
      })
      return json({ id: d.id, thread_id: d.threadId, from: hdr(headers, 'From'), to: hdr(headers, 'To'), subject: hdr(headers, 'Subject'), date: hdr(headers, 'Date'), body_html: html, body_text: text })
    }

    return json({ error: 'Rota não encontrada' }, 404)
  } catch (e: any) {
    return json({ error: e.message }, 500)
  }
})
