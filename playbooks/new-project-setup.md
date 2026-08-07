# Playbook: New Project Setup

## When to Use
Starting a new software project from scratch.

## Process

### Step 1: Requirements Discovery
1. Invoke the **Maker Agent** with the project idea
2. Complete the full discovery protocol
3. Document functional and non-functional requirements
4. Identify constraints and risks

### Step 2: Architecture Design
1. Maker Agent explores architectural options
2. Generate ADRs for all significant decisions
3. Define the technology stack
4. Create system architecture diagram

### Step 3: Design Review
1. Invoke the **Reviewer Agent** on the design artifacts
2. Address all P0/P1 findings
3. Iterate on the design until approved

### Step 4: Project Scaffolding
1. Create the repository structure per [Folder Organization](../governance/folder-organization.md)
2. Set up the build system and dependencies
3. Configure linting, formatting, and testing frameworks
4. Set up CI/CD pipeline
5. Create initial documentation (README, CONTRIBUTING)

### Step 5: Initial Implementation
1. Invoke the **Implementer Agent** for the first feature
2. Follow the implementation workflow
3. Include tests from the start

### Step 6: Gate Review
1. Invoke the **Gatekeeper Agent** before first deployment
2. Verify all production readiness criteria

### Step 7: Record
1. Invoke the **Historian Agent** to record the project inception

## Anti-Patterns
- 🚫 Starting coding without requirements
- 🚫 Skipping architecture design for "simple" projects
- 🚫 Not setting up testing infrastructure from day one
- 🚫 Not setting up CI/CD early
