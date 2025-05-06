## Table of Contents
1. [Align with the Dev Team](#1-align-with-the-dev-team)
2. [Define QA Scope & Strategy](#2-define-qa-scope--strategy)
3. [Set QA Goals](#3-set-qa-goals)

# C++ Alliance QA Plan: Month 1 - Foundation & Planning

## 1. Align with the Dev Team

### Objectives
- Map out the current *CI/CD process*.
- Understand *sprint cadence* and *deployment frequency*.
- Identify *pain points* in development and deployment workflows.

### Current CI/CD Process
- **Tooling**: Utilizing [GitHub Actions](https://github.com/features/actions).
- **Reference**: See [Workflow Mappings](#workflow-mappings) for detailed process documentation.

### Sprint Cadence & Deployment Frequency
- **Sprint Cadence**: *No defined sprint cadence* currently in place.
- **Deployments**:
  - Scheduled on *Mondays*, typically in the *afternoon* or *after hours*, to avoid weekend disruptions.
  - Timing or day may shift based on release requirements or scheduling conflicts.
  - **Constraint**: *Production lockdown* for one month prior to a [Boost release](https://www.boost.org/), requiring schedule adjustments.

### Pain Points
- **No QA Process**: *Lack of dedicated QA* leads to frequent post-deployment bugs.
- **Outdated Documentation**: *Setup docs* are obsolete, hindering onboarding and process efficiency.

---

## 2. Define QA Scope & Strategy

### Integration with CI/CD
- **Placement**: QA to include *pre-merge checks* and *post-deploy validation*.
- **Reference**: See [CI/CD Section](#ci-cd-section) for implementation details.

### Testing Types & Prioritization
- **Functional Testing**: Ensure core features work as intended. See [Functional Test Cases](#functional-test-cases).
- **Smoke Testing**: Verify critical functionality after deployment.
- **Regression Testing**: Confirm new changes don’t break existing features.
- **User Acceptance Testing (UAT)**:
  - *Not currently implemented*.
  - **Action Item**: Collaborate with the team to establish a *UAT process*.

### Testing Approach
- **Shift-Left Testing**: Prioritize *early and frequent testing* to catch issues before production.
  - Discussions initiated to test individual tickets in *local environments* before merging to *staging*.
- **Environments**:
  - Current: Two environments—*Staging* (AKA *Develop*) and *Master*.
  - **Action Item**: Draft a proposal for a *third environment* to enhance testing workflows. Example rationale:
    ```markdown
    A third environment (e.g., QA) allows isolated testing of integrated features before staging, reducing risks in production.
    ```

### Automation Exploration
- **Tool**: Evaluating *Playwright* for test automation.
- **Benefits**:
  - Enables end-to-end testing across browsers.
  - Easy integration with CI/CD pipelines.
- **Limitations**:
  - Requires initial setup and team training.
  - Limited support for legacy systems.
- **Next Steps**:
  - Create a proof of concept to validate Playwright's feasibility.
  - Document findings and share with the team.
---

## 3. Set QA Goals

1. **Catch Critical Bugs**: Identify and resolve *critical issues* before they reach production.
2. **Stable Deploys**: Ensure *predictable and reliable* deployments.
3. **Automated Checks**: Develop *basic automated tests* that run on every *commit* or *pull request* for rapid feedback.
