"""The common drink format every brand parser produces."""

import math
from dataclasses import dataclass
from typing import Literal

Number = int | float

_UNKNOWN = {"", "-"}


def to_number(value: str | None) -> Number | None:
    """Turn a brand's number string into a number.

    "80" -> 80, ".3" -> 0.3, "" / "-" / None -> None (unknown, never 0).
    Any other format raises ValueError so it can't slip in as a wrong number.
    """
    if value is None:
        return None
    text = value.strip()
    if text in _UNKNOWN:
        return None
    try:
        number = float(text)
    except ValueError:
        raise ValueError(f"not a number: {value!r}") from None
    if not math.isfinite(number):
        raise ValueError(f"not a number: {value!r}")
    return int(number) if number.is_integer() else number


@dataclass(frozen=True, kw_only=True)
class Drink:
    """One parsed drink, per cup at size_ml. Unknown values are None, never 0.

    `code` is the brand's product code. It is not the identity (see drink_id).
    The build adds id, first_seen and last_seen when it writes drinks.json.
    """

    code: str
    brand: str
    name: str
    category: str
    temp: Literal["hot", "iced"] | None
    size_label: str | None
    size_ml: int | None
    kcal: Number | None
    sugar_g: Number | None
    carbs_g: Number | None
    protein_g: Number | None
    fat_g: Number | None
    sat_fat_g: Number | None
    sodium_mg: Number | None
    caffeine_mg: Number | None
    source_url: str


def drink_id(drink: Drink) -> str:
    """Name a drink the way customers see it: brand + name + hot/iced.

    All whitespace is removed from the name, and there is no temp part when
    temp is None. The brand's code is never used, so a seasonal drink that
    comes back with a new code keeps its id.
    """
    name = "".join(drink.name.split())
    if not name:
        raise ValueError(
            f"drink has no name: brand={drink.brand!r} code={drink.code!r}"
        )
    parts = [drink.brand, name]
    if drink.temp is not None:
        parts.append(drink.temp)
    return "-".join(parts)
