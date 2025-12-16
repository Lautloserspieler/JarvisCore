# Contributing to JarvisCore

First off, thank you for considering contributing to JarvisCore! 🎉 It's people like you that make JarvisCore such a great tool.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [INSERT CONTACT EMAIL].

## Getting Started

### Prerequisites

- Python 3.11+
- Go 1.21+
- Node.js 18+ and npm
- Docker and Docker Compose
- Git

### Fork & Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/JarvisCore.git
   cd JarvisCore
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/Lautloserspieler/JarvisCore.git
   ```

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs **actual behavior**
- **Screenshots** if applicable
- **Environment details** (OS, Python version, Docker version, etc.)
- **Relevant logs** from `logs/` directory

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **List any alternatives** you've considered

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:

- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `documentation` - Improvements or additions to documentation

### Pull Requests

Pull requests are the best way to propose changes. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`
2. Make your changes
3. Add tests if applicable
4. Ensure all tests pass
5. Update documentation
6. Submit a pull request

## Development Setup

### Local Development (Docker)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/JarvisCore.git
cd JarvisCore

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Local Development (Native)

#### Backend (Python)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend
python main.py
```

#### Frontend (Vue 3)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

#### Go Services

```bash
cd go-services/gateway

# Install dependencies
go mod download

# Run service
go run cmd/gateway/main.go
```

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Adding tests
- `chore/` - Maintenance tasks

### 2. Make Your Changes

- Follow the [Coding Standards](#coding-standards)
- Write meaningful commit messages
- Keep commits atomic and focused
- Add tests for new features

### 3. Test Your Changes

```bash
# Run Python tests
cd backend
pytest tests/

# Run Go tests
cd go-services/gateway
go test ./...

# Run Frontend tests
cd frontend
npm run test

# Run integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### 4. Update Documentation

- Update relevant README sections
- Add/update code comments
- Update API documentation if applicable
- Add entries to CHANGELOG.md

### 5. Submit Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:

- Clear title describing the change
- Detailed description of what and why
- Link to related issues
- Screenshots/GIFs if UI changes
- Checklist of completed tasks

### 6. Code Review

- Address review comments
- Keep discussions focused and professional
- Update your PR based on feedback
- Request re-review when ready

## Coding Standards

### Python (Backend)

- Follow [PEP 8](https://pep8.org/) style guide
- Use [Black](https://black.readthedocs.io/) for formatting
- Use type hints where appropriate
- Maximum line length: 88 characters
- Use meaningful variable names

```python
# Good
def process_user_input(user_message: str) -> dict:
    """Process user message and return response."""
    return {"response": processed_message}

# Bad
def p(m):
    return {"r": m}
```

### Go (Services)

- Follow [Effective Go](https://golang.org/doc/effective_go) guidelines
- Use `gofmt` for formatting
- Use meaningful package names
- Write godoc comments for public functions

```go
// Good
// ProcessMessage handles incoming message and returns response
func ProcessMessage(msg string) (string, error) {
    // ...
}

// Bad
func p(m string) string {
    // ...
}
```

### TypeScript/Vue (Frontend)

- Follow Vue 3 Composition API best practices
- Use TypeScript for type safety
- Use ESLint configuration provided
- Component names in PascalCase
- Props validation required

```typescript
// Good
interface Props {
  userId: string
  userName: string
}

const props = defineProps<Props>()

// Bad
const props = defineProps({
  id: String,
  name: String
})
```

### General Guidelines

- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- Write self-documenting code
- Comment complex logic
- Avoid premature optimization

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Examples

```bash
# Good
feat(backend): add user authentication system
fix(frontend): resolve chat input focus issue
docs(readme): update installation instructions

# Bad
update
fixed bug
added stuff
```

## Testing

### Writing Tests

- Write tests for all new features
- Maintain test coverage above 80%
- Test edge cases and error conditions
- Use descriptive test names

### Test Structure

```python
# Python (pytest)
def test_user_authentication_success():
    """Test successful user authentication."""
    result = authenticate_user("valid_token")
    assert result.is_authenticated
    assert result.user_id is not None

def test_user_authentication_invalid_token():
    """Test authentication with invalid token."""
    with pytest.raises(AuthenticationError):
        authenticate_user("invalid_token")
```

```go
// Go
func TestProcessMessage(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    string
        wantErr bool
    }{
        {"valid input", "hello", "processed", false},
        {"empty input", "", "", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ProcessMessage(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("ProcessMessage() error = %v, wantErr %v", err, tt.wantErr)
            }
            if got != tt.want {
                t.Errorf("ProcessMessage() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

## Documentation

### Code Documentation

- Document all public APIs
- Use docstrings for Python functions/classes
- Use godoc comments for Go functions
- Use JSDoc for TypeScript/JavaScript

### User Documentation

- Update README.md for user-facing changes
- Add examples for new features
- Keep installation instructions current
- Update troubleshooting guide

### API Documentation

- Document all endpoints
- Include request/response examples
- Specify required/optional parameters
- Document error codes

## Getting Help

If you need help, you can:

- Check our [Documentation](docs/)
- Ask in [GitHub Discussions](https://github.com/Lautloserspieler/JarvisCore/discussions)
- Join our [Discord Server](#) (coming soon)
- Email us at [INSERT CONTACT EMAIL]

## Recognition

Contributors will be:

- Listed in [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Mentioned in release notes
- Recognized in our README
- Given special roles in community spaces

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).

---

**Thank you for contributing to JarvisCore!** 🚀
