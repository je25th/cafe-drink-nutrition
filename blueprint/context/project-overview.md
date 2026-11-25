# Cafe Drink Nutrition - Project Overview

<!-- blueprint:source-hash 9591eee5bb5849bca6f4e498ba287990e58eb1d3f4a1fca30647c06b67aa0232 -->

> A mobile-first static site (Korean UI) that puts franchise cafe drink nutrition side by side, so people who watch sugar and calories can sort, filter and compare drinks across brands, per cup, including past seasonal drinks.

## Problem

Each cafe brand publishes nutrition info on its own site, in its own format, and some hide it. Seasonal drinks vanish from the brand site when the season ends. Nobody shows drinks from different brands side by side. This project collects the data into one growing file and one page.

## Users

- **Primary:** people who care about sugar and calories when ordering at a cafe, often checking on a phone while in line (including the author).
- **Maybe later:** readers of the author's cafe drink review blog.
- One access tier: anonymous, read-only. No accounts, no user data.

## Features

v1 brands: **Starbucks and Compose Coffee**. Paik's (빽다방) is after v1. Build order (build-plan numbering; 7a/7b moved to Later):

1. **Project setup** - `scraper/` (Python, pytest) and `web/` (Vite React TS) with a placeholder page. Done.
2. **Common format** - `Drink` dataclass (one parsed drink, with `code`, no `id`/dates), `to_number(value)` (`"80"` -> 80, `".3"` -> 0.3, `""`/`"-"` -> None), `drink_id(drink)`.
3. **Starbucks: fetch** - check robots.txt/terms, one JSON per category into `scraper/raw/starbucks/`, 1-2 s apart, plus `fetched_at.txt`.
4. **Starbucks: parse** - `parse_starbucks(raw_json) -> list[Drink]`; `code` = `product_CD`; Tall/355ml; hot/iced from name and category; find out why two "콜드 브루" share a name.
5. **Build drinks.json** - parse -> overrides (by product code) -> `drink_id` -> validate -> merge into the last `drinks.json` -> write, plus a report.
6a. **Compose: fetch** - check robots.txt/terms, save menu HTML and `fetched_at.txt` into `scraper/raw/compose/`; identify the product code.
6b. **Compose: parse** - `parse_compose(html) -> list[Drink]` with BeautifulSoup; missing size -> null + override. Both brands in `drinks.json`.
8. **Drink list** - load `/drinks.json` once; a card per drink (name, brand, size ml, big sugar and kcal); "판매 종료" badge via `isOnSale`; data date at the bottom. **Headline feature starts here.**
9. **Sort and filter** - `filterDrinks(drinks, {brand, category, temp, onSaleOnly})`, `sortDrinks(drinks, key)` (nulls last); chips, "판매 중만" toggle (off by default), sort selector (당류, 칼로리, 카페인).
10. **Drink detail** - tap a card: all nutrients, official page link, `sugarPercent(sugarG)` (100 g = 100%).
11. **Compare: select** - "+ 비교" on each card, fixed bottom bar ("비교 1/2 · 보기"), max 2, tap again to remove; selection as a pure tested function.
12. **Compare: view** - per column: name and size (ml) big; CSS bars for 당류, 칼로리, 카페인 (larger value = full width); table of other nutrients; unknown = "-".
13. **Polish and deploy** - Korean text, empty/loading states, small-screen check, deploy to GitHub Pages.

Later (not v1): compare up to 3, search inside compare, compare list in the URL, "similar drinks" grouping, Paik's then more brands (Mega MGC Coffee), favorites in the browser, automatic data updates (method undecided), per-drink SEO pages and blog links, nearby-cafe map.

## Data model

One static file is the whole contract between `scraper/` and `web/`. **Locked by Step 5; Steps 8-12 depend on it.**

### DrinksFile (`web/public/drinks.json`)

- `version` (string, `YYYY-MM-DD`) - build date; shown in the UI as the data date
- `fetched` (object: brand -> `YYYY-MM-DD`) - each brand's latest fetch date, from `scraper/raw/<brand>/fetched_at.txt`
- `drinks` (DrinkRecord[]) - **accumulates**: never drops a drink that left the brand's site

### Drink (parser output, Python dataclass in `scraper/`)

Values are per cup at `size_ml`. Unknown = `null` (Python `None`), never `0`.

- `code` (string) - the brand's product code (Starbucks `product_CD`). Not the identity; brands can change it
- `brand` (string) - `starbucks` or `compose` in v1
- `name` (string) - Korean menu name
- `category` (string) - the brand's own category
- `temp` (`"hot"` | `"iced"` | null)
- `size_label` (string | null) - e.g. `Tall`
- `size_ml` (number | null) - Starbucks: 355
- `kcal` (number | null)
- `sugar_g`, `carbs_g`, `protein_g`, `fat_g`, `sat_fat_g` (number | null)
- `sodium_mg`, `caffeine_mg` (number | null)
- `source_url` (string) - the brand's official page for the drink

### DrinkRecord (one entry in `drinks.json`, one TypeScript type in `web/`)

All Drink fields, plus:

- `id` (string) - `drink_id()`: `<brand>-<name with all whitespace removed>-<hot|iced>`, no temp part when temp is null (e.g. `starbucks-자몽허니블랙티-iced`). Unique. Opaque: code never parses it
- `first_seen` (string, `YYYY-MM-DD`) - fetch date when the drink first appeared
- `last_seen` (string, `YYYY-MM-DD`) - latest fetch date that still had it
- On sale = `last_seen` equals `fetched[brand]` (computed in the web app, `isOnSale`)

