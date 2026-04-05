/**
 * Supabase Service - Direct database operations
 * Frontend comunica DIRETAMENTE com Supabase para CRUD de dados
 * RLS garante isolamento por usuário automaticamente via JWT
 */
import { supabase } from '../config/supabase'

/** Helper: obter user_id do usuário autenticado */
async function getCurrentUserId() {
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('Usuário não autenticado')
  return user.id
}

/**
 * LEADS OPERATIONS
 */

export const leadsService = {
  /**
   * Get leads with filters and pagination
   * RLS filtra automaticamente pelo usuário logado
   */
  async getLeads({ limit = 50, offset = 0, conjunto, cidade, search } = {}) {
    let query = supabase
      .from('gmap_leads')
      .select('*', { count: 'exact' })
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (conjunto) query = query.eq('conjunto_de_locais', conjunto)
    if (cidade) query = query.eq('cidade', cidade)
    if (search) query = query.or(`nome.ilike.%${search}%,telefone.ilike.%${search}%,website.ilike.%${search}%,email.ilike.%${search}%`)

    const { data, error, count } = await query
    if (error) throw error
    return { leads: data || [], total: count || 0 }
  },

  /**
   * Get lead statistics (eficiente: conta no banco, não carrega tudo)
   */
  async getStats() {
    const { count: total, error: e1 } = await supabase
      .from('gmap_leads').select('*', { count: 'exact', head: true })
    if (e1) throw e1

    const { count: with_phone, error: e2 } = await supabase
      .from('gmap_leads').select('*', { count: 'exact', head: true })
      .not('telefone', 'is', null).neq('telefone', '').neq('telefone', 'Sem Telefone')
    if (e2) throw e2

    const { count: with_email, error: e3 } = await supabase
      .from('gmap_leads').select('*', { count: 'exact', head: true })
      .not('email', 'is', null).neq('email', '')
    if (e3) throw e3

    const { count: with_website, error: e4 } = await supabase
      .from('gmap_leads').select('*', { count: 'exact', head: true })
      .not('website', 'is', null).neq('website', '').neq('website', 'Sem Website')
    if (e4) throw e4

    return {
      total: total || 0,
      with_phone: with_phone || 0,
      with_email: with_email || 0,
      with_website: with_website || 0,
      without_phone: (total || 0) - (with_phone || 0),
      without_website: (total || 0) - (with_website || 0)
    }
  },

  /** Get unique conjuntos (RLS filtra por usuário automaticamente) */
  async getConjuntos() {
    const { data, error } = await supabase
      .from('gmap_leads')
      .select('conjunto_de_locais')
      .not('conjunto_de_locais', 'is', null)
    if (error) throw error
    const conjuntos = [...new Set(data.map(l => l.conjunto_de_locais).filter(Boolean))]
    return conjuntos.sort()
  },

  /** Get unique cidades for a conjunto */
  async getCidades(conjunto) {
    const { data, error } = await supabase
      .from('gmap_leads')
      .select('cidade')
      .eq('conjunto_de_locais', conjunto)
      .not('cidade', 'is', null)
    if (error) throw error
    const cidades = [...new Set(data.map(l => l.cidade).filter(Boolean))]
    return cidades.sort()
  },

  /** Update a lead */
  async updateLead(leadId, updates) {
    const { data, error } = await supabase
      .from('gmap_leads')
      .update(updates)
      .eq('id', leadId)
      .select()
      .single()
    if (error) throw error
    return data
  },

  /** Delete a lead */
  async deleteLead(leadId) {
    const { error } = await supabase
      .from('gmap_leads')
      .delete()
      .eq('id', leadId)
    if (error) throw error
  },

  /** Delete multiple leads */
  async deleteLeads(leadIds) {
    const { error } = await supabase
      .from('gmap_leads')
      .delete()
      .in('id', leadIds)
    if (error) throw error
  },

  /** Export leads with filters */
  async exportLeads({ conjunto, cidade, search } = {}) {
    let query = supabase
      .from('gmap_leads')
      .select('*')
      .order('created_at', { ascending: false })

    if (conjunto) query = query.eq('conjunto_de_locais', conjunto)
    if (cidade) query = query.eq('cidade', cidade)
    if (search) query = query.or(`nome.ilike.%${search}%,telefone.ilike.%${search}%,website.ilike.%${search}%,email.ilike.%${search}%`)

    const { data, error } = await query
    if (error) throw error
    return data || []
  },

  /** Get leads by IDs (para envio para GSheets) */
  async getLeadsByIds(leadIds) {
    const { data, error } = await supabase
      .from('gmap_leads')
      .select('*')
      .in('id', leadIds)
    if (error) throw error
    return data || []
  }
}

/**
 * TASKS OPERATIONS
 */

