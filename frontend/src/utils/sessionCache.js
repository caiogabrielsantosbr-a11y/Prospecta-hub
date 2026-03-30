/**
 * Session Cache Utility for Location Sets
 * 
 * Manages caching of downloaded location JSON files in browser sessionStorage
 * with a 1-hour TTL. Handles quota exceeded errors by clearing oldest entries.
 */

const CACHE_TTL = 3600000 // 1 hour in milliseconds
const CACHE_KEY_PREFIX = 'location-set:'

/**
 * Session cache management utility
 */
export const sessionCache = {
  /**
   * Retrieve data from session cache
   * @param {string} key - Cache key (without prefix)
   * @returns {any|null} Cached data or null if not found/expired
   */
  get(key) {
    const cacheKey = `${CACHE_KEY_PREFIX}${key}`
    const cached = sessionStorage.getItem(cacheKey)
    
    if (!cached) {
      return null
    }
    
    try {
      const { data, timestamp } = JSON.parse(cached)
      const age = Date.now() - timestamp
      
      // Check if cache entry has expired (>1 hour)
      if (age > CACHE_TTL) {
        sessionStorage.removeItem(cacheKey)
        return null
      }
      
      return data
    } catch (error) {
      console.error('Failed to parse cached data:', error)
      sessionStorage.removeItem(cacheKey)
      return null
    }
  },
  
  /**
   * Store data in session cache with timestamp
   * @param {string} key - Cache key (without prefix)
   * @param {any} data - Data to cache
   */
  set(key, data) {
    const cacheKey = `${CACHE_KEY_PREFIX}${key}`
    
    try {
      sessionStorage.setItem(cacheKey, JSON.stringify({
        data,
        timestamp: Date.now()
      }))
    } catch (error) {
      // Handle quota exceeded error
      if (error.name === 'QuotaExceededError') {
        console.warn('Session storage quota exceeded, clearing oldest entries')
        this.clearOldest()
        
        // Retry after clearing
        try {
          sessionStorage.setItem(cacheKey, JSON.stringify({
            data,
            timestamp: Date.now()
          }))
        } catch (retryError) {
          console.error('Failed to cache after clearing oldest entries:', retryError)
          // Continue without caching - not a critical failure
        }
      } else {
        console.error('Failed to cache data:', error)
      }
    }
  },
  
  /**
   * Remove a specific cache entry
   * @param {string} key - Cache key (without prefix)
   */
  clear(key) {
    const cacheKey = `${CACHE_KEY_PREFIX}${key}`
    sessionStorage.removeItem(cacheKey)
  },
  
  /**
   * Clear all location set cache entries
   */
  clearAll() {
    const keys = Object.keys(sessionStorage)
    keys.forEach(key => {
      if (key.startsWith(CACHE_KEY_PREFIX)) {
        sessionStorage.removeItem(key)
      }
    })
  },
  
  /**
   * Clear the oldest cache entry to free up space
   * @private
   */
  clearOldest() {
    const entries = []
    
    // Collect all location-set cache entries with timestamps
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i)
      
      if (key && key.startsWith(CACHE_KEY_PREFIX)) {
        try {
          const value = JSON.parse(sessionStorage.getItem(key))
          entries.push({ 
            key, 
            timestamp: value.timestamp || 0 
          })
        } catch (error) {
          // If we can't parse it, remove it anyway
          sessionStorage.removeItem(key)
        }
      }
    }
    
    // Sort by timestamp (oldest first) and remove the oldest entry
    if (entries.length > 0) {
      entries.sort((a, b) => a.timestamp - b.timestamp)
      sessionStorage.removeItem(entries[0].key)
      console.log(`Cleared oldest cache entry: ${entries[0].key}`)
    }
  },
  
  /**
   * Get cache statistics
   * @returns {Object} Cache statistics
   */
  getStats() {
    const entries = []
    
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i)
      
      if (key && key.startsWith(CACHE_KEY_PREFIX)) {
        try {
          const value = JSON.parse(sessionStorage.getItem(key))
          const age = Date.now() - (value.timestamp || 0)
          const isExpired = age > CACHE_TTL
          
          entries.push({
            key: key.replace(CACHE_KEY_PREFIX, ''),
            timestamp: value.timestamp,
            age,
            isExpired,
            size: JSON.stringify(value).length
          })
        } catch (error) {
          // Skip invalid entries
        }
      }
    }
    
    return {
      totalEntries: entries.length,
      validEntries: entries.filter(e => !e.isExpired).length,
      expiredEntries: entries.filter(e => e.isExpired).length,
      totalSize: entries.reduce((sum, e) => sum + e.size, 0),
      entries
    }
  }
}

export default sessionCache