Not stored: descriptions, photos (copyright), any user data. No per-100ml values anywhere. Only the latest values are kept; older values live in git history.

### Overrides (`overrides.json`, hand-edited)

- Keyed by brand + product code; each entry sets field values that replace the parsed ones (e.g. `size_ml` for bottled drinks, `temp` when unclear, `name` to tell two same-named drinks apart).
- Applied after parsing, before `drink_id` and validation. The report lists overrides that matched nothing.

### Raw files (`scraper/raw/<brand>/`)

- Unmodified responses (Starbucks: one JSON per category, e.g. `W0000001` = 콜드 브루; Compose: menu HTML) plus `fetched_at.txt`. Parsers read only these; tests use saved copies as fixtures.

### Derived rules

- **Merge (pure, tested):** seen again -> new values, `last_seen` = brand fetch date, `first_seen` kept; new -> `first_seen` = `last_seen` = fetch date; not seen -> kept unchanged. Building twice on the same raw files changes nothing.
- **Hot/iced:** name starts with "아이스" -> iced; always-cold Starbucks categories (콜드 브루, 프라푸치노, 블렌디드, 피지오) -> iced; otherwise null until fixed in overrides.
- **Starbucks:** every drink Tall/355ml; numbers arrive as strings (e.g. `".3"`); no size or temp field.
- **Validation (build stops on failure):** kcal > 0; sugar_g <= carbs_g + 1; no duplicate ids in one run (names both product codes); stop and show the diff if more than 10% of a brand's on-sale drinks leave the site in one run or any value changes by more than 50%. An option accepts the diff after review (e.g. a season ended).
- **Report:** `temp: null` drinks, unmatched overrides, renamed drinks (same code, new name), diff vs last file (added, no longer on sale, back on sale, changed).
- **Sugar %:** `sugar_g` as a percent of the Korean daily reference value, 100 g (25 g = 25%).

## Tech stack

- **Python 3.12+** (`scraper/.venv`) - one scraper per brand; `requests` for HTTP, BeautifulSoup for HTML; no headless browser unless a site needs JavaScript.
- **pytest** - parsers, `to_number`, `drink_id`, merge, validation.
- **React 19 + TypeScript + Vite 8** (`web/`) - static SPA; logic as pure functions in `web/src/lib/`, thin components, `useState` only, plain CSS bars, no state or chart libraries.
- **Vitest** - web logic (on sale, sort, filter, sugar %, compare selection); not installed yet.
- **No** backend server, database, or login.
- **Scraping rules:** robots.txt and terms checked before each brand's first fetch; 1-2 s between requests; about once a week; clear User-Agent with the project name.

## Monetization

None in v1. Free; maybe ads after the service has real users.

## UI/UX

Mobile first, one simple page, Korean UI, clean and calm with easy-to-read numbers.

- `/` (only route) - top: brand, category and hot/iced filters, "판매 중만" toggle (off by default), sort selector (당류, 칼로리, 카페인). Below: drink cards (name, brand, size, big sugar and kcal, "판매 종료" badge when not on sale) with "+ 비교". Small data-date text.
- **Detail** (from tapping a card) - all nutrients, sugar %, official page link.
- **Compare bar** - fixed at the bottom, "비교 1/2 · 보기", opens the compare view at 2 drinks.
- **Compare view** - two columns, name and size (ml) big on top, CSS bars for the three main numbers, table for the rest. Different cup sizes are fine. State is in memory only (resets on refresh).

## Deployment

- **Host:** GitHub Pages, static. Build `cd web && npm run build` -> `web/dist/`. Vite `base` = repo name.
- **Data updates:** manual. Run the scraper build locally, review the report and diff, commit `web/public/drinks.json`.
- No env vars, database, workers or health checks.

> TODO: repo name (for `base`) and how `web/dist/` gets published (Pages action or a `gh-pages` branch) are not decided.

## Open questions

> Contradictions and gaps between the plans. Resolve them in the plans, then re-run /overview.

- **Compose product code:** overrides and rename detection need a `code`; if Compose pages have none, `code` and the overrides key need another rule (Step 6a).
- **temp fixed later:** an override that sets a null temp changes the drink's id, so the old id stays as a "판매 종료" duplicate. Clean up by hand, or let the report flag it?
- **`source_url` of off-sale drinks:** the official page may be gone after the season; the link may 404.
- **`brand` values:** both plans say `brand` but not its form; the overview and Step 2 use codes (`starbucks`). Where do Korean labels for the chips come from?
- **Category filter across brands:** Starbucks and Compose use different category names. Filter by each brand's raw category, or map them to shared categories?
- **File locations:** where `overrides.json` lives (likely `scraper/`), and whether `scraper/raw/` is committed or gitignored.
- **Per-100ml test:** project-plan §5 says Vitest covers "per-100ml logic", but both plans say no per-100ml values anywhere. Probably should read "sugar %".
- **Hosting:** project-plan §5 says "GitHub Pages or Cloudflare Pages"; build-plan settles on GitHub Pages.
- **"the other two are plain HTML"** (build-plan, settled decisions) still counts Paik's; v1 has only Compose.
- **Detail view form:** modal/sheet or inline expand (no router in v1).
