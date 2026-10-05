---
name: feature-docs
description: Mandate for keeping a project's central documentation repository in sync with its code repos. Use when working on features in a multi-repo project that has a separate docs repo (Wiki/, Sprints/, Decisions/, Operations/) — ensures sprint proposals, Wiki feature docs, ADRs, and operational notes stay synced with code behavior.
---

# Feature Documentation Manager

Formalizes the relationship between a project's code repositories and its central **documentation** repository. The docs repo's location is named in the project's `CLAUDE.md` / `AGENTS.md`; if it isn't, ask the user once.

## The Mandate
Any agent working on the project MUST ensure that high-level feature documentation and future-facing ideas are captured in the documentation repository — not left only in code, commits, or chat.

**Rule**: `Wiki/` = current product state (what a feature does today). `Sprints/` = how it evolved (proposals, reviews, decisions — frozen once shipped). If the docs repo's `CONTRIBUTING.md` defines this differently, follow it.

## 1. Feature Documentation (`Wiki/Features/`)
- **When to update**: whenever a feature is shipped or its behavior materially changes (use `/product-doc-sync` after ship).
- **Where to store**: `<docs-repo>/Wiki/Features/<FeatureName>.md` — one living doc per feature.
- **Structure**:
  - `## Description`: What the feature does and who uses it.
  - `## User Flow`: Step-by-step user journey.
  - `## Business Logic`: Rules, edge cases, and calculations.
  - `## Technical Details`: Entities, services, API endpoints, and key files.
  - `## Changed In`: One row per shipped ticket that changed it.
  - `## Backlinks`: Related proposals, sprints, ADRs, and feature docs.

## 2. Sprint Proposals (`Sprints/<version>/<TICKET>-<ShortName>/`)
- **Purpose**: Planning feature work, drafting technical proposals, and tracking approved implementation work.
- **When to use**: When the user asks for Jira planning, feature architecture, proposal drafting, or sprint-scoped work.
- **Workflow**:
  1. Read the docs repo's `CLAUDE.md` / `AGENTS.md`, `CONTRIBUTING.md`, `.jira.json`, and its workflow guide if one exists.
  2. Create or update one proposal document under `Sprints/<version>/<TICKET>-<ShortName>/` (`/jira-feature-architect`), or a bug plan under `Sprints/<version>/bugs/` (`/jira-bugfix-planner`).
  3. Maintain a matching `<TICKET>-PROGRESS.md` only after the proposal has passed review (`/review-proposal`) or the user explicitly accepts bypassing that gate.
  4. Keep `Sprints/<version>/<version>.md` status and proposal links aligned (`/sprint-manager`, `/workflow-status`).

## 3. Other Document Types
- **ADRs** → `Decisions/ADR-<NNN>-<ShortName>.md` for architectural decisions and trade-offs.
- **Incidents** → `Operations/Incidents/<YYYY-MM-DD>-<title>.md` (`/incident-reporter`).
- **Plans without a ticket** → a reviewable markdown doc in the docs repo (or an ADR), not just a chat reply.

## 4. Cross-Repo Sync
- Before marking a feature task complete in a code repo, check whether the corresponding documentation needs an update.
- If a feature is "In Progress", ensure there is a corresponding sprint proposal, progress tracker, or bugfix plan.
- When implementation changes behavior in any code repo, update the Wiki doc, proposal, ADR, or operational note that owns that behavior.
- If new tags are introduced, update the docs repo's tag index (e.g. `tags.md`).

## 5. Jira Integration (Reference Only)
- **Role**: Use Jira ONLY as an information source to enrich proposals and feature docs.
- **Fetching**: Use ticket keys (e.g., `ACME-1849`) to pull specs, logic, and requirements.
- **RESTRICTION**: Do NOT create or update Jira tickets unless explicitly instructed by the user for a specific task. The source of truth for execution state is the sprint/proposal/progress Markdown in the docs repo.
