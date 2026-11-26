from datetime import date

import pytest

from scraper.fetch_starbucks import (
    CATEGORIES,
    FetchError,
    check_categories,
    drink_count,
    fetch_categories,
    page_category_codes,
    save,
)

COLD_BREW = '{"list":[{"product_NM":"콜드 브루"},{"product_NM":"오트 콜드 브루"}]}'.encode()
ESPRESSO = '{"list":[{"product_NM":"카페 라떼"}]}'.encode()
EMPTY = b'{"list":[]}'


def fake_download(responses):
    requested = []

    def download(code):
        requested.append(code)
        result = responses[code]
        if isinstance(result, Exception):
            raise result
        return result

    download.requested = requested
    return download


def test_fetch_categories_returns_exact_bytes_per_code():
    download = fake_download({"A": COLD_BREW, "B": ESPRESSO})

    bodies = fetch_categories(download, ["A", "B"], lambda _: None)

    assert bodies == {"A": COLD_BREW, "B": ESPRESSO}
    assert download.requested == ["A", "B"]


def test_fetch_categories_sleeps_between_requests_only():
    waits = []
    download = fake_download({c: ESPRESSO for c in "ABC"})

    fetch_categories(download, ["A", "B", "C"], waits.append)

    assert len(waits) == 2
    assert all(1 <= wait <= 2 for wait in waits)


@pytest.mark.parametrize(
    "bad",
    [
        FetchError("HTTP 500"),
        b"<html>302 Found</html>",
        b'{"items": []}',
        b'{"list": {}}',
        EMPTY,
    ],
)
def test_fetch_categories_stops_with_the_failing_code(bad):
    download = fake_download({"A": COLD_BREW, "B": bad})

    with pytest.raises(FetchError, match="starbucks B"):
        fetch_categories(download, ["A", "B"], lambda _: None)


def test_save_writes_bodies_and_fetch_date(tmp_path):
    out = tmp_path / "raw" / "starbucks"

    save({"A": COLD_BREW, "B": ESPRESSO}, out, date(2026, 11, 27))

    assert (out / "A.json").read_bytes() == COLD_BREW
    assert (out / "B.json").read_bytes() == ESPRESSO
    assert (out / "fetched_at.txt").read_text(encoding="utf-8") == "2026-11-27\n"


def test_failed_fetch_leaves_previous_files_alone(tmp_path):
    (tmp_path / "A.json").write_bytes(b"old")
    (tmp_path / "fetched_at.txt").write_text("2026-11-20\n", encoding="utf-8")
    download = fake_download({"A": COLD_BREW, "B": FetchError("timeout")})

    with pytest.raises(FetchError):
        save(fetch_categories(download, ["A", "B"], lambda _: None), tmp_path, date(2026, 11, 27))

    assert (tmp_path / "A.json").read_bytes() == b"old"
    assert (tmp_path / "fetched_at.txt").read_text(encoding="utf-8") == "2026-11-20\n"


def test_drink_count():
    assert drink_count(COLD_BREW) == 2
    assert drink_count(EMPTY) == 0
    with pytest.raises(ValueError):
        drink_count(b"not json")


PAGE = """
<script>
function getProductPicList2(tmp_cate) {
    if(f_cate == "W0000001") { f.action = "/menu/drink_view.do"; }
}
function getCateCodeCng(tmp_cate) {
    result = "";
    if(tmp_cate == "product_all") {
        result = "0";
    } else if(tmp_cate == "product_cold_brew") {
        result = "W0000171";
    } else if(tmp_cate == "product_espresso") {
        result = "W0000003";
    }
    return result;
}
var other = { result = "W0000099" };
</script>
"""


def test_page_category_codes_reads_only_the_mapping_function():
    assert page_category_codes(PAGE) == {"W0000171", "W0000003"}


@pytest.mark.parametrize(
    "html",
    ["<html></html>", 'function getCateCodeCng(t) { result = "0"; return result; }'],
)
def test_page_category_codes_fails_when_unreadable(html):
    with pytest.raises(FetchError, match="could not read the category list"):
        page_category_codes(html)


def test_check_categories_passes_when_lists_match():
    check_categories(set(CATEGORIES), CATEGORIES)


def test_check_categories_names_new_and_gone_codes():
    page = set(CATEGORIES) - {"W0000422"} | {"W0000500"}

    with pytest.raises(FetchError, match=r"new: \['W0000500'\], gone: \['W0000422'\]"):
        check_categories(page, CATEGORIES)
