---
name: project-docs-generator
description: Use when users want to generate, update, or maintain foundational project documentation. Automatically researches the current codebase and generates industry-standard Markdown files, including README, ARCHITECTURE, ENVIRONMENT, API, CRONJOBS, DEPLOYMENT, TESTING, CONTRIBUTING, TROUBLESHOOTING, DESIGN guides, and a localized `/update-docs` agent workflow.
---

# Project Documentation Generator

This skill instructs the agent on how to systematically analyze a repository and generate comprehensive, industry-standard project documentation tailored to the project's actual source code.

## Standard Documentation Architecture

Industry best practices mandate decoupling documentation into specific, purpose-driven files inside a `/docs` directory, maintaining a clean root folder:

1.  **`README.md`** (Root): Entry point. Outlines the project purpose, tech stack overview, prerequisite software (Node, Docker), and standard startup commands.
2.  **`docs/ARCHITECTURE.md`**: Technical system design. Must detail processes like SQS queue workers vs standard controllers, scaling mechanisms (e.g. PM2 clusters), and data flows. MUST include a Mermaid.js diagram illustrating architecture interactions. **Preserve existing hand-written technical details and architectural constants (e.g., specific memory limits or worker counts) during updates.**
3.  **`docs/API.md`** or **`docs/CRONJOBS.md`**: Breakdown of integration paths. Map out Express routes, controllers, Cron execution expressions, background loops, and attached scripts found in `package.json`.
4. **`docs/ENVIRONMENT.md`**: A list of required configuration keys. Extracted from `.env.example`, `process.env` references via regex searches, or configuration files, detailing what each variable controls.
5. **`docs/DEPLOYMENT.md`**: Step-by-step release steps. Details cluster configurations (like `ecosystem.config.js`), CI/CD pipelines (Github Actions/Gitlab), Docker configurations, and reverse proxy details.
6. **`docs/TESTING.md`**: Outline for running automated validations. Details unit tests commands, end-to-end framework usage (Playwright/Jest), and debug mechanisms.
7. **`docs/CONTRIBUTING.md`**: Guidelines for team code contributions. Details branching conventions, code style standards (ESLint/Prettier rules from package.json), PR rules, and local environment preparations.
8. **`docs/TROUBLESHOOTING.md`**: Internal operational manual for resolving system failures, interpreting specific backend logs, fixing database locks, and addressing heavy microservice bottlenecks (e.g. SQS deadlocks, OOM heap limits, and background race conditions).
9. **`docs/DESIGN.md`** *(Frontend projects only)*: The central source of truth for design decisions, tokens, and visual principles. Must document:
    - **Typography**: Primary and secondary font families, weights, and usage context (e.g. `Roboto` for general UI, `Inter` for data labels).
    - **Color System**: All design tokens organized by category — brand/primary, neutral/backgrounds, status/semantic, and typography colors. Include both the token name (e.g. `$color-main-1`) and the hex value.
    - **Layout & Spacing**: Base spacing scale (e.g. 8px grid), border radii, and shadow definitions.
    - **UI Library & Patterns**: Which component libraries are used (e.g. Ant Design, MUI, Syncfusion) and what each is responsible for. Document any custom wrapper components or layout patterns (e.g. `CardLayout`).
    - **Feature-Specific UX Patterns**: Document any complex UI features that have specific visual encoding rules (e.g. confidence indicators, status badges, multi-view strategies).
    - **Design Principles**: The guiding philosophy for the application's visual design (e.g. "Dense but Readable", "Empty States are Features").
    - **Preserve existing hand-written design decisions and token values during updates.** Only add new tokens or patterns discovered in code.
10. **`.agent/workflows/update-docs.md`**: A custom "slash command" workflow mapping precisely to these documentation commands. It empowers any local developer to type `/update-docs` and natively trigger instantaneous documentation regeneration without navigating complex prompt chains.

## Cross-Skill Integration: `/update-all` Workflow

After creating `.agent/workflows/update-docs.md`, **always check** if `.agent/workflows/update-bruno.md` already exists in the project (created by the `bruno-cli` skill). If it does, create a combined `.agent/workflows/update-all.md` workflow that scans routes once and produces both outputs in a single pass.

The `/update-all` workflow should contain:

```markdown
---
description: Scan routes once, then update both project documentation and Bruno API collection in a single pass to avoid duplicate token consumption.
---

# Update All — Docs + Bruno

This workflow combines `/update-docs` and `/update-bruno` into a single pass. Instead of scanning controllers and route files twice, the agent reads them once and produces both outputs from the same research.

## Steps

1. **Shared Research Phase**
   Scan all NestJS controllers (`*.controller.ts`) and Express route files (`*.routes.ts`). For each route, extract: HTTP method, path, auth type (guards/middleware), path params, query params, body shape, and any decorators. Also read `package.json` for framework detection. Hold all route data in memory for the next two steps.

2. **Update Documentation**
   // turbo
   `@[.agent/skills/project-docs-generator] Using the route and project data already gathered in this conversation, refresh the documentation for this repository. Do NOT re-scan controller or route files — use what was already collected in step 1.`

3. **Update Bruno Collection**
   // turbo
   `@[/bruno-cli] Using the route data already gathered in this conversation, sync the Bruno collection. Do NOT re-scan controller or route files — use what was already collected in step 1. Preserve existing user-written scripts, tests, and assertions in .bru files.`

4. **Validate Bruno (if applicable)**
   If the Bruno collection exists and `bru` CLI is installed, run:
   `cd bruno && bru run --env local --tests-only`
```

If `.agent/workflows/update-bruno.md` does **not** exist, skip this step — the `/update-all` workflow only makes sense when both skills are present.

## Workflow Execution Steps

When generating or updating documentation for a target repository:

1.  **Context Enrichment (CRITICAL)**: Before drafting any document, first check if the file already exists (e.g., `docs/ARCHITECTURE.md`). Read its contents and identify key technical details, manual notes, and architectural context that may not be easily discoverable via automated code analysis.
2.  **Information Gathering**: Use tools like `list_dir`, `grep_search`, and `view_file` to collect information from:
    - `package.json` (for dependencies and scripts)
    - `ecosystem.config.js` / Dockerfile / `.github/workflows` (for DEPLOYMENT.md)
    - `.env.example` / `config/` (for ENVIRONMENT.md)
    - Routing controllers like `routes.ts`, Express setups, and SQS `getQueueMessage` loops (for API/Architecture)
    - Test files like `*.spec.ts` or `playwright.config` (for TESTING.md)
    - SCSS/CSS variable files, theme configs, and `variables.scss` / `_tokens.scss` (for DESIGN.md)
    - Component library imports and usage patterns across the codebase (for DESIGN.md)
    - Existing `DESIGN.md` or design-system references like Figma token exports (for DESIGN.md)
3.  **Draft the Documents**: Synthesize the findings by **merging** the new information with existing context. Ensure that manual overrides or specific technical explanations in older docs are preserved or updated if they are still true.
4.  **Writing**: Output the standard files using markdown features:
    - **Mermaid.js blocks** for architecture diagrams.
    - **Callout Alerts** for critical deployment info.
    - **Well-Formatted Tables**: Ensure that all markdown tables are properly aligned with spaces so they remain easily readable even when edited as plain text in a terminal.
5.  **Cross-Skill Check**: After all documentation files are written, check if `.agent/workflows/update-bruno.md` exists. If it does and `.agent/workflows/update-all.md` does not, create the `/update-all` workflow as described above.
