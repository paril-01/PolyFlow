# Security Review Protocol

## Trigger
New feature with security implications, periodic security audit, or post-incident review.

## Process
1. **Define scope**: What's being reviewed
2. **Identify threat model**: Who might attack this and how
3. **Review authentication & authorization**: Are access controls correct?
4. **Review data handling**: Is sensitive data protected?
5. **Review input handling**: Are inputs validated?
6. **Review dependencies**: Any known vulnerabilities?
7. **Review infrastructure**: Are security headers, TLS, etc. configured?
8. **Document findings**: Using severity matrix
9. **Prioritize remediation**: P0 security findings are drop-everything priorities

## Reference
See [Security Audit Playbook](../playbooks/security-audit.md) for the detailed checklist.
