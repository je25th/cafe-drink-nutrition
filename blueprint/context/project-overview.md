# Cafe Drink Nutrition - Project Overview

<!-- blueprint:source-hash 1f99161d87af3adc1e424fee5a92bdba44e334abde546b4c6c775db8e2c5f5a6 -->

> A mobile-first static site (Korean UI) that puts franchise cafe drink nutrition side by side, so people who watch sugar and calories can sort, filter and compare drinks across brands, per cup.

## Problem

Each cafe brand publishes nutrition info on its own site, in its own format, and some hide it. Nobody shows drinks from different brands side by side. This project collects the data into one file and one page.

## Users

- **Primary:** people who care about sugar and calories when ordering at a cafe, often checking on a phone while in line (including the author).
- **Maybe later:** readers of the author's cafe drink review blog.
- One access tier: anonymous, read-only. No accounts, no user data.

## Features

v1 brands: **Starbucks and Compose Coffee**. Paik's (빽다방) is after v1. Build order (build-plan numbering; 7a/7b moved to Later):

1. **Project setup** - `scraper/` (Python, pytest) and `web/` (Vite React TS) with a placeholder page.
2. **Common format** - `Drink` dataclass and `to_number(value)` (`"80"` -> 80, `".3"` -> 0.3, `""`/`"-"` -> None).
3. **Starbucks: fetch** - check robots.txt/terms, download one JSON per category into `scraper/raw/starbucks/`, 1-2 s apart.
4. **Starbucks: parse** - `parse_starbucks(raw_json) -> list[Drink]`; Tall/355ml; hot/iced from name and category.
5. **Build drinks.json** - parse raw files -> apply `overrides.json` -> validate -> write `web/public/drinks.json`, plus a report (`temp: null` list, diff vs last file).
6a. **Compose: fetch** - check robots.txt/terms, save menu HTML into `scraper/raw/compose/`.
6b. **Compose: parse** - `parse_compose(html) -> list[Drink]` with BeautifulSoup; missing size -> null + override. Both brands in `drinks.json`.
8. **Drink list** - load `/drinks.json` once; a card per drink (name, brand, size ml, big sugar and kcal); data date at the bottom. **Headline feature starts here.**
9. **Sort and filter** - `filterDrinks(drinks, {brand, category, temp})`, `sortDrinks(drinks, key)` (nulls last), filter chips and sort selector (당류, 칼로리, 카페인). First web logic with Vitest.
10. **Drink detail** - tap a card: all nutrients, official page link, `sugarPercent(sugarG)` (100 g = 100%).
11. **Compare: select** - "+ 비교" on each card, fixed bottom bar ("비교 1/2 · 보기"), max 2, tap again to remove; selection as a pure tested function.
12. **Compare: view** - per column: name and size (ml) big; CSS bars for 당류, 칼로리, 카페인 (larger value = full width); table of other nutrients; unknown = "-".
13. **Polish and deploy** - Korean text, empty/loading states, small-screen check, deploy to GitHub Pages.

Later (not v1): compare up to 3, search inside compare, compare list in the URL, "similar drinks" grouping, Paik's then more brands (Mega MGC Coffee), favorites in the browser, automatic data updates (method undecided), per-drink SEO pages and blog links, nearby-cafe map.

## Data model

One static file is the whole contract between `scraper/` and `web/`. **Locked by Step 5; Steps 8-12 depend on it.**

### DrinksFile (`web/public/drinks.json`)

- `version` (string, `YYYY-MM-DD`) - build date; shown in the UI as the data date
- `drinks` (Drink[])

### Drink

Python dataclass in `scraper/`, mirrored by one TypeScript type in `web/`. Values are per cup at `size_ml`. Unknown = `null` (Python `None`), never `0`.

