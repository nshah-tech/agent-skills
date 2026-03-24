---
name: project-docs-generator
description: Use when users want to generate, update, or maintain foundational project documentation. Automatically researches the current codebase and generates industry-standard Markdown files, including README, ARCHITECTURE, ENVIRONMENT, API, CRONJOBS, DEPLOYMENT, TESTING, CONTRIBUTING, TROUBLESHOOTING guides, and a localized `/update-docs` agent workflow.
---

# Project Documentation Generator

This skill instructs the agent on how to systematically analyze a repository and generate comprehensive, industry-standard project documentation tailored to the project's actual source code.

## Standard Documentation Architecture

Industry best practices mandate decoupling documentation into specific, purpose-driven files inside a `/docs` directory, maintaining a clean root folder:

1. **`README.md`** (Root): Entry point. Outlines the project purpose, tech stack overview, prerequisite software (Node, Docker), and standard startup commands.
2. **`docs/ARCHITECTURE.md`**: Technical system design. Must detail processes like SQS queue workers vs standard controllers, scaling mechanisms (e.g. PM2 clusters), and data flows. MUST include a Mermaid.js diagram illustrating architecture interactions.
3. **`docs/API.md`** or **`docs/CRONJOBS.md`**: Breakdown of integration paths. Map out Express routes, controllers, Cron execution expressions, background loops, and attached scripts found in `package.json`.
4. **`docs/ENVIRONMENT.md`**: A list of required configuration keys. Extracted from `.env.example`, `process.env` references via regex searches, or configuration files, detailing what each variable controls.
5. **`docs/DEPLOYMENT.md`**: Step-by-step release steps. Details cluster configurations (like `ecosystem.config.js`), CI/CD pipelines (Github Actions/Gitlab), Docker configurations, and reverse proxy details.
6. **`docs/TESTING.md`**: Outline for running automated validations. Details unit tests commands, end-to-end framework usage (Playwright/Jest), and debug mechanisms.
7. **`docs/CONTRIBUTING.md`**: Guidelines for team code contributions. Details branching conventions, code style standards (ESLint/Prettier rules from package.json), PR rules, and local environment preparations.
8. **`docs/TROUBLESHOOTING.md`**: Internal operational manual for resolving system failures, interpreting specific backend logs, fixing database locks, and addressing heavy microservice bottlenecks (e.g. SQS deadlocks, OOM heap limits, and background race conditions).
9. **`.agent/workflows/update-docs.md`**: A custom "slash command" workflow mapping precisely to these documentation commands. It empowers any local developer to type `/update-docs` and natively trigger instantaneous documentation regeneration without navigating complex prompt chains.

## Workflow Execution Steps

When generating documentation for a target repository:

1. **Information Gathering**: Use tools like `list_dir`, `grep_search`, and `view_file` to collect information from:
   - `package.json` (for dependencies and scripts)
   - `ecosystem.config.js` / Dockerfile / `.github/workflows` (for DEPLOYMENT.md)
   - `.env.example` / `config/` (for ENVIRONMENT.md)
   - Routing controllers like `routes.ts`, Express setups, and SQS `getQueueMessage` loops (for API/Architecture)
   - Test files like `*.spec.ts` or `playwright.config` (for TESTING.md)
2. **Draft the Documents**: Synthesize the findings completely, omitting guesses in favor of explicit references to code logic. 
3. **Writing**: Output the standard files using markdown features (Tables for APIs/Environment variables, Mermaid.js blocks for architectures, and callout Alerts for critical deployment info).
