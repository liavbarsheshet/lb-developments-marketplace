![claudio banner](./assets/banner.png)

# claudio

Makes Claude a better developer: it enforces a strict coding standard, runs a
post-implementation quality gate, reviews branch-only diffs, responds to PR/MR review
threads, and maintains a `~/.claudio` knowledge base of analyzed repos.

## What it does

- **Always-on coding standard.** A `SessionStart` hook injects claudio's coding rules
  (guard clauses, longest-first ordering, JSDoc-style docs, descriptive names, no magic
  numbers, fail-fast errors, immutability, single responsibility) into every session of
  any project where claudio is installed.
- **Post-implementation quality gate ("the bible").** A `Stop` hook runs after each turn
  on a side branch: it auto-formats the branch-changed files, then drives a checklist —
  duplication check, code review, R&D/quality test, and unit tests — scoped to **only**
  what the branch changed.
- **Branch-scoped review.** Every review targets the diff against the default-branch
  merge-base, so it never flags the user's pre-existing code.
- **GitHub + GitLab.** Remote-aware skills detect the host and use `gh` or `glab`.
- **Repo knowledge base.** Analyzed repos are saved as `~/.claudio/<repo>.md` with the
  default branch's commit hash and analysis date; re-analysis triggers only when 7+ days
  have passed **and** that commit changed.

## API

| Invocation | Mode | Description |
| ---------- | ---- | ----------- |
| `/claudio:claudio-code-review` (alias `/claudio:claudio-cr`) | Explicit | Review only the current branch's changes for quality, security, duplication, and rule compliance. `--post` posts inline comments to the PR/MR. |
| `/claudio:claudio-analyze-repo` (alias `/claudio:claudio-analyze`) | Explicit | Deeply analyze the repo and save an indexed record to `~/.claudio/<repo>.md`. |
| `/claudio:claudio-respond-review` | Explicit | Read and reply to the open review threads on the branch's PR (GitHub) or MR (GitLab), making scoped changes. |
| `/claudio:claudio-refactor [path]` | Explicit | Refactor a target (or branch changes) to the claudio rules without changing behavior. |
| `/claudio:claudio-commit` | Explicit | Craft a high-quality conventional commit from the current work. |
| `/claudio:claudio-clean` | Explicit | Delete every record in `~/.claudio`. |
| `/claudio:claudio-doc [path]` | Explicit / Implicit | Document changed functions/classes in the JSDoc style. Claude may also apply it when asked to "document this". |
| `/claudio:claudio-explain [repo] [question]` | Explicit / Implicit | Answer questions about a repo using its saved analysis record. |
| `/claudio:claudio-status` | Explicit / Implicit | List analyzed repos and their freshness. |
| _SessionStart hook_ | Implicit | Injects the claudio coding rules into context every session. |
| _Stop hook_ | Implicit | Runs the post-implementation quality gate on side-branch changes. |

## Requirements

- `python` on `PATH` (the hooks and scripts are stdlib-only Python 3).
- `git`; and `gh` (GitHub) and/or `glab` (GitLab) for the review-thread skills.
- Optional formatters used by the gate when present: `prettier`, `black`/`ruff`,
  `gofmt`, `rustfmt`.

## Coding rules

The full, authoritative rules live in [`rules/coding-rules.md`](./rules/coding-rules.md)
and are what the `SessionStart` hook injects.

Author: Liav Barsheshet
