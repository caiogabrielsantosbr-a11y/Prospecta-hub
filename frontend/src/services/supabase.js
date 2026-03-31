/**
 * Supabase Service - Direct database operations
 * Frontend comunica DIRETAMENTE com Supabase para CRUD de dados
 */
import { supabase } from '../config/supabase'

/**
 * LEADS OPERATIONS
 */

export const leadsService = {
  /**
   * Get leads with filters and pagination
   */
  async getLeads({ limit = 50, offset = 0, conjunto, cidade, search } = {}) {
    let query = supabase
      .from('gmap_leads')
      .select('*', { count: 'exact' })
      .order('created_at', { ascending: false })
      .range(offset, offset + limit - 1)

    if (conjunto) {
      query = query.eq('conjunto_de_locais', conjunto)
    }

    if (cidade) {
      query = query.eq('cidade', cidade)
    }

    if (search) {
      query = query.or(`nome.ilike.%${search}%,telefone.ilike.%${search}%,website.ilike.%${search}%`)
    }

    const { data, error, count } = await query

    if (error) throw error

    return { leads: data, total: count }
  },

  /**
   * Get lead statistics
   */
  async getStats() {
    const { data, error } = await supabase
      .from('gmap_leads')
      .select('telefone,email,website')

    if (error) throw error

    const total = data.length
    const with_phone = data.filter(l => l.telefone && l.telefone !== 'Sem Telefone').length
    const with_email = data.filter(l => l.email).length
    const with_website = data.filter(l => l.website && l.website !== 'Sem Website').length

    return {
      total,
      with_phone,
      with_email,
      with_website,
      without_phone: total - with_phone,
      without_website: total - with_website
    }
  },

  /**
   * Get unique conjuntos
   */
  async getConjuntos() {
    const { data, error } = await supabase
      .from('gmap_leads')
      .select('conjunto_de_locais')

    if (error) throw error

    const conjuntos = [...new Set(data.map(l => l.conjunto_de_locais).filter(Boolean))]
    return conjuntos.sort()
  },

  /**
   * Get unique cidades for a conjunto
   */
  async getCidades(conjunto) {
    const { data, error } = await supabase
      .from('gmap_leads')
      .select('cidade')
      .eq('conjunto_de_locais', conjunto)

    if (error) throw error

    const cidades = [...new Set(data.map(l => l.cidade).filter(Boolean))]
    return cidades.sort()
  },

  /**
   * Update a lead
   */
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

  /**
   * Delete a lead
   */
  async deleteLead(leadId) {
    const { error } = await supabase
      .from('gmap_leads')
      .delete()
      .eq('id', leadId)

    if (error) throw error
  },

  /**
   * Delete multiple leads
   */
  async deleteLeads(leadIds) {
    const { error } = await supabase
      .from('gmap_leads')
      .delete()
      .in('id', leadIds)

    if (error) throw error
  },

  /**
   * Export leads with filters
   */
  async exportLeads({ conjunto, cidade, search } = {}) {
    let query = supabase
      .from('gmap_leads')
      .select('*')
      .order('created_at', { ascending: false })

    if (conjunto) {
      query = query.eq('conjunto_de_locais', conjunto)
    }

    if (cidade) {
      query = query.eq('cidade', cidade)
    }

    if (search) {
      query = query.or(`nome.ilike.%${search}%,telefone.ilike.%${search}%,website.ilike.%${search}%`)
    }

    const { data, error } = await query

    if (error) throw error
    return data
  }
}

/**
 * LOCATION SETS OPERATIONS (Shared - all users can access)
 */

export const locationSetsService = {
  /**
   * Get all location sets
   */
  async getAll() {
    const { data, error } = await supabase
      .from('location_sets')
      .select('*')
      .order('created_at', { ascending: false })

    if (error) throw error
    return data
  },

  /**
   * Get a single location set
   */
  async getById(id) {
    const { data, error } = await supabase
      .from('location_sets')
      .select('*')
      .eq('id', id)
      .single()

    if (error) throw error
    return data
  },

  /**
   * Create a location set
   */
  async create(locationSet) {
    const { data, error } = await supabase
      .from('location_sets')
      .insert(locationSet)
      .select()
      .single()

    if (error) throw error
    return data
  },

  /**
   * Update a location set
   */
  async update(id, updates) {
    const { data, error } = await supabase
      .from('location_sets')
      .update(updates)
      .eq('id', id)
      .select()
      .single()

    if (error) throw error
    return data
  },

  /**
   * Delete a location set
   */
  async delete(id) {
    const { error } = await supabase
      .from('location_sets')
      .delete()
      .eq('id', id)

    if (error) throw error
  }
}

/**
 * TASKS OPERATIONS
 */

export const tasksService = {
  /**
   * Get all tasks
   */
  async getAll() {
    const { data, error } = await supabase
      .from('tasks')
      .select('*')
      .order('created_at', { ascending: false })

    if (error) throw error
    return data
  },

  /**
   * Get a single task
   */
  async getById(taskId) {
    const { data, error } = await supabase
      .from('tasks')
      .select('*')
      .eq('id', taskId)
      .single()

    if (error) throw error
    return data
  },

  /**
   * Update task status
   */
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
 * REALTIME SUBSCRIPTIONS (Optional)
 */

export const subscriptions = {
  /**
   * Subscribe to leads changes
   */
  subscribeToLeads(callback) {
    const subscription = supabase
      .channel('gmap_leads_changes')
      .on('postgres_changes', 
        { event: '*', schema: 'public', table: 'gmap_leads' },
        callback
      )
      .subscribe()

    return subscription
  },

  /**
   * Subscribe to tasks changes
   */
  subscribeToTasks(callback) {
    const subscription = supabase
      .channel('tasks_changes')
      .on('postgres_changes',
        { event: '*', schema: 'public', table: 'tasks' },
        callback
      )
      .subscribe()

    return subscription
  },

  /**
   * Unsubscribe
   */
  unsubscribe(subscription) {
    supabase.removeChannel(subscription)
  }
}
