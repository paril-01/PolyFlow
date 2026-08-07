# Playbook: Database Migration

## When to Use
Any change to the database schema: adding tables, columns, indexes, constraints, or modifying existing structures.

## Process

### Step 1: Plan
1. Document what's changing and why
2. Assess impact on existing data
3. Estimate migration duration for production data volume
4. Plan downtime (if required)
5. **Write both UP and DOWN migrations**

### Step 2: Write Migration
1. Write the forward (UP) migration
2. Write the rollback (DOWN) migration
3. Handle data transformation if needed
4. Consider backward compatibility (can old code work with new schema?)

### Step 3: Test
1. Test migration on a copy of production data
2. Test rollback migration
3. Verify data integrity after migration
4. Time the migration with production-scale data
5. Verify application works with new schema

### Step 4: Review
1. Reviewer Agent reviews migration scripts
2. Check for data loss risks, locking issues, performance impact

### Step 5: Deploy
1. Take a database backup
2. Run migration in staging first
3. Verify staging
4. Run migration in production during low-traffic period
5. Monitor for issues
6. Keep rollback script ready for 24 hours

## Safety Rules
- ✅ Always have a rollback script
- ✅ Always backup before migrating
- ✅ Always test with production-scale data
- ❌ Never modify production schema without testing
- ❌ Never DROP columns without verifying no code references them
- ❌ Never run migrations during peak traffic
