"""Download Starbucks Korea's drink data, one unmodified JSON file per category.

Run from `scraper/`: `.venv/bin/python -m scraper.fetch_starbucks`
"""

import json
import re
import sys
import time
from collections.abc import Callable, Iterable
from datetime import date
from pathlib import Path

import requests

CATEGORIES = {
    "W0000171": "콜드 브루",
    "W0000060": "브루드 커피",
    "W0000003": "에스프레소",
    "W0000004": "프라푸치노",
    "W0000005": "블렌디드",
    "W0000422": "스타벅스 리프레셔",
    "W0000061": "스타벅스 피지오",
    "W0000075": "티(티바나)",
    "W0000053": "기타 제조 음료",
    "W0000062": "스타벅스 주스(병음료)",
}
# The page's own list call. The static /upload/json/menu/<code>.js files lag
# behind it (new drinks were missing on 261127).
LIST_URL = "https://www.starbucks.co.kr/menu/productListAjax.do"
DRINK_LIST_PAGE_URL = "https://www.starbucks.co.kr/menu/drink_list.do"
USER_AGENT = (
    "cafe-drink-nutrition-scraper (+https://github.com/je25th/cafe-drink-nutrition)"
)
DELAY_SECONDS = 1.5
TIMEOUT_SECONDS = 10
RAW_DIR = Path(__file__).resolve().parents[2] / "raw" / "starbucks"

# 카테고리 확인: 목록 페이지 원본 HTML 속 JS 코드를 "글자로 검색"한다.
# JS를 실행하거나 제대로 파싱하는 것이 아니다.
# HTML 메뉴 링크에는 이름(product_cold_brew)만 있고, 우리가 요청에 쓰는
# 코드(W0000171)는 getCateCodeCng() 함수 안에만 있어서 이 방식을 쓴다.
# [위험 높음] 스타벅스가 이 JS를 조금만 바꿔도(함수 이름 변경, return 줄 변경,
# 코드를 만드는 방식 변경 등) 바로 깨진다. 깨지면 틀린 데이터를 받지 않고
# "could not read the category list"로 멈추므로, 페이지를 보고 아래 두 패턴을
# 직접 고쳐야 한다.
_CATEGORY_FUNCTION = re.compile(r"function getCateCodeCng\(.*?return result;", re.S)
_CATEGORY_CODE = re.compile(r'result\s*=\s*"(W\d+)"')


class FetchError(Exception):
    """A category could not be downloaded or is not the expected JSON."""


def page_category_codes(html: str) -> set[str]:
    """Drink category codes the drink list page uses, from its getCateCodeCng()."""
    match = _CATEGORY_FUNCTION.search(html)
    codes = set(_CATEGORY_CODE.findall(match.group())) if match else set()
    if not codes:
        raise FetchError("starbucks drink list page: could not read the category list")
    return codes


def check_categories(page_codes: set[str], known: Iterable[str]) -> None:
    """Stop when the page's categories differ from CATEGORIES."""
    known = set(known)
    new, gone = sorted(page_codes - known), sorted(known - page_codes)
    if new or gone:
        raise FetchError(
            f"starbucks category list changed on the page (new: {new}, gone: {gone}); "
            "update CATEGORIES"
        )


def drink_count(body: bytes) -> int:
    """Number of drinks in a category body. ValueError if it isn't the expected JSON."""
    try:
        data = json.loads(body)
    except ValueError:
        raise ValueError("body is not JSON") from None
    drinks = data.get("list") if isinstance(data, dict) else None
    if not isinstance(drinks, list):
        raise ValueError('body has no "list" array')
    return len(drinks)


def fetch_categories(
    download: Callable[[str], bytes],
    codes: Iterable[str],
    sleep: Callable[[float], None],
) -> dict[str, bytes]:
    """Download and check every category in memory, waiting between requests.

    `download(code)` raises FetchError on a failed request. Any failure stops
    the whole run, so nothing is saved from a partial download.
    """
    bodies: dict[str, bytes] = {}
    for code in codes:
        if bodies:
            sleep(DELAY_SECONDS)
        try:
            body = download(code)
            # An unknown code still answers 200 with an empty list.
            if drink_count(body) == 0:
                raise ValueError("0 drinks, the category code may have changed")
        except (FetchError, ValueError) as error:
            raise FetchError(f"starbucks {code}: {error}") from error
        bodies[code] = body
    return bodies


def save(bodies: dict[str, bytes], out_dir: Path, fetched: date) -> None:
    """Write each body as `<code>.json`, then the fetch date last."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for code, body in bodies.items():
        (out_dir / f"{code}.json").write_bytes(body)
    (out_dir / "fetched_at.txt").write_text(f"{fetched.isoformat()}\n", encoding="utf-8")


def main() -> int:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    def send(method: str, url: str, **kwargs: object) -> requests.Response:
        try:
            response = session.request(method, url, timeout=TIMEOUT_SECONDS, **kwargs)
            response.raise_for_status()
        except requests.RequestException as error:
            raise FetchError(str(error)) from error
        return response

    def download(code: str) -> bytes:
        return send("POST", LIST_URL, data={"CATE_CD": code, "SOLD_OUT": "1"}).content

    try:
        page = send("GET", DRINK_LIST_PAGE_URL).text
        check_categories(page_category_codes(page), CATEGORIES)
        time.sleep(DELAY_SECONDS)
        bodies = fetch_categories(download, CATEGORIES, time.sleep)
    except FetchError as error:
        print(f"Fetch failed, nothing written: {error}", file=sys.stderr)
        return 1

    save(bodies, RAW_DIR, date.today())
    counts = {code: drink_count(body) for code, body in bodies.items()}
    for code, count in counts.items():
        print(f"{code} {CATEGORIES[code]}: {count}")
    print(f"total: {sum(counts.values())} drinks in {len(counts)} categories")
    return 0


if __name__ == "__main__":
    sys.exit(main())
