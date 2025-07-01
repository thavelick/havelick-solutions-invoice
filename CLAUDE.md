# Claude Code Guidelines

## Development Workflow

### 1. Available Commands
Run `make` or `make help` to see all available commands. This project uses a Makefile for common tasks.

### 2. Linting Requirements
**Always run `make lint` before any commits.** This ensures code quality and consistency by running:
- isort (import sorting)
- black (code formatting)
- pyright (type checking)
- pylint (code quality)

### 3. Git Workflow
- **Do not run `git add`** - The user will handle staging files
- When committing, use the conversation context to write meaningful commit messages rather than relying on `git diff`
- Focus on the "why" of changes based on our discussion, not just the "what"

### 4. Code Quality Standards
- Maintain a high pylint score (currently 9.86/10)
- All Python files should specify UTF-8 encoding when opening files
- Follow PEP 8 style guidelines (enforced by black)
- Keep imports properly ordered (standard library, then third-party)

### 5. Pre-Commit Checklist
Before any commit:
1. Run `make lint` to check and fix code style
2. Ensure all linters pass without errors
3. Verify the generated invoice still works with `make generate`
4. Write a descriptive commit message based on our conversation