export const tasksService = {
  async getAll() {
    const { data, error } = await supabase
      .from('tasks')
      .select('*')
      .order('created_at', { ascending: false })
    if (error) throw error
    return data || []
  },

  async getById(taskId) {
    const { data, error } = await supabase
      .from('tasks')
      .select('*')
      .eq('id', taskId)
      .single()
    if (error) throw error
    return data
  },

  async updateStatus(taskId, status) {
    const { data, error } = await supabase
      .from('tasks')
      .update({ status, updated_at: new Date().toISOString() })
      .eq('id', taskId)
      .select()
      .single()
    if (error) throw error
    return data
  }
}

/**
 * GSHEETS WEBHOOKS
 */

export const gsheetsService = {
  async getWebhooks() {
    const { data, error } = await supabase
      .from('gsheets_webhooks')
      .select('*')
      .order('created_at', { ascending: false })
    if (error) throw error
    return data || []
  },

  async createWebhook({ name, webhook_url, description, daily_limit }) {
    const userId = await getCurrentUserId()
    const { data, error } = await supabase
      .from('gsheets_webhooks')
      .insert({ name, webhook_url, description, daily_limit: daily_limit || 80, user_id: userId })
      .select()
      .single()
    if (error) throw error
    return data
  },

  async updateWebhook(id, updates) {
    const { data, error } = await supabase
      .from('gsheets_webhooks')
      .update(updates)
      .eq('id', id)
      .select()
      .single()
    if (error) throw error
    return data
  },

  async deleteWebhook(id) {
    const { error } = await supabase
      .from('gsheets_webhooks')
      .delete()
      .eq('id', id)
    if (error) throw error
  },

  async getSendHistory({ limit = 20 } = {}) {
    const { data, error } = await supabase
      .from('webhook_send_history')
      .select('*, gsheets_webhooks(name)')
      .order('sent_at', { ascending: false })
      .limit(limit)
    if (error) throw error
    return data || []
  },

  async recordSend({ webhook_id, webhook_name, leads_sent, status = 'success', error_detail }) {
    const userId = await getCurrentUserId()
    const { error } = await supabase
      .from('webhook_send_history')
      .insert({ user_id: userId, webhook_id, webhook_name, leads_sent, status, error_detail })
    if (error) throw error
  },

  /** Stats de envio: hoje, semana, mês */
  async getSendStats() {
    const now = new Date()
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString()
    const weekStart = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString()
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1).toISOString()

    const [todayRes, weekRes, monthRes] = await Promise.all([
      supabase.from('webhook_send_history').select('leads_sent').gte('sent_at', todayStart).eq('status', 'success'),
      supabase.from('webhook_send_history').select('leads_sent').gte('sent_at', weekStart).eq('status', 'success'),
      supabase.from('webhook_send_history').select('leads_sent').gte('sent_at', monthStart).eq('status', 'success'),
    ])

    const sum = (rows) => (rows.data || []).reduce((a, r) => a + (r.leads_sent || 0), 0)

    return {
      today: sum(todayRes),
      week: sum(weekRes),
      month: sum(monthRes)
    }
  }
}

/**
 * EMAIL TEMPLATES
 */

export const emailTemplatesService = {
  async getAll() {
    const { data, error } = await supabase
      .from('email_templates')
      .select('*')
      .order('created_at', { ascending: false })
    if (error) throw error
    return data || []
  },

  async create({ name, subject, body }) {
    const userId = await getCurrentUserId()
    const { data, error } = await supabase
      .from('email_templates')
      .insert({ name, subject, body, user_id: userId })
      .select()
      .single()
    if (error) throw error
    return data
  },

  async delete(id) {
    const { error } = await supabase
      .from('email_templates')
      .delete()
      .eq('id', id)
    if (error) throw error
  }
}

/**
 * GMAIL ACCOUNTS
 */

export const gmailService = {
  async getAccounts() {
    const { data, error } = await supabase
      .from('gmail_accounts')
      .select('id, email, active, created_at')
      .order('created_at', { ascending: false })
    if (error) throw error
    return data || []
  },

  async toggleAccount(id, active) {
    const { data, error } = await supabase
      .from('gmail_accounts')
      .update({ active })
      .eq('id', id)
      .select()
      .single()
    if (error) throw error
    return data
  },

  async deleteAccount(id) {
    const { error } = await supabase
      .from('gmail_accounts')
      .delete()
      .eq('id', id)
    if (error) throw error
  }
}

/**
 * REALTIME SUBSCRIPTIONS
 */

export const subscriptions = {
  subscribeToLeads(callback) {
    return supabase
      .channel('gmap_leads_changes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'gmap_leads' }, callback)
      .subscribe()
  },

  subscribeToTasks(callback) {
    return supabase
      .channel('tasks_changes')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'tasks' }, callback)
      .subscribe()
  },

  unsubscribe(subscription) {
    supabase.removeChannel(subscription)
  }
}
