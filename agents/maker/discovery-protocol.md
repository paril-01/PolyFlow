# Maker Agent — Discovery Protocol

## Purpose

This protocol provides a structured framework for requirement discovery. It ensures no critical requirement category is missed during the discovery phase.

---

## Discovery Framework

### 1. Business Context

| Question | Why It Matters |
|----------|---------------|
| What business problem does this solve? | Ensures the solution addresses a real need |
| Who requested this and why now? | Reveals urgency, constraints, and priorities |
| What happens if we don't build this? | Helps prioritize and assess real value |
| How will success be measured? | Defines acceptance criteria |
| What is the expected timeline? | Sets schedule constraints |

### 2. User Analysis

| Question | Why It Matters |
|----------|---------------|
| Who are the primary users? | Determines the UX and feature priority |
| What are their technical skills? | Influences complexity and documentation needs |
| How many concurrent users are expected? | Drives scalability requirements |
| What are the user's key workflows? | Defines the core feature set |
| What frustrates users about current solutions? | Reveals opportunities and pitfalls |

### 3. Functional Requirements

| Category | Key Questions |
|----------|--------------|
| **Core features** | What must the system absolutely do? |
| **Data** | What data does it process, store, and output? |
| **Integrations** | What systems does it interact with? |
| **Workflows** | What are the step-by-step user processes? |
| **Business rules** | What rules govern behavior and decisions? |
| **Edge cases** | What happens at boundaries? (empty, max, null, concurrent) |
| **Error scenarios** | What should happen when things go wrong? |

### 4. Non-Functional Requirements

| Category | Key Questions | Example Target |
|----------|--------------|----------------|
| **Performance** | Max acceptable response time? | < 200ms p95 |
| **Throughput** | Requests per second? | > 1000 RPS |
| **Availability** | Uptime requirement? | 99.9% |
| **Scalability** | Growth over 1/3/5 years? | 10x users in 3 years |
| **Security** | Authentication method? Data sensitivity? | OAuth 2.0, PII encrypted at rest |
| **Compliance** | Regulatory requirements? | GDPR, SOC 2 |
| **Disaster recovery** | RPO/RTO targets? | RPO: 1 hour, RTO: 4 hours |
| **Observability** | Monitoring requirements? | Logs, metrics, distributed tracing |

### 5. Constraints

| Category | Key Questions |
|----------|--------------|
| **Technology** | Required languages, frameworks, platforms? |
| **Infrastructure** | Cloud provider, on-premise, hybrid? |
| **Budget** | Cost constraints for build and operations? |
| **Team** | Team size, skills, availability? |
| **Regulatory** | Legal or compliance requirements? |
| **Legacy** | Existing systems that must be maintained? |
| **Timeline** | Hard deadlines? Phased delivery? |

### 6. Risk Discovery

| Category | Key Questions |
|----------|--------------|
| **Technical** | Unknown technologies? Complex integrations? |
| **Data** | Data migration? Data quality issues? |
| **Security** | Attack surface? Sensitive data handling? |
| **Operational** | Deployment complexity? Monitoring gaps? |
| **Business** | Changing requirements? Stakeholder alignment? |

---

## Discovery Checklist

Use this checklist to verify discovery completeness:

- [ ] Business problem clearly defined
- [ ] Stakeholders identified and consulted
- [ ] Primary and secondary users identified
- [ ] All functional requirements documented with acceptance criteria
- [ ] Non-functional requirements have specific, measurable targets
- [ ] Technology constraints documented
- [ ] Infrastructure constraints documented
- [ ] Budget and timeline constraints documented
- [ ] Regulatory requirements identified
- [ ] Integration points mapped
- [ ] Edge cases and error scenarios documented
- [ ] Risks identified with probability and impact
- [ ] Assumptions explicitly listed
- [ ] Open questions documented
- [ ] Success metrics defined

---

## Tips for Effective Discovery

1. **Ask open-ended questions first**, then drill down with specific ones
2. **Challenge "obvious" requirements** — they're often incomplete or wrong
3. **Use concrete examples** — "Give me an example of when X would happen"
4. **Quantify everything** — "fast" is not a requirement; "< 200ms" is
5. **Document negative requirements** — what should the system NOT do?
6. **Look for hidden requirements** — audit logging, backup, monitoring are often forgotten
7. **Consider failure modes** — what happens when a dependency is unavailable?
