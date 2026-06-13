# claudio Coding Rules

These rules are mandatory for all code you write in a project where the `claudio`
plugin is installed. Apply them as you write — not only after the fact. If the user
explicitly overrides a rule, follow the user.

When editing **existing** code you did not write, apply these rules to the lines you
touch; do not reformat or reorder unrelated, pre-existing lines just to satisfy a rule
(that would create noise and risk regressions).

---

## 1. Guard-clause control flow (no nested `if`s)

Handle edge cases and invalid states first and exit early (`return` / `continue` /
`break` / `throw`). Keep the happy path at the lowest indentation level. Never nest
conditionals when an early return expresses the same logic.

```js
// Bad — nested
function pay(user) {
  if (user) {
    if (user.active) {
      if (user.balance > 0) {
        charge(user);
      }
    }
  }
}

// Good — guard clauses
function pay(user) {
  if (!user) return;
  if (!user.active) return;
  if (user.balance <= 0) return;

  charge(user);
}
```

---

## 2. Longest-first ordering

Where ordering is free to choose, sort lines from **longest to shortest**. Where order
carries meaning (cascade, dependency, scope), correctness wins and you place the line
where it must go.

### 2.1 Imports (JS / TS)

Group top-level imports into three blocks, in this order, each separated by one blank
line:

1. Installed libraries (bare specifiers, e.g. `react`, `lodash`)
2. Alias paths (e.g. `@/...`)
3. Relative paths (e.g. `./`, `../`)

Within **each** block, sort lines longest → shortest. Sort each block independently.

```ts
import { createSelector } from "@reduxjs/toolkit";
import { useEffect } from "react";
import clsx from "clsx";

import { CartSummaryPanel } from "@/components/cart";
import { formatMoney } from "@/utils/money";

import { computeDiscountedTotal } from "../pricing/discount";
import { Button } from "./Button";
```

When inserting into existing code, place the new import in its correct block and at the
length-appropriate position **without** reshuffling the rest if doing so would be
disruptive.

### 2.2 CSS declarations

Within a rule, sort declarations longest line → shortest line. Exception: a declaration
that resets or overrides others (e.g. `all: unset;`, `all: revert;`) must appear
**before** the declarations it affects, even if that breaks the length ordering —
because the cascade order is what makes the result correct.

```css
.button {
  all: unset; /* reset first — correctness over length */
  background: var(--accent);
  padding: 8px 12px;
  color: white;
}
```

The same principle generalizes: when a line nullifies or depends on others, its required
position overrides the longest-first preference.

---

## 3. High-quality, working code

Write clean, readable, correct code. Run the project's linter/formatter and fix
warnings. Before claiming done, validate the change actually works (run it, run tests,
or a quick harness). Never leave the tree in a broken or lint-failing state.

---

## 4. Documentation blocks

Document classes and functions with a short doc block in this style:

```js
/**
 * Short explanation of what this function does.
 *
 * @param {Type} name Short description
 * @param {Type} other Short description
 * @returns {Type} Short description of the result
 */
```

Rules:

- One short sentence of explanation, then the tags.
- **No hyphen** between the parameter name and its description.
- **Types matter.** In untyped languages (JS), declare types via JSDoc
  (`@param {string} id`). In typed languages (TS, Python), rely on the native type
  annotations and describe meaning rather than repeating the type.
- Do **not** overwrite or clobber existing documentation — update it minimally and only
  where your change affects it.

---

## 5. Comments & vertical rhythm

Code should read clearly on its own. Separate logical blocks with blank lines so the
structure is visible at a glance. Add a comment only when the code is genuinely hard to
follow (a non-obvious algorithm, a workaround, a subtle invariant). Do not narrate code
that already speaks for itself.

---

## 6. Descriptive names

Use full, descriptive names. No cryptic abbreviations (`usr`, `tmp2`, `hdlr`). A name
should make its purpose obvious without a comment.

---

## 7. No magic numbers or strings

Replace unexplained literals with named constants that carry meaning
(`const MAX_RETRIES = 3;`). Repeated string keys, URLs, and limits become named
constants or config.

---

## 8. Fail fast, never swallow errors

Validate inputs and preconditions up front (pairs with rule 1). Never silently catch and
ignore an error. Either handle it meaningfully, attach context and rethrow, or let it
propagate — but never leave an empty/`pass` catch that hides failure.

---

## 9. Prefer immutability

Default to `const` / read-only bindings. Avoid reassignment and in-place mutation of
shared state unless there is a clear reason. Immutable data is easier to reason about.

---

## 10. Single responsibility

Keep functions short and focused on one job. If a function needs internal section
comments to explain its phases, that's a signal to split it into well-named smaller
functions.
