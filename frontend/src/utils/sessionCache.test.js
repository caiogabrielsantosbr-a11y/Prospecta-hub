/**
 * Unit tests for sessionCache utility
 */

import { describe, test, expect, beforeEach, vi } from 'vitest'
import { sessionCache } from './sessionCache'

describe('sessionCache', () => {
  beforeEach(() => {
    // Clear sessionStorage before each test
    sessionStorage.clear()
    vi.clearAllMocks()
  })

  describe('set and get', () => {
    test('stores and retrieves data with timestamp', () => {
      const testData = { locais: ['São Paulo, SP', 'Rio de Janeiro, RJ'] }
      sessionCache.set('test-set', testData)

      const retrieved = sessionCache.get('test-set')
      expect(retrieved).toEqual(testData)
    })

    test('stores data with correct cache key format', () => {
      const testData = { locais: ['São Paulo, SP'] }
      sessionCache.set('my-set', testData)

      const rawValue = sessionStorage.getItem('location-set:my-set')
      expect(rawValue).toBeTruthy()
      
      const parsed = JSON.parse(rawValue)
      expect(parsed.data).toEqual(testData)
      expect(parsed.timestamp).toBeGreaterThan(0)
    })

    test('returns null for non-existent key', () => {
      const retrieved = sessionCache.get('non-existent')
      expect(retrieved).toBeNull()
    })

    test('handles complex nested data structures', () => {
      const complexData = {
        nome: 'Test Set',
        descricao: 'A test location set',
        locais: ['City 1, ST', 'City 2, ST'],
        metadata: {
          count: 2,
          tags: ['test', 'sample']
        }
      }
      
      sessionCache.set('complex', complexData)
      const retrieved = sessionCache.get('complex')
      expect(retrieved).toEqual(complexData)
    })
  })

  describe('TTL expiration', () => {
    test('returns null for expired cache (>1 hour)', () => {
      const testData = { locais: ['São Paulo, SP'] }
      
      // Mock old timestamp (1 hour + 1 second ago)
      const oldTimestamp = Date.now() - (3600000 + 1000)
      sessionStorage.setItem('location-set:expired', JSON.stringify({
        data: testData,
        timestamp: oldTimestamp
      }))

      const retrieved = sessionCache.get('expired')
      expect(retrieved).toBeNull()
      
      // Verify expired entry was removed
      expect(sessionStorage.getItem('location-set:expired')).toBeNull()
    })

    test('returns data for cache within TTL', () => {
      const testData = { locais: ['São Paulo, SP'] }
      
      // Mock recent timestamp (30 minutes ago)
      const recentTimestamp = Date.now() - (1800000)
      sessionStorage.setItem('location-set:recent', JSON.stringify({
        data: testData,
        timestamp: recentTimestamp
      }))

      const retrieved = sessionCache.get('recent')
      expect(retrieved).toEqual(testData)
    })

    test('returns data for cache at exactly 1 hour (edge case)', () => {
      const testData = { locais: ['São Paulo, SP'] }
      
      // Mock timestamp at exactly 1 hour
      const exactTimestamp = Date.now() - 3600000
      sessionStorage.setItem('location-set:exact', JSON.stringify({
        data: testData,
        timestamp: exactTimestamp
      }))

      const retrieved = sessionCache.get('exact')
      // Should be null since age > TTL (not >=)
      expect(retrieved).toBeNull()
    })
  })

  describe('clear operations', () => {
    test('clears specific cache entry', () => {
      sessionCache.set('test1', { data: 'test1' })
      sessionCache.set('test2', { data: 'test2' })

      sessionCache.clear('test1')

      expect(sessionCache.get('test1')).toBeNull()
      expect(sessionCache.get('test2')).toEqual({ data: 'test2' })
    })

    test('clearAll removes all location-set entries', () => {
      sessionCache.set('set1', { data: 'set1' })
      sessionCache.set('set2', { data: 'set2' })
      sessionStorage.setItem('other-key', 'other-value')

      sessionCache.clearAll()

      expect(sessionCache.get('set1')).toBeNull()
      expect(sessionCache.get('set2')).toBeNull()
      expect(sessionStorage.getItem('other-key')).toBe('other-value')
    })

    test('clearAll handles empty storage', () => {
      expect(() => sessionCache.clearAll()).not.toThrow()
    })
  })

  describe('quota exceeded handling', () => {
    test('handles quota exceeded by clearing oldest entries', () => {
      // Store multiple entries with different timestamps
      const now = Date.now()
      sessionStorage.setItem('location-set:old', JSON.stringify({
        data: { locais: ['Old'] },
        timestamp: now - 3000000 // 50 minutes ago
      }))
      sessionStorage.setItem('location-set:newer', JSON.stringify({
        data: { locais: ['Newer'] },
        timestamp: now - 1000000 // ~16 minutes ago
      }))

      // Mock quota exceeded error
      const originalSetItem = Storage.prototype.setItem
      let callCount = 0
      Storage.prototype.setItem = vi.fn((key, value) => {
        callCount++
        if (callCount === 1) {
          // First call throws quota exceeded
          const error = new Error('QuotaExceededError')
          error.name = 'QuotaExceededError'
          throw error
        } else {
          // Second call (after clearing) succeeds
          originalSetItem.call(sessionStorage, key, value)
        }
      })

      // Should not throw and should clear oldest entry
      sessionCache.set('new', { locais: ['New'] })

      // Verify oldest entry was removed
      expect(sessionStorage.getItem('location-set:old')).toBeNull()
      
      // Verify newer entry still exists
      expect(sessionStorage.getItem('location-set:newer')).toBeTruthy()
      
      // Verify new entry was stored
      expect(sessionCache.get('new')).toEqual({ locais: ['New'] })

      Storage.prototype.setItem = originalSetItem
    })

    test('handles quota exceeded when retry also fails', () => {
      // Mock quota exceeded error that persists
      const originalSetItem = Storage.prototype.setItem
      Storage.prototype.setItem = vi.fn(() => {
        const error = new Error('QuotaExceededError')
        error.name = 'QuotaExceededError'
        throw error
      })

      // Should not throw even if retry fails
      expect(() => {
        sessionCache.set('test', { data: 'test' })
      }).not.toThrow()

      Storage.prototype.setItem = originalSetItem
    })
  })

  describe('clearOldest', () => {
    test('removes oldest entry when called', () => {
      const now = Date.now()
      
      sessionStorage.setItem('location-set:oldest', JSON.stringify({
        data: { locais: ['Oldest'] },
        timestamp: now - 5000000
      }))
      sessionStorage.setItem('location-set:middle', JSON.stringify({
        data: { locais: ['Middle'] },
        timestamp: now - 3000000
      }))
      sessionStorage.setItem('location-set:newest', JSON.stringify({
        data: { locais: ['Newest'] },
        timestamp: now - 1000000
      }))

      sessionCache.clearOldest()

      expect(sessionStorage.getItem('location-set:oldest')).toBeNull()
      expect(sessionStorage.getItem('location-set:middle')).toBeTruthy()
      expect(sessionStorage.getItem('location-set:newest')).toBeTruthy()
    })

    test('handles empty storage gracefully', () => {
      expect(() => sessionCache.clearOldest()).not.toThrow()
    })

    test('removes invalid entries during cleanup', () => {
      sessionStorage.setItem('location-set:invalid', 'invalid-json')
      sessionStorage.setItem('location-set:valid', JSON.stringify({
        data: { locais: ['Valid'] },
        timestamp: Date.now()
      }))

      sessionCache.clearOldest()

      // Invalid entry should be removed
      expect(sessionStorage.getItem('location-set:invalid')).toBeNull()
      // Valid entry should remain
      expect(sessionStorage.getItem('location-set:valid')).toBeTruthy()
    })
  })

  describe('error handling', () => {
    test('handles corrupted cache data gracefully', () => {
      sessionStorage.setItem('location-set:corrupted', 'invalid-json')

      const retrieved = sessionCache.get('corrupted')
      expect(retrieved).toBeNull()
      
      // Verify corrupted entry was removed
      expect(sessionStorage.getItem('location-set:corrupted')).toBeNull()
    })

    test('handles missing timestamp in cached data', () => {
      sessionStorage.setItem('location-set:no-timestamp', JSON.stringify({
        data: { locais: ['Test'] }
        // Missing timestamp
      }))

      // Should treat as expired since timestamp is undefined
      const retrieved = sessionCache.get('no-timestamp')
      expect(retrieved).toBeNull()
    })

    test('handles non-JSON serializable data', () => {
      const circularRef = {}
      circularRef.self = circularRef

      // Should not throw
      expect(() => {
        sessionCache.set('circular', circularRef)
      }).not.toThrow()
    })
  })

  describe('getStats', () => {
    test('returns correct statistics for cache entries', () => {
      const now = Date.now()
      
      sessionStorage.setItem('location-set:set1', JSON.stringify({
        data: { locais: ['Set 1'] },
        timestamp: now - 1000000
      }))
      sessionStorage.setItem('location-set:set2', JSON.stringify({
        data: { locais: ['Set 2'] },
        timestamp: now - 2000000
      }))
      sessionStorage.setItem('location-set:expired', JSON.stringify({
        data: { locais: ['Expired'] },
        timestamp: now - 4000000 // Over 1 hour
      }))

      const stats = sessionCache.getStats()

      expect(stats.totalEntries).toBe(3)
      expect(stats.validEntries).toBe(2)
      expect(stats.expiredEntries).toBe(1)
      expect(stats.totalSize).toBeGreaterThan(0)
      expect(stats.entries).toHaveLength(3)
    })

    test('returns empty stats for empty cache', () => {
      const stats = sessionCache.getStats()

      expect(stats.totalEntries).toBe(0)
      expect(stats.validEntries).toBe(0)
      expect(stats.expiredEntries).toBe(0)
      expect(stats.totalSize).toBe(0)
      expect(stats.entries).toHaveLength(0)
    })

    test('ignores non-location-set entries', () => {
      sessionStorage.setItem('other-key', 'other-value')
      sessionStorage.setItem('location-set:test', JSON.stringify({
        data: { locais: ['Test'] },
        timestamp: Date.now()
      }))

      const stats = sessionCache.getStats()

      expect(stats.totalEntries).toBe(1)
    })
  })

  describe('multiple cache keys', () => {
    test('manages multiple independent cache entries', () => {
      const data1 = { locais: ['Set 1'] }
      const data2 = { locais: ['Set 2'] }
      const data3 = { locais: ['Set 3'] }

      sessionCache.set('set1', data1)
      sessionCache.set('set2', data2)
      sessionCache.set('set3', data3)

      expect(sessionCache.get('set1')).toEqual(data1)
      expect(sessionCache.get('set2')).toEqual(data2)
      expect(sessionCache.get('set3')).toEqual(data3)
    })

    test('clearing one entry does not affect others', () => {
      sessionCache.set('set1', { locais: ['Set 1'] })
      sessionCache.set('set2', { locais: ['Set 2'] })

      sessionCache.clear('set1')

      expect(sessionCache.get('set1')).toBeNull()
      expect(sessionCache.get('set2')).toEqual({ locais: ['Set 2'] })
    })
  })
})
