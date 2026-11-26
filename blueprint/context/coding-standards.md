# Coding Standards

> Tuned by `/onboard` (261123) for this repo: a Python scraper in `scraper/` and a
> React + TypeScript + Vite static site in `web/`.

## Project Structure

- One repo, two folders. Root holds only workflow files and `.gitignore`.
- `scraper/` - Python package `scraper` in `scraper/src/scraper/`, tests in
  `scraper/tests/`, raw downloads in `scraper/raw/<brand>/`.
- `web/` - Vite app. Pure logic in `web/src/lib/`, components in
  `web/src/components/`, the data file in `web/public/drinks.json`.
- The only link between the two is `web/public/drinks.json`, written by the
  scraper build and read by the web app.

## Python (scraper)

- Python 3.12+, run from `scraper/.venv`. Dependencies go in
  `scraper/pyproject.toml`.
- HTTP with `requests`, HTML with BeautifulSoup. No headless browser unless a site
  needs JavaScript.
- Fetch and parse are separate: fetch saves raw responses to `scraper/raw/`; parse
  only reads files. Tests never hit the real sites.
- Polite scraping: check robots.txt and terms before a brand's first fetch, wait
  1-2 seconds between requests, send a clear User-Agent with the project name.
- Parsers and validators are pure functions (`parse_<brand>(raw) -> list[Drink]`).
- `Drink` is a dataclass with the fields from the project plan. Type hints on
  public functions.
- Unknown values are `None` (`null` in JSON), never `0`.
- ids come only from `drink_id()`: brand + name with all whitespace removed +
  temp. The brand's product code is stored as `code`, never used as the id.
  Code treats ids as opaque keys and never parses them.
- Store only names and numbers. No descriptions or photos.

## TypeScript

- Strict mode (on by default in TypeScript 7); `noUnusedLocals` and
  `noUnusedParameters` are on.
- No `any` - use proper types or `unknown`.
- One `Drink` type that matches the `drinks.json` format.
- Use type inference where obvious, explicit types where helpful.

## React

- Static single-page app (Vite + React 19). No router, server, or SSR in v1.
- Functional components and hooks only. `useState` is enough for filters and the
  compare selection; no state library.
- Components stay thin. Sorting, filtering, selection and number logic live in
  pure functions in `web/src/lib/`.
- Load `drinks.json` once at start; everything else happens in the browser.

## Naming

- Components: PascalCase (`DrinkCard.tsx`)
- TS functions: camelCase; Python functions and modules: snake_case
- Constants: SCREAMING_SNAKE_CASE
- Types/Interfaces/classes: PascalCase (no prefix)

## Styling

- Plain CSS (`web/src/index.css` and component CSS files). No CSS framework,
  no chart library: compare bars are plain CSS.
- Mobile first. Korean UI text.
- Show per-cup values with the cup size (ml) next to them. No per-100ml values.

## Data and Validation

- `drinks.json` has a `version` (build date, `YYYY-MM-DD`), a `fetched` date per
  brand, and a list of drinks. It accumulates: the build merges into the last
  file and never drops a drink that left the brand's site.
- The scraper build validates before writing: kcal > 0, sugar <= carbs + 1g, no
  duplicate ids. It stops and shows the diff if more than 10% of a brand's
  on-sale drinks leave the site in one run or a value changes by more than 50%.
- Manual fixes go in `overrides.json`, applied by brand + product code.
- The web app shows `-` for unknown (`null`) values and treats them as last when
  sorting.

## Error Handling

- Scraper: fail loudly with a clear message (which brand, which file, which id).
  Never write a partial or unvalidated `drinks.json`.
- Web: show simple Korean loading and error states if `drinks.json` can't load.

## Testing

The blueprint installs no test runner; testing is opt-in at the project level,
because the overlay can't know your stack. Adding unit testing is an explicit
setup task the AI can do through the normal workflow, either as a build-plan item
or with `/tests`. The setup should choose the stack-native runner, wire the
scripts or commands, add a small example test, and update the Commands section
of `AGENTS.md`.

When `AGENTS.md` declares a `Verify` command, treat it as the umbrella automated
gate. It combines only the checks this project actually has, in this order when
available: typecheck, tests, then build. The command does not enable an absent
test runner or replace focused evidence. It gives local work and optional CI one
exact command to run. `/ci` owns Verify and CI setup. `/tests` adds the real test
command to Verify when it already exists, but never creates CI only because
testing was configured.

