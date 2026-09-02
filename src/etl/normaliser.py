import re
from typing import Optional


TICKER_ALIASES = {
    "AGTL": "ATGL",
}

def normalize_year(value: object) -> Optional[int]:
    if value is None:
        return None

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "nat"}:
        return None


    if text.upper() == "TTM":
        return 2024

    match = re.search(r"\b(19\d{2}|20\d{2})\b", text)

    if match:
        return int(match.group(1))

    match = re.search(r"(\d{2})$", text)

    if match:
        year = int(match.group(1))
        return 2000 + year if year <= 49 else 1900 + year

    return None

def normalize_ticker(value: object) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()

    if not text or text.lower() in {"nan", "none", "nat"}:
        return None

    text = text.upper()
    text = re.sub(r"\s+", "", text)
    text = text.strip(".,;:-_/")

    if not text:
        return None

    return TICKER_ALIASES.get(text, text)