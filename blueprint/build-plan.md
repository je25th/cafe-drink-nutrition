# Build Plan

v1 is a mobile-friendly static website that shows the nutrition info of Starbucks and Compose Coffee drinks. You can sort and filter the list, and compare 2 drinks side by side, per cup. The data comes from Python scrapers that I run by hand. Each step should fit in about one hour and end with something I can check: a test passes, a file appears, or I can see it in the browser.

- [ ] 1. **Project setup** - one repo with two folders: `scraper/` (Python, pytest) and `web/` (`npm create vite@latest web -- --template react-ts`). Check: `pytest` runs (one dummy test passes) and `npm run dev` shows a "카페 음료 영양성분" placeholder page
- [ ] 2. **Common format** - a `Drink` dataclass with the fields from the project plan, plus a pure function `to_number(value)` that turns brand strings into numbers (`"80"` → 80, `".3"` → 0.3, `""` / `"-"` → None). Unit tests for each case
- [ ] 3. **Starbucks: fetch** - check Starbucks' robots.txt and terms first. Find the list of drink category codes (`W0000001` = 콜드 브루, …). Write a fetch script that downloads one JSON per category, slowly (1–2 seconds between requests), and saves each one as-is into `scraper/raw/starbucks/`. Check: one file per category, and the drink counts look right
- [ ] 4. **Starbucks: parse** - a pure function `parse_starbucks(raw_json) -> list[Drink]`: keep the useful fields, `id` = `starbucks-<product_CD>`, size Tall / 355ml, and hot/iced from the name and category. Tests use the saved cold brew file as a fixture: 22 drinks, `".3"` handled, both "콜드 브루" items kept with different ids
- [ ] 5. **Build drinks.json** - a `build` script: run the parsers on the raw files → apply `overrides.json` (fix values by id) → validate → write `web/public/drinks.json` with `version` (date). Validation (pure functions, tested): kcal > 0, sugar ≤ carbs + 1g, no duplicate ids. It also prints a report: drinks with `temp: null`, and a diff against the last `drinks.json` (added, removed, changed). Check: the report lists the bottled drinks and unknown temps, and I can fix them in `overrides.json`
- [ ] 6a. **Compose: fetch** - check robots.txt and terms. Save the menu HTML pages into `scraper/raw/compose/`, slowly. Check: the files open and contain the nutrition numbers
- [ ] 6b. **Compose: parse** - `parse_compose(html) -> list[Drink]` with BeautifulSoup. Find the size (ml) on the page; if it's missing, use null and add it to the overrides. Tests use saved HTML files as fixtures. Check: Compose drinks appear in the build report, and both brands are in `drinks.json`
- [ ] 8. **Drink list** - the web app loads `/drinks.json` once and shows a card for each drink: name, brand, size (ml), and big numbers for sugar and kcal. Show the data date at the bottom. Check: all drinks show on my phone (the dev server on the same Wi-Fi)
- [ ] 9. **Sort and filter** - pure functions `filterDrinks(drinks, {brand, category, temp})` and `sortDrinks(drinks, key)` with Vitest tests (null values go to the end). Then the UI: filter chips and a sort selector (당류, 칼로리, 카페인). Check: tests pass, and "lowest sugar first" works in the browser
- [ ] 10. **Drink detail** - tap a card to see all nutrients, a link to the official page, and sugar as % of the daily reference value: a pure function `sugarPercent(sugarG)` (100g = 100%) with tests. Check: numbers match the brand site for 3 random drinks
- [ ] 11. **Compare: select** - a "+ 비교" button on each card, and a bar fixed at the bottom ("비교 1/2 · 보기"). Max 2 drinks; tap again to remove. Selection logic as a pure function with tests (add, remove, no third drink). Check: the bar updates while I scroll the list
- [ ] 12. **Compare: view** - name and size (ml) big at the top of each column; horizontal bars for 당류, 칼로리, 카페인 (plain CSS, the larger value = full width); a table with the other nutrients below. Unknown values show "-". Check: compare a Starbucks Tall and a Compose drink on my phone
- [ ] 13. **Polish and deploy** - Korean UI text, empty and loading states, check on a small phone screen, then deploy to GitHub Pages (set Vite's `base` to the repo name). Check: the site works from the public URL on my phone

## Settled decisions

Decided up front so the build doesn't re-argue them:

- **Two folders in one repo** (`scraper/`, `web/`) - the scraper writes `web/public/drinks.json`, so one commit updates the data and the site together
- **Python 3.12+, `requests` + BeautifulSoup** - Starbucks is JSON and the other two are plain HTML, so no headless browser (Playwright) unless a site turns out to need JavaScript
- **Fetch and parse are separate** - fetch saves raw responses to `scraper/raw/`; parse only reads files. Tests never hit the real sites, and I can re-parse without new requests
- **Polite scraping** - check robots.txt and terms before the first fetch of each brand; 1–2 seconds between requests; run about once a week; a clear User-Agent with the project name
- **Store only names and numbers** - no descriptions or photos (copyright). Each drink links to the official page instead
- **`null` means unknown, never `0`** - sugar 0g and "no data" are different things
- **ids** - `<brand>-<brand's product code>` (e.g. `starbucks-9200000002487`), never the name, because names repeat
- **Starbucks size** - every drink is Tall, 355ml (the site says "Tall 사이즈 기준"). Bottled drinks with other sizes are fixed in `overrides.json`
- **Hot/iced from the name** - name starts with "아이스" → iced; always-cold categories (콜드 브루, 프라푸치노, 블렌디드, 피지오) → iced; otherwise `null` until checked. Fix the rest in `overrides.json`
- **Validation tolerance** - sugar ≤ carbs + 1g (real data has rounding, e.g. sugar 6g vs carbs 5g). If more than 10% of drinks disappear or a value changes by more than 50%, the build stops and shows the diff instead of writing the file
- **`version`** - the build date as `YYYY-MM-DD`
- **Per cup only** - no per-100ml values anywhere. Sizes (ml) are always shown next to the numbers
- **Sugar %** - based on the Korean daily reference value for sugar (1일 영양성분 기준치, 100g)
- **Front end: React + TypeScript with Vite** (Vite 8 is current; it needs Node.js 20.19+), tested with Vitest. Logic lives in pure functions in `src/lib/` with tests; components stay thin
- **No extra libraries for state or charts** - `useState` is enough for filters and a 2-drink selection; bars are plain CSS
- **Compare state lives in memory in v1** - it resets on page refresh (the URL version comes later)
- **Hosting: GitHub Pages** - free and simple for a static site
- **Manual data updates in v1** - I run the build on my computer and commit `drinks.json`

## Later (not v1)

- **Next step: decide how to automate data updates** - not decided yet. Options to compare later: GitHub Actions (free for public repos, 2,000 free minutes/month for private repos on the Free plan), or a scheduled job on my own computer. Whatever we pick: check whether the brand sites block overseas servers, and review the diff before publishing
- Compare up to 3 drinks
- Add drinks from inside the compare screen (search)
- Save the compare list in the URL (shareable link, also for blog posts)
- Grouping "similar drinks" across brands (e.g. all vanilla lattes)
- Paik's (빽다방): fetch (same as 6a, into `scraper/raw/paik/`) and parse (`parse_paik(html) -> list[Drink]`, tests with fixtures)
- More brands (Mega MGC Coffee, etc.)
- Favorites (saved in the browser)
- One static page per drink for search engines (SEO)
- Map of nearby cafes
