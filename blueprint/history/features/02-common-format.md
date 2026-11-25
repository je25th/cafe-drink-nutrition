# Feature: Common format

**From build-plan:** feature 2
**Build attempt:** 1
**Branch:** feature/common-format
**Status:** verified

## Goal

Give every brand parser one shared target: a `Drink` dataclass for one parsed
drink, a pure `to_number(value)` that turns the number strings brands publish
into numbers (`None` for unknown), and a pure `drink_id(drink)` that names a
drink the way customers see it (brand + name + hot/iced), so a seasonal drink
that comes back with a new brand code is still the same drink.

## In scope

- `Drink` dataclass with the parser-output fields from the overview's Data model
  (`code` included; `id`, `first_seen`, `last_seen` are added later by the build).
- `to_number(value)`: `"80"` -> 80, `".3"` -> 0.3, `""` / `"-"` -> None.
- `drink_id(drink)`: `<brand>-<name with all whitespace removed>-<hot|iced>`,
  with no temp part when temp is `None`.
- pytest tests for every case and for the `Drink` field contract.

## Out of scope

- Any parser, fetch script, or brand-specific rule (Steps 3-6b).
- `DrinkRecord`, JSON writing, merge, `overrides.json`, and validation such as
  kcal > 0 or duplicate ids (Step 5).
- The TypeScript types in `web/` (Step 8).
- Thousands separators or units inside strings (`"1,200"`, `"80kcal"`). Add them
  in the parser step that meets them.
- Name normalization beyond whitespace (case, symbols, "NEW" labels).

## Build loop

- Step review: one review for the whole feature (`workflow.stepReview: feature`).
- Checkpoint commits are disabled. `/complete` creates the single feature commit.
- Test gate: `cd scraper && .venv/bin/pytest` must be green before review.
- Revision note: Steps 1-2 were first built with `id` in `Drink`. The plan
  changed (accumulating `drinks.json`, name-based ids), so Step 2 is reopened and
  Step 3 is new.

## Build steps

- [x] 1. **`to_number`** - `to_number(value: str | None) -> int | float | None`
  in `scraper/src/scraper/drink.py`:
  - `None`, `""`, `"-"` (after stripping whitespace) -> `None`.
  - Otherwise `float()` after stripping. Whole numbers return `int`
    (`"80"` -> 80, `"80.0"` -> 80), others `float` (`".3"` -> 0.3).
  - `"0"` -> 0 (a real zero, never `None`).
  - Anything else (`"abc"`, `"1,200"`, `"nan"`, `"inf"`) raises `ValueError`
    with the original value in the message.

  **Done when:** `.venv/bin/pytest` passes with the `to_number` tests.

- [x] 2. **`Drink` dataclass** - `@dataclass(frozen=True, kw_only=True)` in the
  same module with the fields under Data / contracts: `code` first, no `id`.
  No defaults, so a parser must set every field. Export from
  `scraper/__init__.py`. The contract test checks field names and order, and
  that `None` nutrients stay `None`.
  **Done when:** `.venv/bin/pytest` passes, and `Drink` has `code` and no `id`.

- [x] 3. **`drink_id`** - `drink_id(drink: Drink) -> str` in the same module,
  exported from `scraper/__init__.py`:
  - `f"{brand}-{name with every whitespace character removed}-{temp}"`;
    when `temp` is `None`, no `-<temp>` part.
  - Whitespace means anything `str.split()` splits on (spaces, tabs, newlines,
    non-breaking spaces).
  - A name that is empty after removing whitespace raises `ValueError` naming
    the drink's `brand` and `code`.
  - It never uses `code`, so a changed brand code keeps the same id.

  **Done when:** `.venv/bin/pytest` passes with `drink_id` tests.

## Files / areas

- `scraper/src/scraper/drink.py` - `Drink`, `to_number`, `drink_id`.
- `scraper/src/scraper/__init__.py` - re-export all three.
- `scraper/tests/test_drink.py`.
- `scraper/tests/test_setup.py` stays as it is.

