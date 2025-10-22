---
description: Validate system before deployment
allowed-tools: Bash(python:*), Bash(git:*), Bash(poetry:*)
---

Pre-deployment validation checklist:

1. Git status: !`git status`
2. Uncommitted changes check
3. Environment variables validation
4. Dependencies check
5. Test suite execution
6. Database connectivity

Provide a deployment readiness report with any blocking issues.
