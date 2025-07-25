# Flask Foundation & Project Structure Implementation Plan

## Overview
Implement a minimal foundational Flask web application integrated directly into the existing application/ structure. This creates a basic web interface with a simple dashboard showing the 3 most recent invoices, demonstrating database connectivity. No authentication or CRUD needed for this minimal foundation.

## Dashboard Requirements
The dashboard should display:
- Basic welcome message
- List of the 3 most recent invoices (demonstrating database connectivity)
- If no invoices exist, show friendly "No invoices yet" message
- Basic navigation structure ready for expansion
- Simple, clean layout as foundation for future features

### Dashboard Data Structure
The dashboard template will receive:
```python
{
    'recent_invoices': [
        {
            'id': int,
            'invoice_number': str,
            'customer_name': str,
            'invoice_date': date,
            'total_amount': float
        }
    ]  # Empty list if no invoices
}
```

## Health Check Endpoint Requirements
The `/status` endpoint should:
- Return JSON response with application health status
- Test database connectivity by executing `SELECT COUNT(*) FROM invoices`
- Include total invoice count as proof of basic functionality
- Return HTTP 200 for healthy, HTTP 503 for unhealthy
- Response format:
  - Healthy: `{"status": "healthy", "database": "connected", "total_invoices": N}`
  - Unhealthy: `{"status": "unhealthy", "error": "error message"}`

### Error Handling Approach
- Dashboard route: Display friendly error message if database unavailable
- Status endpoint: Catch database exceptions and return 503 with error details
- Use try/except blocks around database operations

## File Structure Changes

### New Files
```
application/
├── app.py                     # Flask app factory with configuration  
├── routes.py                  # Basic routes (just dashboard for now)
├── templates/
│   ├── base.html              # Simple base layout
│   └── dashboard.html         # Simple dashboard template with system info
└── static/
    └── css/
        └── main.css           # Basic minimal styles
```

### Modified Files
- `pyproject.toml` - Add Flask dependencies with uv add
- `README.md` - Add web interface usage instructions
- `Makefile` - Add `make dev` command
- `CLAUDE.md` - Update to reflect that this is now a web application

## New Classes/Functions

### application/app.py
- `create_app()` - Flask app factory function
- `configure_logging()` - Set up application logging

### application/routes.py
- `dashboard()` - Render dashboard with 3 most recent invoices using `Invoice.get_recent(3)`
- `health_check()` - Health endpoint that returns JSON with database connectivity status and invoice count

### application/models.py (additions)
- `Invoice.get_recent(limit)` - Static method to efficiently fetch N most recent invoices with LIMIT clause

## Implementation Strategy

### Phase 1: Minimal Flask Setup
1. Add Flask dependencies with uv add
2. Add `Invoice.get_recent(limit)` method to application/models.py
3. Create Flask app factory in application/app.py
4. Create simple dashboard route in application/routes.py
5. Create basic templates structure

### Phase 2: Basic Templates & Static Assets
1. Create simple base.html template
2. Create dashboard.html template to display recent invoices
3. Add minimal CSS for basic styling
4. Set up static file serving

### Phase 3: Testing & Integration
1. Add Flask test client to existing pytest setup
2. Create basic route test
3. Verify templates render correctly
4. Test integration with existing application structure

## Code Modifications

### pyproject.toml
Add Flask dependencies using uv add:
```bash
uv add flask
uv add flask-wtf
```

### Makefile
Add web development command:
```makefile
dev:
	python -m application.app
```

## Testing Strategy

### Unit Tests
- Test Flask app factory configuration
- Test basic route functions
- Test template rendering with simple data

### Integration Tests  
- Test full request/response cycle for dashboard
- Test static file serving
- Test template inheritance

### Manual Testing
- Verify web application starts with `make dev`
- Verify dashboard loads at http://localhost:5000 and displays recent invoices
- Verify status endpoint at http://localhost:5000/status returns proper JSON
- Verify templates render with proper styling
- Verify static assets load correctly

## Integration Points

### Existing Application Structure
- Flask files located directly in `application/` alongside existing modules
- Can easily import and use existing controllers, models, and utilities
- Seamless code sharing between CLI and web interfaces

### Database Integration
- Uses existing `db.py` connection management for invoice queries
- Adds new `Invoice.get_recent(limit)` method to `models.py` for efficient recent invoice queries
- Dashboard will use `Invoice.get_recent(3)` to show 3 most recent invoices
- Demonstrates database connectivity from the start
- No schema changes required for this minimal foundation

### Template System
- Simple HTML templates with basic structure
- Foundation for more complex templates in future tickets
- Ready to integrate with existing application data when needed

## Configuration Considerations

### Development Configuration
- Debug mode enabled for development
- Auto-reload on file changes
- Simple development server setup

### Basic Flask Configuration  
- Minimal configuration for this foundation
- Ready to expand with environment variables in future tickets
- Static file serving from `application/static/` (may need explicit configuration if Flask defaults don't work)

## Documentation Updates

### README.md Updates
- Add "Web Interface" section with basic setup
- Document new Flask dependencies
- Add `make dev` command usage
- Simple getting started instructions

### CLAUDE.md Updates
- Update project description to reflect web application capabilities
- Add note that Claude should assume user has already run `make dev` for web testing
- Document web interface context for future development

### Usage Instructions
- How to start the web interface (`make dev`)
- How to access the dashboard (http://localhost:5000)
- Basic development workflow

## Implementation Checklist

### Phase 1: Minimal Flask Setup
- [ ] Create new branch `flask_foundation_22`
- [ ] Add Flask dependencies with `uv add flask` and `uv add flask-wtf`
- [ ] Add `Invoice.get_recent(limit)` method to application/models.py
- [ ] Implement minimal Flask app factory in application/app.py
- [ ] Create simple dashboard route in application/routes.py
- [ ] Add `make dev` command to Makefile

### Phase 2: Basic Templates & Static Assets
- [ ] Create application/templates/ directory structure
- [ ] Create simple base.html template
- [ ] Create dashboard.html template to display recent invoices
- [ ] Set up application/static/css/ directory with minimal CSS
- [ ] Configure static file serving in Flask app
- [ ] Test basic template rendering

### Phase 3: Testing & Integration
- [ ] Add Flask test client to existing conftest.py
- [ ] Create test for `Invoice.get_recent(limit)` method
- [ ] Create basic test for dashboard route
- [ ] Test that dashboard displays recent invoices from database
- [ ] Test dashboard with empty invoice database (shows "No invoices yet")
- [ ] Create test for status endpoint (both healthy and error cases)
- [ ] Test template rendering works
- [ ] Test static file serving
- [ ] Verify import structure works when running the app
- [ ] Verify no conflicts with existing application structure

### Phase 4: Quality Assurance
- [ ] Run `make lint` and fix any issues
- [ ] Update README.md with basic web interface documentation
- [ ] Update CLAUDE.md to reflect this is now a web application
- [ ] Test `make dev` command works
- [ ] Verify dashboard loads at http://localhost:5000 and shows recent invoices
- [ ] Verify `make generate` still works (no regressions)
- [ ] Run full test suite to ensure no breakage

## Future Maintenance
- This minimal foundation provides the structure for future web features
- Future routes should integrate with existing controllers in application/controllers/
- Templates can be expanded with more complex components as needed
- The integrated application/ location enables seamless code sharing between CLI and web interfaces
- Future developers should understand the Flask app factory pattern used in application/app.py