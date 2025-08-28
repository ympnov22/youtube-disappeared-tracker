# Devin Project Development Operations Guideline
## Version: v1.0.0

This document defines the operational guidelines for developing with Devin.  
It covers development workflow, documentation updates, GitHub operations, CI/CD, and reporting methods.

---

## 1. Development Workflow (Phase-based)

- Development is divided into **phases (Phase 0, Phase 1, …)**  
- Each phase follows this cycle:  
  1. **Planning** (spec + task list → PR/report)  
  2. **Implementation** (keep docs in sync)  
  3. **Testing** (CI must pass)  
  4. **Reporting/Approval** (deliverables + PR + bilingual report)  
  5. **Transition to next phase**

- To avoid performance degradation, **start a new session when switching phases**  
- Always attach a **handoff block** in PRs for continuity  

---

## 2. Documentation Rules

### Required Updates
- **Specification**: `docs/specification.md`, `README.md`  
- **Task list**: `docs/tasks.md`  
- **Continuity kit**: `docs/continuity.md`  
- **Progress log**: `docs/progress.md`, `CHANGELOG.md`  

### Principles
- Keep implementation and docs **always in sync**  
- Record progress/unresolved issues to allow immediate resumption  
- Save important decisions as **ADR (docs/adr/)**  
- Collect troubleshooting steps in **Runbooks (docs/runbooks/)**  

### Translation
- Documents are **English by default**  
- **Reports and PRs requiring approval must include English + Japanese**  
- Even short updates should include a Japanese translation  

---

## 3. GitHub Rules

### Branching
- `main`: stable branch  
- `devin/<timestamp>-<phase>-<feature>`: working branches  
- No direct commits or force pushes to `main`  

### Pull Requests
- Title + description: **English + Japanese**  
- All CI checks must pass  
- At least one reviewer approval required  
- Cannot merge if `needs-jp-translation` label remains  

### Secrets
- Do not commit API keys or passwords  
- Use GitHub Secrets or Devin-managed env vars  

### CODEOWNERS
- `docs/**` → Docs owner  
- `backend/**` → Backend owner  
- `deploy/**` → Ops owner  

---

## 4. Reporting

- **Phase start**: Plan in English + Japanese translation  
- **Phase progress**: Short updates in English + Japanese  
- **Phase completion**: Deliverables, PR, CI status, next steps → bilingual report  
- **Issues**: Report with investigation details; solutions require approval before coding  

---

## 5. CI/CD

### Workflows
- **CI (`ci.yml`)**: lint, type-check, test, security  
- **Staging deploy (`deploy-staging.yml`)**: auto-deploy on `main` push (Fly.io)  
- **Production deploy (`deploy-prod.yml`)**: manual approval (workflow_dispatch)  

### CI Content
- Lint: `ruff`  
- Type check: `mypy`  
- Security: `pip-audit`, `bandit`  
- Test: `pytest -n auto`  

### Dependabot
- Weekly updates for pip, GitHub Actions, Docker  

---

## 6. PR Template

`.github/pull_request_template.md`

```markdown
## Summary
(EN) What/Why:

(JA) Purpose/Changes:

## Checklists
- [ ] Tests added/updated
- [ ] Docs updated (spec/tasks/continuity)
- [ ] JP translation included for decision/approval points
- [ ] Handoff block included (below)

## Handoff
- Done:
- Next:
- Decisions (ADR):
- Known Issues:
- Env/Secrets:
- How to run:
