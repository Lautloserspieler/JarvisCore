import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@testing-library/vue'
import ChatTab from '@/components/tabs/ChatTab.vue'

describe('ChatTab', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders correctly', () => {
    const wrapper = mount(ChatTab)
    expect(wrapper.exists()).toBe(true)
  })

  it('displays welcome message when no messages', () => {
    const wrapper = mount(ChatTab)
    // Check for welcome elements
    expect(wrapper.html()).toContain('JARVIS')
  })

  it('handles user input', async () => {
    const wrapper = mount(ChatTab)
    const input = wrapper.find('textarea')
    
    expect(input.exists()).toBe(true)
  })

  it('displays connection status', () => {
    const wrapper = mount(ChatTab)
    // Should show connection badge
    expect(wrapper.html()).toContain('badge')
  })
})
