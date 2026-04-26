## MANDATORY GIT WORKFLOW (do not skip)

After any code edit, before declaring a task complete, you MUST:

1. Run `git status` and confirm only the intended files are modified.
2. Run `git diff` and review the actual changes to confirm they are correct.
3. Stage with `git add <specific files>` (never `git add .` blindly).
4. Commit with a descriptive message in imperative mood.
5. Run `git push origin main`.
6. Run `git fetch origin && git log origin/main -1 --oneline` and verify
   the commit hash on origin matches HEAD.
7. Report the commit hash and the URL to the GitHub commit page.

A task is NOT complete until step 7 returns successfully. "Static checks
passed locally" is not the same as "shipped." Railway deploys from
origin/main only — local edits never reach production.

If `git push` fails (auth, conflict, network), STOP and report the exact
error rather than retrying or working around it.
