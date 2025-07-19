# Contributing to AgentShop

Thank you for your interest in contributing to AgentShop! This guide will help you get started with contributing to our simplified AI agent marketplace.

## Getting Started

### Prerequisites

- **Node.js** 16.0+ and npm 8.0+
- **Python** 3.8+
- **Git** for version control
- **SQLite** (for development)

### Development Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/yourusername/agentshop.git
   cd agentshop
   ```

2. **Install Dependencies**
   ```bash
   # Install all dependencies
   npm run install:all
   ```

3. **Set Up Environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Add at least one LLM provider
   echo "LLM_OPENAI_ENABLED=true" >> .env
   echo "LLM_OPENAI_API_KEY=sk-your-key" >> .env
   ```

4. **Start Development Servers**
   ```bash
   # Start both frontend and backend
   npm run dev
   ```

5. **Verify Installation**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5000
   - Test API: http://localhost:5000/api/health

## Development Workflow

### 1. Create a Feature Branch

```bash
# Create and switch to feature branch
git checkout -b feature/amazing-feature

# Or for bug fixes
git checkout -b fix/important-bug
```

### 2. Make Your Changes

**Code Organization:**
- Follow the simplified architecture in `/core/`, `/backend/`, `/frontend/`
- Use existing patterns and conventions
- Import from `/core/` for base implementations

**Key Principles:**
- **Simplicity First** - Avoid over-engineering
- **Single Source of Truth** - Use core implementations
- **Startup-Focused** - Optimize for low traffic (1000+ visitors/day)
- **Documentation** - Update docs for any new features

### 3. Testing

```bash
# Run all tests
npm run test

# Run specific test suites
npm run test:frontend    # React tests
npm run test:backend     # Python tests

# Run linting
npm run lint

# Format code
npm run format
```

### 4. Commit Your Changes

**Commit Message Format:**
```
type(scope): description

Examples:
feat(llm): add Groq provider support
fix(auth): resolve session timeout issue
docs(setup): update installation instructions
refactor(core): consolidate repository patterns
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

### 5. Submit Pull Request

```bash
# Push your branch
git push origin feature/amazing-feature

# Create pull request on GitHub
```

## Architecture Guidelines

### Core Principles

1. **Use Core Implementations**
   ```python
   # Correct
   from core.repositories.base_repository import BaseRepository
   from core.orm.base_model import BaseModel
   
   # Avoid
   from backend.repositories.base_repository import BaseRepository
   ```

2. **Simplified Structure**
   ```
   # Consolidated structure
   backend/
   ├── controllers/     # All API endpoints
   ├── models/         # All domain models
   ├── repositories/   # All data access
   └── services/       # All business logic
   
   # Avoid nested complexity
   backend/webshop/api/controllers/...
   ```

3. **Startup-Focused**
   - Optimize for simplicity over enterprise features
   - Target low-traffic scenarios (1000+ daily visitors)
   - Prefer SQLite for development, PostgreSQL for production
   - Avoid over-abstraction

### File Organization

**Models:**
```python
# File: backend/models/your_model.py
from core.orm.base_model import BaseModel

class YourModel(BaseModel):
    # Implementation
```

**Repositories:**
```python
# File: backend/repositories/your_repository.py
from core.repositories.base_repository import BaseRepository

class YourRepository(BaseRepository[YourModel]):
    # Implementation
```

**Services:**
```python
# File: backend/services/your_service.py
from .your_repository import YourRepository

class YourService:
    # Business logic
```

**Controllers:**
```python
# File: backend/controllers/your_controller.py
from core.api.base_controller import BaseController

class YourController(BaseController):
    # API endpoints
```

## Testing Guidelines

### Backend Testing

**Test Structure:**
```python
# tests/test_your_feature.py
import pytest
from backend.models import YourModel
from backend.repositories import YourRepository

def test_your_feature():
    # Test implementation
    assert True
```

**Run Backend Tests:**
```bash
cd backend
python -m pytest tests/
```

### Frontend Testing

**Component Tests:**
```typescript
// tests/YourComponent.test.tsx
import { render, screen } from '@testing-library/react';
import YourComponent from '../components/YourComponent';

test('renders your component', () => {
  render(<YourComponent />);
  expect(screen.getByText('Expected Text')).toBeInTheDocument();
});
```

**Run Frontend Tests:**
```bash
cd frontend
npm test
```

## Code Style

### Python Style

**Follow PEP 8:**
```python
# Good
def calculate_total_cost(items: List[Item]) -> float:
    """Calculate total cost of items."""
    return sum(item.price for item in items)

