# TODO - Future Enhancements

## CI/CD Pipeline
- [ ] **GitHub Actions for CI**: Set up automated testing and linting on pull requests
  - Run `make lint` and `make test` on every PR
  - Test against multiple Python versions
  - Ensure all checks pass before merge

## Testing Improvements
- [ ] **Add test coverage reporting**: Integrate coverage.py with make command
  - Add `make test-coverage` command to generate coverage reports
  - Set minimum coverage thresholds
  - Display coverage in CI pipeline

## Email Features
- [ ] **Email support**: Add capability to automatically send invoices via email
  - SMTP configuration for sending emails
  - Email templates for invoice delivery
  - Attachment support for PDF invoices
  - Client contact management integration