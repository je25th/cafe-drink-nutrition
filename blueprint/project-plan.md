# Cafe Drink Nutrition - Project Plan

## 1. Problem - What problem are we solving?

People who watch their sugar and calories can't easily compare franchise cafe drinks. Each brand puts its nutrition info on its own website, in its own format, and some cheap brands hide it in hard-to-find pages. Nobody shows drinks from different brands side by side.

This project collects the nutrition info of popular franchise cafe drinks into one place, so you can sort, filter and compare them across brands.

## 2. Users - Who is this for?

- Primary: people who care about sugar and calories when they order at a cafe (including me).
- Maybe later: readers of my cafe drink review blog posts.

## 3. Features - What does v1 need?

- All drinks from two brands: Starbucks and Compose Coffee. Paik's (빽다방) comes after v1.
- One list of drinks with brand, name, category, hot/iced, size, kcal, sugar, caffeine and other nutrients.
- Sort by kcal, sugar or caffeine.
- Filter by brand, category and hot/iced.
- Show values per cup only, with the cup size (ml) clearly shown. No per-100ml values: people drink a whole cup, not a measured amount.
- Show sugar as % of the daily reference value (1일 영양성분 기준치, 100g).
- Compare 2 drinks side by side, per cup. Different cup sizes between drinks are fine.
- Show when the data was last updated, and link each drink to the brand's official page.
- Constraints: read-only, no login, no server code. Data is updated by running the scrapers by hand.

Later (not v1, see build plan):

- Compare up to 3 drinks (v1 is 2).
- Add drinks from inside the compare screen (search).
- Save the compare list in the URL (shareable link).
- Grouping "similar drinks" automatically (e.g. all vanilla lattes across brands).
- More brands: Paik's (빽다방) first, then Mega MGC Coffee, etc.
- Favorites (saved in the browser).
- Automatic data updates (how: decide later).
- Map of nearby cafes.
- One static page per drink for search engines (SEO), and links from blog posts.

## 4. Data - What are we storing?

- One file, `drinks.json`, built by the scrapers and served as a static file. It has a `version` field (date of the data) and a list of drinks.
- Each drink: `id` (brand prefix + the brand's product code), `brand`, `name`, `category`, `temp` (hot / iced / null), `size_label`, `size_ml`, `kcal`, `sugar_g`, `carbs_g`, `protein_g`, `fat_g`, `sat_fat_g`, `sodium_mg`, `caffeine_mg`, `source_url`.
- Unknown values are `null`, never `0`.
- An `overrides` file, edited by hand, to fix wrong values (e.g. bottled drinks with a different size, unclear hot/iced).
- NOT stored: drink descriptions and photos (copyright), any user data.
- Known facts:
  - Starbucks gives one JSON per category, and its values are for Tall size (355ml).
  - Starbucks numbers are strings (sometimes like ".3"). Starbucks has no size or hot/iced field (hot/iced comes from the name).
  - Compose and Paik's need HTML parsing.

## 5. Tech - What stack are we using?

- Scrapers: Python, one scraper per brand. Each one outputs the common format. Then a merge step applies the overrides, validates the data and writes `drinks.json`.
- Validation: e.g. sugar ≤ carbs + 1g, kcal > 0, and a comparison with the last version (stop if many drinks disappear or values change a lot).
- Front end: React + Vite (static build), mobile-friendly. It loads `drinks.json` once and does all sorting, filtering and comparing in the browser.
- Hosting: free static hosting (e.g. GitHub Pages or Cloudflare Pages).
- Tests: pytest for the scrapers' parsing and validation; Vitest for the front end's sort, filter and per-100ml logic.
- NOT used: backend server, database, login.
- Scraping rules: check robots.txt and the terms of use, run about once a week, and request slowly.

## 6. Monetize - How will this make money?

Not now. It's free. I'll think about it (e.g. ads) after the service is real and people use it.

## 7. UI/UX - How should this look and feel?

- Mobile first: most people will check it in line at a cafe. One simple page.
- At the top: brand, category and hot/iced filters, and a sort selector (sugar, kcal, caffeine).
- A list of drink cards: name, brand, size, and big numbers for sugar and kcal (the main things users care about). Tap a card to see all nutrients.
- A "+ 비교" button on each card. Selected drinks collect in a small bar fixed at the bottom of the screen (e.g. "비교 1/2 · 보기"). When 2 are selected, the user opens the compare view.
- Compare view: drink name and cup size (ml) shown big at the top of each column, so users see why one cup has more sugar. Then horizontal bars for the three main numbers (sugar, kcal, caffeine), and a small table with the other nutrients below.
- Clean and calm, numbers easy to read. Small text with the data date.
- Korean UI.
