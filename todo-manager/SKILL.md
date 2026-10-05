---
name: todo-manager
description: Automatically triggers whenever the user asks to add a task, idea, or tech-debt item to the project's TODO list.
---

# TODO Manager Skill

This localized skill allows the agent to seamlessly maintain and organize the project's central `TODO.md` backlog asynchronously.

## Usage Trigger
Agents must actively utilize this sequence whenever the user states phrases like:
- "Add this to the TODO"
- "Put this on the backlog"
- "Create a todo for this technical debt"

## Execution Instructions
1. **Locate the File**: The target file is unconditionally `TODO.md` at the root directory of the repository. (If it is somehow missing, generate it utilizing the standard template).
2. **Format**: Parse the user's request and append the parsed task to the bottom of the `### Task List` section utilizing generic GitHub Markdown checklist syntax (`- [ ] **Category**: Context`).
3. **Contextualize**: If the user did not explicitly define a category, intelligently deduce one based on context (e.g., `**Testing**`, `**Optimization**`, `**Bug**`).
4. **Execution**: Utilize the `multi_replace_file_content` core tool to natively insert the new line item without disrupting or overwriting existing pending checkboxes in the document.
