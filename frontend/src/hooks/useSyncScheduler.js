import { useEffect } from 'react'
import toast from 'react-hot-toast'
import { leadsService, gsheetsService, syncScheduleService } from '../services/supabase'
import { sendLeadsToSheets } from '../utils/sendLeadsToSheets'

/**
 * Roda em background verificando agendamentos de sync a cada 60s.
 * Montar uma vez no App root.
 */
export function useSyncScheduler() {
  useEffect(() => {
    const run = async () => {
      try {
        const schedules = await syncScheduleService.getActive()
        const now = new Date()

        for (const schedule of schedules) {
          if (!schedule.next_run_at) continue
          if (new Date(schedule.next_run_at) > now) continue

          const webhookIds = Array.isArray(schedule.webhook_ids) ? schedule.webhook_ids : []
          const allWebhooks = await gsheetsService.getWebhooks()
          const webhooks = webhookIds.length
            ? allWebhooks.filter(w => webhookIds.includes(w.id) && w.active !== false)
            : allWebhooks.filter(w => w.active !== false)

          if (!webhooks.length) {
            await syncScheduleService.recordRun(schedule.id, schedule)
            continue
          }

          const { leads } = await leadsService.getUnsyncedLeads({ limit: 500 })

          if (leads.length) {
            const { totalSent, errors } = await sendLeadsToSheets({ leads, webhooks, distribution: 'equal' })
            if (totalSent > 0) {
              toast.success(`Sync agendado: ${totalSent} leads enviados`)
            }
            if (errors.length) {
              toast.error(`Sync agendado com erros: ${errors[0]}`)
            }
          }

          await syncScheduleService.recordRun(schedule.id, schedule)
        }
      } catch (e) {
        console.error('[SyncScheduler]', e)
      }
    }

    // Rodar imediatamente e depois a cada 60s
    run()
    const interval = setInterval(run, 60 * 1000)
    return () => clearInterval(interval)
  }, [])
}