## Data / contracts

`Drink` fields, in this order. Values are per cup at `size_ml`, and unknown is
`None`, never `0`. Step 5's `DrinkRecord` adds `id`, `first_seen`, `last_seen`.

| Field | Python type | Note |
|---|---|---|
| `code` | `str` | the brand's product code (Starbucks `product_CD`); not the identity |
| `brand` | `str` | code: `starbucks` or `compose` in v1 |
| `name` | `str` | Korean menu name |
| `category` | `str` | the brand's own category |
| `temp` | `Literal["hot", "iced"] \| None` | |
| `size_label` | `str \| None` | e.g. `Tall` |
| `size_ml` | `int \| None` | Starbucks: 355 |
| `kcal` | `Number \| None` | |
| `sugar_g` | `Number \| None` | |
| `carbs_g` | `Number \| None` | |
| `protein_g` | `Number \| None` | |
| `fat_g` | `Number \| None` | |
| `sat_fat_g` | `Number \| None` | |
| `sodium_mg` | `Number \| None` | |
| `caffeine_mg` | `Number \| None` | |
| `source_url` | `str` | the brand's official page for the drink |

`Number = int | float`, a type alias in `drink.py`.

`drink_id` examples:

| brand | name | temp | id |
|---|---|---|---|
| `starbucks` | `아이스 자몽 허니 블랙 티` | `iced` | `starbucks-아이스자몽허니블랙티-iced` |
| `starbucks` | `콜드 브루` | `None` | `starbucks-콜드브루` |
| `compose` | `아메리카노` (code changed) | `hot` | `compose-아메리카노-hot` (same as before) |

## Testing

- pytest only (`cd scraper && .venv/bin/pytest`). No fixtures needed yet.
- `to_number`: as before (numbers with types, unknown -> `None`, `ValueError`).
- `Drink`: field names and order match the table, `None` values survive,
  missing fields, positional args and assignment fail.
- `drink_id`: spaces, tabs and non-breaking spaces removed; `None` temp has no
  suffix; two drinks with different `code` but the same brand/name/temp get the
  same id; hot vs iced differ; blank name raises `ValueError` with brand and code.

## Notes for the AI

- Standard library only. No new dependencies.
- Type hints on all public names. No `__post_init__` validation; validation
  belongs to Step 5.
- Ids are opaque: nothing should parse them later. No brand constants, enums,
  or `DrinkRecord` yet.


<!-- blueprint:completion {"schemaVersion":2,"specBytes":5791,"specSha256":"8e57f41d0c2887e926cd3b332701be84f6595d5ed7db8fdc4ce4fea02b4e3eed","branch":"refs/heads/feature/common-format","head":"3ebfdb4fe31e984607adf076940b2d51d3959a76","baseRef":"refs/heads/main","baseCommit":"3ebfdb4fe31e984607adf076940b2d51d3959a76","sourceTree":"d6a3e949c41815ee2415563ed22a1e6e7b95e087","landing":"local-merge","absentOptional":[]} -->

## Try it now

Run or do:

```
cd scraper && .venv/bin/python -c "
from scraper import Drink, drink_id
d = dict(brand='starbucks', name='아이스 자몽 허니 블랙 티', category='티바나', temp='iced', size_label='Tall', size_ml=355, kcal=None, sugar_g=None, carbs_g=None, protein_g=None, fat_g=None, sat_fat_g=None, sodium_mg=None, caffeine_mg=None, source_url='')
print(drink_id(Drink(code='111', **d)), drink_id(Drink(code='999', **d)))"
```

Expected:

```
starbucks-아이스자몽허니블랙티-iced starbucks-아이스자몽허니블랙티-iced
```

This proves:

`drink_id` removes whitespace from the name and gives the same id when the brand code changes (`111` -> `999`).