# Avoid
def calcTotalCost(items):
    return sum([item.price for item in items])
```

**Use Type Hints:**
```python
from typing import List, Optional, Dict, Any

def process_data(data: Dict[str, Any]) -> Optional[List[str]]:
    # Implementation with clear types
```

### TypeScript/React Style

**Component Structure:**
```typescript
// Good
interface Props {
  title: string;
  onAction?: () => void;
}

export function YourComponent({ title, onAction }: Props) {
  return <div onClick={onAction}>{title}</div>;
}

// Avoid
export function YourComponent(props: any) {
  return <div onClick={props.onAction}>{props.title}</div>;
}
```

**Use Hooks Appropriately:**
```typescript
// Good
function useApiData(endpoint: string) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Fetch data
  }, [endpoint]);
  
  return { data, loading };
}
```

## Bug Reports

### Reporting Bugs

**Use GitHub Issues:**
1. Check existing issues first
2. Use the bug report template
3. Include reproduction steps
4. Add relevant logs/screenshots

**Issue Template:**
```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 20.04]
- Node.js: [e.g., 18.0.0]
- Python: [e.g., 3.9.0]
- Browser: [e.g., Chrome 100]
```

## Feature Requests

### Proposing Features

**Start with Discussion:**
1. Open a GitHub Discussion or Issue
2. Describe the use case
3. Explain the benefit
4. Consider implementation complexity

**Feature Criteria:**
- **Startup-Focused** - Benefits small-scale deployments
- **Simplicity** - Doesn't add unnecessary complexity
- **Performance** - Improves or maintains performance
- **Documentation** - Can be clearly documented

## UI/UX Contributions

### Design Guidelines

**Keep It Simple:**
- Clean, minimal interface
- Clear navigation
- Mobile-responsive
- Accessible (WCAG 2.1 AA)

**Component Consistency:**
- Use existing design tokens
- Follow established patterns
- Test across devices
- Consider loading states

## Documentation

### Documentation Types

**Code Documentation:**
- Clear docstrings for functions/classes
- Inline comments for complex logic
- Type hints for all parameters

**User Documentation:**
- Step-by-step guides
- Screenshot/video tutorials
- Common use cases
- Troubleshooting tips

**API Documentation:**
- Endpoint descriptions
- Request/response examples
- Error codes
- Rate limiting info

### Writing Style

**Technical Writing:**
- Clear and concise
- Use active voice
- Include examples
- Test all instructions

## Code Review Process

### Submitting for Review

**Pull Request Checklist:**
- [ ] Tests pass (`npm run test`)
- [ ] Code is linted (`npm run lint`)
- [ ] Documentation updated
- [ ] No breaking changes (or clearly noted)
- [ ] Follows architecture guidelines

**PR Description:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] All tests pass

## Screenshots (if applicable)
[Add screenshots for UI changes]
```

### Review Criteria

**Reviewers Check:**
- Code quality and style
- Architecture compliance
- Test coverage
- Documentation completeness
- Performance implications

## Release Process

### Versioning

**Semantic Versioning:**
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes

### Release Notes

**Include:**
- New features
- Bug fixes
- Breaking changes
- Migration guides
- Performance improvements

## Community

### Communication Channels

- **GitHub Issues** - Bug reports, feature requests
- **GitHub Discussions** - General questions, ideas
- **Discord/Slack** - Real-time community chat
- **Email** - contrib@agentshop.com

### Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/):
- Be respectful and inclusive
- Focus on constructive feedback
- Help create a welcoming environment
- Report inappropriate behavior

## Recognition

### Contributors

All contributors are recognized in:
- GitHub contributor list
- Release notes
- Documentation credits
- Community highlights

### Becoming a Maintainer

Regular contributors may be invited to become maintainers based on:
- Quality contributions
- Community involvement
- Technical expertise
- Alignment with project goals

## Getting Help

### Development Questions

- **GitHub Discussions** - Technical questions
- **Discord/Slack** - Real-time help
- **Email** - contrib@agentshop.com

### Resources

- [**Project Structure**](PROJECT_STRUCTURE.md) - Understand the codebase
- [**Installation Guide**](../site_admin/installation.md) - Setup instructions
- [**API Reference**](api-reference.md) - API documentation

---

**Thank you for contributing to AgentShop!**