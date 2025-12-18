import { describe, it, expect, vi } from 'vitest'
import { mount } from '@testing-library/vue'
import PluginsTab from '@/components/tabs/PluginsTab.vue'

describe('PluginsTab', () => {
  it('renders loading state initially', () => {
    const wrapper = mount(PluginsTab)
    expect(wrapper.html()).toContain('Loading')
  })

  it('displays plugin list when loaded', async () => {
    // Mock fetch
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          {
            id: 'test_plugin',
            name: 'Test Plugin',
            enabled: false,
            version: '1.0.0'
          }
        ])
      })
    ) as any

    const wrapper = mount(PluginsTab)
    
    // Wait for data to load
    await new Promise(resolve => setTimeout(resolve, 100))
    
    expect(wrapper.html()).toContain('Plugin')
  })

  it('filters out system plugins', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve([
          { id: 'calculator_plugin', name: 'Calculator', enabled: true },
          { id: 'user_plugin', name: 'User Plugin', enabled: false }
        ])
      })
    ) as any

    const wrapper = mount(PluginsTab)
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // Should not contain system plugins
    expect(wrapper.html()).not.toContain('calculator_plugin')
  })
})
