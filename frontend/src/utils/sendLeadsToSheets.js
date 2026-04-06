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
  if (!leads.length || !webhooks.length) return { totalSent: 0, errors: [] }

  let assignments = []
  if (distribution === 'all') {
    assignments = webhooks.map(w => ({ webhook: w, leads }))
  } else if (distribution === 'equal') {
    const chunkSize = Math.ceil(leads.length / webhooks.length)
    assignments = webhooks.map((w, i) => ({
      webhook: w,
      leads: leads.slice(i * chunkSize, (i + 1) * chunkSize),
    }))
  } else if (distribution === 'daily_limit') {
    let remaining = [...leads]
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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const status = res.ok ? 'success' : 'error'
      await gsheetsService.recordSend({
        webhook_id: webhook.id,
        webhook_name: webhook.name,
        leads_sent: batch.length,
        status,
      })
      if (res.ok) {
        totalSent += batch.length
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
