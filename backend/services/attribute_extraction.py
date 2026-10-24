import re

PROPERTY_TYPE_PATTERNS = {
    "studio": [r"\bстуді[юяї]"],
    "room": [r"\bкімнат[аиу]\b(?!\s*квартир)", r"\bпідселенн"],
    "house": [r"\bбудин(ок|ку|ку)\b", r"\bкотедж"],
    "apartment": [r"\bквартир"],
}

NEGATIVE_PATTERNS = {
    "furnished": [r"без меблів", r"порожня", r"пуста квартира"],
}
POSITIVE_PATTERNS = {
    "furnished": [r"з меблями", r"умебльован", r"повністю укомплектован"],
    "is_new_building": [r"новобудов", r"здан[аоий]\s+в\s+експлуатац"],
    "has_elevator": [r"\bліфт"],
    "has_parking": [r"паркомісц", r"парков[аоі]", r"підземний паркінг"],
    "has_balcony": [r"\bбалкон", r"\bлоджі"],
    "internet_included": [r"інтернет включен", r"з інтернетом", r"wi-?fi включен"],
    "utilities_included": [r"комунальн[іу] включен", r"комуналку не потрібно", r"ком\.послуги включен"],
    "deposit_required": [r"застав[аиу]", r"депозит"],
}
NO_DEPOSIT_PATTERNS = [r"без застав", r"без депозит"]

HEATING_PATTERNS = {
    "autonomous": [r"автономне опаленн", r"автономка"],
    "central": [r"центральне опаленн"],
    "electric": [r"електричне опаленн", r"електроопаленн"],
}

LEASE_MONTHS_PATTERN = re.compile(r"(?:від|мінімум|термін[оу]?м?)?\s*(\d{1,2})\s*(?:міс|місяц)", re.IGNORECASE)


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def extract_rooms(title: str, description: str = "") -> int | None:
    text = f"{title} {description}".lower()
    if "студі" in text:
        return 1
    m = re.search(r"\b(\d)\s*[\-\xad]?\s*(?:кім|кн|к\.?|х\s*км|кімнати|кімнатний|квартири)\b", text)
    if m:
        val = int(m.group(1))
        if val <= 5:
            return val
    if "однокімнатн" in text:
        return 1
    if "двокімнатн" in text:
        return 2
    if "трикімнатн" in text:
        return 3
    return None


def extract_attributes(title: str, description: str) -> dict:
    text = f"{title} {description}".lower()

    property_type = None
    for type_key, patterns in PROPERTY_TYPE_PATTERNS.items():
        if _matches_any(text, patterns):
            property_type = type_key
            break

    furnished = None
    if _matches_any(text, POSITIVE_PATTERNS["furnished"]):
        furnished = True
    elif _matches_any(text, NEGATIVE_PATTERNS["furnished"]):
        furnished = False

    heating_type = None
    for h_key, patterns in HEATING_PATTERNS.items():
        if _matches_any(text, patterns):
            heating_type = h_key
            break

    deposit_required = None
    if _matches_any(text, NO_DEPOSIT_PATTERNS):
        deposit_required = False
    elif _matches_any(text, POSITIVE_PATTERNS["deposit_required"]):
        deposit_required = True

    lease_match = LEASE_MONTHS_PATTERN.search(text)
    min_lease_months = int(lease_match.group(1)) if lease_match else None
    rooms = extract_rooms(title, description)

    return {
        "property_type": property_type,
        "rooms": rooms,
        "is_new_building": _matches_any(text, POSITIVE_PATTERNS["is_new_building"]),
        "furnished": furnished,
        "heating_type": heating_type,
        "has_elevator": True if _matches_any(text, POSITIVE_PATTERNS["has_elevator"]) else None,
        "has_parking": True if _matches_any(text, POSITIVE_PATTERNS["has_parking"]) else None,
        "has_balcony": True if _matches_any(text, POSITIVE_PATTERNS["has_balcony"]) else None,
        "internet_included": True if _matches_any(text, POSITIVE_PATTERNS["internet_included"]) else None,
        "utilities_included": True if _matches_any(text, POSITIVE_PATTERNS["utilities_included"]) else None,
        "min_lease_months": min_lease_months,
        "deposit_required": deposit_required,
    }


def passes_soft_filter(f, attrs: dict) -> bool:
    checks = [
        (f.furnished_only, attrs["furnished"], lambda req, val: not req or val is not False),
        (f.is_new_building, attrs["is_new_building"], lambda req, val: not req or val is not False),
        (f.heating_type, attrs["heating_type"], lambda req, val: not req or val is None or val == req),
        (f.has_elevator, attrs["has_elevator"], lambda req, val: not req or val is not False),
        (f.has_parking, attrs["has_parking"], lambda req, val: not req or val is not False),
        (f.has_balcony, attrs["has_balcony"], lambda req, val: not req or val is not False),
        (f.internet_included, attrs["internet_included"], lambda req, val: not req or val is not False),
        (f.utilities_included, attrs["utilities_included"], lambda req, val: not req or val is not False),
    ]
    for requirement, value, check in checks:
        if requirement and not check(requirement, value):
            return False

    if f.property_types and attrs["property_type"] and attrs["property_type"] not in f.property_types:
        return False

    if f.deposit_required is not None and attrs["deposit_required"] is not None:
        if f.deposit_required != attrs["deposit_required"]:
            return False

    if f.min_lease_months and attrs["min_lease_months"]:
        if attrs["min_lease_months"] > f.min_lease_months:
            return False

    return True
