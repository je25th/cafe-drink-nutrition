# Feature: Starbucks fetch

**From build-plan:** feature 3
**Build attempt:** 1
**Branch:** feature/starbucks-fetch
**Status:** verified

## Goal

Download Starbucks Korea's drink data politely and keep it locally, so the Step 4
parser and the Step 5 build can work from files without touching the site again.
One run saves one unmodified JSON file per drink category into
`scraper/raw/starbucks/`, plus the fetch date in `fetched_at.txt`.

## In scope

- Check Starbucks Korea's robots.txt and terms of use before the first real fetch,
  and stop if either forbids it.
- Find the drink category codes (`W0000001` = 콜드 브루, ...) and the category JSON
  URL the drink list page loads.
- A fetch module that downloads every category, 1-2 seconds apart, with a clear
  User-Agent that names the project, checks each response, and only then writes
  the files.
- `scraper/raw/` added to the root `.gitignore` (public repo; raw files hold drink
  descriptions, which the project must not publish).
- `requests` added as a scraper dependency.
- Tests for the fetch logic with a fake HTTP getter (no network in tests).
- One real run, with drink counts per category printed.

## Out of scope

- Parsing drinks, sizes, temps, or `product_CD` (Step 4).
- Test fixtures under `scraper/tests/fixtures/` (Step 4 decides how to store the
  cold brew fixture; see Notes).
- `overrides.json`, the build, `drinks.json`, validation, the report (Step 5).
- Retries, caching, concurrency, scheduling or automatic updates (Later).
- Detail pages per drink.

## Build loop

Config: `workflow.stepReview` = `feature`, `workflow.checkpointCommits` =
`disabled`. Build all steps, then one review for the whole feature. No checkpoint
commits; `/complete` makes the single feature commit.

## Build steps

- [x] **1. Check the rules and find the endpoint.** Read
  `https://www.starbucks.co.kr/robots.txt` and the site's terms of use (이용약관),
  looking for anything about automated access or copying menu data. Open the drink
  list page and find the category JSON URL it loads (expected shape
  `/upload/json/menu/<code>.js`, confirm it) and every drink category code with its
  Korean name. Fetch one category (콜드 브루) once by hand to confirm: plain GET
  works with our User-Agent (no cookie, Referer or POST needed), the body is plain
  JSON (not wrapped in JavaScript), and the key that holds the drink list.
  Record the results under "Step 1 findings" in Notes for the AI.
  **Stop and ask the user** if robots.txt disallows the URL path, the terms forbid
  automated collection, the body is not plain JSON, or the request needs more than
  a plain GET.
  Done when: the findings section lists the relevant robots.txt lines, the terms
  conclusion, the URL pattern, the drink-list key, and the full code -> name list,
  and the user has no objection.
- [x] **2. Fetch module with tests.** Add `scraper/raw/` to the root `.gitignore`,
  add `requests` to `scraper/pyproject.toml` dependencies and reinstall
  (`.venv/bin/pip install -e '.[dev]'`). Write `scraper/src/scraper/fetch_starbucks.py`
  (contract below) and `scraper/tests/test_fetch_starbucks.py`.
  Done when: `cd scraper && .venv/bin/pytest` passes, including the new tests, and
  no test touches the network.
- [x] **3. Real run.** From `scraper/`, run `.venv/bin/python -m scraper.fetch_starbucks`.
  Done when: `scraper/raw/starbucks/` has exactly one `<code>.json` per category
  from Step 1 and a `fetched_at.txt` with today's date; the printed counts look
  right (콜드 브루 = 22, or the count the site shows today if it changed; spot-check
  one other category against the drink list page); `git status` shows no files
  under `scraper/raw/`; `pytest` still passes.

## Files / areas

- `.gitignore` (root) - add `scraper/raw/`.
- `scraper/pyproject.toml` - `dependencies = ["requests>=2.32"]`.
- `scraper/src/scraper/fetch_starbucks.py` - new.
- `scraper/tests/test_fetch_starbucks.py` - new.
- `scraper/raw/starbucks/` - created by the real run, gitignored, never committed.
- `blueprint/context/current-feature.md` - Step 1 findings.

## Data / contracts

Raw files are the input contract for Step 4 (parser) and Step 5 (build).

- **Directory:** `scraper/raw/starbucks/`, resolved from the package location
  (`scraper/` root = `Path(__file__).resolve().parents[2]`), so the run works from
  any working directory. Created if missing.
