# hed-web

Purpose: browser pages that validate HED annotations (a HED string, a JSON sidecar, a TSV file with its sidecar,
and a whole BIDS dataset) with the `hed-validator` package, deployed to GitHub Pages.
Not in scope: the validation logic itself. That lives in `hed-validator` (the hed-javascript repository); this repo
only collects input, calls the validator and shows the issues.

## Commands

Test framework: Vitest. Never convert the suite to another framework as a side effect of other work.

- Install dev env: `npm ci` (installs exactly what `package-lock.json` pins)
- Run tests: `npm test` (runs `vitest --run`)
- Single test file: `npx vitest run <path>`, for example `npx vitest run src/utils/hedVersion.spec.js`
- Build: `npm run build` (output in `buildweb/`)
- Local dev server: `npm run dev`
- CI (`.github/workflows/ci.yml`) runs `npm ci`, `npm test`, `npm run build`. No linter is configured.

## Layout

- `src/` - one `validate_*.jsx` per page, shared `components/`, `utils/`, and the help text in `help/help_text.json`.
- `validate_*.html`, `index.html` - the Vite entry points, one per page.
- `tests/unit/` - page-flow tests; `tests/helpers/` - their helpers.
- `tests/fixtures/` - test data copied from hed-javascript. Do not edit; `tests/fixtures/README.md` says how to
  refresh it.
- `.status/` - working notes. Gitignored; local to each machine.

## Conventions that differ from defaults

- **ASCII only** in prose, code, comments, and filenames: `-` not em or en dashes, `->` not arrows, `...` not an
  ellipsis character, straight quotes. Exception: genuine data (author names, dataset titles, recorded API
  responses) keeps whatever characters it actually contains.
- Markdown headers use sentence case: capitalize the first word, proper nouns, and acronyms only.
- In Markdown, command code blocks are tagged `shell`, unless the block is genuinely PowerShell-specific.

## Rules that are easy to get wrong

- `hed-validator` is installed from a hed-javascript git commit, not a semver range. The commit is in
  `package.json` and `package-lock.json`; read it there, never restate it elsewhere.
- Tests live in two trees, `src/**/*.spec.{js,jsx}` and `tests/unit/`; `vitest.config.js` `include` lists both.
  A new spec file outside them is silently not run.

## Related repositories

- `hed-javascript` - publishes `hed-validator` and is the source of `tests/fixtures/`. Not vendored here; a session
  that needs it must be granted access to that checkout.

## Where the thinking lives

`.status/` is gitignored, so it exists only on the machine that wrote it and never in a fresh clone or worktree.

- `.status/README.md` - current state, unfinished work, and an ordered `Next` list. Read this first.
- `.status/development_history.md` - what has shipped, newest first, with pointers to the records. History only; append at the top when a PR merges.
- `.status/decisions.md` - why things are the way they are. Read before proposing structural changes. Append entries; never rewrite one.
- `.status/plans/*.md` - unfinished plans only. Check the `Status:` header and the `[ ]` / `[x]` markers before starting work. A finished plan moves to `.status/archive/completed_plans/`, renamed `archived_YYYY-MM-DD_<name>` with the day it was archived; split any still-open boxes into a new plan first.
- `.status/notes/` - dated records, always named `YYYY-MM-DD_<slug>.md`. Write-once.
- `.status/local-environment.md` - this machine's paths, interpreter, and quirks. Tool-agnostic. Never copy its contents into a committed file.
- IMPORTANT: do not read `.status/archive/` unless a file is named for you. The `.status/` root holds only `README.md`, `decisions.md`, `development_history.md`, and `local-environment.md`; nothing else is created there.

## Working agreements

- IMPORTANT: every file written to `.status/` opens with a `For humans:` summary - three or four sentences, at the
  very top: what the file is and what a person needs to take from it. The same applies to a long answer in a
  session: lead with the conclusion.
- IMPORTANT: temporary scripts, experiments, and one-off test files go in `.status/scratch/` - **never the
  repository root**. Delete them when the experiment ends; anything in `scratch/` may be deleted unread.
- IMPORTANT: never delete or rewrite a file under `.status/` without asking first. Appending is fine.
- All changes go on a branch cut from `main` and reach `main` by pull request. Never edit or commit on `main`.
- For a change spanning more than three files, write a plan to `.status/plans/` and stop for review before editing.
- When you are guessing about an external API or data format, say so explicitly rather than assuming.
- Show evidence, not assertions: the command you ran and its actual output.
- Do not commit, push, or create branches unless asked.