- `id` (string) - `<brand>-<brand product code>`, e.g. `starbucks-9200000002487`; never the name (names repeat). Unique.
- `brand` (string) - `starbucks` or `compose` in v1 (see Open questions)
- `name` (string) - Korean menu name
- `category` (string) - the brand's own category
- `temp` (`"hot"` | `"iced"` | null)
- `size_label` (string | null) - e.g. `Tall`
- `size_ml` (number | null) - Starbucks: 355
- `kcal` (number | null)
- `sugar_g`, `carbs_g`, `protein_g`, `fat_g`, `sat_fat_g` (number | null)
- `sodium_mg`, `caffeine_mg` (number | null)
- `source_url` (string) - the brand's official page for the drink

Not stored: descriptions, photos (copyright), any user data. No per-100ml values anywhere.

### Overrides (`overrides.json`, hand-edited)

- Keyed by drink `id`; each entry sets field values that replace the parsed ones (e.g. `size_ml` for bottled drinks, `temp` when the name is unclear).
- Applied after parsing, before validation.

### Raw files (`scraper/raw/<brand>/`)

- Unmodified responses (Starbucks: one JSON per category, e.g. `W0000001` = 콜드 브루; Compose: menu HTML). Parsers read only these; tests use saved copies as fixtures.

### Derived rules

- **Hot/iced:** name starts with "아이스" -> iced; always-cold Starbucks categories (콜드 브루, 프라푸치노, 블렌디드, 피지오) -> iced; otherwise null until fixed in overrides.
- **Starbucks:** every drink Tall/355ml; numbers arrive as strings (e.g. `".3"`); no size or temp field.
- **Validation (build stops on failure):** kcal > 0; sugar_g <= carbs_g + 1; no duplicate ids; stop and show the diff if more than 10% of drinks disappear or any value changes by more than 50% vs the last `drinks.json`.
- **Sugar %:** `sugar_g` as a percent of the Korean daily reference value, 100 g (25 g = 25%).

## Tech stack

- **Python 3.12+** (`scraper/.venv`) - one scraper per brand; `requests` for HTTP, BeautifulSoup for HTML; no headless browser unless a site needs JavaScript.
- **pytest** - parsers, `to_number`, validation.
- **React 19 + TypeScript + Vite 8** (`web/`) - static SPA; logic as pure functions in `web/src/lib/`, thin components, `useState` only, plain CSS bars, no state or chart libraries.
- **Vitest** - web logic (sort, filter, sugar %, compare selection); not installed yet.
- **No** backend server, database, or login.
- **Scraping rules:** robots.txt and terms checked before each brand's first fetch; 1-2 s between requests; about once a week; clear User-Agent with the project name.

## Monetization

None in v1. Free; maybe ads after the service has real users.

## UI/UX

Mobile first, one simple page, Korean UI, clean and calm with easy-to-read numbers.

- `/` (only route) - top: brand, category and hot/iced filters plus sort selector (당류, 칼로리, 카페인). Below: drink cards (name, brand, size, big sugar and kcal) with "+ 비교". Small data-date text.
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

- **Per-100ml test:** project-plan §5 says Vitest covers "per-100ml logic", but both plans say no per-100ml values anywhere. Probably should read "sugar %".
- **Hosting:** project-plan §5 says "GitHub Pages or Cloudflare Pages"; build-plan settles on GitHub Pages.
- **"the other two are plain HTML"** (build-plan, settled decisions) still counts Paik's; v1 has only Compose.
- **`brand` values:** code (`starbucks`) or display name (`스타벅스`)? Where do Korean labels for the filter chips come from?
- **Category filter across brands:** Starbucks and Compose use different category names. Filter by each brand's raw category, or map them to shared categories?
- **Compose details:** size (ml), hot/iced, product code for the id, and the official page URL are unknown until Step 6a.
- **File locations:** where `overrides.json` lives (likely `scraper/`), and whether `scraper/raw/` is committed or gitignored.
- **Detail view form:** modal/sheet or inline expand (no router in v1).
- **Step 1 is done** (scaffold commit) but still unchecked in build-plan.md.