- **Category files:** `<code>.json` (e.g. `W0000001.json`), the response body bytes
  exactly as received. Never re-encoded or pretty-printed. A category file is
  overwritten on each run. Files of categories no longer in the list are left alone
  (local only; Step 1 fixes the list).
- **Date file:** `fetched_at.txt` holds the local date of the run as `YYYY-MM-DD`
  plus one newline. Readers strip whitespace. It is written last, only after every
  category file was written.
- **Category list check first (user decision 261127):** each run first GETs the
  drink list page (`https://www.starbucks.co.kr/menu/drink_list.do`) and reads the
  `W...` codes inside its `getCateCodeCng()` function. If none can be read, or the
  set differs from `CATEGORIES` (a new or a gone code), the run raises `FetchError`
  naming the new and gone codes, fetches no category and writes nothing. The page is
  a check only: the codes fetched always come from `CATEGORIES`, which a person
  updates.
- **All or nothing:** every category is downloaded and checked in memory first. If
  any request fails (connection error, timeout, non-2xx status), or a body is not
  JSON, or it lacks the drink-list key from Step 1 as a list, or that list is empty
  (an unknown or changed category code answers 200 with `{"list":[]}`; user
  decision 261127), the run raises
  `FetchError` naming the category code and the reason, writes nothing, and exits
  non-zero. The previous raw files and `fetched_at.txt` stay as they were, so a
  failed run never looks like fresh data.
- **Module shape** (names may be adjusted in implementation if the reason is
  noted; keep the seams):
  - `CATEGORIES: dict[str, str]` - code -> Korean category name, from Step 1.
  - `LIST_URL: str` - `https://www.starbucks.co.kr/menu/productListAjax.do`, sent
    as a form POST with `CATE_CD=<code>` and `SOLD_OUT=1`, the same request the
    drink list page makes (user decision 261127; the static GET file lags).
  - `USER_AGENT: str` (e.g.
    `cafe-drink-nutrition-scraper (+https://github.com/je25th/cafe-drink-nutrition)`;
    no personal email).
  - `DELAY_SECONDS = 1.5` (within the 1-2 s rule).
  - `class FetchError(Exception)`.
  - `fetch_categories(download, codes, sleep) -> dict[str, bytes]` -
    `download(code) -> bytes` raises `FetchError` on failure; `sleep(seconds)` is
    called between requests (not before the first or after the last). Checks every
    body as described above.
  - `save(bodies, out_dir, fetched) -> None` - writes the category files, then
    `fetched_at.txt` from `fetched: date`.
  - `drink_count(body: bytes) -> int` - length of the drink list, for the printout.
  - `page_category_codes(html) -> set[str]` and
    `check_categories(page_codes, known) -> None` - the category list check above.
  - `main()` - `requests.Session` with the User-Agent, a 10 s timeout,
    `raise_for_status()`; wraps `requests` errors in `FetchError`; checks the page's
    category list, waits `DELAY_SECONDS`, then fetches the categories; prints one line
    per category (`W0000171 콜드 브루: 22`) and the total; on `FetchError` prints a
    clear message (brand, code, reason) and exits with status 1. Run as
    `python -m scraper.fetch_starbucks`.

## Testing

Test command: `cd scraper && .venv/bin/pytest`. New `tests/test_fetch_starbucks.py`
with a fake `download` (dict of code -> bytes, or raising) and a recording `sleep`,
and `tmp_path` for files:

- Every code is requested once, in order; the result maps each code to its exact
  bytes.
- `sleep` is called `len(codes) - 1` times, each with a value between 1 and 2.
- `save` writes `<code>.json` with identical bytes and `fetched_at.txt` ==
  `"2026-11-27\n"` for a fixed date; creates the directory when missing.
- A failing `download`, a non-JSON body, a body missing the drink-list key, and an
  empty drink list each
  raise `FetchError` whose message contains the code, and nothing gets written
  when the flow stops there (pre-existing files in `tmp_path` unchanged).
- `drink_count` returns the list length.
- `page_category_codes` reads only the `W...` codes inside `getCateCodeCng()` from a
  short synthetic page (not a copy of the Starbucks page), ignoring `"0"` and codes
  elsewhere; it raises `FetchError` when the function or its codes are missing.
- `check_categories` passes on a match and names both new and gone codes otherwise.

`main()` and the real network call are verified by the Step 3 run, not unit tests.

## Notes for the AI

