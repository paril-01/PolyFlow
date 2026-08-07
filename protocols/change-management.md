# Change Management Protocol

## Trigger
Any modification to production systems, code, configuration, or infrastructure.

## Process
1. **Classify the change**: Feature, bug fix, hotfix, configuration, infrastructure
2. **Assess risk**: Using [Change Philosophy](../constitution/change-philosophy.md) risk assessment
3. **Determine approval level**: Per [Change Approval](../governance/change-approval.md)
4. **Plan the change**: Implementation plan, testing plan, rollback plan
5. **Execute**: Implement, test, review
6. **Deploy**: Following [Release Process](../governance/release-process.md)
7. **Verify**: Post-deployment verification
8. **Record**: Historian Agent records the change

## Emergency Changes
For production incidents requiring immediate changes:
1. Apply the fix with verbal approval
2. Document within 24 hours
3. Submit for post-hoc review
4. Track any shortcuts as technical debt