**The opt-in switch is one signal: a `test` command in the Commands section of
`AGENTS.md`.** Declare one and **tests become a gate for logic-bearing steps**,
not an optional extra; leave it out and the loop verifies logic with the evidence
it already uses (run it, a screenshot, the build). Adding the runner is itself a
deliberate step, never a silent mid-step install. This is the single definition
of the switch; the skills and `ai-interaction.md` only point back here.

- **What to test (the scope rule):** pure logic where a wrong answer is possible -
  parsers, formatters, validators, id/slug builders, server actions. These have
  assertable inputs and outputs and real edge cases (empty, missing, malformed).
- **What not to test:** UI components and integration-level surfaces (render or
  export routes, anything driving a real browser or external service). Verify those
  with a screenshot and the build, not brittle unit tests.
- **The gate (when a runner is configured):** a build step that adds in-scope logic
  must ship a passing test in the same reviewable diff. The project's test command
  must be green before the step is approved, before any checkpoint commit, and
  before `/complete` merges. UI and integration-only steps are exempt and ride on
  screenshot plus build evidence.
- **When it's named:** the `/feature` spec's Testing section predicts the coverage,
  `/implement` writes the test with the step, and if a step surfaces logic the spec
  didn't foresee, add a focused test then.
- An empty suite should fail, not pass, so "no tests ran" never looks like "passed".
- Web test files live next to source files (for example `web/src/lib/sort.test.ts`).
  Scraper tests live in `scraper/tests/` (`test_<module>.py`), with saved raw
  files as fixtures in `scraper/tests/fixtures/`.
- Run them via the project's test command (see Commands in `AGENTS.md`), not a
  hardcoded tool name.

Stack binding: the scraper uses pytest (configured). The web app will use Vitest
for `web/src/lib/` once `/tests` adds it; until then, web logic has no test gate.

## Browser Verification

For UI and integration behavior, prefer real browser evidence over reading the
code and assuming it works.

- Browser automation is separately opt-in through `/tests browser`. That setup
  reuses a compatible runner or prefers Playwright for supported projects, then
  documents the exact command as `Browser tests` in `AGENTS.md`.
- When `Browser tests` is declared, add focused coverage for stable behavioral
  done-whens when it is proportionate, and run the documented command during
  `/check`. Do not assume it proves visual fidelity, real authenticated-profile
  behavior, browser chrome, or another claim the test does not observe.
- If no Browser tests command is declared, do not add a runner silently in the
  middle of an unrelated feature. Use the available dev server, browser
  screenshots, build output, API output, or manual evidence instead.
- Browser tests are not part of the default Verify command or CI unless the user
  separately chooses that slower gate.
- Browser evidence is especially important for flows that click, type, submit,
  navigate, download files, render complex layouts, or depend on client-side
  state.

## Code Quality

- No commented-out code unless specified
- No unused imports or variables
- Keep functions under 50 lines when possible

## Comments

Write code that explains itself; comment only what the code cannot say.
Over-commenting is a common AI tell, so resist it.

- Comment the **why**, not the **what**. Delete any comment that restates the code.
- No banner/header blocks, section dividers, or step-by-step narration of obvious
  code. A file does not need a comment announcing each region.
- A comment earns its place only when it captures something the code can't: a
  non-obvious decision, a gotcha or workaround, why a value is what it is, or a
  link to a spec or issue.
- Prefer self-documenting names and small functions over explanatory comments.
- Keep doc comments minimal: a one-line purpose on an exported type or function is
  plenty; don't write JSDoc that just repeats the signature.
- When in doubt, leave the comment out.
- Language: ordinary comments and docstrings are in English. Important warnings
  are in Korean, so the owner reads them at a glance: high-risk or fragile code
  (for example scraping that breaks when a brand site changes), what breaks and
  why, and what to do by hand when it does. Start the risk line with `[위험 높음]`
  or `[주의]`.

## Writing

- No em dashes (U+2014) in generated content: docs, comments, commit messages,
  READMEs, specs. They read as AI-generated.
- Use a hyphen for `term - description` separators; rephrase prose with commas,
  parentheses, or a colon. Avoid en dashes and the ellipsis character too.
