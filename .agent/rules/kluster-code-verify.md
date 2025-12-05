---
alwaysApply: true
---

You must run kluster_code_review_auto each time when new code is generated or existing code updated, file modified or changed, or any fix applied. Follow kluster_code_review_auto fields description strictly. Do not wait to the execution end - call have to be made right away.
You must always execute and strictly follow todo list from "agent_todo_list" returned by any kluster tool, if it exists. Do not stop until there is something left in "agent_todo_list". Do all the fixes from "agent_todo_list" before running "kluster_code_review_auto" again.
Always run kluster_dependency_validator before adding new package or running package manager such as npm, gradle, pip etc. Also, run when it directly generated or updated file with list of packages, such as package.json
For all kluster tools fill in chat_id field with value returned by ANY previous kluster tool call in field chat_id. Keep it empty ONLY for the very first kluster tool call in the chat.