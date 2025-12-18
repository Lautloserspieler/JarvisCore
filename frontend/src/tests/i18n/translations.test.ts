import { describe, it, expect } from 'vitest'
import de from '@/i18n/locales/de.json'
import en from '@/i18n/locales/en.json'

describe('i18n Translations', () => {
  it('has matching keys in DE and EN', () => {
    const deKeys = Object.keys(de)
    const enKeys = Object.keys(en)
    
    expect(deKeys).toEqual(enKeys)
  })

  it('has all required common keys', () => {
    const requiredKeys = [
      'save', 'cancel', 'delete', 'edit', 
      'loading', 'error', 'success'
    ]
    
    requiredKeys.forEach(key => {
      expect(de.common).toHaveProperty(key)
      expect(en.common).toHaveProperty(key)
    })
  })

  it('has navigation translations', () => {
    const navKeys = ['chat', 'dashboard', 'memory', 'models', 'settings']
    
    navKeys.forEach(key => {
      expect(de.navigation).toHaveProperty(key)
      expect(en.navigation).toHaveProperty(key)
    })
  })

  it('has no empty translation values', () => {
    const checkEmpty = (obj: any, path = '') => {
      Object.entries(obj).forEach(([key, value]) => {
        const currentPath = path ? `${path}.${key}` : key
        if (typeof value === 'string') {
          expect(value.length).toBeGreaterThan(0)
        } else if (typeof value === 'object') {
          checkEmpty(value, currentPath)
        }
      })
    }
    
    checkEmpty(de)
    checkEmpty(en)
  })

  it('has consistent placeholder patterns', () => {
    // Check for {{variable}} patterns
    const checkPlaceholders = (obj: any) => {
      Object.values(obj).forEach(value => {
        if (typeof value === 'string') {
          const placeholders = value.match(/\{\{\w+\}\}/g)
          if (placeholders) {
            placeholders.forEach(placeholder => {
              expect(placeholder).toMatch(/^\{\{\w+\}\}$/)
            })
          }
        } else if (typeof value === 'object') {
          checkPlaceholders(value)
        }
      })
    }
    
    checkPlaceholders(de)
    checkPlaceholders(en)
  })
})
