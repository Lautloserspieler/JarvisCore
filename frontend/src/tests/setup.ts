import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/vue'
import '@testing-library/jest-dom/vitest'

// Cleanup after each test
afterEach(() => {
  cleanup()
})
