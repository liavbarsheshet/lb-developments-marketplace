---
name: claudio-doc
description: Document the functions and classes the current branch changed, in the claudio JSDoc-style format, without overwriting good existing docs. Use when asked to document code, add docstrings, or write doc comments.
argument-hint: "[path]"
---

# claudio-doc

Add or improve documentation for code the current branch changed (or a specific `path`
if provided), following claudio's documentation rule.

## Steps

1. Determine targets:
   - If a `path` argument is given, document that file/directory.
   - Otherwise use the branch-changed files:
     `python "${CLAUDE_PLUGIN_ROOT}/scripts/branch_changed_files.py"`.

2. For each public class/function lacking a clear doc block, add one in this style:

   ```js
   /**
    * Short explanation of what this does.
    *
    * @param {Type} name Short description
    * @returns {Type} Short description
    */
   ```

   - One short sentence, then tags. **No hyphen** after the parameter name.
   - In JS (untyped), declare types via JSDoc. In TS/Python, rely on native type
     annotations and describe meaning, not the type.

3. **Do not overwrite** good existing documentation — update only what your change
   affects, minimally.

4. Keep comments out of the body unless the code is genuinely hard to follow (claudio
   rule 5). Report which symbols you documented.
