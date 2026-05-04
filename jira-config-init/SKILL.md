---
name: jira-config-init
description: MANUAL TRIGGER ONLY: invoke only when user types /jira-config-init. Triggers when the user asks to set up or initialise Jira config for a project. Also triggers when the user says "init jira", "setup jira config", or "create jira config".
---

# Jira Config Init — Skill

Set up or initialise Jira configuration (`.jira.json`) for the local workspace. You should suggest running this skill whenever you enter a new project directory that lacks Jira configuration but the user requests a Jira operation.

## Steps

### Step 1. Check for existing config

First, check if `.jira.json` already exists in the current directory (`ls -la .jira.json`).
- If the file exists, read it, show its contents to the user, and ask if they wish to overwrite or update it. Wait for response.
- If it doesn't exist, proceed.

### Step 2. Ask the user for config values

Ask the user to provide the three required pieces of configuration (in a single message):
1. **Atlassian site URL** — e.g. `acme.atlassian.net` (This will be the standard `cloudId` for tools)
2. **Default project key** — e.g. `ACME`
3. **Display name** (optional) — e.g. `Acme – Backend API`

Stop and wait for the user to provide these.

### Step 3. Write the config file

Generate the config file `.jira.json` in the current working directory containing their provided details. Do not inject placeholders if the user provided values.

```json
{
  "cloudId": "<cloudId>",
  "defaultProject": "<defaultProject>",
  "displayName": "<displayName>"
}
```

### Step 4. Confirm and suggest commit

Inform the user that the configuration file is structurally ready and provide them with the commit command they can run on their own to save it for their team:

```bash
git add .jira.json
git commit -m "chore: add jira config"
```

Remind them that `.jira.json` contains no personal secrets or passwords (as auth is seamlessly handled underneath via MCP scopes) and is strictly meant to be committed so that all teammates pull standard workflow mappings. Have a great day!
