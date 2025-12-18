# 🧪 Testing Guide for JARVIS Core

## Overview

JARVIS Core uses comprehensive testing strategies for both backend and frontend:

- **Backend**: pytest for Python tests
- **Frontend**: Vitest for Vue 3 components
- **CI/CD**: GitHub Actions for automated testing

---

## 🐍 Backend Testing (Python/pytest)

### Setup

```bash
cd backend
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_plugin_manager.py

# Run with verbose output
pytest -v

# Run only fast tests (skip slow)
pytest -m "not slow"
```

### Test Structure

```
backend/tests/
├── __init__.py
├── conftest.py                  # Fixtures and configuration
├── test_plugin_manager.py       # Plugin system tests
├── test_settings.py             # Settings management tests
├── test_api_endpoints.py        # FastAPI endpoint tests
└── test_model_downloader.py     # Model download tests
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch

class TestYourFeature:
    def test_basic_functionality(self):
        """Test description"""
        result = your_function()
        assert result == expected_value
    
    def test_with_fixture(self, mock_settings):
        """Use fixtures from conftest.py"""
        assert mock_settings['llm']['enabled'] is True
    
    @pytest.mark.slow
    def test_slow_operation(self):
        """Mark slow tests"""
        # Long-running test
        pass
```

### Coverage Goals

- **Target**: 80%+ code coverage
- **Critical paths**: 100% coverage for plugin system, API endpoints
- **View report**: Open `htmlcov/index.html` after running coverage

---

## 🎨 Frontend Testing (Vue/Vitest)

### Setup

```bash
cd frontend
npm install
```

### Running Tests

```bash
# Run tests in watch mode
npm run test

# Run tests once
npm run test:run

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

### Test Structure

```
frontend/src/tests/
├── setup.ts                     # Test configuration
├── components/
│   ├── ChatTab.test.ts         # ChatTab component tests
│   └── PluginsTab.test.ts      # PluginsTab component tests
└── i18n/
    └── translations.test.ts     # i18n validation tests
```

### Writing Component Tests

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@testing-library/vue'
import YourComponent from '@/components/YourComponent.vue'

describe('YourComponent', () => {
  it('renders correctly', () => {
    const wrapper = mount(YourComponent)
    expect(wrapper.exists()).toBe(true)
  })

  it('handles user interaction', async () => {
    const wrapper = mount(YourComponent)
    const button = wrapper.find('button')
    await button.trigger('click')
    
    expect(wrapper.emitted('click')).toBeTruthy()
  })
})
```

### Coverage Goals

- **Target**: 70%+ code coverage
- **Critical components**: 90%+ for ChatTab, PluginsTab, Settings
- **View report**: Open `coverage/index.html`

---

## 🔄 CI/CD Pipeline (GitHub Actions)

### Automatic Testing

Tests run automatically on:
- ✅ Every push to `main` or `develop`
- ✅ Every pull request
- ✅ Manual workflow dispatch

### Pipeline Stages

1. **Backend Tests**
   - Install Python dependencies
   - Run pytest with coverage
   - Upload to Codecov

2. **Frontend Tests**
   - Install Node.js dependencies
   - Run Vitest with coverage
   - Upload to Codecov

3. **Linting**
   - Python: Black, Flake8, MyPy
   - TypeScript: ESLint

4. **Build Test**
   - Test production build
   - Upload artifacts

### Viewing Results

- **GitHub Actions**: https://github.com/YOUR_USERNAME/JarvisCore/actions
- **Status Badge**: Add to README.md
  ```markdown
  ![CI](https://github.com/YOUR_USERNAME/JarvisCore/workflows/CI%2FCD%20Pipeline/badge.svg)
  ```

---

## 📊 Test Coverage

### Current Coverage

| Component | Coverage | Status |
|-----------|----------|--------|
| **Backend** | TBD | 🟡 In Progress |
| Plugin Manager | TBD | 🟡 In Progress |
| API Endpoints | TBD | 🟡 In Progress |
| **Frontend** | TBD | 🟡 In Progress |
| Components | TBD | 🟡 In Progress |
| i18n | TBD | 🟡 In Progress |

### Improving Coverage

1. **Identify untested code**:
   ```bash
   # Backend
   pytest --cov=. --cov-report=term-missing
   
   # Frontend
   npm run test:coverage
   ```

2. **Add tests for uncovered lines**

3. **Focus on critical paths first**:
   - Plugin enable/disable
   - Model loading
   - Chat message handling
   - Settings persistence

---

## 🐛 Debugging Tests

### Backend (pytest)

```bash
# Run with debugger
pytest --pdb

# Stop on first failure
pytest -x

# Print output even for passing tests
pytest -s
```

### Frontend (Vitest)

```bash
# Run UI for debugging
npm run test:ui

# Run specific test file
npm run test -- src/tests/components/ChatTab.test.ts
```

---

## ✅ Test Checklist for PRs

Before submitting a pull request:

- [ ] All tests pass locally
- [ ] New features have tests
- [ ] Coverage hasn't decreased
- [ ] Tests follow naming conventions
- [ ] No console errors in test output
- [ ] CI pipeline passes on GitHub

---

## 📝 Best Practices

### General

1. **Test naming**: Use descriptive names
   - ✅ `test_plugin_enables_successfully_with_valid_config`
   - ❌ `test_1`

2. **One assertion per test** (when possible)
   - Makes failures easier to debug

3. **Use fixtures** for reusable test data

4. **Mock external dependencies**
   - Don't make real API calls
   - Don't access real files

### Backend-Specific

1. **Use `@pytest.mark.asyncio`** for async tests
2. **Mock database calls**
3. **Test error cases**, not just happy paths

### Frontend-Specific

1. **Test user interactions**, not implementation
2. **Use `data-testid`** for reliable selectors
3. **Mock API calls** with `vi.fn()`

---

## 🚀 Running Full Test Suite

### Local Development

```bash
# Run everything
./run_all_tests.sh  # If script exists

# Or manually:
cd backend && pytest && cd ..
cd frontend && npm run test:run && cd ..
```

### Before Deployment

```bash
# Backend
cd backend
pytest --cov=. --cov-report=html --cov-fail-under=80

# Frontend
cd frontend
npm run test:coverage -- --coverage.lines=70
```

---

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Vue Test Utils](https://test-utils.vuejs.org/)
- [Testing Library](https://testing-library.com/)

---

## 🤝 Contributing Tests

See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Test contribution guidelines
- Code review process
- Test quality standards

---

**Questions?** Open an issue or ask in discussions!
