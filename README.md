# Agent Skills Repository 🚀

A curated collection of powerful AI coding assistant skills designed to automate tasks, improve code quality, enforce consistency, and standardize development workflows.

## What is this?
These skills extend the capabilities of AI coding agents, providing them with specialized tools and context for specific workflows. From automated testing and project planning to code consistency and security audits, these skills serve as a force multiplier for engineering tasks.

---

## 🛠️ General Skills

These skills generally trigger **automatically** during conversational development based on intent.

### 🖥️ Development & Code Quality
- **`code-consistency`**: Analyzes existing patterns and rules (e.g. `CONTRIBUTION.md`) before writing any code to ensure output is indistinguishable from the rest of the codebase.
- **`ts-refactor`**: Expert TypeScript/TSX refactoring skill. Cleans up files, splits components, improves type safety, and reduces technical debt.
- **`project-docs-generator`**: Automatically researches the codebase and generates/updates comprehensive Markdown documentation (README, ARCHITECTURE, ENVIRONMENT, etc.).
- **`todo-manager`**: Automatically captures and manages tasks, ideas, or tech debt in the project's TODO list.
- **`skill-creator`**: Develops, refines, evaluates, and optimizes other AI agent skills!

### 🔌 Integrations
- **`bruno-cli`** & **`bruno-docs`**: Automates API testing and collection management using Bruno, keeping REST API endpoints organized, documented, and tested.
- **`jira-config-init`**: One-off initialization of Jira workspace configurations.
- **`jira-bugfix-planner`**: Fetches Jira tickets, explains issues, researches code, and automatically generates implementation plans for bug fixes and small tasks.
- **`jira-feature-architect`**: Strategic feature designer. Fetches Jira tickets, researches codebase, and produces persistent technical proposal documents and progress trackers in the documentation repository.
- **`jira-bug-reporter`**: Automates creating robust bug reports directly in Jira from local debug sessions.

---

## ⚙️ The gstack Ecosystem

`gstack` is a specialized suite of workflows primarily triggered manually via slash commands. They enforce rigorous engineering standards from planning to deployment.

### How to use gstack
- Run `/gstack` to open the central hub for development and QA workflows, which will guide you through the available tools.
- Use `/gstack-upgrade` with a single command to ensure the suite is fully up to date.
- Manually trigger any of the workflows below by using their slash command (e.g., `/qa`, `/ship`, `/cso`).

### 🗺️ Project Planning & Review
- **`/office-hours`**: YC-style design-thinking and brainstorming workflow for framing and pitching projects.
- **`/plan-ceo-review`**: Founder-mode plan review that challenges the status quo, expands project scope, and pushes for ambitious 10-star product execution.
- **`/plan-eng-review`**: Engineering manager review to rigorously vet architecture, constraints, data flow, and test coverage before implementation starts.
- **`/plan-design-review`** & **`/design-consultation`**: Generates complete design systems, evaluates aesthetics, and audits frontend plans for visually stunning UIs.
- **`/autoplan`**: Executes the full sequence of CEO, Engineering, and Design review phases on a plan automatically.

### 🧪 QA, Debugging & Security
- **`/qa`** & **`/qa-only`**: Systematically tests web applications using a headless Chromium browser. Finds bugs, generates reports, and can optionally fix the bugs found in source code.
- **`/benchmark`**: Performance regression detection. Tracks Core Web Vitals, page speed, and bundle sizes across PRs.
- **`/browse`**: A fast headless browser for dogfooding, QA testing, taking annotated screenshots, and verifying functionality.
- **`/setup-browser-cookies`**: Imports your real Chromium session cookies into the headless browse session to seamlessly test authenticated pages.
- **`/investigate`**: Systematic debugging workflow containing four phases (investigate, analyze, hypothesize, implement) with strict root cause analysis.
- **`/careful`** & **`/guard`**: Safety mode that provides warnings before running destructive commands (like `rm -rf` or `DROP TABLE`), and allows directory-scoped edits to strictly limit AI blast radius on a codebase.
- **`/freeze`** & **`/unfreeze`**: Explicitly restrict code edits to a specific directory to prevent stray file modifications elsewhere in a project.
- **`/cso`** (Chief Security Officer): Deep security audit covering secrets, dependency supply chains, OWASP top 10, STRIDE threat models, and more.
- **`/design-review`**: Visual QA that audits live site designs, catching awkward spacing, UI slop, and fixing them actively in source code.

### 🚢 Shipping & Operations
- **`/ship`**: End-to-end ship workflow. Auto-merges, updates CHANGELOG, bumps versions, and creates clean PRs.
- **`/review`**: Pre-landing code reviews actively looking for SQL errors, LLM trust boundary violations, and side effects.
- **`/land-and-deploy`**: Lands PRs, awaits CI passage, ships to production, and performs canary verifications.
- **`/setup-deploy`**: Auto-configures zero-touch deployments for various platforms (Vercel, Fly.io, Netlify, Render).
- **`/canary`**: Continuous post-deployment monitoring against pre-deploy baselines (visual regressions, logs, performance).
- **`/document-release`**: Post-ship doc updates. Syncs documentation (README, CHANGELOG, ARCHITECTURE) to match newly shipped features without manual intervention.
- **`/retro`**: Generates a weekly engineering retrospective highlighting the team's contributions, commits, praise, and growth areas.

---

## 📜 License
This repository is open-sourced under the [MIT License](LICENSE).
