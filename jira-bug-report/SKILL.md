---
name: jira-bug-report
description: MANUAL TRIGGER ONLY: invoke only when user types /jira-bug-report. Capture a bug report from the user, format it cleanly, auto-triage it, and publish it to Jira.
---

# QA Bug Reporter — Skill

Capture a bug report from the QA engineer, format it cleanly with exact location mapping, auto-evaluate severity and tags, ask about related tickets, and publish it to Jira.

## Steps

### Step 1. Load Config
- Check `.jira.json` in your current working directory. Extract `cloudId` and `defaultProject`. 

### Step 2. Validate input
- Check if the user has provided a clear description of the bug. 
- If the description is too vague (no steps or context), ask the user for clarification before generating the ticket. 
- Ensure you have understood what page or component they are talking about. If they didn't specify, ask them where this happens.

### Step 3. MANDATORY: Triage, Tags, and Links Validation
- **Priority**: Assess the severity of the bug described. If it's a crash or data loss, evaluate it as `High`. For logic/workflow bugs, evaluate as `Medium`. For UI/Cosmetic, evaluate as `Low`.
- **Labels**: Deduce logical tags for the bug (e.g. `frontend`, `backend`, `regression` or specific component names).
- Before creating anything, you MUST pause and ask the QA:
    *"I have triaged this bug as Priority: **[Priority]** and assigned tags **[Tags]**. Can you confirm this is correct? Also, do you want to link this bug ticket to a specific feature or parent ticket? (e.g. PROJ-1401). Finally, would you like me to capture a video recording of the Chrome browser using my `browser_subagent` to include? If yes, please provide the exact reproduction steps for the browser."*
- STOP and wait for their response. Ensure you integrate any corrections they have for Priority or Labels.
- If the user responds YES to capturing a video, use your `browser_subagent` tool to perform the reproduction steps and generate the WebP video artifact.

### Step 4. Format the Bug Report
Translate the user's description into the formalized QA bug structure below. Use bold formatting and emojis to visually simulate Jira panels for easier engineering readability.

```markdown
> 📍 **1. Location Mapping**
> - **URL / Page:** [Deduce the page name based on context]
> - **Component / Field:** [Deduce the exact button or field based on context]

**2. Steps to Reproduce**
[Convert their narrative into a numbered 1-2-3 list]

🛑 **3. Current Behavior**
[Explain what is going wrong]

✅ **4. Expected Behavior**
[Explain what should happen instead]

📸 **5. Evidence**
- [ ] Visuals generated or provided as context by the reporter.
```

### Step 5. Create the Ticket
1. Use `mcp_atlassian-mcp-server_createJiraIssue` to create the ticket.
    - `cloudId`: (from config)
    - `projectKey`: (from config)
    - `issueTypeName`: "Bug"
    - `summary`: A concise 1-sentence title for the bug. 
    - `description`: The markdown structure you generated in Step 4.
    - `contentFormat`: "markdown"
    - `additional_fields`: `{ "priority": {"name": "[Confirmed Priority]"}, "labels": ["[tag1]", "[tag2]"] }` *(Note: use the exact priority and tags confirmed in Step 3)*
2. The tool will return the new ticket ID (e.g., `PROJ-2015`).

### Step 6. Link the Ticket (If specified)
If the user provided a ticket to link to in Step 3:
1. Use `mcp_atlassian-mcp-server_createIssueLink`.
    - `cloudId`: (from config)
    - `inwardIssue`: (The newly created ticket ID, e.g. PROJ-2015)
    - `outwardIssue`: (The user's provided feature ticket, e.g. PROJ-1401)
    - `type`: "Relates" (or ask `mcp_atlassian-mcp-server_getIssueLinkTypes` for the exact type if Relates fails. Default to "Relates").

### Step 7. Finalize
Return the fully generated Jira link and its ticket key back to the QA tester. Let them know it was successfully created and linked.
- **IMPORTANT CLEANUP**: If you generated a video using the `browser_subagent` during this session, use the `run_command` tool to delete the video file (e.g., `rm /path/to/video.webp`) after creating the ticket so the user does not have to worry about local cleanup.
