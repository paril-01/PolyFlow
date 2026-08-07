# Observability Standards

## Three Pillars

### 1. Logging
- **Structured logging** (JSON format)
- **Log levels**: DEBUG, INFO, WARN, ERROR, FATAL
- **Correlation IDs**: Request ID in every log entry
- **Context**: Include user ID, operation, and relevant data
- **Never log**: Passwords, tokens, PII, credit card numbers
- **Centralized**: Aggregate logs in a searchable system

### 2. Metrics
- **RED Method** (for services): Rate, Errors, Duration
- **USE Method** (for resources): Utilization, Saturation, Errors
- **Business metrics**: Key business events and outcomes
- **SLI/SLO tracking**: Service Level Indicators and Objectives
- **Dashboard**: Visual monitoring for key metrics

### 3. Distributed Tracing
- **Trace ID propagation** across service boundaries
- **Span creation** for significant operations
- **Context propagation** through async operations
- **Sampling strategy** for high-volume services

## Alerting
- Alert on **symptoms** (error rate, latency), not causes
- Alerts must be **actionable** — if you can't act on it, don't alert
- Set **severity levels** that match response expectations
- Avoid **alert fatigue** — tune thresholds, aggregate similar alerts
- Include **runbook links** in alerts
