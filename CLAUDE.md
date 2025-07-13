# Claude Code Guidelines

## Development Workflow

### 1. Available Commands
Run `make` or `make help` to see all available commands. This project uses a Makefile for common tasks.

### 2. Linting Requirements
**Always run `make lint` before any commits.** This ensures code quality and consistency by running:
- ruff (linting and formatting)
- pyright (type checking)
- pylint (code quality)

### 3. Git Workflow
- **Do not run `git add`** - The user will handle staging files
- When committing, use the conversation context to write meaningful commit messages rather than relying on `git diff`
- Focus on the "why" of changes based on our discussion, not just the "what"
- Always do work on a new branch, not main
- When working on a ticket, put the ticket number in commit message and PR
- When user says "Review time":
  a. Make sure we're not on main branch
  b. Commit what we've done
  c. Push to remote
  d. Create a PR with `gh`
- When user says "made suggestions on the pr":
  - Get PR comments with `gh api repos/OWNER/REPO/pulls/PULL_NUMBER/comments`
  - Address those comments
  - Watch out for multiple PR comments on one code line
- When user says "merge", do a gh pr merge with a merge commit and use the option to delete local and remote branches
- When we merge via gh, it deletes the branch on remote AND LOCAL and checks out main for us

### 4. Code Quality Standards
- Maintain a high pylint score (currently 10.00/10)
- All Python files should specify UTF-8 encoding when opening files
- Follow PEP 8 style guidelines (enforced by ruff)
- Keep imports properly ordered (enforced by ruff)

### 5. Pre-Commit Checklist
Before any commit:
1. Run `make lint` to check and fix code style
2. Ensure all linters pass without errors
3. Verify the generated invoice still works with `make generate`
4. Write a descriptive commit message based on our conversation