# Security Review Checklist

- [ ] Authentication is enforced on all protected endpoints
- [ ] Authorization checks exist and are correct
- [ ] Inputs are validated and sanitized (server-side)
- [ ] SQL uses parameterized queries
- [ ] No XSS vulnerabilities (output encoding in place)
- [ ] CSRF protection enabled
- [ ] No hardcoded secrets in code or config files
- [ ] Sensitive data is not logged
- [ ] Data encrypted at rest and in transit (TLS)
- [ ] CORS is properly configured (not wildcard in production)
- [ ] Rate limiting on authentication endpoints
- [ ] Dependencies scanned for known vulnerabilities
- [ ] File uploads validated (type, size, content)
- [ ] Error messages don't expose internal details
- [ ] Security headers configured (CSP, HSTS, X-Content-Type-Options)
