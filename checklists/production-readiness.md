# Production Readiness Checklist

Use this for the first-ever production deployment of a system.

## Application
- [ ] All CRUD operations work correctly
- [ ] Authentication and authorization enforced
- [ ] Input validation on all endpoints
- [ ] Rate limiting configured
- [ ] Error handling is comprehensive
- [ ] Health check endpoint exists

## Data
- [ ] Database schema is finalized and migrated
- [ ] Backup strategy configured and tested
- [ ] Data retention policy defined
- [ ] Sensitive data encrypted at rest

## Observability
- [ ] Structured logging implemented
- [ ] Log aggregation configured
- [ ] Key metrics instrumented (latency, error rate, throughput)
- [ ] Monitoring dashboards created
- [ ] Alerts configured for critical conditions
- [ ] Distributed tracing (if applicable)

## Reliability
- [ ] Timeouts configured for all external calls
- [ ] Retry logic with backoff for transient failures
- [ ] Graceful shutdown handles in-flight requests
- [ ] Circuit breakers for external dependencies

## Security
- [ ] Security audit completed (see [Security Audit Playbook](../playbooks/security-audit.md))
- [ ] TLS/HTTPS enforced
- [ ] Security headers configured
- [ ] Dependency vulnerability scan clean

## Operations
- [ ] Deployment is automated
- [ ] Rollback procedure documented and tested
- [ ] On-call rotation established
- [ ] Runbook for common issues created
- [ ] Disaster recovery plan documented

## Documentation
- [ ] API documentation complete
- [ ] Architecture documented
- [ ] Deployment guide exists
- [ ] Configuration reference exists
