---
name: claudio-respond-review
description: Read and reply to the open review threads on the current branch's pull/merge request, on GitHub or GitLab. Use when asked to respond to review comments, address PR/MR feedback, or answer reviewer threads.
disable-model-invocation: true
---

# claudio-respond-review

Answer the reviewer threads on the current branch's PR (GitHub) or MR (GitLab), making
the requested code changes where appropriate and replying in-thread.

## 1. Detect platform and the request

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/detect_platform.py"
```

- **github** (`gh`): find the PR for the current branch — `gh pr view --json number,url`.
  List review threads/comments — `gh api repos/{owner}/{repo}/pulls/{number}/comments`
  (and `.../reviews` for review summaries).
- **gitlab** (`glab`): find the MR — `glab mr view`. List discussion threads —
  `glab api projects/:id/merge_requests/{iid}/discussions`.

If there is no open PR/MR for the branch, tell the user and stop.

## 2. Triage each unresolved thread

For every open/unresolved thread:

1. Read the comment and the code it points at (file + line).
2. Decide: does it ask for a **change**, a **question/answer**, or is it a **nit/won't-fix**?
3. If a change is warranted, make it — on the changed lines only, following the claudio
   coding rules. Keep edits minimal and scoped to the feedback.

## 3. Reply in-thread

Post a concise, professional reply on the **same thread** (not a new top-level comment):

- **GitHub:** reply to the review comment via
  `gh api -X POST repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies -f body=...`
  (or the threaded replies endpoint). State what you changed (with the commit) or, for a
  question, answer it directly.
- **GitLab:** add a note to the discussion via
  `glab api -X POST projects/:id/merge_requests/{iid}/discussions/{discussion_id}/notes -f body=...`.
  Resolve the discussion when the request is fully addressed
  (`...discussions/{id}?resolved=true`).

## 4. Summarize

List each thread, what you did (changed / answered / deferred with reason), and whether
it was resolved. If you made code changes, remind the user to commit and push so the
replies reference the new commit.

Never resolve or dismiss feedback you did not actually address.
