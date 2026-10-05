---
name: generate-migration
description: Generate a TypeORM database migration after changing any *.entity.ts file. Use whenever a task adds, drops, or alters an entity column, index, relation, or table, or when the user asks to "create a migration", "generate a migration", "add a column", or makes any schema change. Migrations MUST be produced by the project's TypeORM generate script — never hand-written.
---

# Generate Database Migrations using TypeORM

Migrations live in the repo that owns the entities (look for `ormconfig.*`, a TypeORM `DataSource`, or a `migrations` path in the TypeORM config — commonly `src/migrations/`). If you are working from a separate documentation/planning repo, run every command below from the entity-owning repo.

> [!IMPORTANT]
> - **NEVER hand-write a migration file.** Every migration must come out of the project's generate script (e.g. `yarn migration:generate`). If you are about to author a migration `.ts` file with the Write tool, stop and run the CLI instead.
> - ONLY run `migration:generate` and `migration:show` (or the project's equivalents).
> - ALWAYS run `nvm use` (or the project's runtime pin) before any migration command.
> - DO NOT run other migration commands (`migration:run`, `migration:create`, `migration:revert`) even if requested — applying migrations is the user's call. If the project documents a guarded exception (e.g. a local-only test-DB reset wrapper), follow its exact conditions and never point it at a shared database.

## When planning a migration (proposals and PROGRESS trackers)

Planning work usually *specifies* a migration rather than generating one. When writing a proposal or a PROGRESS task that involves schema:

- Describe the **entity change**, not the SQL. The migration is a generated artifact; the `*.entity.ts` diff is the source of truth.
- A task that says "write the migration" is wrong — phrase it as "change the entity, then generate the migration via the `generate-migration` skill".
- If the target tables are created by an **un-merged** migration in the same epic, amending that migration in place is acceptable. This does **not** extend to another ticket's new tables — those get their own migration file.
- Removing an entity property means removing any class-level `@Index` that references it, or TypeORM metadata goes stale and initialization fails.
- Column **type** changes: TypeORM generates `DROP COLUMN` + `ADD COLUMN`, which wipes data. Replace that pair with `ALTER COLUMN … TYPE … USING …` so existing values are preserved.
- Stale columns should be dropped via migration rather than left behind (follow the project's stale-data rule if it has one).

## Prerequisites

1. **Runtime**: `nvm use` (or the project's pin).
2. **Environment**: confirm the DB connection variables the TypeORM config reads (e.g. `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USERNAME`, `POSTGRES_PASSWORD`, `POSTGRES_DATABASE`) are set in `.env`, and that they point at a **local or disposable** database — generation diffs entities against a live schema.

## Steps

### 1. Identify Changes
Migrations are only affected by changes to `*.entity.ts` files. Run `git diff` on those files to see what changed.

### 2. Suggest a name
Based on the diff, recommend a migration name. Ask the user to confirm or change it.

### 3. Generate the Migration
```bash
yarn migration:generate $NAME   # or the project's equivalent script
```

### 4. Post-Generation Cleanup
Open the generated file and:
- **Remove unrelated changes**: drop any statements that do NOT correspond to this entity diff (drift from other branches shows up here).
- **Preserve data**: rewrite any `DROP`+`ADD` type change as `ALTER … TYPE … USING` (see above).
- **Add comments** explaining what the migration does.
- **Format SQL** for readability without changing its logic.
- **Format layout** of **only the generated file** with scoped Prettier — never a repo-wide format command:
  ```bash
  npx prettier --write <migrations-dir>/<generated-migration-file>.ts
  ```
  *(If Prettier is unavailable, use ESLint scoped to the same file.)*

## Troubleshooting

- **Connection errors**: check `.env` credentials; for cloud databases, confirm your IP is allowed by the DB's firewall/security group.
- **Empty migration**: the entity is not registered in the TypeORM config, or the change does not alter schema (e.g. a transient/virtual property). Confirm registration before assuming no migration is needed.
- **Wrong branch/worktree**: if the entities your task changed are absent, you are on a branch that predates them and will generate against the wrong schema set. Confirm the branch before generating.
