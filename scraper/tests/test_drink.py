from dataclasses import FrozenInstanceError, fields

import pytest

from scraper import Drink, drink_id, to_number


@pytest.mark.parametrize(
    ("value", "expected", "kind"),
    [
        ("80", 80, int),
        ("80.0", 80, int),
        ("0", 0, int),
        (" 12 ", 12, int),
        (".3", 0.3, float),
        ("5.5", 5.5, float),
    ],
)
def test_to_number_parses_numbers(value, expected, kind):
    result = to_number(value)
    assert result == expected
    assert type(result) is kind


@pytest.mark.parametrize("value", ["", "-", " - ", "  ", None])
def test_to_number_unknown_is_none(value):
    assert to_number(value) is None


@pytest.mark.parametrize("value", ["abc", "1,200", "nan", "inf", "80kcal"])
def test_to_number_rejects_other_formats(value):
    with pytest.raises(ValueError, match=repr(value)):
        to_number(value)


DRINK_FIELDS = [
    "code",
    "brand",
    "name",
    "category",
    "temp",
    "size_label",
    "size_ml",
    "kcal",
    "sugar_g",
    "carbs_g",
    "protein_g",
    "fat_g",
    "sat_fat_g",
    "sodium_mg",
    "caffeine_mg",
    "source_url",
]


def make_drink(**changes):
    values = dict(
        code="9200000002487",
        brand="starbucks",
        name="콜드 브루",
        category="콜드 브루",
        temp="iced",
        size_label="Tall",
        size_ml=355,
        kcal=5,
        sugar_g=0,
        carbs_g=0,
        protein_g=0.3,
        fat_g=0,
        sat_fat_g=0,
        sodium_mg=11,
        caffeine_mg=150,
        source_url="https://www.starbucks.co.kr/",
    )
    values.update(changes)
    return Drink(**values)


def test_drink_fields_match_drinks_json_contract():
    assert [f.name for f in fields(Drink)] == DRINK_FIELDS


def test_drink_keeps_none_values():
    drink = make_drink(temp=None, size_ml=None, sugar_g=None, caffeine_mg=None)
    assert drink.temp is None
    assert drink.size_ml is None
    assert drink.sugar_g is None
    assert drink.caffeine_mg is None
    assert drink.kcal == 5


def test_drink_requires_every_field():
    with pytest.raises(TypeError):
        Drink(code="1", brand="starbucks")


def test_drink_is_keyword_only_and_frozen():
    with pytest.raises(TypeError):
        Drink(*range(len(DRINK_FIELDS)))
    drink = make_drink()
    with pytest.raises(FrozenInstanceError):
        drink.kcal = 10


@pytest.mark.parametrize(
    ("name", "temp", "expected"),
    [
        ("아이스 자몽 허니 블랙 티", "iced", "starbucks-아이스자몽허니블랙티-iced"),
        ("카페\t라떼\n", "hot", "starbucks-카페라떼-hot"),
        ("바닐라 라떼", "hot", "starbucks-바닐라라떼-hot"),
        ("콜드 브루", None, "starbucks-콜드브루"),
    ],
)
def test_drink_id_from_brand_name_and_temp(name, temp, expected):
    assert drink_id(make_drink(name=name, temp=temp)) == expected


def test_drink_id_ignores_brand_code():
    old = make_drink(code="9200000002487")
    new = make_drink(code="9300000009999")
    assert drink_id(old) == drink_id(new)


def test_drink_id_hot_and_iced_differ():
    assert drink_id(make_drink(temp="hot")) != drink_id(make_drink(temp="iced"))


@pytest.mark.parametrize("name", ["", "   ", " "])
def test_drink_id_rejects_blank_name(name):
    with pytest.raises(ValueError, match="starbucks.*9200000002487"):
        drink_id(make_drink(name=name))
