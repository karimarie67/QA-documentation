# Ticketing Workflow for Boost.io

## 1. Objective

- Embed QA processes within the GitHub Issues ticketing system to ensure quality assurance is a core component of the development lifecycle.
- Ensure bugs, test requirements, and library enhancements are documented, prioritized, and addressed to support our commitment to our users.

## 2. Setup and Configuration

### 2.1 Configure GitHub Issues

**Create a Project Board**:
- Set up a GitHub Project board with columns: **Backlog**, **To Do**, **In Progress**, **In QA**, **Done**.

**Define Labels**:
- Create labels for issue categorization, aligned with our development needs:
  - `bug`: For defects in library.
  - `enhancement`: For new features or improvements.
  - `qa`: For QA-specific tasks (e.g., regression test execution, test case updates).
  - `test-case`: For issues related to test case development.

**Create Issue Templates**:
- Use GitHub’s issue templates (`.github/ISSUE_TEMPLATE/`) to standardize bug reports and QA tasks.
- Include a **bug report template** with fields for:
  - Description
  - Steps to Reproduce
  - Actual vs. Expected Behavior
  - Test Case Reference
  - Environment Details (e.g., compiler, platform, Boost version)
- Create a **QA task template** for test case creation or execution, with fields for:
  - Test Objective
  - Test Cases
  - Dependencies

## 3. Workflow Process

### 3.1 Pre-Development: QA Planning

**Create QA Task Issues**:
- QA testers create issues tagged with `qa` and `test-case` to document test planning tasks.
- Link to relevant issues (e.g., `enhancement` or `bug`) to align testing with development.

**Define Test Cases**:
- Document test cases within the issue or link to test files in the repository.

**Assign and Prioritize**:
- Assign QA task issues to tester(s).

### 3.2 Development: QA Input and Monitoring

**Review Feature Issues**:
- QA testers review `enhancement` issues to understand requirements and ensure testability.

**Monitor Development Progress**:
- Track feature issues in the “In Progress” column to anticipate testing needs.
- Communicate via issue comments to clarify requirements.

### 3.3 Testing: Bug Identification and Reporting

**Execute Test Cases**:
- Developers run unit tests.
- Document results in the ticket/issue, noting pass/fail status and problems encountered.
- Once unit tests pass, QA performs testing.

**Report Bugs**:
- Create a new issue for each bug using the bug report template, following bug reporting guidelines.
- **Example**:
  - **Title**: “Unreadable Compiler Output in Boost.Test on Clang”
  - **Labels**: `bug`, `qa`, `severity: medium`, `priority: medium`
  - **Description**: “Compiler output for BOOST_TEST failures is unreadable on Clang 9.0.”
  - **Steps to Reproduce**: Compile `test/example.cpp` with Clang 9.0, run test, observe output.
  - **Actual Behavior**: Output lacks clear failure details.
  - **Test Case Reference**: `test/example.cpp`, `BOOST_AUTO_TEST_CASE`.
  - **Compiler/Platform**: Clang 9.0, Ubuntu 20.04.
  - **Boost Version**: 1.87.0.
  - **Attachments**: Logs, compiler output, or test artifacts.
- Move to “To Do” and assign to a developer (e.g., Rob).

**Link Related Issues**:
- Link bug issues to the original `qa` or `enhancement` issue.

### 3.4 Bug Resolution: QA Verification

**Developer Fixes**:
- Developers assign bug issues, move to “In Progress,” and implement fixes via pull requests (PRs).
- Developers comment with fix details and PR link (e.g., “Fixed in PR #370, improved output parsing”).
- Assign to QA tester.

**QA Verification**:
- QA testers move the issue to “In QA” and verify the fix using the steps to reproduce.
- Run relevant tests.
- **If the fix is successful**:
  - Comment: “Verified on x environment, output now readable.”
  - Move to “Done” and close the issue.
- **If the fix fails**:
  - Comment: “Output still unreadable, see log test-failure.log.”
  - Reopen, move to “To Do,” and notify the developer.

**Update Test Cases**:
- If the fix introduces new behavior, update test cases.
- Document updates in the original `qa` issue or create a new `test-case` issue.

### 3.5 Post-Release: Regression Testing

**Regression Testing**:
- After a Boost release, QA testers create a `qa` issue for regression testing.
- Run regression tests.
- Report regression bugs as new issues, referencing the release.

## 4. Best Practices

- **Maintain Traceability**:
  - Link bugs to test cases, features, or PRs.
- **Regularly Review Backlog**:
  - Conduct weekly triage to review open issues and close stale ones.

## 5. Example Workflow for a Bug

**Scenario**: QA tester finds that `BOOST_TEST` produces unreadable compiler output on Clang 9.0.

**Steps**:
1. **Create Bug Issue**:
   - **Title**: “Unreadable Compiler Output in Boost.Test on Clang”
   - **Labels**: `bug`, `qa`, `severity: medium`, `priority: medium`
   - **Description**: Includes steps to reproduce, test case, and Clang output.
   - Assign to team, add to “To Do” column.
2. **Developer Fix**:
   - Moves to “In Progress.”
   - Developer fixes issue, creates PR.
   - Comments: “Fixed in PR #370, improved diagnostics.”
   - Assigns to QA tester.
3. **QA Verification**:
   - Tester moves to “In QA,” runs `test/example.cpp` on Clang 9.0, verifies output.
   - Comments: “Verified on Clang 9.0, Ubuntu 20.04, output readable.”
   - Moves to “Done,” closes issue.
4. **Regression Testing**:
   - Tester includes test in regression suite for Boost 1.88.0 release.
   - Reports any new issues as separate bug issues.

## 6. Metrics and Reporting

**Track QA Metrics**:
- Number of bugs reported/resolved.
- Test coverage.
- Average time to resolve `severity: critical` bugs.

**Report Progress**:
- Use GitHub Project board to visualize issue status.
- Generate reports (e.g., monthly report showing 10 bugs resolved, 5 in QA).

## 7. Additional Notes

**Automation Opportunities**:
- Automate ticket assignment:
  - When a ticket is ready for QA (e.g., PR is approved), automatically assign to a QA tester.
  - When QA approves, automatically merge to staging.
- **Auto-Merge Concern**:
  - Risk of accidental approval leading to unintended merges.
  - **Mitigation Plan**:
    - Require multiple QA approvals (e.g., using GitHub’s branch protection rules).
    - Implement a rollback mechanism (e.g., revert PR or restore previous staging state).
    - Add a confirmation step (e.g., GitHub Action to prompt for final approval).

**Other GitHub Actions Opportunities**:
- **Automated Test Execution**: Run unit or integration tests on issue creation or PR updates, updating issue status (e.g., add `qa-ready` label if tests pass).
- **Bug Triage Automation**: Auto-assign issues based on labels (e.g., `bug` to developers, `qa` to testers) using actions like `actions-ecosystem/action-add-labels`.
- **Regression Test Triggers**: Automatically create `qa` issues for regression testing on new releases.
- **Metrics Generation**: Use actions to generate weekly/monthly QA reports (e.g., count open/closed issues, calculate resolution time).
- **Dependency Checks**: Enhance `dependency_report.yml` with automated vulnerability scans (e.g., using `dependabot` or `snyk`).