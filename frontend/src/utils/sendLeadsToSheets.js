import { leadsService, gsheetsService, syncFieldsService, SYNC_FIELD_OPTIONS, DEFAULT_SYNC_FIELDS } from '../services/supabase'

/**
 * Distribui e envia leads para webhooks do Google Sheets.
 * Marca os leads enviados como synced_to_sheets = true.
 *
 * @param {Object}   params
 * @param {Array}    params.leads        - array de objetos lead
 * @param {Array}    params.webhooks     - array de objetos webhook
 * @param {string}   params.distribution - 'equal' | 'all' | 'daily_limit'
 * @param {string[]} [params.fields]     - campos a enviar (default: preferência salva ou todos)
 * @returns {{ totalSent: number, errors: string[] }}
 */
export async function sendLeadsToSheets({ leads, webhooks, distribution = 'equal', fields }) {
  // Carregar preferência salva se não informada
  if (!fields) {
    try { fields = await syncFieldsService.get() } catch { fields = DEFAULT_SYNC_FIELDS }
  }

  // Filtrar apenas leads com email E website/domínio preenchidos
  const validLeads = leads.filter(l =>
    l.email && l.email.trim() &&
    l.website && l.website.trim() && l.website !== 'Sem Website'
  )
  if (!validLeads.length || !webhooks.length) return { totalSent: 0, errors: [] }

  let assignments = []
  if (distribution === 'all') {
    assignments = webhooks.map(w => ({ webhook: w, leads: validLeads }))
  } else if (distribution === 'equal') {
    const chunkSize = Math.ceil(validLeads.length / webhooks.length)
    assignments = webhooks.map((w, i) => ({
      webhook: w,
      leads: validLeads.slice(i * chunkSize, (i + 1) * chunkSize),
    }))
  } else if (distribution === 'daily_limit') {
    let remaining = [...validLeads]
    assignments = webhooks.map(w => {
      const chunk = remaining.splice(0, w.daily_limit || 80)
      return { webhook: w, leads: chunk }
    })
  }

  let totalSent = 0
  const errors = []
  const syncedIds = []

  for (const { webhook, leads: batch } of assignments) {
    if (!batch.length) continue
    try {
      const activeOptions = SYNC_FIELD_OPTIONS.filter(o => fields.includes(o.key))
      const payload = {
        leads: batch.map(l => {
          const row = {}
          activeOptions.forEach(o => { row[o.key] = l[o.leadField] || '' })
          return row
        }),
        source: 'prospectahub',
        sent_at: new Date().toISOString(),
      }
      const res = await fetch(webhook.webhook_url, {
        method: 'POST',
        body: JSON.stringify({ action: 'add_leads', ...payload }),
      })
      const status = res.ok ? 'success' : 'error'
      await gsheetsService.recordSend({
        webhook_id: webhook.id,
        webhook_name: webhook.name,
        leads_sent: batch.length,
        status,
      })
      if (res.ok) {
        let rowsAdded = batch.length
        try {
          const json = await res.json()
          if (typeof json.rows_added === 'number') rowsAdded = json.rows_added
        } catch (_) {}
        totalSent += rowsAdded
        syncedIds.push(...batch.map(l => l.id))
      } else {
        errors.push(`${webhook.name}: HTTP ${res.status}`)
      }
    } catch (e) {
      errors.push(`${webhook.name}: ${e.message}`)
      await gsheetsService.recordSend({
        webhook_id: webhook.id,
        webhook_name: webhook.name,
        leads_sent: 0,
        status: 'error',
        error_detail: e.message,
      }).catch(() => {})
    }
  }

  if (syncedIds.length) {
    await leadsService.markAsSynced(syncedIds)
  }

  return { totalSent, errors }
}
