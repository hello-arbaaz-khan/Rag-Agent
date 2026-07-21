# Command: Update Context Before Push

When this file is read, perform the following steps:

1. Review all code changes made in this session/branch
   (git diff against main or last commit) — check for ADDED,
   MODIFIED, and DELETED files/functions/endpoints.

2. Open context.md and update ONLY the sections affected:

   IF SOMETHING WAS ADDED:
   - New API endpoint → add new row to "API Reference Map"
   - New file → add new entry to "Full Codebase Map"
   - New architecture piece → update "Architecture" or "Data Flow"

   IF SOMETHING WAS MODIFIED:
   - Changed function/logic → update its one-line purpose/description
     in "Full Codebase Map" and/or "API Reference Map"
   - Update file:line references if line numbers shifted
   - Update "Data Flow" if the sequence of calls changed

   IF SOMETHING WAS DELETED:
   - Remove the corresponding row/entry from "API Reference Map"
   - Remove the corresponding entry from "Full Codebase Map"
   - Remove references to deleted file/function from "Data Flow",
     "Core Modules", and "Do Not Touch / Gotchas" if mentioned there
   - Do NOT leave dangling references to files/functions/endpoints
     that no longer exist — a stale reference is worse than no
     reference, since it will misdirect future lookups

3. Always update "Recent Changes / Current Work" with a short summary:
   what was added, changed, and removed, and why.

4. If a deleted feature had a "gotcha" note in "Do Not Touch", check
   if that gotcha still applies elsewhere or should be removed entirely.

5. Do NOT touch sections/rows that are unrelated to this change.

6. After updating, output a short summary of exactly what was added,
   modified, and removed in context.md, so it can be reviewed before push.
