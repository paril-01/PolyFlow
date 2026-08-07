# Playbook: Security Audit

## When to Use
Conducting a security review of an application or component.

## Process

### Step 1: Scope Definition
1. Define what's being audited (full app, specific component, API)
2. Identify the threat model — who are the potential attackers?
3. Identify sensitive data — PII, credentials, financial data
4. Review compliance requirements — GDPR, HIPAA, PCI-DSS

### Step 2: Authentication & Authorization Review
- [ ] Authentication mechanism is industry standard (OAuth 2.0, OIDC)
- [ ] Passwords are hashed with bcrypt/argon2 (never MD5/SHA)
- [ ] Session management is secure (proper expiry, rotation)
- [ ] Authorization checks at every endpoint
- [ ] Principle of least privilege enforced

### Step 3: Input Validation Review
- [ ] All user inputs validated and sanitized
- [ ] SQL injection protection (parameterized queries)
- [ ] XSS protection (output encoding)
- [ ] Command injection prevention
- [ ] File upload validation (type, size, content)

### Step 4: Data Protection Review
- [ ] Sensitive data encrypted at rest
- [ ] All communication over TLS/HTTPS
- [ ] No sensitive data in logs
- [ ] No hardcoded credentials
- [ ] Secrets management solution in place

### Step 5: Infrastructure Review
- [ ] Security headers configured (CSP, HSTS, X-Frame-Options)
- [ ] CORS properly configured
- [ ] Rate limiting on auth and API endpoints
- [ ] Network segmentation appropriate
- [ ] Dependencies scanned for vulnerabilities

### Step 6: Report
Document findings using the Reviewer Agent's severity matrix. All P0/P1 security findings must be addressed immediately.

## Anti-Patterns
- 🚫 Security as an afterthought
- 🚫 "We'll add auth later"
- 🚫 Trusting client-side validation only
- 🚫 Security by obscurity
