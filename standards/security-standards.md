# Security Standards

## Core Principles
1. **Secure by default** — systems must be secure out of the box
2. **Defense in depth** — multiple layers of security
3. **Least privilege** — minimum access needed
4. **Zero trust** — verify everything, trust nothing

## Standards

### Authentication
- Use industry-standard protocols (OAuth 2.0, OIDC, SAML)
- Hash passwords with bcrypt or argon2 (never MD5, SHA-1, or SHA-256 alone)
- Enforce strong passwords or passkeys
- Implement account lockout after failed attempts
- Use MFA for privileged accounts

### Authorization
- Check permissions at every access point (not just the UI)
- Use role-based or attribute-based access control
- Audit privilege escalation events
- Review access permissions periodically

### Data Protection
- Encrypt sensitive data at rest (AES-256 or equivalent)
- Enforce TLS 1.2+ for all communications
- Classify data by sensitivity level
- Implement data retention and deletion policies
- Never log PII, credentials, or tokens

### Input Security
- Validate and sanitize ALL external inputs on the server side
- Use parameterized queries (never string concatenation for SQL)
- Encode output to prevent XSS
- Validate file uploads (type, size, content scanning)

### Infrastructure
- Keep all software up to date (OS, runtime, libraries)
- Scan dependencies for known vulnerabilities regularly
- Configure security headers (CSP, HSTS, X-Frame-Options, etc.)
- Implement rate limiting on all public endpoints
- Use network segmentation and firewalls
