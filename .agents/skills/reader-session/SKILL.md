---
name: reader-session
description: Stop a session that only reads. Use when a worker searches or restates the task and has not written the change.
---

# A read is not the job

If the task is a patch or a repo edit, the first action is the write. A session that only reads has failed. Stop it and do not resume it. The next prompt names that failure and starts with the write.
