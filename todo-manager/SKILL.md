---
name: todo-manager
description: Automatically triggers whenever the user asks to add a task, idea, or tech-debt item to the project's TODO list.
---

# TODO Manager Skill

This localized skill allows the agent to seamlessly maintain and organize the project's central `TODO.md` backlog.

## Usage Trigger
Agents must actively utilize this sequence whenever the user states phrases like:
- "Add this to the TODO"
- "Put this on the backlog"
- "Create a todo for this technical debt"

## Execution Instructions
1. **Locate the File**: The target file is `TODO.md` at the root directory of the repository.
2. **Format**: Parse the user's request and append the task to the bottom of the `## Task List` section using GitHub Markdown checklist syntax (`- [ ] **Category**: Context`).
3. **Contextualize**: If the user did not explicitly define a category, intelligently deduce one based on context (e.g., **Testing**, **Optimization**, **Documentation**, **Bug**).
4. **Execution**: Use the `replace_file_content` or `multi_replace_file_content` tool to insert the new line item.