- Scraping rules from the plan: robots.txt and terms first, 1-2 s between requests,
  clear User-Agent with the project name, about once a week, store only names and
  numbers in anything published. Raw files are local only, which is why
  `scraper/raw/` is gitignored (the user's own plan from 261126).
- Step 4 heads-up (do not act on it here): the plan says Step 4 tests use "the
  saved cold brew file as a fixture", but `scraper/raw/` is not committed and the
  raw JSON has descriptions. Step 4 will need a fixture under
  `scraper/tests/fixtures/` that keeps only the fields the parser uses. Mention this
  at `/complete` so the Step 4 spec handles it.
- Use local time for `fetched_at` (`date.today()`, the user is in Korea), passed into
  `save` so tests can fix it.
- Keep comments sparse; no em dashes.

### Step 1 findings

Checked 261127.

- **robots.txt:** `User-agent: *` / `Allow: /`. Nothing disallowed.
- **Endpoint:** plain GET `https://www.starbucks.co.kr/upload/json/menu/<code>.js`
  works with our User-Agent (no cookie, Referer or POST). Body is plain JSON
  (`Content-Type: application/x-javascript`), drink list under the `list` key.
  The drink list page itself loads data by POST `/menu/productListAjax.do`
  (`CATE_CD`, `SOLD_OUT=1`). The fetch now uses that POST (see Step 3 spot check).
- **Category codes changed:** cold brew is now `W0000171`, not the plan's
  `W0000001` (which now answers 302). `W0000171` returned 22 drinks,
  including two "콜드 브루" (`9200000004770`, `9200000000038`).
- **Codes from the page's `getCateCodeCng`** (only `W0000171` fetched so far):
  `W0000171` 콜드 브루, `W0000060` 브루드 커피, `W0000003` 에스프레소,
  `W0000004` 프라푸치노, `W0000005` 블렌디드, `W0000422` 스타벅스 리프레셔,
  `W0000061` 스타벅스 피지오, `W0000075` 티(티바나), `W0000053` 기타 제조 음료,
  `W0000062` 스타벅스 주스(병음료).
- **Terms (홈페이지 이용약관, effective 2025-09-25), 제1조 3항:** "본 홈페이지에
  포함된 자료는 이용자에게 정보 제공을 위한 목적으로만 제공됩니다. 이용자는 본
  홈페이지의 내용에 대하여 어떤 방법으로도 배포, 출판, 전송, 변경, 전시, 모방작품의
  창조 혹은 개발할 수 없습니다. ... 본 홈페이지의 자료를 허가 없이 유용할 수
  없습니다." Nothing names automated access, but this forbids republishing site
  content without permission, which is what `drinks.json` on a public site does.
- **User decision (261127):** fetch locally now (raw stays gitignored). Settle
  publishing before deploy (Step 13); the expected path is to publish non-commercially
  with names and numbers only, a source link per drink, and takedown on request.
  Optionally ask Starbucks Korea for permission in the meantime.
- **Plan wording:** the build plan still says `W0000001` = 콜드 브루. The code list
  above replaces it for this feature; the user may update the plan text.
- **Step 3 spot check (261127):** the real run fetched 198 drinks in 10 categories
  (콜드 브루 22). Compared with the page's own call (POST `/menu/productListAjax.do`,
  `CATE_CD=W0000004`, `SOLD_OUT=1`), 프라푸치노 has 16 there but 15 in the static
  GET file: `9200000007427` 제주 파인애플 코코 프라푸치노 is missing from the static
  file. The static file lags behind the live list. User chose (261127) to fetch
  with the page's POST instead.


<!-- blueprint:completion {"schemaVersion":2,"specBytes":12384,"specSha256":"418166ae93f3d70668e0576ce199b74ca54c52223198be2b726c852b931e16a5","branch":"refs/heads/feature/starbucks-fetch","head":"28216879c3f4a210c5299e18f75caf13d74d2d2d","baseRef":"refs/heads/main","baseCommit":"28216879c3f4a210c5299e18f75caf13d74d2d2d","sourceTree":"df2d9e7a5356eddda5340c38c58eacb063358ed1","landing":"local-merge","absentOptional":[]} -->

## Try it now

Run or do:

```
cat scraper/raw/starbucks/fetched_at.txt && ls scraper/raw/starbucks | wc -l
```

Expected:

```
2026-11-27
      11
```

This proves:

The real run wrote the 10 category files and the fetch date file into
`scraper/raw/starbucks/`.
